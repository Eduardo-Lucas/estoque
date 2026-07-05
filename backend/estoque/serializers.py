from decimal import Decimal

from rest_framework import serializers

from .models import Categoria, Fornecedor, Movimentacao, Produto
from .services import ServicoEstoque, TIPOS_SAIDA


class _EmpresaDoUsuarioDefault:
    """Default de campo oculto usado por todo serializer com unique_together
    envolvendo `empresa`: sem isso o DRF não consegue gerar o
    UniqueTogetherValidator (precisa que todo campo da constraint esteja no
    serializer) e a violação vaza como IntegrityError/500 em vez de 400.

    Mesmo protocolo que `serializers.CurrentUserDefault` usa
    (`requires_context = True`) — o ViewSet já passa `request` no contexto
    por padrão, então nenhum outro lugar precisa mudar por causa disso."""

    requires_context = True

    def __call__(self, serializer_field):
        return serializer_field.context['request'].user.empresa

    def __repr__(self):
        return '%s()' % self.__class__.__name__


class CategoriaSerializer(serializers.ModelSerializer):
    empresa = serializers.HiddenField(default=_EmpresaDoUsuarioDefault())

    class Meta:
        model = Categoria
        fields = ['id', 'empresa', 'nome', 'descricao', 'ativo']


class FornecedorSerializer(serializers.ModelSerializer):
    empresa = serializers.HiddenField(default=_EmpresaDoUsuarioDefault())

    class Meta:
        model = Fornecedor
        fields = ['id', 'empresa', 'nome', 'cnpj', 'telefone', 'email', 'endereco', 'ativo']


class ProdutoSerializer(serializers.ModelSerializer):
    empresa = serializers.HiddenField(default=_EmpresaDoUsuarioDefault())
    # unique_together com "empresa" faz o DRF forçar required=True em campos
    # sem default (mesmo com null=True/blank=True no model) — precisa de um
    # default explícito para sku continuar opcional.
    sku = serializers.CharField(max_length=50, required=False, allow_null=True, default=None)
    categoria_nome = serializers.SerializerMethodField()
    fornecedor_nome = serializers.SerializerMethodField()
    saldo = serializers.SerializerMethodField()
    custo_medio = serializers.SerializerMethodField()

    def get_categoria_nome(self, obj):
        return obj.categoria.nome if obj.categoria_id else None

    def get_fornecedor_nome(self, obj):
        return obj.fornecedor.nome if obj.fornecedor_id else None

    def get_saldo(self, obj):
        return ServicoEstoque.saldo_disponivel(obj)

    def get_custo_medio(self, obj):
        deposito = ServicoEstoque.get_deposito_padrao(obj.empresa)
        saldo = obj.saldos.filter(deposito=deposito).first()
        return saldo.custo_medio if saldo else Decimal('0.0000')

    def get_fields(self):
        # categoria/fornecedor não podem apontar pra outra empresa — sem isso
        # bastaria adivinhar o id de uma categoria alheia pra "vazar" a
        # referência entre tenants (o registro em si continuaria isolado,
        # mas o FK ficaria incoerente).
        fields = super().get_fields()
        request = self.context.get('request')
        empresa = getattr(getattr(request, 'user', None), 'empresa', None)
        if empresa is not None:
            fields['categoria'].queryset = Categoria.objects.filter(empresa=empresa)
            fields['fornecedor'].queryset = Fornecedor.objects.filter(empresa=empresa)
        return fields

    class Meta:
        model = Produto
        fields = [
            'id', 'empresa', 'nome', 'sku', 'codigo_barras', 'descricao',
            'categoria', 'categoria_nome', 'fornecedor', 'fornecedor_nome',
            'unidade_medida', 'saldo', 'custo_medio', 'estoque_minimo',
            'preco_custo_referencia', 'preco', 'ativo', 'criado_em', 'atualizado_em',
        ]
        read_only_fields = ['criado_em', 'atualizado_em']


class MovimentacaoSerializer(serializers.ModelSerializer):
    produto_nome = serializers.CharField(source='produto.nome', read_only=True)

    def get_fields(self):
        # mesma razão do ProdutoSerializer: produto não pode ser de outra empresa.
        fields = super().get_fields()
        request = self.context.get('request')
        empresa = getattr(getattr(request, 'user', None), 'empresa', None)
        if empresa is not None:
            fields['produto'].queryset = Produto.objects.filter(empresa=empresa)
        return fields

    class Meta:
        model = Movimentacao
        fields = [
            'id', 'produto', 'produto_nome', 'tipo', 'quantidade',
            'custo_unitario', 'solicitante', 'observacao', 'data',
        ]
        read_only_fields = ['data']

    def validate(self, attrs):
        produto = attrs.get('produto')
        tipo = attrs.get('tipo')
        quantidade = attrs.get('quantidade')

        if tipo in TIPOS_SAIDA and produto and quantidade and not produto.resolve_permite_estoque_negativo():
            saldo = ServicoEstoque.saldo_disponivel(produto)
            if quantidade > saldo:
                raise serializers.ValidationError(
                    f'Estoque insuficiente para "{produto.nome}". Disponível: {saldo}.'
                )
        return attrs
