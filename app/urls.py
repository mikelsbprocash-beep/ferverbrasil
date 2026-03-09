"""
URL configuration for app project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/6.0/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.urls import path
from django.contrib.auth import views as auth_views
from django.conf import settings
from django.conf.urls.static import static
from django.http import HttpResponse
from ferver import views

urlpatterns = [
    path('', views.ferver_view, name='home'),
    path('checkout/<str:tipo_plano>/', views.checkout_plano, name='checkout_plano'),
    path('sucesso/', views.sucesso_pagamento, name='sucesso_pagamento'),
    path('webhook/mercadopago/', views.webhook_mercadopago, name='webhook_mercadopago'),
    path('admin/', admin.site.urls),
    path('ferver/', views.ferver_view, name='ferver'),
    path('cadastro/', views.cadastrar_perfil, name='cadastro'),
    path('login/', views.login_view, name='login'),    
    path('logout/', views.logout_view, name='logout'),
    path('gerenciar-perfil/', views.gerenciar_perfil_view, name='gerenciar_perfil'),
    path('perfil/<int:perfil_id>/', views.perfil_detalhe_view, name='perfil_detalhe'),

    # Rotas de Recuperação de Senha
    path('reset_password/', auth_views.PasswordResetView.as_view(template_name="ferver/password_reset.html"), name="password_reset"),
    path('reset_password_sent/', auth_views.PasswordResetDoneView.as_view(template_name="ferver/password_reset_sent.html"), name="password_reset_done"),
    path('reset/<uidb64>/<token>/', auth_views.PasswordResetConfirmView.as_view(template_name="ferver/password_reset_confirm.html"), name="password_reset_confirm"),
    path('reset_password_complete/', auth_views.PasswordResetCompleteView.as_view(template_name="ferver/password_reset_complete.html"), name="password_reset_complete"),
]

# Servir arquivos de mídia em modo de desenvolvimento
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)