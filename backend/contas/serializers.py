from django.contrib.auth import authenticate
from rest_framework import serializers


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
