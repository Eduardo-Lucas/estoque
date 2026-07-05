from django.conf import settings
from django.core.exceptions import ValidationError
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


class RegimeTributario(models.TextChoices):
    SIMPLES_NACIONAL = 'simples_nacional', 'Simples Nacional'
    LUCRO_PRESUMIDO = 'lucro_presumido', 'Lucro Presumido'
    LUCRO_REAL = 'lucro_real', 'Lucro Real'
    MEI = 'mei', 'MEI'


class MetodoValoracao(models.TextChoices):
    FIFO = 'fifo', 'PEPS / FIFO'
    MEDIA_MOVEL = 'media_movel', 'Custo Médio Móvel'
    CUSTO_PADRAO = 'custo_padrao', 'Custo Padrão (Standard Cost)'


class ConfiguracaoEstoque(models.Model):
    """Parametrização por empresa consumida por `services.obter_estrategia`
    para escolher a estratégia de custeio (e, no futuro, o comportamento
    fiscal). Toda empresa precisa de exatamente uma linha aqui — a empresa
    padrão já vem semeada por migration."""

    empresa = models.OneToOneField(Empresa, on_delete=models.CASCADE, related_name='config_estoque')
    regime_tributario = models.CharField(
        max_length=30, choices=RegimeTributario.choices, default=RegimeTributario.SIMPLES_NACIONAL,
    )
    metodo_valoracao = models.CharField(
        max_length=20, choices=MetodoValoracao.choices, default=MetodoValoracao.MEDIA_MOVEL,
    )
    permite_estoque_negativo = models.BooleanField(default=False)
    controla_lote_por_padrao = models.BooleanField(default=False)
    multi_deposito = models.BooleanField(default=True)

    class Meta:
        verbose_name_plural = 'configurações de estoque'

    def __str__(self):
        return f'Config[{self.empresa}] {self.metodo_valoracao}/{self.regime_tributario}'


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
    # Overrides por produto — None = herda de ConfiguracaoEstoque.
    controla_lote = models.BooleanField(null=True, blank=True)
    permite_estoque_negativo = models.BooleanField(null=True, blank=True)
    ativo = models.BooleanField(default=True)
    criado_em = models.DateTimeField(auto_now_add=True)
    atualizado_em = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['nome']
        unique_together = ('empresa', 'sku')

    def __str__(self):
        return self.nome

    def resolve_controla_lote(self) -> bool:
        if self.controla_lote is not None:
            return self.controla_lote
        return self.empresa.config_estoque.controla_lote_por_padrao

    def resolve_permite_estoque_negativo(self) -> bool:
        if self.permite_estoque_negativo is not None:
            return self.permite_estoque_negativo
        return self.empresa.config_estoque.permite_estoque_negativo


class Lote(models.Model):
    """Opcional — só relevante quando `Produto.resolve_controla_lote()` é True."""

    produto = models.ForeignKey(Produto, on_delete=models.CASCADE, related_name='lotes')
    numero_lote = models.CharField(max_length=64)
    data_fabricacao = models.DateField(null=True, blank=True)
    data_validade = models.DateField(null=True, blank=True)

    class Meta:
        unique_together = ('produto', 'numero_lote')

    def __str__(self):
        return f'{self.produto.sku}/{self.numero_lote}'


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
    lote = models.ForeignKey(Lote, on_delete=models.PROTECT, null=True, blank=True, related_name='movimentacoes')
    tipo = models.CharField(max_length=20, choices=TIPO_CHOICES)
    quantidade = models.DecimalField(max_digits=14, decimal_places=3)
    # Informado em entradas (COMPRA/AJUSTE_POSITIVO) para atualizar o custo em
    # SaldoEstoque (média móvel/FIFO/custo padrão, conforme a estratégia da
    # empresa); em saídas é preenchido pela própria estratégia de custeio.
    custo_unitario = models.DecimalField(max_digits=14, decimal_places=4, null=True, blank=True)
    # Preenchido em saídas (quem solicitou); entradas de compra/ajuste não têm
    # solicitante — usam `usuario` para saber quem lançou a movimentação.
    solicitante = models.CharField(max_length=150, blank=True)
    # Obrigatório: toda movimentação precisa do log de quem a lançou.
    usuario = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT, related_name='+')
    observacao = models.TextField(blank=True)
    data = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-data']

    def __str__(self):
        return f'{self.get_tipo_display()} - {self.produto.nome} ({self.quantidade})'

    def clean(self):
        if self.produto.resolve_controla_lote() and self.lote_id is None:
            raise ValidationError(
                f'Produto {self.produto.sku or self.produto.nome} exige controle de lote.'
            )


class SaldoEstoque(models.Model):
    """Fonte da verdade para consulta rápida de saldo — sempre mantida por
    ServicoEstoque (services.py) dentro da mesma transação da Movimentacao
    que a originou. Nunca editar diretamente."""

    empresa = models.ForeignKey(Empresa, on_delete=models.CASCADE, related_name='saldos')
    produto = models.ForeignKey(Produto, on_delete=models.CASCADE, related_name='saldos')
    deposito = models.ForeignKey(Deposito, on_delete=models.CASCADE, related_name='saldos')
    lote = models.ForeignKey(Lote, on_delete=models.CASCADE, null=True, blank=True, related_name='saldos')
    quantidade = models.DecimalField(max_digits=14, decimal_places=3, default=0)
    custo_medio = models.DecimalField(max_digits=14, decimal_places=4, default=0)
    quantidade_reservada = models.DecimalField(max_digits=14, decimal_places=3, default=0)
    atualizado_em = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = ('produto', 'deposito', 'lote')
        indexes = [models.Index(fields=['empresa', 'produto'], name='estoque_sal_empresa_idx')]

    @property
    def quantidade_disponivel(self):
        return self.quantidade - self.quantidade_reservada

    def __str__(self):
        return f'{self.produto.nome}@{self.deposito.codigo}: {self.quantidade}'


class CamadaCusto(models.Model):
    """Sustenta o motor FIFO (EstrategiaFIFO em services.py). Não usada pelas
    demais estratégias de custeio (média móvel/custo padrão)."""

    produto = models.ForeignKey(Produto, on_delete=models.PROTECT, related_name='camadas_custo')
    deposito = models.ForeignKey(Deposito, on_delete=models.PROTECT, related_name='camadas_custo')
    lote = models.ForeignKey(Lote, on_delete=models.PROTECT, null=True, blank=True, related_name='camadas_custo')
    movimento_origem = models.ForeignKey(Movimentacao, on_delete=models.PROTECT, related_name='camada_gerada')

    quantidade_original = models.DecimalField(max_digits=14, decimal_places=3)
    quantidade_disponivel = models.DecimalField(max_digits=14, decimal_places=3)
    custo_unitario = models.DecimalField(max_digits=14, decimal_places=4)
    criado_em = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['criado_em']  # ordem natural de consumo FIFO
        indexes = [models.Index(fields=['produto', 'deposito', 'criado_em'])]
        constraints = [
            models.CheckConstraint(check=models.Q(quantidade_disponivel__gte=0), name='camada_saldo_nao_negativo'),
        ]

    def __str__(self):
        return f'Camada[{self.produto.nome}] {self.quantidade_disponivel}/{self.quantidade_original}'


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
