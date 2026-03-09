from django.urls import path
from . import views

urlpatterns = [
    path('', views.ferver_view, name='ferver'),
    path('cadastro/', views.cadastrar_perfil, name='cadastro'),
    path('login/', views.login_view, name='login'),
    path('logout/', views.logout_view, name='logout'),
    path('gerenciar-perfil/', views.gerenciar_perfil_view, name='gerenciar_perfil'),
    path('perfil/<int:perfil_id>/', views.perfil_detalhe_view, name='perfil_detalhe'),
    path('checkout/<str:tipo_plano>/', views.checkout_plano, name='checkout_plano'),
    path('sucesso/', views.sucesso_pagamento, name='sucesso_pagamento'),
    path('webhook/mercadopago/', views.webhook_mercadopago, name='webhook_mercadopago'),
]
