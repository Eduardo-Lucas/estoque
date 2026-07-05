"""Motor de Custeio e Serviço de Movimentação — app `estoque`.

Ponto único de entrada para alterar estoque. Nunca crie uma `Movimentacao`
diretamente fora daqui (inclusive no processamento de NF-e) — ou o saldo
cacheado e as camadas de custo ficam inconsistentes.

A estratégia de custeio usada em cada chamada é resolvida a partir de
`empresa.config_estoque.metodo_valoracao` (`ConfiguracaoEstoque`), o que
permite Simples Nacional/Lucro Presumido/Lucro Real/MEI conviverem com
média móvel, FIFO ou custo padrão sem branch de código aqui.
"""

from abc import ABC, abstractmethod
from decimal import Decimal

from django.db import transaction
from django.db.models import F

from .models import CamadaCusto, Deposito, Empresa, Movimentacao, Produto, SaldoEstoque

CNPJ_EMPRESA_PADRAO = '00000000000000'
CODIGO_DEPOSITO_PADRAO = 'PADRAO'

# Precisão dos campos Movimentacao.quantidade/custo_unitario — quantizado aqui
# porque full_clean() rejeita valores com mais casas decimais que o campo
# (ex: quantidade de NF-e vem com 4 casas, o campo aceita 3).
_PRECISAO_QUANTIDADE = Decimal('0.001')
_PRECISAO_CUSTO = Decimal('0.0001')

TIPOS_ENTRADA = {Movimentacao.DEVOLUCAO, Movimentacao.COMPRA, Movimentacao.AJUSTE_POSITIVO}
TIPOS_SAIDA = {Movimentacao.REQUISICAO, Movimentacao.AJUSTE_NEGATIVO}


class SaldoInsuficienteError(Exception):
    def __init__(self, mensagem):
        super().__init__(mensagem)
        self.mensagem = mensagem


# ---------------------------------------------------------------------------
# Estratégias de custeio
# ---------------------------------------------------------------------------

class EstrategiaCusteio(ABC):
    @abstractmethod
    def processar_entrada(self, movimento: Movimentacao, saldo: SaldoEstoque) -> None: ...

    @abstractmethod
    def processar_saida(self, movimento: Movimentacao, saldo: SaldoEstoque) -> Decimal: ...


class EstrategiaMediaMovel(EstrategiaCusteio):
    def processar_entrada(self, movimento, saldo):
        qtd_atual, custo_atual = saldo.quantidade, saldo.custo_medio
        qtd_nova, custo_novo = movimento.quantidade, (movimento.custo_unitario or Decimal('0'))

        valor_total = (qtd_atual * custo_atual) + (qtd_nova * custo_novo)
        qtd_total = qtd_atual + qtd_nova

        saldo.custo_medio = (valor_total / qtd_total) if qtd_total > 0 else Decimal('0')
        saldo.quantidade = qtd_total
        saldo.save(update_fields=['custo_medio', 'quantidade', 'atualizado_em'])

    def processar_saida(self, movimento, saldo):
        custo_total = saldo.custo_medio * movimento.quantidade
        saldo.quantidade = F('quantidade') - movimento.quantidade
        saldo.save(update_fields=['quantidade', 'atualizado_em'])
        saldo.refresh_from_db()
        movimento.custo_unitario = saldo.custo_medio
        return custo_total


class EstrategiaFIFO(EstrategiaCusteio):
    def processar_entrada(self, movimento, saldo):
        CamadaCusto.objects.create(
            produto=movimento.produto, deposito=movimento.deposito, lote=movimento.lote,
            movimento_origem=movimento, quantidade_original=movimento.quantidade,
            quantidade_disponivel=movimento.quantidade,
            custo_unitario=movimento.custo_unitario or Decimal('0'),
        )
        saldo.quantidade = F('quantidade') + movimento.quantidade
        saldo.save(update_fields=['quantidade', 'atualizado_em'])

    def processar_saida(self, movimento, saldo):
        camadas = (
            CamadaCusto.objects.select_for_update()
            .filter(produto=movimento.produto, deposito=movimento.deposito,
                     lote=movimento.lote, quantidade_disponivel__gt=0)
            .order_by('criado_em')
        )
        restante, custo_total = movimento.quantidade, Decimal('0')
        ultima_camada = None
        for camada in camadas:
            if restante <= 0:
                break
            consumido = min(camada.quantidade_disponivel, restante)
            custo_total += consumido * camada.custo_unitario
            camada.quantidade_disponivel -= consumido
            camada.save(update_fields=['quantidade_disponivel'])
            restante -= consumido
            ultima_camada = camada

        if restante > 0:
            custo_total += restante * (ultima_camada.custo_unitario if ultima_camada else Decimal('0'))

        saldo.quantidade = F('quantidade') - movimento.quantidade
        saldo.save(update_fields=['quantidade', 'atualizado_em'])
        movimento.custo_unitario = (custo_total / movimento.quantidade) if movimento.quantidade else Decimal('0')
        return custo_total


class EstrategiaCustoPadrao(EstrategiaCusteio):
    def processar_entrada(self, movimento, saldo):
        saldo.quantidade = F('quantidade') + movimento.quantidade
        saldo.custo_medio = movimento.produto.preco_custo_referencia or Decimal('0')
        saldo.save(update_fields=['quantidade', 'custo_medio', 'atualizado_em'])

    def processar_saida(self, movimento, saldo):
        custo_padrao = movimento.produto.preco_custo_referencia or Decimal('0')
        saldo.quantidade = F('quantidade') - movimento.quantidade
        saldo.save(update_fields=['quantidade', 'atualizado_em'])
        movimento.custo_unitario = custo_padrao
        return custo_padrao * movimento.quantidade


