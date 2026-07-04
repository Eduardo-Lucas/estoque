import pytest
from django.urls import reverse
from rest_framework import status

from estoque.models import Movimentacao, Produto

pytestmark = pytest.mark.django_db


class TestMovimentacaoApi:
    def test_requisicao_reduz_estoque(self, api_client, produto):
        quantidade_inicial = produto.quantidade
        resposta = api_client.post(reverse('movimentacao-list'), {
            'produto': produto.id,
            'tipo': Movimentacao.REQUISICAO,
            'quantidade': 10,
            'solicitante': 'Ana',
        })
        assert resposta.status_code == status.HTTP_201_CREATED
        produto.refresh_from_db()
        assert produto.quantidade == quantidade_inicial - 10

    def test_devolucao_aumenta_estoque(self, api_client, produto):
        quantidade_inicial = produto.quantidade
        resposta = api_client.post(reverse('movimentacao-list'), {
            'produto': produto.id,
            'tipo': Movimentacao.DEVOLUCAO,
            'quantidade': 7,
            'solicitante': 'Bia',
        })
        assert resposta.status_code == status.HTTP_201_CREATED
        produto.refresh_from_db()
        assert produto.quantidade == quantidade_inicial + 7

    def test_requisicao_maior_que_estoque_e_bloqueada(self, api_client, produto):
        quantidade_inicial = produto.quantidade
        resposta = api_client.post(reverse('movimentacao-list'), {
            'produto': produto.id,
            'tipo': Movimentacao.REQUISICAO,
            'quantidade': quantidade_inicial + 1,
            'solicitante': 'Ana',
        })
        assert resposta.status_code == status.HTTP_400_BAD_REQUEST
        produto.refresh_from_db()
        assert produto.quantidade == quantidade_inicial
        assert Movimentacao.objects.count() == 0

    def test_requisicao_igual_ao_estoque_e_permitida(self, api_client, produto):
        quantidade_inicial = produto.quantidade
        resposta = api_client.post(reverse('movimentacao-list'), {
            'produto': produto.id,
            'tipo': Movimentacao.REQUISICAO,
            'quantidade': quantidade_inicial,
            'solicitante': 'Ana',
        })
        assert resposta.status_code == status.HTTP_201_CREATED
        produto.refresh_from_db()
        assert produto.quantidade == 0

    def test_listagem_traz_nome_do_produto(self, api_client, produto):
        Movimentacao.objects.create(
            produto=produto, tipo=Movimentacao.REQUISICAO, quantidade=1, solicitante='Ana',
        )
        resposta = api_client.get(reverse('movimentacao-list'))
        assert resposta.data['results'][0]['produto_nome'] == produto.nome

    def test_filtro_por_produto_retorna_apenas_suas_movimentacoes(self, api_client, produto, categoria, fornecedor):
        outro_produto = Produto.objects.create(nome='Outro produto', categoria=categoria, fornecedor=fornecedor, quantidade=10)
        Movimentacao.objects.create(produto=produto, tipo=Movimentacao.REQUISICAO, quantidade=1, solicitante='Ana')
        Movimentacao.objects.create(produto=outro_produto, tipo=Movimentacao.REQUISICAO, quantidade=1, solicitante='Bia')

        resposta = api_client.get(reverse('movimentacao-list'), {'produto': produto.id})

        assert resposta.data['count'] == 1
        assert resposta.data['results'][0]['produto'] == produto.id

    def test_sem_filtro_retorna_movimentacoes_de_todos_os_produtos(self, api_client, produto, categoria, fornecedor):
        outro_produto = Produto.objects.create(nome='Outro produto', categoria=categoria, fornecedor=fornecedor, quantidade=10)
        Movimentacao.objects.create(produto=produto, tipo=Movimentacao.REQUISICAO, quantidade=1, solicitante='Ana')
        Movimentacao.objects.create(produto=outro_produto, tipo=Movimentacao.REQUISICAO, quantidade=1, solicitante='Bia')

        resposta = api_client.get(reverse('movimentacao-list'))

        assert resposta.data['count'] == 2
