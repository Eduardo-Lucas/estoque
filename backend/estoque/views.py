import csv
import io

from django.db import transaction
from django.http import HttpResponse
from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.parsers import MultiPartParser
from rest_framework.response import Response

from .models import Produto, Categoria, Fornecedor, Movimentacao
from .serializers import ProdutoSerializer, CategoriaSerializer, FornecedorSerializer, MovimentacaoSerializer


def _formatar_erros(erros_por_campo):
    partes = []
    for campo, mensagens in erros_por_campo.items():
        primeira = mensagens[0] if isinstance(mensagens, list) else mensagens
        partes.append(f'{campo}: {primeira}')
    return '; '.join(partes)


def _ler_csv(arquivo):
    """Decodifica o upload e devolve um csv.DictReader detectando o delimitador."""
    conteudo = arquivo.read().decode('utf-8-sig')
    try:
        delimitador = csv.Sniffer().sniff(conteudo[:1024], delimiters=',;\t').delimiter
    except csv.Error:
        delimitador = ','
    return csv.DictReader(io.StringIO(conteudo), delimiter=delimitador)


def _valor_categoria(nome):
    nome = (nome or '').strip()
    if not nome:
        return None
    categoria, _ = Categoria.objects.get_or_create(nome=nome)
    return categoria.id


def _valor_fornecedor(nome):
    nome = (nome or '').strip()
    if not nome:
        return None
    fornecedor, _ = Fornecedor.objects.get_or_create(nome=nome)
    return fornecedor.id


def _valor_preco(texto):
    # aceita "19,90" (padrão BR) além de "19.90"
    return (texto or '0').strip().replace(',', '.')


def _valor_booleano(texto):
    texto = (texto or '').strip().lower()
    if not texto:
        return True
    return texto in ('1', 'true', 'sim', 'verdadeiro', 'yes')


# campos opcionais aceitos no CSV de produtos, além de nome/quantidade (obrigatórios)
_CAMPOS_OPCIONAIS_PRODUTO = [
    'sku', 'codigo_barras', 'descricao', 'categoria', 'fornecedor',
    'unidade_medida', 'estoque_minimo', 'preco_custo', 'preco', 'ativo',
]


def _dados_opcionais_produto(linha, colunas_presentes, incluir_vazios):
    """
    Monta os campos opcionais presentes no cabeçalho do CSV.
    Quando incluir_vazios=False (atualização de produto existente), células vazias
    são ignoradas para não sobrescrever um valor já cadastrado.
    """
    dados = {}
    for campo in _CAMPOS_OPCIONAIS_PRODUTO:
        if campo not in colunas_presentes:
            continue
        bruto = (linha.get(campo) or '').strip()
        if not bruto and not incluir_vazios and campo != 'ativo':
            continue

        if campo == 'categoria':
            dados['categoria'] = _valor_categoria(bruto)
        elif campo == 'fornecedor':
            dados['fornecedor'] = _valor_fornecedor(bruto)
        elif campo in ('preco', 'preco_custo'):
            dados[campo] = _valor_preco(bruto)
        elif campo == 'ativo':
            dados['ativo'] = _valor_booleano(linha.get('ativo'))
        elif campo == 'unidade_medida':
            dados['unidade_medida'] = bruto.upper() or Produto.UNIDADE_UNIDADE
        elif campo == 'sku':
            dados['sku'] = bruto or None
        else:
            dados[campo] = bruto

    return dados


def _importar_csv_simples(request, model, serializer_class, coluna_chave, colunas_dados):
    """
    Upsert genérico por uma coluna-chave, para CSVs de texto simples
    (sem parsing especial de número/FK). Usado por Categoria e Fornecedor.
    """
    arquivo = request.FILES.get('arquivo')
    if not arquivo:
        return Response(
            {'detail': 'Envie um arquivo CSV no campo "arquivo".'},
            status=status.HTTP_400_BAD_REQUEST,
        )

    try:
        leitor = _ler_csv(arquivo)
    except UnicodeDecodeError:
        return Response(
            {'detail': 'Não foi possível ler o arquivo. Salve o CSV em UTF-8.'},
            status=status.HTTP_400_BAD_REQUEST,
        )

    colunas_presentes = set(leitor.fieldnames or [])
    if coluna_chave not in colunas_presentes:
        return Response(
            {'detail': f'Não foi possível identificar as colunas do CSV. A coluna "{coluna_chave}" é obrigatória.'},
            status=status.HTTP_400_BAD_REQUEST,
        )

    criados = 0
    atualizados = 0
    erros = []
    for numero_linha, linha in enumerate(leitor, start=2):
        chave = (linha.get(coluna_chave) or '').strip()
        if not chave:
            erros.append({'linha': numero_linha, 'mensagem': f'{coluna_chave}: não pode ser vazio.'})
            continue

        dados = {coluna_chave: chave}
        for campo in colunas_dados:
            if campo in colunas_presentes:
                dados[campo] = (linha.get(campo) or '').strip()

        instancia = model.objects.filter(**{coluna_chave: chave}).first()
        serializer = serializer_class(instancia, data=dados, partial=bool(instancia))
        if serializer.is_valid():
            serializer.save()
            if instancia:
                atualizados += 1
            else:
                criados += 1
        else:
            erros.append({'linha': numero_linha, 'mensagem': _formatar_erros(serializer.errors)})

    return Response(
        {'criados': criados, 'atualizados': atualizados, 'erros': erros},
        status=status.HTTP_200_OK,
    )


