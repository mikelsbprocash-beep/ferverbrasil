from django.conf import settings
from django.urls import reverse
import mercadopago

class MercadoPagoService:
    def __init__(self):
        self.token = settings.MERCADOPAGO_ACCESS_TOKEN
        self.sdk = None
        if self.token:
            self.sdk = mercadopago.SDK(self.token)

    def criar_preferencia(self, request, perfil, tipo_plano):
        if not self.sdk:
            return None

        planos = {
            'destaque': {'titulo': 'Plano Destaque (7 dias)', 'preco': 149.90},
            'premium': {'titulo': 'Plano Premium (30 dias)', 'preco': 99.90},
            'verificado': {'titulo': 'Taxa de Verificação', 'preco': 49.90},
        }

        if tipo_plano not in planos:
            return None

        dados_plano = planos[tipo_plano]
        external_ref = f"{perfil.id}_{tipo_plano}"

        preference_data = {
            "items": [
                {
                    "title": dados_plano['titulo'],
                    "quantity": 1,
                    "unit_price": float(dados_plano['preco']),
                    "currency_id": "BRL"
                }
            ],
            "payer": {
                "email": request.user.email or "email@teste.com"
            },
            "back_urls": {
                "success": request.build_absolute_uri(reverse('sucesso_pagamento')),
                "failure": request.build_absolute_uri(reverse('ferver')),
                "pending": request.build_absolute_uri(reverse('ferver')),
            },
            "external_reference": external_ref
        }

        # Lógica para evitar erro de auto_return em localhost com chave de produção
        is_production_token = not self.token.startswith("TEST")
        is_localhost = "127.0.0.1" in request.get_host() or "localhost" in request.get_host()

        if not (is_production_token and is_localhost):
            preference_data["auto_return"] = "approved"

        try:
            preference_response = self.sdk.preference().create(preference_data)
            return preference_response.get("response")
        except Exception as e:
            print(f"Erro MP: {e}")
            return None

    def verificar_pagamento(self, payment_id):
        if not self.sdk:
            return None
        
        try:
            payment_info = self.sdk.payment().get(payment_id)
            if payment_info.get("status") == 200:
                return payment_info["response"]
        except Exception:
            pass
        return None