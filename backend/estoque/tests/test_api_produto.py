import pytest
from django.core.files.uploadedfile import SimpleUploadedFile
from django.urls import reverse
from rest_framework import status

from estoque.models import Categoria, Fornecedor, Movimentacao, Produto
from estoque.services import ServicoEstoque

pytestmark = pytest.mark.django_db


def _arquivo_csv(conteudo_bytes, nome='produtos.csv'):
    return SimpleUploadedFile(nome, conteudo_bytes, content_type='text/csv')


class TestProdutoApiCrud:
    def test_criar_produto_minimo(self, api_client):
        resposta = api_client.post(reverse('produto-list'), {'nome': 'Caneta Azul', 'preco': '1.50'})
        assert resposta.status_code == status.HTTP_201_CREATED
        assert resposta.data['ativo'] is True
        assert resposta.data['unidade_medida'] == 'UN'
        assert resposta.data['saldo'] == 0

    def test_criar_produto_com_categoria_e_fornecedor(self, api_client, categoria, fornecedor):
        resposta = api_client.post(reverse('produto-list'), {
            'nome': 'Furadeira',
            'preco': '199.90',
            'categoria': categoria.id,
            'fornecedor': fornecedor.id,
        })
        assert resposta.status_code == status.HTTP_201_CREATED
        assert resposta.data['categoria_nome'] == categoria.nome
        assert resposta.data['fornecedor_nome'] == fornecedor.nome

    def test_sku_duplicado_e_rejeitado(self, api_client, produto):
        resposta = api_client.post(reverse('produto-list'), {
            'nome': 'Outro nome', 'sku': produto.sku, 'preco': '1.00',
        })
        assert resposta.status_code == status.HTTP_400_BAD_REQUEST

    def test_atualizar_produto(self, api_client, produto):
        resposta = api_client.patch(reverse('produto-detail', args=[produto.id]), {'preco': '3.00'})
        assert resposta.status_code == status.HTTP_200_OK
        produto.refresh_from_db()
        assert str(produto.preco) == '3.00'

    def test_remover_produto_inativa_em_vez_de_excluir(self, api_client, produto):
        resposta = api_client.delete(reverse('produto-detail', args=[produto.id]))
        assert resposta.status_code == status.HTTP_204_NO_CONTENT
        produto.refresh_from_db()
        assert Produto.objects.filter(id=produto.id).exists()
        assert produto.ativo is False

    def test_listagem_e_paginada(self, api_client, produto):
        resposta = api_client.get(reverse('produto-list'))
        assert resposta.status_code == status.HTTP_200_OK
        assert set(resposta.data.keys()) == {'count', 'next', 'previous', 'results'}


class TestProdutoApiFiltros:
    def test_filtro_por_nome_e_parcial_e_case_insensitive(self, api_client, produto):
        Produto.objects.create(empresa=produto.empresa, nome='Martelo de Borracha')

        resposta = api_client.get(reverse('produto-list'), {'nome': 'parafuso'})

        assert resposta.data['count'] == 1
        assert resposta.data['results'][0]['nome'] == produto.nome

    def test_filtro_por_nome_sem_correspondencia_retorna_vazio(self, api_client, produto):
        resposta = api_client.get(reverse('produto-list'), {'nome': 'inexistente'})
        assert resposta.data['count'] == 0

    def test_filtro_por_categoria(self, api_client, produto, categoria):
        outra_categoria = Categoria.objects.create(empresa=produto.empresa, nome='Elétrica')
        Produto.objects.create(empresa=produto.empresa, nome='Fita isolante', categoria=outra_categoria)

        resposta = api_client.get(reverse('produto-list'), {'categoria': categoria.id})

        assert resposta.data['count'] == 1
        assert resposta.data['results'][0]['nome'] == produto.nome

    def test_filtro_por_fornecedor(self, api_client, produto, fornecedor):
        outro_fornecedor = Fornecedor.objects.create(empresa=produto.empresa, nome='Distribuidora XYZ')
        Produto.objects.create(empresa=produto.empresa, nome='Cabo de aço', fornecedor=outro_fornecedor)

        resposta = api_client.get(reverse('produto-list'), {'fornecedor': fornecedor.id})

        assert resposta.data['count'] == 1
        assert resposta.data['results'][0]['nome'] == produto.nome

    def test_filtros_combinados(self, api_client, produto, categoria, fornecedor):
        Produto.objects.create(empresa=produto.empresa, nome='Parafuso 20mm', categoria=categoria)

        resposta = api_client.get(
            reverse('produto-list'), {'nome': 'parafuso', 'categoria': categoria.id, 'fornecedor': fornecedor.id},
        )

        assert resposta.data['count'] == 1
        assert resposta.data['results'][0]['nome'] == produto.nome

    def test_sem_filtro_retorna_todos(self, api_client, produto):
        Produto.objects.create(empresa=produto.empresa, nome='Martelo de Borracha')
        resposta = api_client.get(reverse('produto-list'))
        assert resposta.data['count'] == 2


