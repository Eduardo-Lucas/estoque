from pathlib import Path

import pytest
from django.core.files.uploadedfile import SimpleUploadedFile
from django.urls import reverse
from rest_framework import status

from estoque.models import Fornecedor, ItemNotaFiscalCompra, Movimentacao, NotaFiscalCompra, Produto
from estoque.services import ServicoEstoque

pytestmark = pytest.mark.django_db

FIXTURES_DIR = Path(__file__).parent / 'fixtures'


def _arquivo_fixture(nome):
    conteudo = (FIXTURES_DIR / nome).read_bytes()
    return SimpleUploadedFile(nome, conteudo, content_type='application/xml')


def _importar(api_client, nome_fixture='nfe_exemplo.xml'):
    return api_client.post(
        reverse('produto-importar-nfe'), {'arquivo': _arquivo_fixture(nome_fixture)}, format='multipart',
    )


class TestImportarNfeFeliz:
    def test_processa_item_existente_por_sku(self, api_client, produto):
        resposta = _importar(api_client)

        assert resposta.status_code == status.HTTP_200_OK
        assert resposta.data['itens_processados'] == 1
        assert resposta.data['itens_ja_processados'] == 0
        assert resposta.data['numero_nfe'] == '1234'

        produto.refresh_from_db()
        assert ServicoEstoque.saldo_disponivel(produto) == 150  # 100 + 50 (qCom do item 1)
        assert str(produto.preco_custo_referencia) == '1.50'  # vUnCom do item 1, arredondado

    def test_cria_movimentacao_do_tipo_compra(self, api_client, produto):
        _importar(api_client)
        movimentacao = Movimentacao.objects.get(produto=produto)
        assert movimentacao.tipo == Movimentacao.COMPRA
        assert movimentacao.quantidade == 50
        assert '1234' in movimentacao.observacao

        item = ItemNotaFiscalCompra.objects.get(numero_item=1)
        assert item.processado is True
        assert item.produto_id == produto.id
        assert item.movimentacao_id == movimentacao.id

    def test_item_sem_produto_correspondente_fica_pendente(self, api_client, produto):
        resposta = _importar(api_client)
        assert resposta.data['nao_encontrados'] == [
            {'item': 2, 'codigo_fornecedor': 'NOVO-XYZ', 'descricao': 'Produto Desconhecido'},
        ]
        # não cria produto novo
        assert not Produto.objects.filter(sku='NOVO-XYZ').exists()

    def test_fornecedor_e_criado_quando_nao_existe(self, api_client, produto):
        _importar(api_client)
        assert Fornecedor.objects.filter(nome='Distribuidora ABC Ltda', cnpj='12345678000199').exists()

    def test_fornecedor_e_casado_por_cnpj_com_formatacao_diferente(self, api_client, produto):
        total_fornecedores_antes = Fornecedor.objects.count()
        fornecedor = Fornecedor.objects.create(empresa=produto.empresa, nome='Nome Diferente Ltda', cnpj='12.345.678/0001-99')
        _importar(api_client)

        # não cria fornecedor novo: casou pelo CNPJ (normalizado) com o que já existia
        assert Fornecedor.objects.count() == total_fornecedores_antes + 1
        nota = NotaFiscalCompra.objects.get()
        assert nota.fornecedor_id == fornecedor.id


class TestReimportacaoIdempotente:
    def test_reimportar_mesmo_arquivo_nao_duplica_estoque_nem_movimentacao(self, api_client, produto):
        _importar(api_client)
        resposta2 = _importar(api_client)

        assert resposta2.data['itens_processados'] == 0
        assert resposta2.data['itens_ja_processados'] == 1
        assert ServicoEstoque.saldo_disponivel(produto) == 150  # não dobrou
        assert Movimentacao.objects.filter(produto=produto).count() == 1
        assert NotaFiscalCompra.objects.count() == 1

    def test_cadastrar_produto_pendente_e_reimportar_processa_so_o_pendente(self, api_client, produto):
        _importar(api_client)

        produto_novo = Produto.objects.create(empresa=produto.empresa, nome='Produto Desconhecido', sku='NOVO-XYZ')
        resposta2 = _importar(api_client)

        assert resposta2.data['itens_processados'] == 1
        assert resposta2.data['itens_ja_processados'] == 1
        assert resposta2.data['nao_encontrados'] == []
        assert ServicoEstoque.saldo_disponivel(produto_novo) == 3  # qCom do item 2


