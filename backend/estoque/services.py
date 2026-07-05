"""Ponto único de escrita de estoque.

Todo ajuste de saldo — requisição, devolução, compra ou ajuste manual de
inventário — passa por `ServicoEstoque.registrar_movimentacao`, que grava a
`Movimentacao` (ledger, imutável) e atualiza o `SaldoEstoque` (cache de
leitura) na mesma transação, com `select_for_update` para evitar a condição
de corrida que existia na leitura-e-gravação direta de `Produto.quantidade`.
"""

from decimal import Decimal

from django.db import transaction

from .models import Deposito, Empresa, Movimentacao, SaldoEstoque

CNPJ_EMPRESA_PADRAO = '00000000000000'
CODIGO_DEPOSITO_PADRAO = 'PADRAO'

TIPOS_ENTRADA = {Movimentacao.DEVOLUCAO, Movimentacao.COMPRA, Movimentacao.AJUSTE_POSITIVO}
TIPOS_SAIDA = {Movimentacao.REQUISICAO, Movimentacao.AJUSTE_NEGATIVO}


class SaldoInsuficienteError(Exception):
    """Levantada quando uma saída deixaria o saldo negativo.

    Nesta PR a regra é rígida (sem override por empresa/produto) — isso só
    fica parametrizável quando `ConfiguracaoEstoque` existir."""

    def __init__(self, mensagem):
        super().__init__(mensagem)
        self.mensagem = mensagem


class ServicoEstoque:
    @staticmethod
    def get_empresa_padrao():
        return Empresa.objects.get(cnpj=CNPJ_EMPRESA_PADRAO)

    @staticmethod
    def get_deposito_padrao(empresa=None):
        empresa = empresa or ServicoEstoque.get_empresa_padrao()
        return Deposito.objects.get(empresa=empresa, codigo=CODIGO_DEPOSITO_PADRAO)

    @staticmethod
    def saldo_disponivel(produto, deposito=None):
        deposito = deposito or ServicoEstoque.get_deposito_padrao(produto.empresa)
        saldo = SaldoEstoque.objects.filter(produto=produto, deposito=deposito).first()
        return saldo.quantidade if saldo else Decimal('0.000')

    @staticmethod
    def registrar_movimentacao(
        *, produto, tipo, quantidade, deposito=None, custo_unitario=None,
        solicitante='', observacao='',
    ):
        empresa = produto.empresa
        deposito = deposito or ServicoEstoque.get_deposito_padrao(empresa)
        quantidade = Decimal(quantidade)

        with transaction.atomic():
            saldo, _criado = SaldoEstoque.objects.select_for_update().get_or_create(
                produto=produto, deposito=deposito, defaults={'empresa': empresa},
            )

            if tipo in TIPOS_SAIDA:
                if quantidade > saldo.quantidade:
                    raise SaldoInsuficienteError(
                        f'Estoque insuficiente para "{produto.nome}". Disponível: {saldo.quantidade}.'
                    )
                saldo.quantidade -= quantidade
            else:
                nova_quantidade = saldo.quantidade + quantidade
                if custo_unitario is not None and nova_quantidade > 0:
                    custo_unitario = Decimal(custo_unitario)
                    saldo.custo_medio = (
                        (saldo.quantidade * saldo.custo_medio) + (quantidade * custo_unitario)
                    ) / nova_quantidade
                saldo.quantidade = nova_quantidade

            saldo.save(update_fields=['quantidade', 'custo_medio', 'atualizado_em'])

            movimentacao = Movimentacao.objects.create(
                empresa=empresa,
                produto=produto,
                deposito=deposito,
                tipo=tipo,
                quantidade=quantidade,
                custo_unitario=custo_unitario,
                solicitante=solicitante,
                observacao=observacao,
            )

        return movimentacao

    @staticmethod
    def definir_saldo_inicial(produto, quantidade, *, deposito=None, observacao=''):
        """Usado pela importação de CSV: reconcilia o saldo atual com o valor
        da planilha através de um ajuste de inventário (com histórico),
        em vez de sobrescrever o saldo silenciosamente."""
        deposito = deposito or ServicoEstoque.get_deposito_padrao(produto.empresa)
        quantidade_alvo = Decimal(quantidade)
        delta = quantidade_alvo - ServicoEstoque.saldo_disponivel(produto, deposito)

        if delta == 0:
            return None

        tipo = Movimentacao.AJUSTE_POSITIVO if delta > 0 else Movimentacao.AJUSTE_NEGATIVO
        return ServicoEstoque.registrar_movimentacao(
            produto=produto,
            tipo=tipo,
            quantidade=abs(delta),
            deposito=deposito,
            solicitante='importação CSV',
            observacao=observacao or 'Ajuste por importação de CSV',
        )
