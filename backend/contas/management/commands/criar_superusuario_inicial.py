import os

from django.core.management.base import BaseCommand

from contas.models import Usuario


class Command(BaseCommand):
    """Cria o primeiro superusuário a partir de env vars, se ainda não existir.

    Pensado pro Web Service free do Render, que não tem acesso a Shell —
    sem isso não haveria como rodar `createsuperuser` interativo em produção.
    Idempotente (não recria nem falha se o superusuário já existir), e não
    faz nada se as env vars não estiverem configuradas — seguro de chamar em
    todo deploy (ver build.sh)."""

    help = 'Cria o superusuário inicial a partir de DJANGO_SUPERUSER_EMAIL/DJANGO_SUPERUSER_PASSWORD.'

    def handle(self, *args, **options):
        email = os.environ.get('DJANGO_SUPERUSER_EMAIL')
        password = os.environ.get('DJANGO_SUPERUSER_PASSWORD')

        if not email or not password:
            self.stdout.write('DJANGO_SUPERUSER_EMAIL/DJANGO_SUPERUSER_PASSWORD não configurados — nada a fazer.')
            return

        if Usuario.objects.filter(email__iexact=email).exists():
            self.stdout.write(f'Já existe uma conta com o e-mail {email} — nada a fazer.')
            return

        Usuario.objects.create_superuser(email=email, password=password)
        self.stdout.write(self.style.SUCCESS(f'Superusuário {email} criado.'))
