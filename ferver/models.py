from django.db import models
from django.contrib.auth.models import User

# Modelo para estados
class Estado(models.Model):
    nome = models.CharField(max_length=100, unique=True)
    uf = models.CharField(max_length=2, unique=True)  # Sigla do estado

    def __str__(self):
        return f"{self.nome} ({self.uf})"

# Modelo para cidades
class Cidade(models.Model):
    nome = models.CharField(max_length=100)
    estado = models.ForeignKey(Estado, on_delete=models.CASCADE, related_name='cidades')

    class Meta:
        unique_together = ('nome', 'estado')

    def __str__(self):
        return f"{self.nome}, {self.estado.uf}"

# Modelo para anúncios
class Perfil(models.Model):
    usuario = models.ForeignKey(User, on_delete=models.CASCADE)
    nome = models.CharField(max_length=100)
    idade = models.PositiveIntegerField(null=True, blank=True)
    estado = models.ForeignKey(Estado, on_delete=models.SET_NULL, null=True, blank=True)
    cidade = models.ForeignKey(Cidade, on_delete=models.SET_NULL, null=True, blank=True)
    descricao = models.TextField(blank=True)
    telefone = models.CharField(max_length=20, blank=True)
    maioridade = models.BooleanField(default=False)
    documento = models.FileField(upload_to='documentos/', blank=True, null=True)
    foto = models.ImageField(upload_to='perfis/', blank=True, null=True)
    foto2 = models.ImageField(upload_to='perfis/', blank=True, null=True)
    verificado = models.BooleanField(default=False)
    top_geral = models.BooleanField(default=False, verbose_name="Top Geral (Banner)")
    boost = models.BooleanField(default=False, verbose_name="Destaque (Card)")
    pago = models.BooleanField(default=False)
    preco = models.IntegerField(default=2000)  # valor em centavos
    stripe_session_id = models.CharField(max_length=255, blank=True, null=True)
    mercadopago_id = models.CharField(max_length=255, blank=True, null=True)
    criado_em = models.DateTimeField(auto_now_add=True)
    ativo = models.BooleanField(default=True,null=True)

    def __str__(self):
        return self.nome

# Modelo para mensagens de contato
class Ferver(models.Model):
    nome = models.CharField(max_length=100)
    sobrenome = models.CharField(max_length=100)
    email = models.EmailField()
    telefone = models.CharField(max_length=20)
    mensagem = models.TextField()
   


    def __str__(self):
        return self.nome
