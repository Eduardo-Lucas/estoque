import pytest
from django.urls import reverse
from django.utils.encoding import force_bytes
from django.utils.http import urlsafe_base64_encode
from rest_framework import status
from rest_framework.test import APIClient

from contas.models import Usuario
from contas.tokens import gerador_token_confirmacao

pytestmark = pytest.mark.django_db

DADOS_REGISTRO = {
    'email': 'nova@empresa.com',
    'password': 'senha-super-forte-2026',
    'nome': 'Fulana de Tal',
    'empresa_razao_social': 'Empresa Nova LTDA',
    'empresa_cnpj': '11222333000144',
}


def _registrar_e_obter_usuario(client):
    client.post(reverse('api_registro'), DADOS_REGISTRO)
    return Usuario.objects.get(email=DADOS_REGISTRO['email'])


def _uid_e_token(usuario):
    uid = urlsafe_base64_encode(force_bytes(usuario.pk))
    token = gerador_token_confirmacao.make_token(usuario)
    return uid, token


class TestConfirmarEmail:
    def test_token_valido_ativa_a_conta_e_devolve_token_de_sessao(self):
        client = APIClient()
        usuario = _registrar_e_obter_usuario(client)
        uid, token = _uid_e_token(usuario)

        resposta = client.post(reverse('api_confirmar_email'), {'uid': uid, 'token': token})

        assert resposta.status_code == status.HTTP_200_OK
        assert 'token' in resposta.data
        assert resposta.data['email'] == DADOS_REGISTRO['email']
        usuario.refresh_from_db()
        assert usuario.is_active is True

    def test_apos_confirmar_o_login_normal_passa_a_funcionar(self):
        client = APIClient()
        usuario = _registrar_e_obter_usuario(client)
        uid, token = _uid_e_token(usuario)
        client.post(reverse('api_confirmar_email'), {'uid': uid, 'token': token})

        resposta = client.post(reverse('api_token_auth'), {
            'email': DADOS_REGISTRO['email'], 'password': DADOS_REGISTRO['password'],
        })

        assert resposta.status_code == status.HTTP_200_OK
        assert 'token' in resposta.data

    def test_token_invalido_e_rejeitado(self):
        client = APIClient()
        usuario = _registrar_e_obter_usuario(client)
        uid, _token = _uid_e_token(usuario)

        resposta = client.post(reverse('api_confirmar_email'), {'uid': uid, 'token': 'token-forjado'})

        assert resposta.status_code == status.HTTP_400_BAD_REQUEST
        usuario.refresh_from_db()
        assert usuario.is_active is False

    def test_uid_invalido_e_rejeitado(self):
        resposta = APIClient().post(reverse('api_confirmar_email'), {'uid': 'lixo-invalido', 'token': 'qualquer'})
        assert resposta.status_code == status.HTTP_400_BAD_REQUEST

    def test_token_nao_pode_ser_reaproveitado_apos_confirmar(self):
        client = APIClient()
        usuario = _registrar_e_obter_usuario(client)
        uid, token = _uid_e_token(usuario)

        primeira = client.post(reverse('api_confirmar_email'), {'uid': uid, 'token': token})
        assert primeira.status_code == status.HTTP_200_OK

        segunda = client.post(reverse('api_confirmar_email'), {'uid': uid, 'token': token})
        assert segunda.status_code == status.HTTP_400_BAD_REQUEST
