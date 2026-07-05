from django.db import models


class Categoria(models.Model):
    nome = models.CharField(max_length=100, unique=True)
    descricao = models.TextField(blank=True)
    ativo = models.BooleanField(default=True)

    class Meta:
        ordering = ['nome']
        verbose_name_plural = 'categorias'

    def __str__(self):
        return self.nome


class Fornecedor(models.Model):
    nome = models.CharField(max_length=200, unique=True)
    cnpj = models.CharField(max_length=20, blank=True)
    telefone = models.CharField(max_length=20, blank=True)
    email = models.EmailField(blank=True)
    endereco = models.CharField(max_length=255, blank=True)
    ativo = models.BooleanField(default=True)

    class Meta:
        ordering = ['nome']

    def __str__(self):
        return self.nome


class Produto(models.Model):
    UNIDADE_UNIDADE = 'UN'
    UNIDADE_QUILOGRAMA = 'KG'
    UNIDADE_LITRO = 'LT'
    UNIDADE_METRO = 'MT'
    UNIDADE_CAIXA = 'CX'
    UNIDADE_PACOTE = 'PC'
    UNIDADE_CHOICES = [
        (UNIDADE_UNIDADE, 'Unidade'),
        (UNIDADE_QUILOGRAMA, 'Quilograma'),
        (UNIDADE_LITRO, 'Litro'),
        (UNIDADE_METRO, 'Metro'),
        (UNIDADE_CAIXA, 'Caixa'),
        (UNIDADE_PACOTE, 'Pacote'),
    ]

    nome = models.CharField(max_length=200, unique=True)
    sku = models.CharField('SKU', max_length=50, unique=True, null=True, blank=True)
    codigo_barras = models.CharField('código de barras', max_length=50, blank=True)
    descricao = models.TextField(blank=True)
    categoria = models.ForeignKey(
        Categoria, related_name='produtos', on_delete=models.SET_NULL, null=True, blank=True,
    )
    fornecedor = models.ForeignKey(
        Fornecedor, related_name='produtos', on_delete=models.SET_NULL, null=True, blank=True,
    )
    unidade_medida = models.CharField(max_length=2, choices=UNIDADE_CHOICES, default=UNIDADE_UNIDADE)
    quantidade = models.PositiveIntegerField(default=0)
    estoque_minimo = models.PositiveIntegerField(default=0)
    preco_custo = models.DecimalField('preço de custo', max_digits=10, decimal_places=2, default=0)
    preco = models.DecimalField('preço de venda', max_digits=10, decimal_places=2, default=0)
    ativo = models.BooleanField(default=True)
    criado_em = models.DateTimeField(auto_now_add=True)
    atualizado_em = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['nome']

    def __str__(self):
        return self.nome


class Movimentacao(models.Model):
    REQUISICAO = 'REQUISICAO'
    DEVOLUCAO = 'DEVOLUCAO'
    COMPRA = 'COMPRA'
    TIPO_CHOICES = [
        (REQUISICAO, 'Requisição'),
        (DEVOLUCAO, 'Devolução'),
        (COMPRA, 'Compra'),
    ]

    produto = models.ForeignKey(Produto, related_name='movimentacoes', on_delete=models.CASCADE)
    tipo = models.CharField(max_length=20, choices=TIPO_CHOICES)
    quantidade = models.PositiveIntegerField()
    solicitante = models.CharField(max_length=150)
    observacao = models.TextField(blank=True)
    data = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-data']

    def __str__(self):
        return f'{self.get_tipo_display()} - {self.produto.nome} ({self.quantidade})'


class NotaFiscalCompra(models.Model):
    chave_acesso = models.CharField(max_length=44, unique=True)
    numero = models.CharField(max_length=20, blank=True)
    fornecedor = models.ForeignKey(
        Fornecedor, related_name='notas_fiscais', on_delete=models.SET_NULL, null=True,
    )
    valor_total = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    data_emissao = models.DateTimeField(null=True, blank=True)
    importado_em = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-importado_em']

    def __str__(self):
        return f'NF-e {self.numero or self.chave_acesso}'


class ItemNotaFiscalCompra(models.Model):
    nota_fiscal = models.ForeignKey(NotaFiscalCompra, related_name='itens', on_delete=models.CASCADE)
    numero_item = models.PositiveIntegerField()
    codigo_produto_fornecedor = models.CharField(max_length=60, blank=True)
    descricao = models.CharField(max_length=255)
    quantidade = models.DecimalField(max_digits=12, decimal_places=4)
    valor_unitario = models.DecimalField(max_digits=12, decimal_places=4)
    produto = models.ForeignKey(
        Produto, related_name='itens_nfe', on_delete=models.SET_NULL, null=True, blank=True,
    )
    movimentacao = models.ForeignKey(
        Movimentacao, related_name='+', on_delete=models.SET_NULL, null=True, blank=True,
    )
    processado = models.BooleanField(default=False)

    class Meta:
        ordering = ['numero_item']
        unique_together = [('nota_fiscal', 'numero_item')]

    def __str__(self):
        return f'Item {self.numero_item} - {self.descricao}'
