from datetime import timedelta

import pytest
from django.urls import reverse
from django.utils import timezone
from rest_framework import status

from estoque.models import Movimentacao, Produto
from estoque.services import ServicoEstoque

pytestmark = pytest.mark.django_db


class TestMovimentacaoApi:
    def test_requisicao_reduz_estoque(self, api_client, produto):
        saldo_inicial = ServicoEstoque.saldo_disponivel(produto)
        resposta = api_client.post(reverse('movimentacao-list'), {
            'produto': produto.id,
            'tipo': Movimentacao.REQUISICAO,
            'quantidade': 10,
            'solicitante': 'Ana',
        })
        assert resposta.status_code == status.HTTP_201_CREATED
        assert ServicoEstoque.saldo_disponivel(produto) == saldo_inicial - 10

    def test_devolucao_aumenta_estoque(self, api_client, produto):
        saldo_inicial = ServicoEstoque.saldo_disponivel(produto)
        resposta = api_client.post(reverse('movimentacao-list'), {
            'produto': produto.id,
            'tipo': Movimentacao.DEVOLUCAO,
            'quantidade': 7,
            'solicitante': 'Bia',
        })
        assert resposta.status_code == status.HTTP_201_CREATED
        assert ServicoEstoque.saldo_disponivel(produto) == saldo_inicial + 7

    def test_requisicao_maior_que_estoque_e_bloqueada(self, api_client, produto):
        saldo_inicial = ServicoEstoque.saldo_disponivel(produto)
        resposta = api_client.post(reverse('movimentacao-list'), {
            'produto': produto.id,
            'tipo': Movimentacao.REQUISICAO,
            'quantidade': saldo_inicial + 1,
            'solicitante': 'Ana',
        })
        assert resposta.status_code == status.HTTP_400_BAD_REQUEST
        assert ServicoEstoque.saldo_disponivel(produto) == saldo_inicial
        assert Movimentacao.objects.count() == 0

    def test_requisicao_igual_ao_estoque_e_permitida(self, api_client, produto):
        saldo_inicial = ServicoEstoque.saldo_disponivel(produto)
        resposta = api_client.post(reverse('movimentacao-list'), {
            'produto': produto.id,
            'tipo': Movimentacao.REQUISICAO,
            'quantidade': saldo_inicial,
            'solicitante': 'Ana',
        })
        assert resposta.status_code == status.HTTP_201_CREATED
        assert ServicoEstoque.saldo_disponivel(produto) == 0

    def test_ajuste_positivo_aumenta_estoque_sem_limite(self, api_client, produto):
        saldo_inicial = ServicoEstoque.saldo_disponivel(produto)
        resposta = api_client.post(reverse('movimentacao-list'), {
            'produto': produto.id,
            'tipo': Movimentacao.AJUSTE_POSITIVO,
            'quantidade': 5,
            'solicitante': 'Ana',
        })
        assert resposta.status_code == status.HTTP_201_CREATED
        assert ServicoEstoque.saldo_disponivel(produto) == saldo_inicial + 5

    def test_ajuste_negativo_e_bloqueado_acima_do_saldo(self, api_client, produto):
        saldo_inicial = ServicoEstoque.saldo_disponivel(produto)
        resposta = api_client.post(reverse('movimentacao-list'), {
            'produto': produto.id,
            'tipo': Movimentacao.AJUSTE_NEGATIVO,
            'quantidade': saldo_inicial + 1,
            'solicitante': 'Ana',
        })
        assert resposta.status_code == status.HTTP_400_BAD_REQUEST
        assert ServicoEstoque.saldo_disponivel(produto) == saldo_inicial

    def test_listagem_traz_nome_do_produto(self, api_client, produto, deposito, usuario):
        Movimentacao.objects.create(
            empresa=produto.empresa, produto=produto, deposito=deposito, usuario=usuario,
            tipo=Movimentacao.REQUISICAO, quantidade=1, solicitante='Ana',
        )
        resposta = api_client.get(reverse('movimentacao-list'))
        assert resposta.data['results'][0]['produto_nome'] == produto.nome

    def test_filtro_por_produto_retorna_apenas_suas_movimentacoes(self, api_client, produto, categoria, fornecedor, deposito, usuario):
        outro_produto = Produto.objects.create(empresa=produto.empresa, nome='Outro produto', categoria=categoria, fornecedor=fornecedor)
        Movimentacao.objects.create(empresa=produto.empresa, produto=produto, deposito=deposito, usuario=usuario, tipo=Movimentacao.REQUISICAO, quantidade=1, solicitante='Ana')
        Movimentacao.objects.create(empresa=produto.empresa, produto=outro_produto, deposito=deposito, usuario=usuario, tipo=Movimentacao.REQUISICAO, quantidade=1, solicitante='Bia')

        resposta = api_client.get(reverse('movimentacao-list'), {'produto': produto.id})

        assert resposta.data['count'] == 1
        assert resposta.data['results'][0]['produto'] == produto.id

    def test_sem_filtro_retorna_movimentacoes_de_todos_os_produtos(self, api_client, produto, categoria, fornecedor, deposito, usuario):
        outro_produto = Produto.objects.create(empresa=produto.empresa, nome='Outro produto', categoria=categoria, fornecedor=fornecedor)
        Movimentacao.objects.create(empresa=produto.empresa, produto=produto, deposito=deposito, usuario=usuario, tipo=Movimentacao.REQUISICAO, quantidade=1, solicitante='Ana')
        Movimentacao.objects.create(empresa=produto.empresa, produto=outro_produto, deposito=deposito, usuario=usuario, tipo=Movimentacao.REQUISICAO, quantidade=1, solicitante='Bia')

        resposta = api_client.get(reverse('movimentacao-list'))

        assert resposta.data['count'] == 2


