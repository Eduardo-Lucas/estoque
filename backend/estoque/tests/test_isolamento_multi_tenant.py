"""A garantia real que todo o resto desta entrega existe pra dar: dados de
uma empresa não podem aparecer, nem ser referenciados, por outra."""

import pytest
from django.urls import reverse
from rest_framework import status
from rest_framework.authtoken.models import Token
from rest_framework.test import APIClient

from contas.models import Usuario
from estoque.models import Categoria, ConfiguracaoEstoque, Deposito, Empresa, Fornecedor, Produto

pytestmark = pytest.mark.django_db


def _client_para(usuario):
    token, _ = Token.objects.get_or_create(user=usuario)
    client = APIClient()
    client.credentials(HTTP_AUTHORIZATION=f'Token {token.key}')
    return client


@pytest.fixture
def empresa_b():
    empresa = Empresa.objects.create(razao_social='Empresa B', cnpj='99888777000166')
    ConfiguracaoEstoque.objects.create(empresa=empresa)
    Deposito.objects.create(empresa=empresa, codigo='PADRAO', nome='Depósito Padrão')
    return empresa


@pytest.fixture
def usuario_b(empresa_b):
    return Usuario.objects.create_user(email='usuaria@empresab.com', password='senha-forte-123', empresa=empresa_b)


@pytest.fixture
def client_b(usuario_b):
    return _client_para(usuario_b)


class TestIsolamentoEntreEmpresas:
    def test_produtos_de_uma_empresa_nao_aparecem_para_outra(self, api_client, produto, client_b, empresa_b):
        categoria_b = Categoria.objects.create(empresa=empresa_b, nome='Categoria B')
        fornecedor_b = Fornecedor.objects.create(empresa=empresa_b, nome='Fornecedor B')
        produto_b = Produto.objects.create(
            empresa=empresa_b, nome='Produto da Empresa B', categoria=categoria_b, fornecedor=fornecedor_b,
        )

        resposta_a = api_client.get(reverse('produto-list'))
        resposta_b = client_b.get(reverse('produto-list'))

        nomes_a = {p['nome'] for p in resposta_a.data['results']}
        nomes_b = {p['nome'] for p in resposta_b.data['results']}

        assert produto.nome in nomes_a
        assert produto.nome not in nomes_b
        assert produto_b.nome in nomes_b
        assert produto_b.nome not in nomes_a

    def test_categorias_e_fornecedores_tambem_sao_isolados(self, api_client, categoria, fornecedor, client_b, empresa_b):
        Categoria.objects.create(empresa=empresa_b, nome='Categoria B')
        Fornecedor.objects.create(empresa=empresa_b, nome='Fornecedor B')

        categorias_b = {c['nome'] for c in client_b.get(reverse('categoria-list')).data['results']}
        fornecedores_b = {f['nome'] for f in client_b.get(reverse('fornecedor-list')).data['results']}

        assert categoria.nome not in categorias_b
        assert fornecedor.nome not in fornecedores_b

    def test_nao_e_possivel_criar_produto_referenciando_categoria_de_outra_empresa(self, api_client, empresa_b):
        categoria_b = Categoria.objects.create(empresa=empresa_b, nome='Categoria B')

        resposta = api_client.post(reverse('produto-list'), {
            'nome': 'Produto Suspeito', 'preco': '10.00', 'categoria': categoria_b.id,
        })

        assert resposta.status_code == status.HTTP_400_BAD_REQUEST

    def test_nao_e_possivel_registrar_movimentacao_em_produto_de_outra_empresa(self, api_client, empresa_b):
        produto_b = Produto.objects.create(empresa=empresa_b, nome='Produto B')

        resposta = api_client.post(reverse('movimentacao-list'), {
            'produto': produto_b.id, 'tipo': 'AJUSTE_POSITIVO', 'quantidade': 5,
        })

        assert resposta.status_code == status.HTTP_400_BAD_REQUEST

    def test_usuario_sem_empresa_recebe_403(self):
        usuario_sem_empresa = Usuario.objects.create_user(email='orfa@example.com', password='senha-forte-123')
        client = _client_para(usuario_sem_empresa)

        resposta = client.get(reverse('produto-list'))

        assert resposta.status_code == status.HTTP_403_FORBIDDEN
