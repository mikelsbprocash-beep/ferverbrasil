from django.contrib import admin
from .models import Perfil, Estado, Cidade, Ferver, FotoAdicional

class FotoAdicionalInline(admin.TabularInline):
    model = FotoAdicional
    extra = 1 # Mostra 1 slot extra para upload

@admin.register(Perfil)
class PerfilAdmin(admin.ModelAdmin):
    # Campos que aparecem na lista
    list_display = ('nome', 'cidade', 'premium', 'top_geral', 'boost', 'verificado', 'ativo', 'pago', 'criado_em')
    
    # Campos que podem ser editados diretamente na lista (muito prático)
    list_editable = ('premium', 'top_geral', 'boost', 'verificado', 'ativo', 'pago')
    
    # Filtros laterais
    list_filter = ('estado', 'cidade', 'premium', 'top_geral', 'boost', 'ativo', 'pago')
    
    # Campo de busca
    search_fields = ('nome', 'usuario__email', 'telefone', 'cidade__nome')
    
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
            'fields': ('ativo', 'premium', 'validade_premium', 'top_geral', 'boost', 'validade_destaque', 'verificado', 'pago', 'preco')
        }),
        ('Integrações', {
            'fields': ('mercadopago_id', 'stripe_session_id')
        }),
    )

    inlines = [FotoAdicionalInline]

# Registrar as outras tabelas para gerenciamento municipal
admin.site.register(Estado)
class CidadeAdmin(admin.ModelAdmin):
    list_filter = ('estado',)
    search_fields = ('nome',)
admin.site.register(Cidade, CidadeAdmin)
admin.site.register(Ferver)