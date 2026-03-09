from django.contrib import admin
from .models import Perfil, Estado, Cidade, Ferver

@admin.register(Perfil)
class PerfilAdmin(admin.ModelAdmin):
    # Campos que aparecem na lista
    list_display = ('nome', 'cidade', 'top_geral', 'boost', 'verificado', 'ativo', 'pago', 'criado_em')
    
    # Campos que podem ser editados diretamente na lista (muito prático)
    list_editable = ('top_geral', 'boost', 'verificado', 'ativo', 'pago')
    
    # Filtros laterais
    list_filter = ('estado', 'cidade', 'top_geral', 'boost', 'ativo', 'pago')
    
    # Campo de busca
    search_fields = ('nome', 'email', 'telefone', 'cidade__nome')
    
    # Organização dos campos no formulário de edição
    fieldsets = (
        ('Dados Básicos', {
            'fields': ('usuario', 'nome', 'idade', 'descricao', 'telefone', 'maioridade')
        }),
        ('Localização (Municipal)', {
            'fields': ('estado', 'cidade')
        }),
        ('Mídia', {
            'fields': ('foto', 'foto2', 'documento')
        }),
        ('Status e Destaques', {
            'fields': ('ativo', 'top_geral', 'boost', 'verificado', 'pago', 'preco')
        }),
        ('Integrações', {
            'fields': ('mercadopago_id', 'stripe_session_id')
        }),
    )

# Registrar as outras tabelas para gerenciamento municipal
admin.site.register(Estado)
class CidadeAdmin(admin.ModelAdmin):
    list_filter = ('estado',)
    search_fields = ('nome',)
admin.site.register(Cidade, CidadeAdmin)
admin.site.register(Ferver)