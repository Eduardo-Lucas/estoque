import pytest
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APIClient

pytestmark = pytest.mark.django_db


@pytest.mark.parametrize('nome_rota', ['produto-list', 'categoria-list', 'fornecedor-list', 'movimentacao-list'])
def test_endpoints_exigem_autenticacao(nome_rota):
    client = APIClient()
    resposta = client.get(reverse(nome_rota))
    assert resposta.status_code == status.HTTP_401_UNAUTHORIZED


def test_token_valido_permite_acesso(api_client):
    resposta = api_client.get(reverse('produto-list'))
    assert resposta.status_code == status.HTTP_200_OK


def test_login_retorna_token(usuario):
    client = APIClient()
    resposta = client.post(
        reverse('api_token_auth'),
        {'email': 'eduardo@example.com', 'password': 'senha-forte-123'},
    )
    assert resposta.status_code == status.HTTP_200_OK
    assert 'token' in resposta.data


def test_login_com_senha_errada_falha(usuario):
    client = APIClient()
    resposta = client.post(
        reverse('api_token_auth'),
        {'email': 'eduardo@example.com', 'password': 'senha-errada'},
    )
    assert resposta.status_code == status.HTTP_400_BAD_REQUEST


def test_login_com_username_em_vez_de_email_falha(usuario):
    """O contrato mudou: o campo agora é `email`, não `username`."""
    client = APIClient()
    resposta = client.post(
        reverse('api_token_auth'),
        {'username': 'eduardo@example.com', 'password': 'senha-forte-123'},
    )
    assert resposta.status_code == status.HTTP_400_BAD_REQUEST
