import pytest
from django.contrib.auth.models import User
from rest_framework.authtoken.models import Token
from rest_framework.test import APIClient

from estoque.models import Categoria, Fornecedor, Produto


@pytest.fixture
def usuario(db):
    return User.objects.create_user(username='eduardo', password='senha-forte-123')


@pytest.fixture
def api_client(usuario):
    token, _ = Token.objects.get_or_create(user=usuario)
    client = APIClient()
    client.credentials(HTTP_AUTHORIZATION=f'Token {token.key}')
    return client


@pytest.fixture
def categoria(db):
    return Categoria.objects.create(nome='Ferragens', descricao='Parafusos e afins')


@pytest.fixture
def fornecedor(db):
    return Fornecedor.objects.create(nome='Distribuidora ABC', email='contato@abc.com')


@pytest.fixture
def produto(db, categoria, fornecedor):
    return Produto.objects.create(
        nome='Parafuso 10mm',
        sku='PRF-001',
        categoria=categoria,
        fornecedor=fornecedor,
        quantidade=100,
        estoque_minimo=10,
        preco_custo='1.00',
        preco='2.50',
    )
