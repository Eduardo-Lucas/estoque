import pytest
from rest_framework.authtoken.models import Token
from rest_framework.test import APIClient

from contas.models import Usuario
from estoque.models import Categoria, Fornecedor, Produto, SaldoEstoque
from estoque.services import ServicoEstoque


@pytest.fixture
def usuario(db):
    return Usuario.objects.create_user(email='eduardo@example.com', password='senha-forte-123')


@pytest.fixture
def api_client(usuario):
    token, _ = Token.objects.get_or_create(user=usuario)
    client = APIClient()
    client.credentials(HTTP_AUTHORIZATION=f'Token {token.key}')
    return client


@pytest.fixture
def empresa(db):
    """A empresa 'padrão' já vem semeada por migration — os testes reaproveitam
    essa mesma linha, já que hoje o sistema todo assume uma empresa só."""
    return ServicoEstoque.get_empresa_padrao()


@pytest.fixture
def deposito(empresa):
    return ServicoEstoque.get_deposito_padrao(empresa)


@pytest.fixture
def categoria(empresa):
    return Categoria.objects.create(empresa=empresa, nome='Ferragens', descricao='Parafusos e afins')


@pytest.fixture
def fornecedor(empresa):
    return Fornecedor.objects.create(empresa=empresa, nome='Distribuidora ABC', email='contato@abc.com')


@pytest.fixture
def produto(empresa, categoria, fornecedor, deposito):
    produto = Produto.objects.create(
        empresa=empresa,
        nome='Parafuso 10mm',
        sku='PRF-001',
        categoria=categoria,
        fornecedor=fornecedor,
        estoque_minimo=10,
        preco_custo_referencia='1.00',
        preco='2.50',
    )
    # Saldo inicial de teste é escrito direto (sem Movimentacao/ledger), do
    # mesmo jeito que a fixture antiga só setava produto.quantidade=100 —
    # é estado de partida do teste, não um evento de negócio a auditar.
    SaldoEstoque.objects.create(empresa=empresa, produto=produto, deposito=deposito, quantidade=100)
    return produto