_ESTRATEGIAS = {
    'media_movel': EstrategiaMediaMovel,
    'fifo': EstrategiaFIFO,
    'custo_padrao': EstrategiaCustoPadrao,
}


def obter_estrategia(config) -> EstrategiaCusteio:
    classe = _ESTRATEGIAS.get(config.metodo_valoracao)
    if classe is None:
        raise NotImplementedError(f"Método '{config.metodo_valoracao}' sem estratégia registrada.")
    return classe()


# ---------------------------------------------------------------------------
# Serviço de movimentação
# ---------------------------------------------------------------------------

class ServicoEstoque:
    @staticmethod
    def get_empresa_padrao() -> Empresa:
        return Empresa.objects.get(cnpj=CNPJ_EMPRESA_PADRAO)

    @staticmethod
    def get_deposito_padrao(empresa=None) -> Deposito:
        empresa = empresa or ServicoEstoque.get_empresa_padrao()
        return Deposito.objects.get(empresa=empresa, codigo=CODIGO_DEPOSITO_PADRAO)

    @staticmethod
    def saldo_disponivel(produto, deposito=None) -> Decimal:
        deposito = deposito or ServicoEstoque.get_deposito_padrao(produto.empresa)
        saldo = SaldoEstoque.objects.filter(produto=produto, deposito=deposito, lote__isnull=True).first()
        return saldo.quantidade_disponivel if saldo else Decimal('0.000')

    @staticmethod
    @transaction.atomic
    def registrar_entrada(*, produto: Produto, quantidade: Decimal, custo_unitario: Decimal = None,
                           empresa=None, deposito=None, usuario=None, lote=None,
                           tipo=Movimentacao.COMPRA, observacao='') -> Movimentacao:
        empresa = empresa or produto.empresa
        deposito = deposito or ServicoEstoque.get_deposito_padrao(empresa)
        quantidade = Decimal(quantidade).quantize(_PRECISAO_QUANTIDADE)
        if custo_unitario is not None:
            custo_unitario = Decimal(custo_unitario).quantize(_PRECISAO_CUSTO)

        saldo, _criado = SaldoEstoque.objects.select_for_update().get_or_create(
            empresa=empresa, produto=produto, deposito=deposito, lote=lote,
        )
        movimento = Movimentacao.objects.create(
            empresa=empresa, produto=produto, deposito=deposito, lote=lote,
            tipo=tipo, quantidade=quantidade, custo_unitario=custo_unitario,
            usuario=usuario, observacao=observacao,
        )
        movimento.full_clean(exclude=['usuario'])
        estrategia = obter_estrategia(empresa.config_estoque)
        estrategia.processar_entrada(movimento, saldo)
        return movimento

    @staticmethod
    @transaction.atomic
    def registrar_saida(*, produto: Produto, quantidade: Decimal, empresa=None, deposito=None,
                         usuario=None, lote=None, tipo=Movimentacao.REQUISICAO,
                         observacao='', solicitante='') -> Movimentacao:
        empresa = empresa or produto.empresa
        deposito = deposito or ServicoEstoque.get_deposito_padrao(empresa)
        quantidade = Decimal(quantidade).quantize(_PRECISAO_QUANTIDADE)

        saldo, _criado = SaldoEstoque.objects.select_for_update().get_or_create(
            empresa=empresa, produto=produto, deposito=deposito, lote=lote,
        )
        if not produto.resolve_permite_estoque_negativo() and saldo.quantidade_disponivel < quantidade:
            raise SaldoInsuficienteError(
                f'Estoque insuficiente para "{produto.nome}". Disponível: {saldo.quantidade_disponivel}.'
            )

        movimento = Movimentacao.objects.create(
            empresa=empresa, produto=produto, deposito=deposito, lote=lote,
            tipo=tipo, quantidade=quantidade, usuario=usuario,
            observacao=observacao, solicitante=solicitante,
        )
        movimento.full_clean(exclude=['usuario'])
        estrategia = obter_estrategia(empresa.config_estoque)
        estrategia.processar_saida(movimento, saldo)
        movimento.save(update_fields=['custo_unitario'])
        return movimento

    @staticmethod
    def definir_saldo_inicial(produto, quantidade, *, deposito=None, observacao='', usuario=None):
        """Usado pela importação de CSV: reconcilia o saldo atual com o valor
        da planilha através de um ajuste de inventário (com histórico), em
        vez de sobrescrever o saldo silenciosamente."""
        deposito = deposito or ServicoEstoque.get_deposito_padrao(produto.empresa)
        quantidade_alvo = Decimal(quantidade)
        delta = quantidade_alvo - ServicoEstoque.saldo_disponivel(produto, deposito)

        if delta == 0:
            return None

        observacao = observacao or 'Ajuste por importação de CSV'
        if delta > 0:
            return ServicoEstoque.registrar_entrada(
                produto=produto, quantidade=delta, custo_unitario=None, deposito=deposito,
                usuario=usuario, tipo=Movimentacao.AJUSTE_POSITIVO, observacao=observacao,
            )
        return ServicoEstoque.registrar_saida(
            produto=produto, quantidade=abs(delta), deposito=deposito, usuario=usuario,
            tipo=Movimentacao.AJUSTE_NEGATIVO, solicitante='importação CSV', observacao=observacao,
        )
