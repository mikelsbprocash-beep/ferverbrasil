from django.test import TestCase, Client
from django.urls import reverse
from ferver.models import Perfil, User, Estado, Cidade

class PerfilDetalheViewTest(TestCase):
    def setUp(self):
        self.client = Client()
        self.estado = Estado.objects.create(nome='Test State', uf='TS')
        self.cidade = Cidade.objects.create(nome='Test City', estado=self.estado)
        self.user = User.objects.create_user(username='testuser', password='password')
        self.perfil = Perfil.objects.create(
            usuario=self.user,
            nome='Test Perfil',
            idade=25,
            estado=self.estado,
            cidade=self.cidade,
            preco=100
        )
        self.url = reverse('perfil_detalhe', args=[self.perfil.id])

    def test_perfil_detalhe_view_success(self):
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'ferver/perfil_detalhe.html')
        self.assertContains(response, self.perfil.nome)

    def test_perfil_detalhe_view_not_found(self):
        url = reverse('perfil_detalhe', args=[999])
        response = self.client.get(url)
        self.assertEqual(response.status_code, 404)