class TestMovimentacaoApiFiltroPeriodo:
    def _criar_com_data(self, *, produto, deposito, usuario, data):
        movimentacao = Movimentacao.objects.create(
            empresa=produto.empresa, produto=produto, deposito=deposito, usuario=usuario,
            tipo=Movimentacao.REQUISICAO, quantidade=1, solicitante='Ana',
        )
        # auto_now_add só se aplica no INSERT — dá pra sobrescrever com um UPDATE direto
        Movimentacao.objects.filter(pk=movimentacao.pk).update(data=data)
        movimentacao.refresh_from_db()
        return movimentacao

    def test_data_inicio_exclui_movimentacoes_anteriores(self, api_client, produto, deposito, usuario):
        agora = timezone.now()
        antiga = self._criar_com_data(produto=produto, deposito=deposito, usuario=usuario, data=agora - timedelta(days=10))
        recente = self._criar_com_data(produto=produto, deposito=deposito, usuario=usuario, data=agora)

        resposta = api_client.get(reverse('movimentacao-list'), {
            'data_inicio': (agora - timedelta(days=1)).date().isoformat(),
        })

        assert resposta.data['count'] == 1
        assert resposta.data['results'][0]['id'] == recente.id
        assert antiga.id not in [r['id'] for r in resposta.data['results']]

    def test_data_fim_exclui_movimentacoes_posteriores(self, api_client, produto, deposito, usuario):
        agora = timezone.now()
        antiga = self._criar_com_data(produto=produto, deposito=deposito, usuario=usuario, data=agora - timedelta(days=10))
        self._criar_com_data(produto=produto, deposito=deposito, usuario=usuario, data=agora)

        resposta = api_client.get(reverse('movimentacao-list'), {
            'data_fim': (agora - timedelta(days=1)).date().isoformat(),
        })

        assert resposta.data['count'] == 1
        assert resposta.data['results'][0]['id'] == antiga.id

    def test_intervalo_combinado_restringe_aos_dois_limites(self, api_client, produto, deposito, usuario):
        agora = timezone.now()
        self._criar_com_data(produto=produto, deposito=deposito, usuario=usuario, data=agora - timedelta(days=10))
        do_meio = self._criar_com_data(produto=produto, deposito=deposito, usuario=usuario, data=agora - timedelta(days=5))
        self._criar_com_data(produto=produto, deposito=deposito, usuario=usuario, data=agora)

        resposta = api_client.get(reverse('movimentacao-list'), {
            'data_inicio': (agora - timedelta(days=7)).date().isoformat(),
            'data_fim': (agora - timedelta(days=3)).date().isoformat(),
        })

        assert resposta.data['count'] == 1
        assert resposta.data['results'][0]['id'] == do_meio.id

    def test_data_invalida_e_ignorada_sem_quebrar_a_listagem(self, api_client, produto, deposito, usuario):
        self._criar_com_data(produto=produto, deposito=deposito, usuario=usuario, data=timezone.now())

        resposta = api_client.get(reverse('movimentacao-list'), {'data_inicio': 'nao-e-uma-data'})

        assert resposta.status_code == status.HTTP_200_OK
        assert resposta.data['count'] == 1
