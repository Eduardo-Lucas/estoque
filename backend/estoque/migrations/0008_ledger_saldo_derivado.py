from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('estoque', '0007_empresa_fk_backfill'),
    ]

    operations = [
        migrations.RenameField(
            model_name='produto',
            old_name='preco_custo',
            new_name='preco_custo_referencia',
        ),
        migrations.AlterField(
            model_name='produto',
            name='preco_custo_referencia',
            field=models.DecimalField(decimal_places=2, default=0, max_digits=10, verbose_name='preço de custo (referência)'),
        ),
        migrations.AlterField(
            model_name='categoria',
            name='nome',
            field=models.CharField(max_length=100),
        ),
        migrations.AlterUniqueTogether(
            name='categoria',
            unique_together={('empresa', 'nome')},
        ),
        migrations.AlterField(
            model_name='fornecedor',
            name='nome',
            field=models.CharField(max_length=200),
        ),
        migrations.AlterUniqueTogether(
            name='fornecedor',
            unique_together={('empresa', 'nome')},
        ),
        migrations.AlterField(
            model_name='produto',
            name='nome',
            field=models.CharField(max_length=200),
        ),
        migrations.AlterField(
            model_name='produto',
            name='sku',
            field=models.CharField(blank=True, max_length=50, null=True, verbose_name='SKU'),
        ),
        migrations.AlterUniqueTogether(
            name='produto',
            unique_together={('empresa', 'sku')},
        ),
        migrations.AlterField(
            model_name='movimentacao',
            name='quantidade',
            field=models.DecimalField(decimal_places=3, max_digits=14),
        ),
        migrations.AddField(
            model_name='movimentacao',
            name='custo_unitario',
            field=models.DecimalField(blank=True, decimal_places=4, max_digits=14, null=True),
        ),
        migrations.AlterField(
            model_name='movimentacao',
            name='tipo',
            field=models.CharField(choices=[
                ('REQUISICAO', 'Requisição'),
                ('DEVOLUCAO', 'Devolução'),
                ('COMPRA', 'Compra'),
                ('AJUSTE_POSITIVO', 'Ajuste de inventário (+)'),
                ('AJUSTE_NEGATIVO', 'Ajuste de inventário (-)'),
            ], max_length=20),
        ),
        migrations.RemoveField(
            model_name='produto',
            name='quantidade',
        ),
    ]
