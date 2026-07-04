from django.db import models


class Produto(models.Model):
    nome = models.CharField(max_length=200, unique=True)
    descricao = models.TextField(blank=True)
    quantidade = models.PositiveIntegerField(default=0)
    preco = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    criado_em = models.DateTimeField(auto_now_add=True)
    atualizado_em = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['nome']

    def __str__(self):
        return self.nome


class Movimentacao(models.Model):
    REQUISICAO = 'REQUISICAO'
    DEVOLUCAO = 'DEVOLUCAO'
    TIPO_CHOICES = [
        (REQUISICAO, 'Requisição'),
        (DEVOLUCAO, 'Devolução'),
    ]

    produto = models.ForeignKey(Produto, related_name='movimentacoes', on_delete=models.CASCADE)
    tipo = models.CharField(max_length=20, choices=TIPO_CHOICES)
    quantidade = models.PositiveIntegerField()
    solicitante = models.CharField(max_length=150)
    observacao = models.TextField(blank=True)
    data = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-data']

    def __str__(self):
        return f'{self.get_tipo_display()} - {self.produto.nome} ({self.quantidade})'