class TestErrosDeImportacao:
    def test_quantidade_fracionaria_e_aceita(self, api_client, produto):
        """Movimentacao.quantidade é Decimal — a guarda que só existia por
        causa do antigo PositiveIntegerField foi removida (ver plano da PR)."""
        resposta = _importar(api_client, 'nfe_quantidade_fracionaria.xml')

        assert resposta.status_code == status.HTTP_200_OK
        assert resposta.data['itens_processados'] == 1
        assert resposta.data['erros'] == []

        produto.refresh_from_db()
        assert ServicoEstoque.saldo_disponivel(produto) == pytest.approx(102.5)

    def test_arquivo_ausente_retorna_400(self, api_client):
        resposta = api_client.post(reverse('produto-importar-nfe'), {}, format='multipart')
        assert resposta.status_code == status.HTTP_400_BAD_REQUEST

    def test_xml_corrompido_retorna_400(self, api_client):
        arquivo = SimpleUploadedFile('nfe.xml', b'isso nao e xml', content_type='application/xml')
        resposta = api_client.post(reverse('produto-importar-nfe'), {'arquivo': arquivo}, format='multipart')
        assert resposta.status_code == status.HTTP_400_BAD_REQUEST

    def test_xml_sem_infnfe_retorna_400(self, api_client):
        arquivo = SimpleUploadedFile('nfe.xml', b'<root></root>', content_type='application/xml')
        resposta = api_client.post(reverse('produto-importar-nfe'), {'arquivo': arquivo}, format='multipart')
        assert resposta.status_code == status.HTTP_400_BAD_REQUEST

    def test_xml_sem_cnpj_do_emitente_retorna_400(self, api_client):
        xml = b'''<?xml version="1.0"?>
        <NFe xmlns="http://www.portalfiscal.inf.br/nfe">
          <infNFe Id="NFe35240112345678000199550010000012341123456789">
            <ide><nNF>1</nNF></ide>
            <emit><xNome>Fornecedor Sem CNPJ</xNome></emit>
            <det nItem="1"><prod><xProd>Item</xProd><qCom>1</qCom><vUnCom>1.00</vUnCom></prod></det>
            <total><ICMSTot><vNF>1.00</vNF></ICMSTot></total>
          </infNFe>
        </NFe>'''
        arquivo = SimpleUploadedFile('nfe.xml', xml, content_type='application/xml')
        resposta = api_client.post(reverse('produto-importar-nfe'), {'arquivo': arquivo}, format='multipart')
        assert resposta.status_code == status.HTTP_400_BAD_REQUEST

    def test_xml_sem_itens_retorna_400(self, api_client):
        xml = b'''<?xml version="1.0"?>
        <NFe xmlns="http://www.portalfiscal.inf.br/nfe">
          <infNFe Id="NFe35240112345678000199550010000012341123456789">
            <ide><nNF>1</nNF></ide>
            <emit><CNPJ>12345678000199</CNPJ><xNome>Fornecedor</xNome></emit>
            <total><ICMSTot><vNF>0.00</vNF></ICMSTot></total>
          </infNFe>
        </NFe>'''
        arquivo = SimpleUploadedFile('nfe.xml', xml, content_type='application/xml')
        resposta = api_client.post(reverse('produto-importar-nfe'), {'arquivo': arquivo}, format='multipart')
        assert resposta.status_code == status.HTTP_400_BAD_REQUEST

    def test_xml_com_valor_numerico_invalido_retorna_400(self, api_client):
        xml = b'''<?xml version="1.0"?>
        <NFe xmlns="http://www.portalfiscal.inf.br/nfe">
          <infNFe Id="NFe35240112345678000199550010000012341123456789">
            <ide><nNF>1</nNF></ide>
            <emit><CNPJ>12345678000199</CNPJ><xNome>Fornecedor</xNome></emit>
            <det nItem="1"><prod><xProd>Item</xProd><qCom>abc</qCom><vUnCom>1.00</vUnCom></prod></det>
            <total><ICMSTot><vNF>1.00</vNF></ICMSTot></total>
          </infNFe>
        </NFe>'''
        arquivo = SimpleUploadedFile('nfe.xml', xml, content_type='application/xml')
        resposta = api_client.post(reverse('produto-importar-nfe'), {'arquivo': arquivo}, format='multipart')
        assert resposta.status_code == status.HTTP_400_BAD_REQUEST


def test_endpoint_exige_autenticacao():
    from rest_framework.test import APIClient
    client = APIClient()
    resposta = client.post(reverse('produto-importar-nfe'), {}, format='multipart')
    assert resposta.status_code == status.HTTP_401_UNAUTHORIZED


def test_xml_sem_protocolo_de_autorizacao_usa_id_do_infnfe(api_client):
    resposta = _importar(api_client, 'nfe_sem_protocolo.xml')
    assert resposta.status_code == status.HTTP_200_OK
    assert NotaFiscalCompra.objects.get().chave_acesso == '35240112345678000199550010000012341123456789'
