import os
from pathlib import Path

import dj_database_url

BASE_DIR = Path(__file__).resolve().parent.parent

# Em produção (Render), SECRET_KEY vem de uma env var gerada automaticamente
# pelo render.yaml (`generateValue: true`). O valor abaixo só é usado em dev local.
SECRET_KEY = os.environ.get('SECRET_KEY', 'django-insecure-troque-esta-chave-em-producao')

DEBUG = os.environ.get('DEBUG', 'True') == 'True'

_hosts_env = os.environ.get('ALLOWED_HOSTS', '')
ALLOWED_HOSTS = [h.strip() for h in _hosts_env.split(',') if h.strip()]
# Render injeta esse hostname automaticamente em todo Web Service.
_render_hostname = os.environ.get('RENDER_EXTERNAL_HOSTNAME')
if _render_hostname:
    ALLOWED_HOSTS.append(_render_hostname)
if not ALLOWED_HOSTS:
    ALLOWED_HOSTS = ['*']  # dev local: nenhuma env var configurada

# Necessário porque o proxy do Render termina o HTTPS e repassa por HTTP
# internamente — sem isso, Django acha que a requisição é insegura (CSRF falha).
SECURE_PROXY_SSL_HEADER = ('HTTP_X_FORWARDED_PROTO', 'https')
CSRF_TRUSTED_ORIGINS = [f'https://{h}' for h in ALLOWED_HOSTS if h != '*']

if not DEBUG:
    SECURE_SSL_REDIRECT = True
    SESSION_COOKIE_SECURE = True
    CSRF_COOKIE_SECURE = True
    SECURE_HSTS_SECONDS = 60 * 60 * 24 * 7  # 7 dias — aumentar depois de confirmar que o HTTPS está estável
    SECURE_HSTS_INCLUDE_SUBDOMAINS = True

INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',

    # Terceiros
    'rest_framework',
    'rest_framework.authtoken',
    'corsheaders',

    # Apps locais
    'contas',
    'estoque',
]

AUTH_USER_MODEL = 'contas.Usuario'

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'whitenoise.middleware.WhiteNoiseMiddleware',  # serve os estáticos do admin em produção
    'corsheaders.middleware.CorsMiddleware',  # precisa vir antes do CommonMiddleware
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

ROOT_URLCONF = 'estoque_backend.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.debug',
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
            ],
        },
    },
]

WSGI_APPLICATION = 'estoque_backend.wsgi.application'

# Em produção, DATABASE_URL vem do Postgres do Render (ligado via `fromDatabase`
# no render.yaml). Sem essa env var (dev local), cai no sqlite de sempre.
_database_url = os.environ.get('DATABASE_URL')
if _database_url:
    DATABASES = {'default': dj_database_url.config(default=_database_url, conn_max_age=600)}
else:
    DATABASES = {
        'default': {
            'ENGINE': 'django.db.backends.sqlite3',
            'NAME': BASE_DIR / 'db.sqlite3',
        }
    }

AUTH_PASSWORD_VALIDATORS = [
    {'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator'},
    {'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator'},
    {'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator'},
    {'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator'},
]

LANGUAGE_CODE = 'pt-br'
TIME_ZONE = 'America/Bahia'
USE_I18N = True
USE_TZ = True

STATIC_URL = 'static/'
STATIC_ROOT = BASE_DIR / 'staticfiles'
STORAGES = {
    'staticfiles': {
        'BACKEND': 'whitenoise.storage.CompressedManifestStaticFilesStorage',
    },
}

DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'


def _url_publica_render(valor: str) -> str:
    """O render.yaml injeta FRONTEND_URL/CORS_ALLOWED_ORIGINS via `fromService`
    (property: host), que devolve o hostname da rede *privada* do Render (ex:
    'estoque-frontend-hp5y', sem esquema nem `.onrender.com`) — essa propriedade
    foi pensada pra comunicação interna entre serviços, não pra uso público no
    navegador. Completa esquema e domínio quando estiverem faltando."""
    if valor.startswith('http'):
        return valor
    if '.' not in valor:
        valor = f'{valor}.onrender.com'
    return f'https://{valor}'


# CORS: em dev, libera o Angular local; em produção, a env var vem do
# render.yaml apontando pro host do Static Site do frontend.
_cors_env = os.environ.get('CORS_ALLOWED_ORIGINS', 'http://localhost:4200,http://127.0.0.1:4200')
CORS_ALLOWED_ORIGINS = [_url_publica_render(origem.strip()) for origem in _cors_env.split(',') if origem.strip()]

# E-mail de confirmação de cadastro: por padrão cai no console (dev, e
# produção enquanto o SMTP não estiver configurado). Em produção, o
# render.yaml troca EMAIL_BACKEND pra smtp.EmailBackend e informa host/porta/
# credenciais de um SMTP real (Gmail) via env vars.
EMAIL_BACKEND = os.environ.get('EMAIL_BACKEND', 'django.core.mail.backends.console.EmailBackend')
DEFAULT_FROM_EMAIL = os.environ.get('DEFAULT_FROM_EMAIL', 'no-reply@estoque.local')
EMAIL_HOST = os.environ.get('EMAIL_HOST', '')
EMAIL_PORT = int(os.environ.get('EMAIL_PORT', '587'))
EMAIL_USE_TLS = os.environ.get('EMAIL_USE_TLS', 'True') == 'True'
EMAIL_HOST_USER = os.environ.get('EMAIL_HOST_USER', '')
EMAIL_HOST_PASSWORD = os.environ.get('EMAIL_HOST_PASSWORD', '')

# Base da URL do frontend, usada para montar o link de confirmação de e-mail.
FRONTEND_URL = _url_publica_render(os.environ.get('FRONTEND_URL', 'http://localhost:4200'))

REST_FRAMEWORK = {
    'DEFAULT_PAGINATION_CLASS': 'estoque.pagination.PaginacaoPadrao',
    'PAGE_SIZE': 20,
    'DEFAULT_AUTHENTICATION_CLASSES': [
        'rest_framework.authentication.TokenAuthentication',
    ],
    'DEFAULT_PERMISSION_CLASSES': [
        'rest_framework.permissions.IsAuthenticated',
    ],
    # o frontend sempre envia JSON (HttpClient); usar o mesmo formato nos testes
    # evita falsos-negativos causados pela semântica de formulário HTML do DRF
    # (ex: BooleanField ausente em multipart é interpretado como False).
    'TEST_REQUEST_DEFAULT_FORMAT': 'json',
}
