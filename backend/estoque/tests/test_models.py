import pytest
from django.db import IntegrityError

from estoque.models import Categoria, Fornecedor, Movimentacao, Produto


pytestmark = pytest.mark.django_db


class TestCategoria:
    def test_str_retorna_nome(self, categoria):
        assert str(categoria) == 'Ferragens'

    def test_nome_e_unico(self, categoria):
        with pytest.raises(IntegrityError):
            Categoria.objects.create(nome='Ferragens')

    def test_ordering_por_nome(self):
        Categoria.objects.create(nome='Zebra')
        Categoria.objects.create(nome='Alpha')
        nomes = list(Categoria.objects.values_list('nome', flat=True))
        assert nomes == sorted(nomes)


class TestFornecedor:
    def test_str_retorna_nome(self, fornecedor):
        assert str(fornecedor) == 'Distribuidora ABC'

    def test_nome_e_unico(self, fornecedor):
        with pytest.raises(IntegrityError):
            Fornecedor.objects.create(nome='Distribuidora ABC')

    def test_campos_de_contato_sao_opcionais(self):
        fornecedor = Fornecedor.objects.create(nome='Fornecedor Simples')
        assert fornecedor.cnpj == ''
        assert fornecedor.telefone == ''
        assert fornecedor.email == ''
        assert fornecedor.endereco == ''


class TestProduto:
    def test_str_retorna_nome(self, produto):
        assert str(produto) == 'Parafuso 10mm'

    def test_defaults(self):
        produto = Produto.objects.create(nome='Produto Simples')
        assert produto.sku is None
        assert produto.unidade_medida == Produto.UNIDADE_UNIDADE
        assert produto.quantidade == 0
        assert produto.estoque_minimo == 0
        assert produto.preco_custo == 0
        assert produto.preco == 0
        assert produto.ativo is True

    def test_nome_e_unico(self, produto):
        with pytest.raises(IntegrityError):
            Produto.objects.create(nome='Parafuso 10mm')

    def test_sku_e_unico_quando_preenchido(self, produto):
        with pytest.raises(IntegrityError):
            Produto.objects.create(nome='Outro produto', sku='PRF-001')

    def test_multiplos_produtos_podem_ter_sku_nulo(self):
        Produto.objects.create(nome='Produto A', sku=None)
        Produto.objects.create(nome='Produto B', sku=None)
        assert Produto.objects.filter(sku__isnull=True).count() == 2

    def test_remover_categoria_nao_apaga_produto(self, produto, categoria):
        categoria.delete()
        produto.refresh_from_db()
        assert produto.categoria_id is None

    def test_remover_fornecedor_nao_apaga_produto(self, produto, fornecedor):
        fornecedor.delete()
        produto.refresh_from_db()
        assert produto.fornecedor_id is None


class TestMovimentacao:
    def test_str_retorna_resumo(self, produto):
        movimentacao = Movimentacao.objects.create(
            produto=produto, tipo=Movimentacao.REQUISICAO, quantidade=5, solicitante='Ana',
        )
        assert str(movimentacao) == f'Requisição - {produto.nome} (5)'

    def test_remover_produto_remove_movimentacoes(self, produto):
        Movimentacao.objects.create(
            produto=produto, tipo=Movimentacao.REQUISICAO, quantidade=5, solicitante='Ana',
        )
        produto.delete()
        assert Movimentacao.objects.count() == 0

    def test_ordering_mais_recente_primeiro(self, produto):
        primeira = Movimentacao.objects.create(
            produto=produto, tipo=Movimentacao.REQUISICAO, quantidade=1, solicitante='Ana',
        )
        segunda = Movimentacao.objects.create(
            produto=produto, tipo=Movimentacao.DEVOLUCAO, quantidade=1, solicitante='Bia',
        )
        assert list(Movimentacao.objects.all()) == [segunda, primeira]
