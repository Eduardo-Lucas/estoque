from django.contrib.auth import authenticate, password_validation
from django.core import exceptions as django_exceptions
from django.db import transaction
from rest_framework import serializers

from estoque.models import ConfiguracaoEstoque, Deposito, Empresa
from estoque.services import CODIGO_DEPOSITO_PADRAO

from .models import Usuario


class EmailAuthTokenSerializer(serializers.Serializer):
    email = serializers.EmailField(label='E-mail')
    password = serializers.CharField(
        label='Senha', style={'input_type': 'password'}, trim_whitespace=False,
    )

    def validate(self, attrs):
        email = attrs.get('email')
        password = attrs.get('password')

        usuario = authenticate(
            request=self.context.get('request'), username=email, password=password,
        )
        if not usuario:
            raise serializers.ValidationError(
                'Não foi possível autenticar com as credenciais informadas.', code='authorization',
            )

        attrs['usuario'] = usuario
        return attrs


class RegistroSerializer(serializers.Serializer):
    """Cria a conta do usuário e a empresa dele juntas — hoje não existe fluxo
    de convite, então toda conta nova é dona de uma empresa nova. Confirmação
    por e-mail suspensa temporariamente (Render free tier bloqueia SMTP de
    saída — ver RegistroView): a conta já nasce ativa, e-mail único basta."""

    email = serializers.EmailField()
    password = serializers.CharField(write_only=True, style={'input_type': 'password'})
    nome = serializers.CharField(max_length=150)
    empresa_razao_social = serializers.CharField(max_length=255)
    empresa_nome_fantasia = serializers.CharField(max_length=255, required=False, allow_blank=True, default='')
    empresa_cnpj = serializers.CharField(max_length=20)

    def validate_email(self, value):
        value = Usuario.objects.normalize_email(value)
        if Usuario.objects.filter(email__iexact=value).exists():
            raise serializers.ValidationError('Já existe uma conta com este e-mail.')
        return value

    def validate_empresa_cnpj(self, value):
        if Empresa.objects.filter(cnpj=value).exists():
            raise serializers.ValidationError('Já existe uma empresa cadastrada com este CNPJ.')
        return value

    def validate_password(self, value):
        try:
            password_validation.validate_password(value)
        except django_exceptions.ValidationError as exc:
            raise serializers.ValidationError(list(exc.messages))
        return value

    @transaction.atomic
    def create(self, validated_data):
        empresa = Empresa.objects.create(
            razao_social=validated_data['empresa_razao_social'],
            nome_fantasia=validated_data['empresa_nome_fantasia'],
            cnpj=validated_data['empresa_cnpj'],
        )
        ConfiguracaoEstoque.objects.create(empresa=empresa)
        Deposito.objects.create(empresa=empresa, codigo=CODIGO_DEPOSITO_PADRAO, nome='Depósito Padrão')

        return Usuario.objects.create_user(
            email=validated_data['email'],
            password=validated_data['password'],
            nome=validated_data['nome'],
            empresa=empresa,
        )
