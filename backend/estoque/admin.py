from django.contrib import admin
from django.db.models import Sum

from .models import (
    CamadaCusto, Categoria, ConfiguracaoEstoque, Deposito, Empresa, Fornecedor,
    ItemNotaFiscalCompra, Lote, Movimentacao, NotaFiscalCompra, Produto, SaldoEstoque,
)


@admin.register(Produto)
class ProdutoAdmin(admin.ModelAdmin):
    list_display = ('nome', 'sku', 'categoria', 'fornecedor', 'saldo_total', 'preco', 'ativo', 'atualizado_em')
    list_filter = ('categoria', 'fornecedor', 'ativo')
    search_fields = ('nome', 'sku', 'codigo_barras')

    @admin.display(description='saldo')
    def saldo_total(self, produto):
        return produto.saldos.aggregate(total=Sum('quantidade'))['total'] or 0


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
    list_display = ('produto', 'tipo', 'quantidade', 'deposito', 'solicitante', 'usuario', 'data')
    list_filter = ('tipo', 'deposito', 'usuario')
    search_fields = ('produto__nome', 'usuario__email')


class ItemNotaFiscalCompraInline(admin.TabularInline):
    model = ItemNotaFiscalCompra
    extra = 0


@admin.register(NotaFiscalCompra)
class NotaFiscalCompraAdmin(admin.ModelAdmin):
    list_display = ('numero', 'fornecedor', 'valor_total', 'data_emissao', 'importado_em')
    search_fields = ('numero', 'chave_acesso')
    inlines = [ItemNotaFiscalCompraInline]


@admin.register(Empresa)
class EmpresaAdmin(admin.ModelAdmin):
    list_display = ('nome_fantasia', 'razao_social', 'cnpj', 'ativo')


@admin.register(Deposito)
class DepositoAdmin(admin.ModelAdmin):
    list_display = ('nome', 'codigo', 'empresa', 'ativo')
    list_filter = ('empresa',)


@admin.register(SaldoEstoque)
class SaldoEstoqueAdmin(admin.ModelAdmin):
    list_display = ('produto', 'deposito', 'lote', 'quantidade', 'custo_medio', 'atualizado_em')
    list_filter = ('deposito',)
    search_fields = ('produto__nome',)


@admin.register(ConfiguracaoEstoque)
class ConfiguracaoEstoqueAdmin(admin.ModelAdmin):
    list_display = ('empresa', 'regime_tributario', 'metodo_valoracao', 'permite_estoque_negativo', 'controla_lote_por_padrao')


@admin.register(Lote)
class LoteAdmin(admin.ModelAdmin):
    list_display = ('produto', 'numero_lote', 'data_fabricacao', 'data_validade')
    search_fields = ('produto__nome', 'numero_lote')


@admin.register(CamadaCusto)
class CamadaCustoAdmin(admin.ModelAdmin):
    list_display = ('produto', 'deposito', 'lote', 'quantidade_disponivel', 'quantidade_original', 'custo_unitario', 'criado_em')
    list_filter = ('deposito',)
    search_fields = ('produto__nome',)
