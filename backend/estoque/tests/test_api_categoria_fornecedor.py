import pytest
from django.urls import reverse
from rest_framework import status

from estoque.models import Categoria, Fornecedor

pytestmark = pytest.mark.django_db


class TestCategoriaApi:
    def test_criar_categoria(self, api_client):
        resposta = api_client.post(
            reverse('categoria-list'), {'nome': 'Eletrônicos', 'descricao': 'Componentes'},
        )
        assert resposta.status_code == status.HTTP_201_CREATED
        assert Categoria.objects.filter(nome='Eletrônicos').exists()

    def test_nome_duplicado_e_rejeitado(self, api_client, categoria):
        resposta = api_client.post(reverse('categoria-list'), {'nome': categoria.nome})
        assert resposta.status_code == status.HTTP_400_BAD_REQUEST

    def test_atualizar_categoria(self, api_client, categoria):
        resposta = api_client.put(
            reverse('categoria-detail', args=[categoria.id]),
            {'nome': categoria.nome, 'descricao': 'Nova descrição'},
        )
        assert resposta.status_code == status.HTTP_200_OK
        categoria.refresh_from_db()
        assert categoria.descricao == 'Nova descrição'

    def test_remover_categoria(self, api_client, categoria):
        resposta = api_client.delete(reverse('categoria-detail', args=[categoria.id]))
        assert resposta.status_code == status.HTTP_204_NO_CONTENT
        assert not Categoria.objects.filter(id=categoria.id).exists()

    def test_importar_csv_cria_e_atualiza(self, api_client):
        conteudo = (
            b'nome,descricao\n'
            b'Ferragens,Parafusos e afins\n'
            b'Eletronicos,Componentes\n'
        )
        arquivo = _arquivo_csv('categorias.csv', conteudo)
        resposta = api_client.post(reverse('categoria-importar-csv'), {'arquivo': arquivo}, format='multipart')

        assert resposta.status_code == status.HTTP_200_OK
        assert resposta.data['criados'] == 2
        assert resposta.data['atualizados'] == 0

        conteudo_atualizado = b'nome,descricao\nFerragens,Descricao nova\n'
        arquivo2 = _arquivo_csv('categorias.csv', conteudo_atualizado)
        resposta2 = api_client.post(reverse('categoria-importar-csv'), {'arquivo': arquivo2}, format='multipart')
        assert resposta2.data['criados'] == 0
        assert resposta2.data['atualizados'] == 1
        assert Categoria.objects.get(nome='Ferragens').descricao == 'Descricao nova'

    def test_exportar_csv(self, api_client, categoria):
        resposta = api_client.get(reverse('categoria-exportar-csv'))
        assert resposta.status_code == status.HTTP_200_OK
        conteudo = resposta.content.decode('utf-8')
        assert 'nome,descricao' in conteudo
        assert categoria.nome in conteudo

    def test_filtro_por_nome_e_parcial_e_case_insensitive(self, api_client, categoria):
        Categoria.objects.create(nome='Elétrica')

        resposta = api_client.get(reverse('categoria-list'), {'nome': 'ferrag'})

        assert resposta.data['count'] == 1
        assert resposta.data['results'][0]['nome'] == categoria.nome

    def test_filtro_por_nome_sem_correspondencia_retorna_vazio(self, api_client, categoria):
        resposta = api_client.get(reverse('categoria-list'), {'nome': 'inexistente'})
        assert resposta.data['count'] == 0

    def test_sem_filtro_retorna_todas(self, api_client, categoria):
        Categoria.objects.create(nome='Elétrica')
        resposta = api_client.get(reverse('categoria-list'))
        assert resposta.data['count'] == 2


class TestFornecedorApi:
    def test_criar_fornecedor(self, api_client):
        resposta = api_client.post(
            reverse('fornecedor-list'), {'nome': 'Distribuidora XYZ', 'email': 'contato@xyz.com'},
        )
        assert resposta.status_code == status.HTTP_201_CREATED
        assert Fornecedor.objects.filter(nome='Distribuidora XYZ').exists()

    def test_nome_duplicado_e_rejeitado(self, api_client, fornecedor):
        resposta = api_client.post(reverse('fornecedor-list'), {'nome': fornecedor.nome})
        assert resposta.status_code == status.HTTP_400_BAD_REQUEST

    def test_remover_fornecedor(self, api_client, fornecedor):
        resposta = api_client.delete(reverse('fornecedor-detail', args=[fornecedor.id]))
        assert resposta.status_code == status.HTTP_204_NO_CONTENT
        assert not Fornecedor.objects.filter(id=fornecedor.id).exists()

    def test_importar_csv_cria_e_atualiza(self, api_client):
        conteudo = b'nome,cnpj,telefone,email,endereco\nDistribuidora ABC,12.345.678/0001-99,1140028922,contato@abc.com,Rua A\n'
        arquivo = _arquivo_csv('fornecedores.csv', conteudo)
        resposta = api_client.post(reverse('fornecedor-importar-csv'), {'arquivo': arquivo}, format='multipart')

        assert resposta.status_code == status.HTTP_200_OK
        assert resposta.data['criados'] == 1

        conteudo_atualizado = b'nome,cnpj,telefone,email,endereco\nDistribuidora ABC,,,novo@abc.com,\n'
        arquivo2 = _arquivo_csv('fornecedores.csv', conteudo_atualizado)
        resposta2 = api_client.post(reverse('fornecedor-importar-csv'), {'arquivo': arquivo2}, format='multipart')
        assert resposta2.data['atualizados'] == 1
        assert Fornecedor.objects.get(nome='Distribuidora ABC').email == 'novo@abc.com'

    def test_exportar_csv(self, api_client, fornecedor):
        resposta = api_client.get(reverse('fornecedor-exportar-csv'))
        assert resposta.status_code == status.HTTP_200_OK
        assert fornecedor.nome in resposta.content.decode('utf-8')

    def test_filtro_por_nome_e_parcial_e_case_insensitive(self, api_client, fornecedor):
        Fornecedor.objects.create(nome='Distribuidora XYZ')

        resposta = api_client.get(reverse('fornecedor-list'), {'nome': 'abc'})

        assert resposta.data['count'] == 1
        assert resposta.data['results'][0]['nome'] == fornecedor.nome

    def test_filtro_por_nome_sem_correspondencia_retorna_vazio(self, api_client, fornecedor):
        resposta = api_client.get(reverse('fornecedor-list'), {'nome': 'inexistente'})
        assert resposta.data['count'] == 0

    def test_sem_filtro_retorna_todos(self, api_client, fornecedor):
        Fornecedor.objects.create(nome='Distribuidora XYZ')
        resposta = api_client.get(reverse('fornecedor-list'))
        assert resposta.data['count'] == 2


def _arquivo_csv(nome, conteudo_bytes):
    from django.core.files.uploadedfile import SimpleUploadedFile
    return SimpleUploadedFile(nome, conteudo_bytes, content_type='text/csv')
