import csv
import io

from django.db import transaction
from django.http import HttpResponse
from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.parsers import MultiPartParser
from rest_framework.response import Response

from .models import Produto, Movimentacao
from .serializers import ProdutoSerializer, MovimentacaoSerializer


def _formatar_erros(erros_por_campo):
    partes = []
    for campo, mensagens in erros_por_campo.items():
        primeira = mensagens[0] if isinstance(mensagens, list) else mensagens
        partes.append(f'{campo}: {primeira}')
    return '; '.join(partes)


class ProdutoViewSet(viewsets.ModelViewSet):
    """
    CRUD completo de produtos.
    GET    /api/produtos/       -> lista
    POST   /api/produtos/       -> cria
    GET    /api/produtos/{id}/  -> detalhe
    PUT    /api/produtos/{id}/  -> atualiza
    DELETE /api/produtos/{id}/  -> remove
    """
    queryset = Produto.objects.all()
    serializer_class = ProdutoSerializer

    @action(detail=False, methods=['post'], parser_classes=[MultiPartParser])
    def importar_csv(self, request):
        """
        POST /api/produtos/importar_csv/  -> importação em lote via arquivo CSV
        Cabeçalho esperado: nome,descricao,quantidade,preco
        Se já existir um produto com o mesmo nome, apenas a quantidade é atualizada;
        caso contrário, um novo produto é criado com os dados da linha.
        Linhas inválidas são reportadas individualmente, sem interromper o restante do arquivo.
        """
        arquivo = request.FILES.get('arquivo')
        if not arquivo:
            return Response(
                {'detail': 'Envie um arquivo CSV no campo "arquivo".'},
                status=status.HTTP_400_BAD_REQUEST,
            )

        try:
            conteudo = arquivo.read().decode('utf-8-sig')
        except UnicodeDecodeError:
            return Response(
                {'detail': 'Não foi possível ler o arquivo. Salve o CSV em UTF-8.'},
                status=status.HTTP_400_BAD_REQUEST,
            )

        try:
            delimitador = csv.Sniffer().sniff(conteudo[:1024], delimiters=',;\t').delimiter
        except csv.Error:
            delimitador = ','

        leitor = csv.DictReader(io.StringIO(conteudo), delimiter=delimitador)

        colunas_obrigatorias = {'nome', 'quantidade'}
        if not colunas_obrigatorias.issubset(set(leitor.fieldnames or [])):
            return Response(
                {
                    'detail': (
                        'Não foi possível identificar as colunas do CSV. Verifique se a primeira linha '
                        'é "nome,descricao,quantidade,preco" separada por vírgula, ponto e vírgula ou tabulação.'
                    )
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

        criados = 0
        atualizados = 0
        erros = []
        # linha 1 é o cabeçalho, então os dados começam na linha 2
        for numero_linha, linha in enumerate(leitor, start=2):
            nome = (linha.get('nome') or '').strip()
            quantidade = (linha.get('quantidade') or '0').strip()

            produto_existente = Produto.objects.filter(nome=nome).first() if nome else None

            if produto_existente:
                # produto já cadastrado -> só atualiza a quantidade
                serializer = ProdutoSerializer(
                    produto_existente, data={'quantidade': quantidade}, partial=True
                )
                if serializer.is_valid():
                    serializer.save()
                    atualizados += 1
                else:
                    erros.append({'linha': numero_linha, 'mensagem': _formatar_erros(serializer.errors)})
                continue

            dados = {
                'nome': nome,
                'descricao': (linha.get('descricao') or '').strip(),
                'quantidade': quantidade,
                # aceita "19,90" (padrão BR) além de "19.90"
                'preco': (linha.get('preco') or '0').strip().replace(',', '.'),
            }
            serializer = ProdutoSerializer(data=dados)
            if serializer.is_valid():
                serializer.save()
                criados += 1
            else:
                erros.append({'linha': numero_linha, 'mensagem': _formatar_erros(serializer.errors)})

        return Response(
            {'criados': criados, 'atualizados': atualizados, 'erros': erros},
            status=status.HTTP_200_OK,
        )

    @action(detail=False, methods=['get'])
    def exportar_csv(self, request):
        """
        GET /api/produtos/exportar_csv/  -> exporta todos os produtos cadastrados como CSV
        """
        response = HttpResponse(content_type='text/csv')
        response['Content-Disposition'] = 'attachment; filename="produtos.csv"'

        escritor = csv.writer(response)
        escritor.writerow(['nome', 'descricao', 'quantidade', 'preco'])
        for produto in self.get_queryset():
            escritor.writerow([produto.nome, produto.descricao, produto.quantidade, produto.preco])

        return response


class MovimentacaoViewSet(viewsets.ModelViewSet):
    """
    Registra requisições e devoluções, ajustando o estoque do produto
    dentro de uma transação atômica.
    """
    queryset = Movimentacao.objects.select_related('produto').all()
    serializer_class = MovimentacaoSerializer

    @transaction.atomic
    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        movimentacao = serializer.save()

        produto = movimentacao.produto
        if movimentacao.tipo == Movimentacao.REQUISICAO:
            produto.quantidade -= movimentacao.quantidade
        else:
            produto.quantidade += movimentacao.quantidade
        produto.save(update_fields=['quantidade', 'atualizado_em'])

        return Response(self.get_serializer(movimentacao).data, status=status.HTTP_201_CREATED)
