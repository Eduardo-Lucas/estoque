from decimal import Decimal

import pytest
from django.core.exceptions import ValidationError

from estoque.models import CamadaCusto, ConfiguracaoEstoque, Deposito, Empresa, MetodoValoracao, Movimentacao, Produto, SaldoEstoque
from estoque.services import SaldoInsuficienteError, ServicoEstoque

pytestmark = pytest.mark.django_db


@pytest.fixture
def produto_zerado(empresa, categoria, fornecedor):
    """Produto sem saldo pré-existente, pra deixar as contas de custeio exatas
    (a fixture `produto` já nasce com 100 unidades escritas direto, sem
    CamadaCusto — não serve pra testar FIFO)."""
    return Produto.objects.create(
        empresa=empresa, nome='Produto Zerado', sku='ZERO-001',
        categoria=categoria, fornecedor=fornecedor, preco='1.00',
    )


def _usar_metodo(empresa, metodo):
    config = empresa.config_estoque
    config.metodo_valoracao = metodo
    config.save(update_fields=['metodo_valoracao'])


class TestMediaMovel:
    def test_entradas_sucessivas_ponderam_o_custo_medio(self, produto_zerado, usuario):
        ServicoEstoque.registrar_entrada(produto=produto_zerado, quantidade=10, custo_unitario='2.00', usuario=usuario)
        ServicoEstoque.registrar_entrada(produto=produto_zerado, quantidade=10, custo_unitario='4.00', usuario=usuario)

        saldo = produto_zerado.saldos.get(lote__isnull=True)
        assert saldo.quantidade == 20
        assert saldo.custo_medio == Decimal('3.0000')

    def test_saida_usa_o_custo_medio_vigente(self, produto_zerado, usuario):
        ServicoEstoque.registrar_entrada(produto=produto_zerado, quantidade=10, custo_unitario='2.00', usuario=usuario)
        ServicoEstoque.registrar_entrada(produto=produto_zerado, quantidade=10, custo_unitario='4.00', usuario=usuario)

        movimento = ServicoEstoque.registrar_saida(produto=produto_zerado, quantidade=5, solicitante='Ana', usuario=usuario)

        assert movimento.custo_unitario == Decimal('3.0000')
        assert ServicoEstoque.saldo_disponivel(produto_zerado) == 15


class TestFIFO:
    def test_entrada_cria_camada_de_custo(self, produto_zerado, usuario):
        _usar_metodo(produto_zerado.empresa, MetodoValoracao.FIFO)

        ServicoEstoque.registrar_entrada(produto=produto_zerado, quantidade=10, custo_unitario='2.00', usuario=usuario)

        camada = CamadaCusto.objects.get(produto=produto_zerado)
        assert camada.quantidade_original == 10
        assert camada.quantidade_disponivel == 10
        assert camada.custo_unitario == Decimal('2.0000')

    def test_saida_consome_camadas_mais_antigas_primeiro(self, produto_zerado, usuario):
        _usar_metodo(produto_zerado.empresa, MetodoValoracao.FIFO)

        ServicoEstoque.registrar_entrada(produto=produto_zerado, quantidade=10, custo_unitario='2.00', usuario=usuario)
        ServicoEstoque.registrar_entrada(produto=produto_zerado, quantidade=10, custo_unitario='5.00', usuario=usuario)

        movimento = ServicoEstoque.registrar_saida(produto=produto_zerado, quantidade=15, solicitante='Ana', usuario=usuario)

        # consome as 10 unidades a 2.00 + 5 unidades a 5.00 = 45 / 15 = 3.00
        assert movimento.custo_unitario == Decimal('3.0000')
        assert ServicoEstoque.saldo_disponivel(produto_zerado) == 5

        camada_antiga, camada_nova = CamadaCusto.objects.filter(produto=produto_zerado).order_by('criado_em')
        assert camada_antiga.quantidade_disponivel == 0
        assert camada_nova.quantidade_disponivel == 5


class TestCustoPadrao:
    def test_entrada_grava_saldo_pelo_custo_padrao_mesmo_com_preco_de_compra_diferente(self, produto_zerado, usuario):
        # A entrada mantém o preço de compra real no próprio movimento (útil
        # pra análise de variação de preço), mas o saldo é sempre valorizado
        # pelo custo padrão do produto — é isso que EstrategiaCustoPadrao
        # garante ao gravar `saldo.custo_medio` a partir de preco_custo_referencia.
        _usar_metodo(produto_zerado.empresa, MetodoValoracao.CUSTO_PADRAO)
        produto_zerado.preco_custo_referencia = Decimal('7.50')
        produto_zerado.save(update_fields=['preco_custo_referencia'])

        entrada = ServicoEstoque.registrar_entrada(produto=produto_zerado, quantidade=10, custo_unitario='999.00', usuario=usuario)
        assert entrada.custo_unitario == Decimal('999.0000')  # preço de compra real, preservado no movimento
        assert produto_zerado.saldos.get(lote__isnull=True).custo_medio == Decimal('7.5000')

        saida = ServicoEstoque.registrar_saida(produto=produto_zerado, quantidade=4, solicitante='Ana', usuario=usuario)
        assert saida.custo_unitario == Decimal('7.5000')  # saída sempre relia pelo custo padrão vigente


