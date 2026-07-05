import django.db.models.deletion
from django.db import migrations, models

CNPJ_EMPRESA_PADRAO = '00000000000000'
CODIGO_DEPOSITO_PADRAO = 'PADRAO'


def semear_empresa_e_deposito_padrao(apps, schema_editor):
    Empresa = apps.get_model('estoque', 'Empresa')
    Deposito = apps.get_model('estoque', 'Deposito')

    empresa, _ = Empresa.objects.get_or_create(
        cnpj=CNPJ_EMPRESA_PADRAO,
        defaults={'razao_social': 'Empresa Padrão', 'nome_fantasia': 'Empresa Padrão'},
    )
    Deposito.objects.get_or_create(
        empresa=empresa, codigo=CODIGO_DEPOSITO_PADRAO,
        defaults={'nome': 'Depósito Padrão'},
    )


def remover_empresa_e_deposito_padrao(apps, schema_editor):
    Empresa = apps.get_model('estoque', 'Empresa')
    Empresa.objects.filter(cnpj=CNPJ_EMPRESA_PADRAO).delete()


class Migration(migrations.Migration):

    dependencies = [
        ('estoque', '0005_categoria_ativo_fornecedor_ativo'),
    ]

    operations = [
        migrations.CreateModel(
            name='Empresa',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('razao_social', models.CharField(max_length=255)),
                ('nome_fantasia', models.CharField(blank=True, max_length=255)),
                ('cnpj', models.CharField(max_length=20, unique=True)),
                ('ativo', models.BooleanField(default=True)),
                ('criado_em', models.DateTimeField(auto_now_add=True)),
            ],
            options={
                'verbose_name_plural': 'empresas',
            },
        ),
        migrations.CreateModel(
            name='Deposito',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('codigo', models.CharField(max_length=20)),
                ('nome', models.CharField(max_length=100)),
                ('ativo', models.BooleanField(default=True)),
                ('empresa', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='depositos', to='estoque.empresa')),
            ],
            options={
                'ordering': ['nome'],
                'unique_together': {('empresa', 'codigo')},
            },
        ),
        migrations.RunPython(semear_empresa_e_deposito_padrao, remover_empresa_e_deposito_padrao),
    ]
