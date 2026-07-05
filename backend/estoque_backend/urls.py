from django.contrib import admin
from django.urls import path, include

from contas.views import ConfirmarEmailView, LoginView, RegistroView

urlpatterns = [
    path('admin/', admin.site.urls),
    path('api/auth/token/', LoginView.as_view(), name='api_token_auth'),
    path('api/auth/registro/', RegistroView.as_view(), name='api_registro'),
    path('api/auth/confirmar-email/', ConfirmarEmailView.as_view(), name='api_confirmar_email'),
    path('api/', include('estoque.urls')),
]
