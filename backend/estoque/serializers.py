from rest_framework import serializers
from .models import Produto, Movimentacao


class ProdutoSerializer(serializers.ModelSerializer):
    class Meta:
        model = Produto
        fields = ['id', 'nome', 'descricao', 'quantidade', 'preco', 'criado_em', 'atualizado_em']
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