class TestProdutoImportarCsv:
    def test_criacao_com_campos_opcionais_e_fk_por_nome(self, api_client):
        conteudo = (
            b'nome,quantidade,preco,sku,categoria,fornecedor,unidade_medida,estoque_minimo,preco_custo,ativo\n'
            b'Parafuso Novo,50,9.90,PRF-CSV-1,Ferragens,Distribuidora ABC,CX,10,5.00,true\n'
        )
        resposta = api_client.post(
            reverse('produto-importar-csv'), {'arquivo': _arquivo_csv(conteudo)}, format='multipart',
        )

        assert resposta.status_code == status.HTTP_200_OK
        assert resposta.data == {'criados': 1, 'atualizados': 0, 'erros': []}

        produto_criado = Produto.objects.get(nome='Parafuso Novo')
        assert produto_criado.sku == 'PRF-CSV-1'
        assert produto_criado.categoria.nome == 'Ferragens'
        assert produto_criado.fornecedor.nome == 'Distribuidora ABC'
        assert produto_criado.unidade_medida == 'CX'
        assert produto_criado.estoque_minimo == 10
        assert str(produto_criado.preco_custo_referencia) == '5.00'

        # o saldo inicial é lançado como um ajuste de inventário, não escrito direto
        assert ServicoEstoque.saldo_disponivel(produto_criado) == 50
        movimentacao = Movimentacao.objects.get(produto=produto_criado)
        assert movimentacao.tipo == Movimentacao.AJUSTE_POSITIVO
        assert movimentacao.quantidade == 50

        # categoria e fornecedor não existiam e devem ter sido criados automaticamente
        assert Categoria.objects.filter(nome='Ferragens').exists()
        assert Fornecedor.objects.filter(nome='Distribuidora ABC').exists()

    def test_upsert_por_nome_nao_sobrescreve_campos_vazios(self, api_client, produto):
        conteudo = f'nome,quantidade,preco\n{produto.nome},999,15.00\n'.encode()
        resposta = api_client.post(
            reverse('produto-importar-csv'), {'arquivo': _arquivo_csv(conteudo)}, format='multipart',
        )

        assert resposta.data == {'criados': 0, 'atualizados': 1, 'erros': []}
        produto.refresh_from_db()
        assert ServicoEstoque.saldo_disponivel(produto) == 999
        assert str(produto.preco) == '15.00'
        # sku e categoria não vieram na linha (vazios) e devem permanecer intocados
        assert produto.sku == 'PRF-001'
        assert produto.categoria is not None

    def test_linha_invalida_e_reportada_sem_interromper_arquivo(self, api_client):
        conteudo = (
            b'nome,quantidade,preco\n'
            b',10,1.00\n'
            b'Produto Valido,5,2.00\n'
        )
        resposta = api_client.post(
            reverse('produto-importar-csv'), {'arquivo': _arquivo_csv(conteudo)}, format='multipart',
        )
        assert resposta.status_code == status.HTTP_200_OK
        assert resposta.data['criados'] == 1
        assert len(resposta.data['erros']) == 1
        assert resposta.data['erros'][0]['linha'] == 2
        assert Produto.objects.filter(nome='Produto Valido').exists()

    def test_colunas_obrigatorias_ausentes_retorna_400(self, api_client):
        conteudo = b'descricao\nsem nome nem quantidade\n'
        resposta = api_client.post(
            reverse('produto-importar-csv'), {'arquivo': _arquivo_csv(conteudo)}, format='multipart',
        )
        assert resposta.status_code == status.HTTP_400_BAD_REQUEST

    def test_sem_arquivo_retorna_400(self, api_client):
        resposta = api_client.post(reverse('produto-importar-csv'), {}, format='multipart')
        assert resposta.status_code == status.HTTP_400_BAD_REQUEST


class TestProdutoExportarCsv:
    def test_exportar_csv_inclui_novas_colunas(self, api_client, produto):
        resposta = api_client.get(reverse('produto-exportar-csv'))
        assert resposta.status_code == status.HTTP_200_OK
        conteudo = resposta.content.decode('utf-8')
        cabecalho = conteudo.splitlines()[0]
        assert cabecalho == 'nome,sku,codigo_barras,categoria,fornecedor,unidade_medida,quantidade,estoque_minimo,preco_custo,preco,ativo,descricao'
        assert produto.nome in conteudo
        assert produto.sku in conteudo
        assert produto.categoria.nome in conteudo
