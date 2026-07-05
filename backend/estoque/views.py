import csv
import io
import re
from decimal import Decimal

from django.http import HttpResponse
from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.exceptions import ValidationError
from rest_framework.parsers import MultiPartParser
from rest_framework.response import Response

from . import nfe
from .models import Produto, Categoria, Fornecedor, Movimentacao, NotaFiscalCompra, ItemNotaFiscalCompra
from .serializers import ProdutoSerializer, CategoriaSerializer, FornecedorSerializer, MovimentacaoSerializer
from .services import ServicoEstoque, SaldoInsuficienteError, TIPOS_ENTRADA


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


def _valor_categoria(nome, empresa):
    nome = (nome or '').strip()
    if not nome:
        return None
    categoria, _ = Categoria.objects.get_or_create(empresa=empresa, nome=nome)
    return categoria.id


def _valor_fornecedor(nome, empresa):
    nome = (nome or '').strip()
    if not nome:
        return None
    fornecedor, _ = Fornecedor.objects.get_or_create(empresa=empresa, nome=nome)
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


def _dados_opcionais_produto(linha, colunas_presentes, incluir_vazios, empresa):
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
            dados['categoria'] = _valor_categoria(bruto, empresa)
        elif campo == 'fornecedor':
            dados['fornecedor'] = _valor_fornecedor(bruto, empresa)
        elif campo == 'preco':
            dados['preco'] = _valor_preco(bruto)
        elif campo == 'preco_custo':
            dados['preco_custo_referencia'] = _valor_preco(bruto)
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

    empresa = ServicoEstoque.get_empresa_padrao()
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

        instancia = model.objects.filter(empresa=empresa, **{coluna_chave: chave}).first()
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


class InativarAoRemoverMixin:
    """
    Substitui o comportamento padrão do DELETE: em vez de remover o registro
    do banco, marca ativo=False. Nenhuma entidade do sistema (Produto,
    Categoria, Fornecedor) é de fato excluída — só deixa de aparecer como ativa.
    """
    def perform_destroy(self, instance):
        instance.ativo = False
        instance.save(update_fields=['ativo'])


def _buscar_produto_por_item_nfe(item_nfe, empresa):
    """Casa um item da NF-e com um Produto existente por SKU (código do
    fornecedor) ou, na falta desse match, por nome. Nunca cria produto novo."""
    codigo = (item_nfe.codigo_produto_fornecedor or '').strip()
    if codigo:
        produto = Produto.objects.filter(empresa=empresa, sku=codigo).first()
        if produto:
            return produto
    return Produto.objects.filter(empresa=empresa, nome__iexact=item_nfe.descricao.strip()).first()


def _obter_ou_criar_fornecedor_por_nfe(emitente, empresa):
    """Casa o emitente da NF-e com um Fornecedor existente por CNPJ (normalizado,
    já que o campo não tem formatação obrigatória) ou por nome; cria se não achar."""
    cnpj_nota = re.sub(r'\D', '', emitente.cnpj or '')
    if cnpj_nota:
        for fornecedor in Fornecedor.objects.filter(empresa=empresa).exclude(cnpj=''):
            if re.sub(r'\D', '', fornecedor.cnpj) == cnpj_nota:
                return fornecedor

    fornecedor, _ = Fornecedor.objects.get_or_create(
        empresa=empresa,
        nome__iexact=emitente.nome,
        defaults={'nome': emitente.nome, 'cnpj': emitente.cnpj},
    )
    return fornecedor


