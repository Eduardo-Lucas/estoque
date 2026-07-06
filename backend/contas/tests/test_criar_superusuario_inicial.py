import pytest
from django.core.management import call_command

from contas.models import Usuario

pytestmark = pytest.mark.django_db


class TestCriarSuperusuarioInicial:
    def test_nao_faz_nada_sem_env_vars(self, monkeypatch):
        monkeypatch.delenv('DJANGO_SUPERUSER_EMAIL', raising=False)
        monkeypatch.delenv('DJANGO_SUPERUSER_PASSWORD', raising=False)

        call_command('criar_superusuario_inicial')

        assert not Usuario.objects.exists()

    def test_cria_superusuario_com_env_vars(self, monkeypatch):
        monkeypatch.setenv('DJANGO_SUPERUSER_EMAIL', 'admin@empresa.com')
        monkeypatch.setenv('DJANGO_SUPERUSER_PASSWORD', 'senha-super-forte-2026')

        call_command('criar_superusuario_inicial')

        usuario = Usuario.objects.get(email='admin@empresa.com')
        assert usuario.is_superuser is True
        assert usuario.is_staff is True
        assert usuario.check_password('senha-super-forte-2026')

    def test_e_idempotente_quando_ja_existe(self, monkeypatch):
        monkeypatch.setenv('DJANGO_SUPERUSER_EMAIL', 'admin@empresa.com')
        monkeypatch.setenv('DJANGO_SUPERUSER_PASSWORD', 'senha-super-forte-2026')
        Usuario.objects.create_superuser(email='admin@empresa.com', password='outra-senha-ja-existente')

        call_command('criar_superusuario_inicial')

        assert Usuario.objects.filter(email='admin@empresa.com').count() == 1
        usuario = Usuario.objects.get(email='admin@empresa.com')
        assert usuario.check_password('outra-senha-ja-existente')
