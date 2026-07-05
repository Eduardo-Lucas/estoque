from django.contrib import admin
from django.urls import path, include

from contas.views import LoginView

urlpatterns = [
    path('admin/', admin.site.urls),
    path('api/auth/token/', LoginView.as_view(), name='api_token_auth'),
    path('api/', include('estoque.urls')),
]
