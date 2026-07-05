from rest_framework.authtoken.models import Token
from rest_framework.authtoken.views import ObtainAuthToken
from rest_framework.response import Response

from .serializers import EmailAuthTokenSerializer


class LoginView(ObtainAuthToken):
    """POST /api/auth/token/ — login por e-mail, retorna o token do usuário."""

    serializer_class = EmailAuthTokenSerializer

    def post(self, request, *args, **kwargs):
        serializer = self.serializer_class(data=request.data, context={'request': request})
        serializer.is_valid(raise_exception=True)
        usuario = serializer.validated_data['usuario']
        token, _criado = Token.objects.get_or_create(user=usuario)
        return Response({'token': token.key})
