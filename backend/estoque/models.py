from django.db import models


class Empresa(models.Model):
    """Tenant raiz. Nesta PR existe só como scaffolding: uma única linha
    'padrão' semeada por migration, sem login/seleção de empresa amarrado
    a ela ainda — isso fica para a PR de autenticação multi-tenant."""

    razao_social = models.CharField(max_length=255)
    nome_fantasia = models.CharField(max_length=255, blank=True)
    cnpj = models.CharField(max_length=20, unique=True)
    ativo = models.BooleanField(default=True)
    criado_em = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name_plural = 'empresas'

    def __str__(self):
        return self.nome_fantasia or self.razao_social


class Deposito(models.Model):
    """Depósito/local de estoque. Nesta PR toda empresa tem exatamente um
    depósito 'PADRAO' (semeado por migration); múltiplos depósitos por
    empresa e transferência entre eles ficam para uma PR futura."""

    empresa = models.ForeignKey(Empresa, on_delete=models.CASCADE, related_name='depositos')
    codigo = models.CharField(max_length=20)
    nome = models.CharField(max_length=100)
    ativo = models.BooleanField(default=True)

    class Meta:
        ordering = ['nome']
        unique_together = ('empresa', 'codigo')

    def __str__(self):
        return self.nome


class Categoria(models.Model):
    empresa = models.ForeignKey(Empresa, on_delete=models.CASCADE, related_name='categorias')
    nome = models.CharField(max_length=100)
    descricao = models.TextField(blank=True)
    ativo = models.BooleanField(default=True)

    class Meta:
        ordering = ['nome']
        unique_together = ('empresa', 'nome')
        verbose_name_plural = 'categorias'

    def __str__(self):
        return self.nome


class Fornecedor(models.Model):
    empresa = models.ForeignKey(Empresa, on_delete=models.CASCADE, related_name='fornecedores')
    nome = models.CharField(max_length=200)
    cnpj = models.CharField(max_length=20, blank=True)
    telefone = models.CharField(max_length=20, blank=True)
    email = models.EmailField(blank=True)
    endereco = models.CharField(max_length=255, blank=True)
    ativo = models.BooleanField(default=True)

    class Meta:
        ordering = ['nome']
        unique_together = ('empresa', 'nome')

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

    empresa = models.ForeignKey(Empresa, on_delete=models.CASCADE, related_name='produtos')
    nome = models.CharField(max_length=200)
    sku = models.CharField('SKU', max_length=50, null=True, blank=True)
    codigo_barras = models.CharField('código de barras', max_length=50, blank=True)
    descricao = models.TextField(blank=True)
    categoria = models.ForeignKey(
        Categoria, related_name='produtos', on_delete=models.SET_NULL, null=True, blank=True,
    )
    fornecedor = models.ForeignKey(
        Fornecedor, related_name='produtos', on_delete=models.SET_NULL, null=True, blank=True,
    )
    unidade_medida = models.CharField(max_length=2, choices=UNIDADE_CHOICES, default=UNIDADE_UNIDADE)
    # Saldo deixou de ser um campo mutável aqui — é derivado do ledger de
    # Movimentacao e cacheado em SaldoEstoque (sempre escrito via services.ServicoEstoque).
    estoque_minimo = models.PositiveIntegerField(default=0)
    # Só usado como valor de referência/fallback em importações; o custo real
    # em uso é SaldoEstoque.custo_medio, mantido pelo ServicoEstoque.
    preco_custo_referencia = models.DecimalField(
        'preço de custo (referência)', max_digits=10, decimal_places=2, default=0,
    )
    preco = models.DecimalField('preço de venda', max_digits=10, decimal_places=2, default=0)
    ativo = models.BooleanField(default=True)
    criado_em = models.DateTimeField(auto_now_add=True)
    atualizado_em = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['nome']
        unique_together = ('empresa', 'sku')

    def __str__(self):
        return self.nome


class Movimentacao(models.Model):
    REQUISICAO = 'REQUISICAO'
    DEVOLUCAO = 'DEVOLUCAO'
    COMPRA = 'COMPRA'
    AJUSTE_POSITIVO = 'AJUSTE_POSITIVO'
    AJUSTE_NEGATIVO = 'AJUSTE_NEGATIVO'
    TIPO_CHOICES = [
        (REQUISICAO, 'Requisição'),
        (DEVOLUCAO, 'Devolução'),
        (COMPRA, 'Compra'),
        (AJUSTE_POSITIVO, 'Ajuste de inventário (+)'),
        (AJUSTE_NEGATIVO, 'Ajuste de inventário (-)'),
    ]

    empresa = models.ForeignKey(Empresa, on_delete=models.CASCADE, related_name='movimentacoes')
    produto = models.ForeignKey(Produto, related_name='movimentacoes', on_delete=models.CASCADE)
    deposito = models.ForeignKey(Deposito, on_delete=models.PROTECT, related_name='movimentacoes')
    tipo = models.CharField(max_length=20, choices=TIPO_CHOICES)
    quantidade = models.DecimalField(max_digits=14, decimal_places=3)
    # Informado em entradas (COMPRA/AJUSTE_POSITIVO) para atualizar a média
    # móvel em SaldoEstoque.custo_medio; ausente em saídas.
    custo_unitario = models.DecimalField(max_digits=14, decimal_places=4, null=True, blank=True)
    solicitante = models.CharField(max_length=150)
    observacao = models.TextField(blank=True)
    data = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-data']

    def __str__(self):
        return f'{self.get_tipo_display()} - {self.produto.nome} ({self.quantidade})'


class SaldoEstoque(models.Model):
    """Fonte da verdade para consulta rápida de saldo — sempre mantida por
    ServicoEstoque (services.py) dentro da mesma transação da Movimentacao
    que a originou. Nunca editar diretamente."""

    empresa = models.ForeignKey(Empresa, on_delete=models.CASCADE, related_name='saldos')
    produto = models.ForeignKey(Produto, on_delete=models.CASCADE, related_name='saldos')
    deposito = models.ForeignKey(Deposito, on_delete=models.CASCADE, related_name='saldos')
    quantidade = models.DecimalField(max_digits=14, decimal_places=3, default=0)
    custo_medio = models.DecimalField(max_digits=14, decimal_places=4, default=0)
    atualizado_em = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = ('produto', 'deposito')
        indexes = [models.Index(fields=['empresa', 'produto'], name='estoque_sal_empresa_idx')]

    def __str__(self):
        return f'{self.produto.nome}@{self.deposito.codigo}: {self.quantidade}'


class NotaFiscalCompra(models.Model):
    empresa = models.ForeignKey(Empresa, on_delete=models.CASCADE, related_name='notas_fiscais')
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
