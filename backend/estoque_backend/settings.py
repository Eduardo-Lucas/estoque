import os
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent

# Chave apenas para desenvolvimento local. Troque em produção.
SECRET_KEY = 'django-insecure-troque-esta-chave-em-producao'

DEBUG = True

ALLOWED_HOSTS = ['*']

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

DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

# CORS: liberado para o Angular rodando em localhost durante o desenvolvimento
CORS_ALLOWED_ORIGINS = [
    'http://localhost:4200',
    'http://127.0.0.1:4200',
]

# E-mail de confirmação de cadastro: em dev cai no console do runserver
# (nenhum SMTP configurado). Em produção, sobrescreva via variável de ambiente.
EMAIL_BACKEND = os.environ.get('EMAIL_BACKEND', 'django.core.mail.backends.console.EmailBackend')
DEFAULT_FROM_EMAIL = os.environ.get('DEFAULT_FROM_EMAIL', 'no-reply@estoque.local')

# Base da URL do frontend, usada para montar o link de confirmação de e-mail.
FRONTEND_URL = os.environ.get('FRONTEND_URL', 'http://localhost:4200')

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
