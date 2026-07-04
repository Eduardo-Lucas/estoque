from django.contrib import admin
from .models import Produto, Movimentacao


@admin.register(Produto)
class ProdutoAdmin(admin.ModelAdmin):
    list_display = ('nome', 'quantidade', 'preco', 'atualizado_em')
    search_fields = ('nome',)


@admin.register(Movimentacao)
class MovimentacaoAdmin(admin.ModelAdmin):
    list_display = ('produto', 'tipo', 'quantidade', 'solicitante', 'data')
    list_filter = ('tipo',)