def _exportar_csv_simples(queryset, nome_arquivo, colunas, extrair_linha):
    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = f'attachment; filename="{nome_arquivo}"'

    escritor = csv.writer(response)
    escritor.writerow(colunas)
    for objeto in queryset:
        escritor.writerow(extrair_linha(objeto))

    return response


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
        Colunas obrigatórias: nome,quantidade
        Colunas opcionais: sku,codigo_barras,descricao,categoria,fornecedor,
        unidade_medida,estoque_minimo,preco_custo,preco,ativo
        (categoria/fornecedor são identificados pelo nome; se não existirem, são criados)
        Se já existir um produto com o mesmo nome, os campos presentes na linha são
        atualizados (células vazias não sobrescrevem valores já cadastrados);
        caso contrário, um novo produto é criado.
        Linhas inválidas são reportadas individualmente, sem interromper o restante do arquivo.
        """
        arquivo = request.FILES.get('arquivo')
        if not arquivo:
            return Response(
                {'detail': 'Envie um arquivo CSV no campo "arquivo".'},
                status=status.HTTP_400_BAD_REQUEST,
            )

        try:
            leitor = _ler_csv(arquivo)
        except UnicodeDecodeError:
            return Response(
                {'detail': 'Não foi possível ler o arquivo. Salve o CSV em UTF-8.'},
                status=status.HTTP_400_BAD_REQUEST,
            )

        colunas_presentes = set(leitor.fieldnames or [])
        colunas_obrigatorias = {'nome', 'quantidade'}
        if not colunas_obrigatorias.issubset(colunas_presentes):
            return Response(
                {
                    'detail': (
                        'Não foi possível identificar as colunas do CSV. Verifique se a primeira linha '
                        'contém ao menos "nome" e "quantidade", separadas por vírgula, ponto e vírgula ou tabulação.'
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
                dados = {
                    'quantidade': quantidade,
                    **_dados_opcionais_produto(linha, colunas_presentes, incluir_vazios=False),
                }
                serializer = ProdutoSerializer(produto_existente, data=dados, partial=True)
                if serializer.is_valid():
                    serializer.save()
                    atualizados += 1
                else:
                    erros.append({'linha': numero_linha, 'mensagem': _formatar_erros(serializer.errors)})
                continue

            dados = {
                'nome': nome,
                'quantidade': quantidade,
                **_dados_opcionais_produto(linha, colunas_presentes, incluir_vazios=True),
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
        escritor.writerow([
            'nome', 'sku', 'codigo_barras', 'categoria', 'fornecedor', 'unidade_medida',
            'quantidade', 'estoque_minimo', 'preco_custo', 'preco', 'ativo', 'descricao',
        ])
        for produto in self.get_queryset().select_related('categoria', 'fornecedor'):
            escritor.writerow([
                produto.nome,
                produto.sku or '',
                produto.codigo_barras,
                produto.categoria.nome if produto.categoria_id else '',
                produto.fornecedor.nome if produto.fornecedor_id else '',
                produto.unidade_medida,
                produto.quantidade,
                produto.estoque_minimo,
                produto.preco_custo,
                produto.preco,
                'true' if produto.ativo else 'false',
                produto.descricao,
            ])

        return response


class CategoriaViewSet(viewsets.ModelViewSet):
    """CRUD de categorias de produto."""
    queryset = Categoria.objects.all()
    serializer_class = CategoriaSerializer

    @action(detail=False, methods=['post'], parser_classes=[MultiPartParser])
    def importar_csv(self, request):
        """
        POST /api/categorias/importar_csv/  -> importação em lote via CSV
        Cabeçalho esperado: nome,descricao
        Categoria existente (mesmo nome) tem a descrição atualizada; caso
        contrário, uma nova categoria é criada.
        """
        return _importar_csv_simples(request, Categoria, CategoriaSerializer, 'nome', ['descricao'])

    @action(detail=False, methods=['get'])
    def exportar_csv(self, request):
        """GET /api/categorias/exportar_csv/  -> exporta todas as categorias como CSV"""
        return _exportar_csv_simples(
            self.get_queryset(), 'categorias.csv', ['nome', 'descricao'],
            lambda c: [c.nome, c.descricao],
        )


class FornecedorViewSet(viewsets.ModelViewSet):
    """CRUD de fornecedores."""
    queryset = Fornecedor.objects.all()
    serializer_class = FornecedorSerializer

    @action(detail=False, methods=['post'], parser_classes=[MultiPartParser])
    def importar_csv(self, request):
        """
        POST /api/fornecedores/importar_csv/  -> importação em lote via CSV
        Cabeçalho esperado: nome,cnpj,telefone,email,endereco
        Fornecedor existente (mesmo nome) tem os dados atualizados; caso
        contrário, um novo fornecedor é criado.
        """
        return _importar_csv_simples(
            request, Fornecedor, FornecedorSerializer, 'nome',
            ['cnpj', 'telefone', 'email', 'endereco'],
        )

    @action(detail=False, methods=['get'])
    def exportar_csv(self, request):
        """GET /api/fornecedores/exportar_csv/  -> exporta todos os fornecedores como CSV"""
        return _exportar_csv_simples(
            self.get_queryset(), 'fornecedores.csv', ['nome', 'cnpj', 'telefone', 'email', 'endereco'],
            lambda f: [f.nome, f.cnpj, f.telefone, f.email, f.endereco],
        )


class MovimentacaoViewSet(viewsets.ModelViewSet):
    """
    Registra requisições e devoluções, ajustando o estoque do produto
    dentro de uma transação atômica.
    """
    queryset = Movimentacao.objects.select_related('produto').all()
    serializer_class = MovimentacaoSerializer

    def get_queryset(self):
        """GET /api/movimentacoes/?produto=<id> -> histórico de um produto específico"""
        queryset = super().get_queryset()
        produto_id = self.request.query_params.get('produto')
        if produto_id:
            queryset = queryset.filter(produto_id=produto_id)
        return queryset

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
