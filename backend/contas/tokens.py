from django.contrib.auth.tokens import PasswordResetTokenGenerator


class GeradorTokenConfirmacaoEmail(PasswordResetTokenGenerator):
    """Mesma técnica do "esqueci minha senha" do Django, aplicada à confirmação
    de e-mail: o token é derivado do estado do usuário (sem precisar de uma
    tabela própria) e inclui `is_active` no hash — assim que a conta é
    confirmada, qualquer link antigo já fica inválido sozinho."""

    def _make_hash_value(self, usuario, timestamp):
        return f'{usuario.pk}{usuario.is_active}{usuario.password}{timestamp}'


gerador_token_confirmacao = GeradorTokenConfirmacaoEmail()
