from django.utils.encoding import force_str
from django.utils.http import urlsafe_base64_decode
from rest_framework import status
from rest_framework.authtoken.models import Token
from rest_framework.authtoken.views import ObtainAuthToken
from rest_framework.exceptions import ValidationError
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework.views import APIView

from .models import Usuario
from .serializers import EmailAuthTokenSerializer, RegistroSerializer
from .tokens import gerador_token_confirmacao


class LoginView(ObtainAuthToken):
    """POST /api/auth/token/ — login por e-mail, retorna o token do usuário."""

    serializer_class = EmailAuthTokenSerializer

    def post(self, request, *args, **kwargs):
        serializer = self.serializer_class(data=request.data, context={'request': request})
        serializer.is_valid(raise_exception=True)
        usuario = serializer.validated_data['usuario']
        token, _criado = Token.objects.get_or_create(user=usuario)
        return Response({'token': token.key})


class RegistroView(APIView):
    """
    POST /api/auth/registro/ — cria a conta do usuário e a empresa dele numa
    tacada só. Confirmação por e-mail suspensa temporariamente (Render free
    tier bloqueia SMTP de saída): a conta já nasce ativa e pronta pra login,
    contanto que o e-mail seja único (ver ConfirmarEmailView, ainda de pé
    pra quando o envio de e-mail via API HTTP for reativado).
    """
    permission_classes = [AllowAny]
    authentication_classes = []

    def post(self, request, *args, **kwargs):
        serializer = RegistroSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save()

        return Response(
            {'detail': 'Cadastro realizado. Faça login para continuar.'},
            status=status.HTTP_201_CREATED,
        )


class ConfirmarEmailView(APIView):
    """
    POST /api/auth/confirmar-email/ (body: {"uid", "token"}) — confirma a
    conta e já devolve um token de sessão (login automático), no mesmo
    formato de LoginView.
    """
    permission_classes = [AllowAny]
    authentication_classes = []

    def post(self, request, *args, **kwargs):
        uid = request.data.get('uid') or ''
        token = request.data.get('token') or ''

        try:
            pk = force_str(urlsafe_base64_decode(uid))
            usuario = Usuario.objects.get(pk=pk)
        except (TypeError, ValueError, OverflowError, Usuario.DoesNotExist):
            raise ValidationError('Link de confirmação inválido.')

        if usuario.is_active:
            raise ValidationError('Esta conta já foi confirmada.')

        if not gerador_token_confirmacao.check_token(usuario, token):
            raise ValidationError('Link de confirmação inválido ou expirado.')

        usuario.is_active = True
        usuario.save(update_fields=['is_active'])

        token_sessao, _criado = Token.objects.get_or_create(user=usuario)
        return Response({'token': token_sessao.key, 'email': usuario.email})