class ProdutoViewSet(InativarAoRemoverMixin, viewsets.ModelViewSet):
    """
    CRUD completo de produtos.
    GET    /api/produtos/       -> lista (aceita ?nome=, ?categoria=<id>, ?fornecedor=<id> para filtrar)
    POST   /api/produtos/       -> cria
    GET    /api/produtos/{id}/  -> detalhe
    PUT    /api/produtos/{id}/  -> atualiza
    DELETE /api/produtos/{id}/  -> inativa (define ativo=False; não remove o registro)
    """
    queryset = Produto.objects.all()
    serializer_class = ProdutoSerializer

    def get_queryset(self):
        """
        Filtros opcionais de busca na listagem:
        ?nome=<texto>       -> busca parcial, sem diferenciar maiúsculas/minúsculas
        ?categoria=<id>     -> só produtos dessa categoria
        ?fornecedor=<id>    -> só produtos desse fornecedor
        """
        queryset = super().get_queryset().filter(empresa=ServicoEstoque.get_empresa_padrao())

        nome = self.request.query_params.get('nome')
        if nome:
            queryset = queryset.filter(nome__icontains=nome)

        categoria_id = self.request.query_params.get('categoria')
        if categoria_id:
            queryset = queryset.filter(categoria_id=categoria_id)

        fornecedor_id = self.request.query_params.get('fornecedor')
        if fornecedor_id:
            queryset = queryset.filter(fornecedor_id=fornecedor_id)

        return queryset

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
        caso contrário, um novo produto é criado. A coluna "quantidade" nunca
        sobrescreve o saldo diretamente — gera um ajuste de inventário com histórico.
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

        empresa = ServicoEstoque.get_empresa_padrao()
        criados = 0
        atualizados = 0
        erros = []
        # linha 1 é o cabeçalho, então os dados começam na linha 2
        for numero_linha, linha in enumerate(leitor, start=2):
            nome = (linha.get('nome') or '').strip()
            quantidade = (linha.get('quantidade') or '0').strip()

            produto_existente = Produto.objects.filter(empresa=empresa, nome=nome).first() if nome else None

            if produto_existente:
                dados = _dados_opcionais_produto(linha, colunas_presentes, incluir_vazios=False, empresa=empresa)
                serializer = ProdutoSerializer(produto_existente, data=dados, partial=True)
                if serializer.is_valid():
                    produto = serializer.save()
                    ServicoEstoque.definir_saldo_inicial(produto, quantidade, usuario=request.user)
                    atualizados += 1
                else:
                    erros.append({'linha': numero_linha, 'mensagem': _formatar_erros(serializer.errors)})
                continue

            dados = {
                'nome': nome,
                **_dados_opcionais_produto(linha, colunas_presentes, incluir_vazios=True, empresa=empresa),
            }
            serializer = ProdutoSerializer(data=dados)
            if serializer.is_valid():
                produto = serializer.save()
                ServicoEstoque.definir_saldo_inicial(produto, quantidade, usuario=request.user)
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
                ServicoEstoque.saldo_disponivel(produto),
                produto.estoque_minimo,
                produto.preco_custo_referencia,
                produto.preco,
                'true' if produto.ativo else 'false',
                produto.descricao,
            ])

        return response

    @action(detail=False, methods=['post'], parser_classes=[MultiPartParser])
    def importar_nfe(self, request):
        """
        POST /api/produtos/importar_nfe/  -> dá entrada em estoque a partir do
        XML de uma NF-e de compra (padrão SEFAZ).

        Casa os itens da nota com produtos existentes por SKU (código do
        produto no fornecedor) ou por nome. Itens sem correspondência NÃO
        criam produto novo: ficam pendentes em "nao_encontrados" até o
        produto ser cadastrado manualmente e o mesmo arquivo ser reimportado.
        Reimportar o mesmo arquivo é seguro — itens já processados são
        ignorados (idempotente), só os pendentes/com erro são reprocessados.
        """
        arquivo = request.FILES.get('arquivo')
        if not arquivo:
            return Response(
                {'detail': 'Envie o XML da NF-e no campo "arquivo".'},
                status=status.HTTP_400_BAD_REQUEST,
            )

        try:
            dados = nfe.parse_nfe(arquivo.read())
        except nfe.NFeInvalidaError as exc:
            return Response({'detail': str(exc)}, status=status.HTTP_400_BAD_REQUEST)

        empresa = ServicoEstoque.get_empresa_padrao()
        fornecedor = _obter_ou_criar_fornecedor_por_nfe(dados.emitente, empresa)
        nota_fiscal, _ = NotaFiscalCompra.objects.get_or_create(
            chave_acesso=dados.chave_acesso,
            defaults={
                'empresa': empresa,
                'numero': dados.numero,
                'fornecedor': fornecedor,
                'valor_total': dados.valor_total,
                'data_emissao': dados.data_emissao,
            },
        )

        itens_processados = 0
        itens_ja_processados = 0
        nao_encontrados = []
        erros = []

        for item_nfe in dados.itens:
            item_registro, _ = ItemNotaFiscalCompra.objects.get_or_create(
                nota_fiscal=nota_fiscal,
                numero_item=item_nfe.numero_item,
                defaults={
                    'codigo_produto_fornecedor': item_nfe.codigo_produto_fornecedor,
                    'descricao': item_nfe.descricao,
                    'quantidade': item_nfe.quantidade,
                    'valor_unitario': item_nfe.valor_unitario,
                },
            )

            if item_registro.processado:
                itens_ja_processados += 1
                continue

            produto = _buscar_produto_por_item_nfe(item_nfe, empresa)
            if produto is None:
                nao_encontrados.append({
                    'item': item_nfe.numero_item,
                    'codigo_fornecedor': item_nfe.codigo_produto_fornecedor,
                    'descricao': item_nfe.descricao,
                })
                continue

            preco_custo = item_nfe.valor_unitario.quantize(Decimal('0.01'))
            preco_serializer = ProdutoSerializer(
                produto, data={'preco_custo_referencia': str(preco_custo)}, partial=True,
            )
            if not preco_serializer.is_valid():
                erros.append({'item': item_nfe.numero_item, 'mensagem': _formatar_erros(preco_serializer.errors)})
                continue

            preco_serializer.save()
            movimentacao = ServicoEstoque.registrar_entrada(
                produto=produto,
                tipo=Movimentacao.COMPRA,
                quantidade=item_nfe.quantidade,
                custo_unitario=item_nfe.valor_unitario,
                usuario=request.user,
                observacao=f'Compra via NF-e {dados.numero}',
            )
            item_registro.produto = produto
            item_registro.movimentacao = movimentacao
            item_registro.processado = True
            item_registro.save(update_fields=['produto', 'movimentacao', 'processado'])

            itens_processados += 1

        return Response({
            'numero_nfe': dados.numero,
            'fornecedor': fornecedor.nome,
            'itens_processados': itens_processados,
            'itens_ja_processados': itens_ja_processados,
            'nao_encontrados': nao_encontrados,
            'erros': erros,
        }, status=status.HTTP_200_OK)