class TestPermiteEstoqueNegativo:
    def test_saida_alem_do_saldo_e_bloqueada_por_padrao(self, produto_zerado, usuario):
        with pytest.raises(SaldoInsuficienteError):
            ServicoEstoque.registrar_saida(produto=produto_zerado, quantidade=1, solicitante='Ana', usuario=usuario)

    def test_override_no_produto_permite_saldo_negativo(self, produto_zerado, usuario):
        produto_zerado.permite_estoque_negativo = True
        produto_zerado.save(update_fields=['permite_estoque_negativo'])

        movimento = ServicoEstoque.registrar_saida(produto=produto_zerado, quantidade=5, solicitante='Ana', usuario=usuario)

        assert movimento.tipo == Movimentacao.REQUISICAO
        assert ServicoEstoque.saldo_disponivel(produto_zerado) == -5


class TestControlaLote:
    def test_produto_com_controle_de_lote_exige_lote_na_movimentacao(self, produto_zerado, usuario):
        produto_zerado.controla_lote = True
        produto_zerado.save(update_fields=['controla_lote'])

        with pytest.raises(ValidationError):
            ServicoEstoque.registrar_entrada(produto=produto_zerado, quantidade=10, custo_unitario='1.00', usuario=usuario)


class TestUsuarioObrigatorio:
    """Toda movimentação precisa do log de quem a lançou — reforçado tanto na
    assinatura do serviço (TypeError sem o kwarg) quanto no banco (usuario
    é NOT NULL em Movimentacao)."""

    def test_registrar_entrada_sem_usuario_falha(self, produto_zerado):
        with pytest.raises(TypeError):
            ServicoEstoque.registrar_entrada(produto=produto_zerado, quantidade=10, custo_unitario='1.00')

    def test_registrar_saida_sem_usuario_falha(self, produto_zerado):
        with pytest.raises(TypeError):
            ServicoEstoque.registrar_saida(produto=produto_zerado, quantidade=1, solicitante='Ana')

    def test_definir_saldo_inicial_sem_usuario_falha(self, produto_zerado):
        with pytest.raises(TypeError):
            ServicoEstoque.definir_saldo_inicial(produto_zerado, 10)


class TestComparativoFifoVsMediaMovel:
    """Mesmo cenário (duas entradas a custos diferentes, uma saída que atravessa
    a fronteira entre as duas) rodado com cada estratégia, pra deixar explícito
    que elas divergem tanto no custo da saída quanto no que fica em SaldoEstoque."""

    def _rodar_cenario(self, metodo, usuario):
        empresa = Empresa.objects.create(razao_social=f'Teste {metodo}', cnpj=f'CNPJ-{metodo}')
        ConfiguracaoEstoque.objects.create(empresa=empresa, metodo_valoracao=metodo)
        deposito = Deposito.objects.create(empresa=empresa, codigo='PADRAO', nome='Depósito Padrão')
        produto = Produto.objects.create(empresa=empresa, nome='Parafuso M8', sku='PRF-M8')

        ServicoEstoque.registrar_entrada(
            empresa=empresa, produto=produto, deposito=deposito, usuario=usuario,
            quantidade=Decimal('10'), custo_unitario=Decimal('10.00'),
        )
        ServicoEstoque.registrar_entrada(
            empresa=empresa, produto=produto, deposito=deposito, usuario=usuario,
            quantidade=Decimal('10'), custo_unitario=Decimal('14.00'),
        )
        saida = ServicoEstoque.registrar_saida(
            empresa=empresa, produto=produto, deposito=deposito, usuario=usuario, quantidade=Decimal('12'),
        )
        saida.refresh_from_db()  # custo_unitario é quantizado só ao salvar no banco
        saldo = SaldoEstoque.objects.get(empresa=empresa, produto=produto, deposito=deposito, lote=None)
        return saida, saldo

    def test_fifo_consome_a_camada_mais_antiga_e_depois_a_seguinte(self, usuario):
        saida, saldo = self._rodar_cenario('fifo', usuario)

        # 10 un a R$10,00 + 2 un a R$14,00 = R$128,00 / 12 = R$10,6667
        assert saida.custo_unitario == Decimal('10.6667')
        assert saldo.quantidade == Decimal('8.000')
        # FIFO não mantém custo médio corrente em SaldoEstoque — só as camadas
        # (CamadaCusto) sabem o custo real; isso fica 0 de propósito.
        assert saldo.custo_medio == Decimal('0.0000')

    def test_media_movel_pondera_as_duas_entradas_antes_da_saida(self, usuario):
        saida, saldo = self._rodar_cenario('media_movel', usuario)

        # custo médio após as entradas: (10*10 + 10*14) / 20 = R$12,00
        assert saida.custo_unitario == Decimal('12.0000')
        assert saldo.quantidade == Decimal('8.000')
        assert saldo.custo_medio == Decimal('12.0000')
