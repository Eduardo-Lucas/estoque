from rest_framework import serializers
from .models import Produto, Categoria, Fornecedor, Movimentacao


class CategoriaSerializer(serializers.ModelSerializer):
    class Meta:
        model = Categoria
        fields = ['id', 'nome', 'descricao']


class FornecedorSerializer(serializers.ModelSerializer):
    class Meta:
        model = Fornecedor
        fields = ['id', 'nome', 'cnpj', 'telefone', 'email', 'endereco']


class ProdutoSerializer(serializers.ModelSerializer):
    categoria_nome = serializers.SerializerMethodField()
    fornecedor_nome = serializers.SerializerMethodField()

    def get_categoria_nome(self, obj):
        return obj.categoria.nome if obj.categoria_id else None

    def get_fornecedor_nome(self, obj):
        return obj.fornecedor.nome if obj.fornecedor_id else None

    class Meta:
        model = Produto
        fields = [
            'id', 'nome', 'sku', 'codigo_barras', 'descricao',
            'categoria', 'categoria_nome', 'fornecedor', 'fornecedor_nome',
            'unidade_medida', 'quantidade', 'estoque_minimo',
            'preco_custo', 'preco', 'ativo', 'criado_em', 'atualizado_em',
        ]
        read_only_fields = ['criado_em', 'atualizado_em']


class MovimentacaoSerializer(serializers.ModelSerializer):
    produto_nome = serializers.CharField(source='produto.nome', read_only=True)

    class Meta:
        model = Movimentacao
        fields = ['id', 'produto', 'produto_nome', 'tipo', 'quantidade', 'solicitante', 'observacao', 'data']
        read_only_fields = ['data']

    def validate(self, attrs):
        produto = attrs.get('produto')
        tipo = attrs.get('tipo')
        quantidade = attrs.get('quantidade')

        if tipo == Movimentacao.REQUISICAO and produto and quantidade:
            if quantidade > produto.quantidade:
                raise serializers.ValidationError(
                    f'Estoque insuficiente para "{produto.nome}". Disponível: {produto.quantidade}.'
                )
        return attrs