class CategoriaViewSet(InativarAoRemoverMixin, viewsets.ModelViewSet):
    """
    CRUD de categorias de produto. GET aceita ?nome=<texto> para filtrar.
    DELETE inativa (define ativo=False) em vez de remover o registro.
    """
    queryset = Categoria.objects.all()
    serializer_class = CategoriaSerializer

    def get_queryset(self):
        queryset = super().get_queryset().filter(empresa=ServicoEstoque.get_empresa_padrao())
        nome = self.request.query_params.get('nome')
        if nome:
            queryset = queryset.filter(nome__icontains=nome)
        return queryset

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


class FornecedorViewSet(InativarAoRemoverMixin, viewsets.ModelViewSet):
    """
    CRUD de fornecedores. GET aceita ?nome=<texto> para filtrar.
    DELETE inativa (define ativo=False) em vez de remover o registro.
    """
    queryset = Fornecedor.objects.all()
    serializer_class = FornecedorSerializer

    def get_queryset(self):
        queryset = super().get_queryset().filter(empresa=ServicoEstoque.get_empresa_padrao())
        nome = self.request.query_params.get('nome')
        if nome:
            queryset = queryset.filter(nome__icontains=nome)
        return queryset

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
    Registra requisições, devoluções, compras e ajustes de inventário,
    delegando o cálculo/gravação do saldo ao ServicoEstoque.
    """
    queryset = Movimentacao.objects.select_related('produto').all()
    serializer_class = MovimentacaoSerializer

    def get_queryset(self):
        """GET /api/movimentacoes/?produto=<id> -> histórico de um produto específico"""
        queryset = super().get_queryset().filter(empresa=ServicoEstoque.get_empresa_padrao())
        produto_id = self.request.query_params.get('produto')
        if produto_id:
            queryset = queryset.filter(produto_id=produto_id)
        return queryset

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        dados = serializer.validated_data
        tipo = dados['tipo']

        try:
            if tipo in TIPOS_ENTRADA:
                movimentacao = ServicoEstoque.registrar_entrada(
                    produto=dados['produto'],
                    quantidade=dados['quantidade'],
                    custo_unitario=dados.get('custo_unitario'),
                    usuario=request.user,
                    tipo=tipo,
                    observacao=dados.get('observacao', ''),
                )
            else:
                movimentacao = ServicoEstoque.registrar_saida(
                    produto=dados['produto'],
                    quantidade=dados['quantidade'],
                    usuario=request.user,
                    tipo=tipo,
                    observacao=dados.get('observacao', ''),
                    solicitante=dados.get('solicitante', ''),
                )
        except SaldoInsuficienteError as exc:
            raise ValidationError(exc.mensagem)

        return Response(self.get_serializer(movimentacao).data, status=status.HTTP_201_CREATED)
