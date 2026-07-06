import pytest
from django.core import mail
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APIClient

from contas.models import Usuario
from estoque.models import ConfiguracaoEstoque, Deposito
from estoque.services import CODIGO_DEPOSITO_PADRAO, ServicoEstoque

pytestmark = pytest.mark.django_db


def _dados_registro(**overrides):
    dados = {
        'email': 'nova@empresa.com',
        'password': 'senha-super-forte-2026',
        'nome': 'Fulana de Tal',
        'empresa_razao_social': 'Empresa Nova LTDA',
        'empresa_nome_fantasia': 'Empresa Nova',
        'empresa_cnpj': '11222333000144',
    }
    dados.update(overrides)
    return dados


class TestRegistro:
    def test_cria_conta_ativa_e_empresa_com_deposito_e_configuracao(self):
        resposta = APIClient().post(reverse('api_registro'), _dados_registro())

        assert resposta.status_code == status.HTTP_201_CREATED

        usuario = Usuario.objects.get(email='nova@empresa.com')
        assert usuario.is_active is True
        assert usuario.check_password('senha-super-forte-2026')
        assert usuario.nome == 'Fulana de Tal'

        empresa = usuario.empresa
        assert empresa.razao_social == 'Empresa Nova LTDA'
        assert empresa.cnpj == '11222333000144'
        assert ConfiguracaoEstoque.objects.filter(empresa=empresa).exists()
        assert Deposito.objects.filter(empresa=empresa, codigo=CODIGO_DEPOSITO_PADRAO).exists()

    def test_nao_envia_email_com_confirmacao_suspensa(self):
        APIClient().post(reverse('api_registro'), _dados_registro())

        assert len(mail.outbox) == 0

    def test_email_duplicado_e_rejeitado(self):
        empresa_existente = ServicoEstoque.get_empresa_padrao()
        Usuario.objects.create_user(email='ja-existe@empresa.com', password='outra-senha-123', empresa=empresa_existente)

        resposta = APIClient().post(reverse('api_registro'), _dados_registro(email='ja-existe@empresa.com'))

        assert resposta.status_code == status.HTTP_400_BAD_REQUEST

    def test_cnpj_duplicado_e_rejeitado(self):
        empresa_existente = ServicoEstoque.get_empresa_padrao()

        resposta = APIClient().post(reverse('api_registro'), _dados_registro(empresa_cnpj=empresa_existente.cnpj))

        assert resposta.status_code == status.HTTP_400_BAD_REQUEST

    def test_senha_fraca_e_rejeitada(self):
        resposta = APIClient().post(reverse('api_registro'), _dados_registro(password='123'))
        assert resposta.status_code == status.HTTP_400_BAD_REQUEST

    def test_login_funciona_imediatamente_apos_registro(self):
        APIClient().post(reverse('api_registro'), _dados_registro())

        resposta = APIClient().post(reverse('api_token_auth'), {
            'email': 'nova@empresa.com', 'password': 'senha-super-forte-2026',
        })

        assert resposta.status_code == status.HTTP_200_OK
        assert 'token' in resposta.data
