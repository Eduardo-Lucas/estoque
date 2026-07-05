import django.db.models.deletion
from django.db import migrations, models

CNPJ_EMPRESA_PADRAO = '00000000000000'
CODIGO_DEPOSITO_PADRAO = 'PADRAO'


def preencher_empresa_e_deposito_padrao(apps, schema_editor):
    Empresa = apps.get_model('estoque', 'Empresa')
    Deposito = apps.get_model('estoque', 'Deposito')
    Categoria = apps.get_model('estoque', 'Categoria')
    Fornecedor = apps.get_model('estoque', 'Fornecedor')
    Produto = apps.get_model('estoque', 'Produto')
    Movimentacao = apps.get_model('estoque', 'Movimentacao')
    NotaFiscalCompra = apps.get_model('estoque', 'NotaFiscalCompra')

    empresa = Empresa.objects.get(cnpj=CNPJ_EMPRESA_PADRAO)
    deposito = Deposito.objects.get(empresa=empresa, codigo=CODIGO_DEPOSITO_PADRAO)

    Categoria.objects.filter(empresa__isnull=True).update(empresa=empresa)
    Fornecedor.objects.filter(empresa__isnull=True).update(empresa=empresa)
    Produto.objects.filter(empresa__isnull=True).update(empresa=empresa)
    NotaFiscalCompra.objects.filter(empresa__isnull=True).update(empresa=empresa)
    Movimentacao.objects.filter(empresa__isnull=True).update(empresa=empresa, deposito=deposito)


def reverter_preenchimento(apps, schema_editor):
    # Nada a fazer: os dados voltam a ficar sem empresa/depósito quando os
    # campos forem removidos pelo reverse das operações seguintes.
    pass


class Migration(migrations.Migration):

    dependencies = [
        ('estoque', '0006_empresa_deposito_saldoestoque'),
    ]

    operations = [
        migrations.AddField(
            model_name='categoria',
            name='empresa',
            field=models.ForeignKey(null=True, on_delete=django.db.models.deletion.CASCADE, related_name='categorias', to='estoque.empresa'),
        ),
        migrations.AddField(
            model_name='fornecedor',
            name='empresa',
            field=models.ForeignKey(null=True, on_delete=django.db.models.deletion.CASCADE, related_name='fornecedores', to='estoque.empresa'),
        ),
        migrations.AddField(
            model_name='produto',
            name='empresa',
            field=models.ForeignKey(null=True, on_delete=django.db.models.deletion.CASCADE, related_name='produtos', to='estoque.empresa'),
        ),
        migrations.AddField(
            model_name='notafiscalcompra',
            name='empresa',
            field=models.ForeignKey(null=True, on_delete=django.db.models.deletion.CASCADE, related_name='notas_fiscais', to='estoque.empresa'),
        ),
        migrations.AddField(
            model_name='movimentacao',
            name='empresa',
            field=models.ForeignKey(null=True, on_delete=django.db.models.deletion.CASCADE, related_name='movimentacoes', to='estoque.empresa'),
        ),
        migrations.AddField(
            model_name='movimentacao',
            name='deposito',
            field=models.ForeignKey(null=True, on_delete=django.db.models.deletion.PROTECT, related_name='movimentacoes', to='estoque.deposito'),
        ),
        migrations.RunPython(preencher_empresa_e_deposito_padrao, reverter_preenchimento),
        migrations.AlterField(
            model_name='categoria',
            name='empresa',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='categorias', to='estoque.empresa'),
        ),
        migrations.AlterField(
            model_name='fornecedor',
            name='empresa',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='fornecedores', to='estoque.empresa'),
        ),
        migrations.AlterField(
            model_name='produto',
            name='empresa',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='produtos', to='estoque.empresa'),
        ),
        migrations.AlterField(
            model_name='notafiscalcompra',
            name='empresa',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='notas_fiscais', to='estoque.empresa'),
        ),
        migrations.AlterField(
            model_name='movimentacao',
            name='empresa',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='movimentacoes', to='estoque.empresa'),
        ),
        migrations.AlterField(
            model_name='movimentacao',
            name='deposito',
            field=models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, related_name='movimentacoes', to='estoque.deposito'),
        ),
        migrations.CreateModel(
            name='SaldoEstoque',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('quantidade', models.DecimalField(decimal_places=3, default=0, max_digits=14)),
                ('custo_medio', models.DecimalField(decimal_places=4, default=0, max_digits=14)),
                ('atualizado_em', models.DateTimeField(auto_now=True)),
                ('deposito', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='saldos', to='estoque.deposito')),
                ('empresa', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='saldos', to='estoque.empresa')),
                ('produto', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='saldos', to='estoque.produto')),
            ],
            options={
                'unique_together': {('produto', 'deposito')},
                'indexes': [models.Index(fields=['empresa', 'produto'], name='estoque_sal_empresa_idx')],
            },
        ),
    ]
