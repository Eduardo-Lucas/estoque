from django.contrib import admin
from .models import Produto, Categoria, Fornecedor, Movimentacao


@admin.register(Produto)
class ProdutoAdmin(admin.ModelAdmin):
    list_display = ('nome', 'sku', 'categoria', 'fornecedor', 'quantidade', 'preco', 'ativo', 'atualizado_em')
    list_filter = ('categoria', 'fornecedor', 'ativo')
    search_fields = ('nome', 'sku', 'codigo_barras')


@admin.register(Categoria)
class CategoriaAdmin(admin.ModelAdmin):
    list_display = ('nome',)
    search_fields = ('nome',)


@admin.register(Fornecedor)
class FornecedorAdmin(admin.ModelAdmin):
    list_display = ('nome', 'cnpj', 'telefone', 'email')
    search_fields = ('nome', 'cnpj')


@admin.register(Movimentacao)
class MovimentacaoAdmin(admin.ModelAdmin):
    list_display = ('produto', 'tipo', 'quantidade', 'solicitante', 'data')
    list_filter = ('tipo',)
