from django.shortcuts import render, redirect, get_object_or_404
from django.conf import settings
from .models import Perfil, Estado, Cidade, FotoAdicional
from django.contrib.auth.models import User
from django.contrib.auth import login, logout, authenticate
from django.contrib.auth.decorators import login_required
from django.urls import reverse
import re
import mercadopago
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.utils import timezone
from datetime import timedelta
from django.db.models import Q


def login_view(request):
    if request.method == "POST":
        email = request.POST.get("email")
        senha = request.POST.get("senha")
        
        # Tenta autenticar pelo username (já que estamos usando o email)
        user = authenticate(request, username=email, password=senha)
        
        if user is not None:
            login(request, user)
            # Verifica se tem uma url de destino (next)
            next_url = request.POST.get('next') or request.GET.get('next')
            if next_url:
                return redirect(next_url)
            return redirect("ferver")
        else:
            return render(request, "ferver/login.html", {"erro": "E-mail ou senha inválidos."})
            
    return render(request, "ferver/login.html")

def logout_view(request):
    logout(request)
    return redirect("ferver")

@login_required
def gerenciar_perfil_view(request):
    try:
        # Use select_related to pre-fetch related objects and avoid extra queries
        perfil = Perfil.objects.select_related('cidade', 'estado').get(usuario=request.user)
    except Perfil.DoesNotExist:
        return redirect('cadastro')

    # --- VERIFICAÇÃO DE VALIDADE DOS PLANOS (Lazy Check) ---
    # Se o plano venceu, remove o status automaticamente ao acessar o painel
    now = timezone.now()
    if perfil.premium and perfil.validade_premium and perfil.validade_premium < now:
        perfil.premium = False
        perfil.save()
    
    if perfil.boost and perfil.validade_destaque and perfil.validade_destaque < now:
        perfil.boost = False
        perfil.save()

    if request.method == "POST":
        # Update fields from POST data
        nome = request.POST.get("nome")
        if nome:
            perfil.nome = nome

        perfil.idade = request.POST.get("idade") or None
        perfil.descricao = request.POST.get("descricao", perfil.descricao)
        perfil.telefone = request.POST.get("telefone", perfil.telefone)
        
        if 'foto' in request.FILES:
            perfil.foto = request.FILES["foto"]

        if 'foto2' in request.FILES:
            perfil.foto2 = request.FILES["foto2"]

        # --- LÓGICA DA GALERIA PREMIUM ---
        # 1. Deletar fotos selecionadas
        delete_ids = request.POST.getlist('delete_fotos')
        if delete_ids:
            FotoAdicional.objects.filter(id__in=delete_ids, perfil=perfil).delete()

        # 2. Upload de novas fotos (Apenas se for Premium)
        if perfil.premium:
            fotos_novas = request.FILES.getlist('fotos_extras')
            qtd_atual = perfil.fotos_adicionais.count()
            limite = 5 # Limite de fotos extras
            
            for foto in fotos_novas:
                if qtd_atual < limite:
                    FotoAdicional.objects.create(perfil=perfil, imagem=foto)
                    qtd_atual += 1

        # Handle city update
        nome_cidade = request.POST.get("cidade")
        if nome_cidade and (not perfil.cidade or nome_cidade.lower() != perfil.cidade.nome.lower()):
            cidade_obj = Cidade.objects.filter(nome__iexact=nome_cidade).first()
            if cidade_obj:
                perfil.cidade = cidade_obj
                perfil.estado = cidade_obj.estado
            else:
                # If city doesn't exist, create it in a default state (or handle error)
                # This logic is copied from cadastro, might be better to have a dropdown
                estado_padrao = Estado.objects.filter(uf='SP').first() or Estado.objects.first()
                if estado_padrao:
                    cidade_obj, _ = Cidade.objects.get_or_create(nome=nome_cidade, estado=estado_padrao)
                    perfil.cidade = cidade_obj
                    perfil.estado = cidade_obj.estado

        # Handle price update

        valor_str = request.POST.get("valor")
        if valor_str:
            # Remove non-digit characters and convert to integer
            valor_limpo = re.sub(r'[^\d]', '', valor_str)
            perfil.preco = int(valor_limpo) * 100 if valor_limpo else perfil.preco

        perfil.save()
        return redirect('gerenciar_perfil')

    context = {'perfil': perfil}
    return render(request, "ferver/gerenciar_perfil.html", context)

def perfil_detalhe_view(request, perfil_id):
    perfil = get_object_or_404(Perfil, id=perfil_id)
    return render(request, "ferver/perfil_detalhe.html", {"perfil": perfil})

def cadastrar_perfil(request):

    if request.method == "POST":
        # only create if user confirmed age
        maior = request.POST.get("maioridade") == "on"
        
        # 1. Resolver Usuário (Se não estiver logado, cria um temporário baseado no nome)
        if request.user.is_authenticated:
            usuario_atual = request.user
        else:
            # Tenta pegar email e senha do formulário
            email = request.POST.get("email")
            senha = request.POST.get("senha")
            
            if email and senha:
                # Verifica se já existe para evitar erro 500
                if User.objects.filter(username=email).exists():
                    return render(request, "ferver/cadastro.html", {"erro": "Este e-mail já está cadastrado."})

                # Cria usuário real com senha para poder logar depois
                usuario_atual = User.objects.create_user(username=email, email=email, password=senha)
                # Autentica para definir o backend corretamente antes do login
                usuario_atual = authenticate(request, username=email, password=senha)
            else:
                # Fallback para usuário temporário se não preencher email/senha (não recomendado)
                username_temp = request.POST.get("nome", "").lower().replace(" ", "") + "_user"
                # Garante que o usuário seja criado ou recuperado sem conflito
                usuario_atual, created = User.objects.get_or_create(username=username_temp)
                # Define backend manualmente para login funcionar sem senha
                usuario_atual.backend = 'django.contrib.auth.backends.ModelBackend'
        
        # Realiza login automático para garantir que o checkout funcione
        if usuario_atual:
            login(request, usuario_atual)

        # 2. Resolver Cidade e Estado
        nome_cidade = request.POST.get("cidade")
        cidade_obj = None
        estado_obj = None

        if nome_cidade:
            # Tenta achar a cidade pelo nome (case insensitive)
            cidade_obj = Cidade.objects.filter(nome__iexact=nome_cidade).first()
            
            if cidade_obj:
                estado_obj = cidade_obj.estado
            else:
                # Se não achar a cidade, pega um estado padrão (ex: SP) e cria a cidade
                # Isso evita o erro, mas o ideal seria um dropdown no formulário
                estado_padrao = Estado.objects.filter(uf='SP').first() or Estado.objects.first()
                if estado_padrao:
                    cidade_obj = Cidade.objects.create(nome=nome_cidade, estado=estado_padrao)
                    estado_obj = estado_padrao

        # 3. Limpar Valor (R$ 300 -> 300)
        valor_str = request.POST.get("valor", "")
        valor_limpo = re.sub(r'[^\d]', '', valor_str) # Remove tudo que não é número
        preco_final = int(valor_limpo) * 100 if valor_limpo else 0

        perfil = Perfil.objects.create(
            usuario=usuario_atual,
            nome=request.POST.get("nome"),
            idade=request.POST.get("idade") or None, # Use None instead of empty string
            cidade=cidade_obj,
            estado=estado_obj,
            descricao=request.POST.get("descricao"),
            telefone=request.POST.get("telefone"),
            maioridade=maior,
            documento=request.FILES.get("documento"),
            preco=preco_final,
            foto=request.FILES.get("foto"),
            foto2=request.FILES.get("foto2")
        )

        return redirect("ferver")

    return render(request, "ferver/cadastro.html")


def ferver_view(request):
    # Separa os perfis para as diferentes seções do template
    now = timezone.now()

    # --- FILTROS DE BUSCA ---
    estado_busca = request.GET.get('estado')
    cidade_busca = request.GET.get('cidade')
    termo_busca = request.GET.get('q')

    filtros = Q(ativo=True)

    if estado_busca and estado_busca != '':
        filtros &= Q(estado__uf=estado_busca)
    
    if cidade_busca and cidade_busca != '':
        filtros &= Q(cidade__nome=cidade_busca)
        
    if termo_busca:
        filtros &= (Q(nome__icontains=termo_busca) | Q(cidade__nome__icontains=termo_busca) | Q(estado__nome__icontains=termo_busca))

    # 1. Pega os perfis TOP GERAL (maior prioridade) - Aplicando filtros também
    top_geral = Perfil.objects.filter(filtros, top_geral=True).order_by('-criado_em')[:5]

    # 2. Pega os perfis em DESTAQUE, mas EXCLUI os que já são TOP GERAL para não duplicar
    top_destaques = Perfil.objects.filter(
        filtros, 
        boost=True,
        top_geral=False # Exclui para não duplicar
    ).filter(Q(validade_destaque__isnull=True) | Q(validade_destaque__gte=now)).order_by('?')[:5]

    # 3. Pega os perfis COMUNS, excluindo os que são TOP GERAL ou DESTAQUE
    perfis_comuns = Perfil.objects.filter(
        filtros, 
        boost=False, 
        top_geral=False # Exclui para não duplicar
    ).order_by('-criado_em')

    total_perfis = len(top_geral) + len(top_destaques) + len(perfis_comuns)

    return render(request, "ferver/ferver.html", {
        "top_geral": top_geral,
        "top_destaques": top_destaques,
        "perfis_comuns": perfis_comuns,
        "total_perfis": total_perfis,
    })

# --- LÓGICA DO MERCADO PAGO ---

@login_required
def checkout_plano(request, tipo_plano):
    print(f"--- CHECKOUT INICIADO: Plano '{tipo_plano}' para usuário '{request.user}' ---")

    if not settings.MERCADOPAGO_ACCESS_TOKEN:
        print("ERRO CRÍTICO: Token do Mercado Pago não encontrado no .env")
        return redirect('ferver')

    # Substitua pelo seu ACCESS TOKEN de Produção ou Teste do Mercado Pago
    sdk = mercadopago.SDK(settings.MERCADOPAGO_ACCESS_TOKEN)

    # Define preços e títulos baseados no plano
    planos = {
        'destaque': {'titulo': 'Plano Destaque (7 dias)', 'preco': 149.90},
        'premium': {'titulo': 'Plano Premium (30 dias)', 'preco': 99.90},
        'verificado': {'titulo': 'Taxa de Verificação', 'preco': 49.90},
    }

    if tipo_plano not in planos:
        return redirect('ferver')

    dados_plano = planos[tipo_plano]
    
    perfil = Perfil.objects.filter(usuario=request.user).first()
    if not perfil:
        # Se o usuário logado não tem perfil, manda criar um
        return redirect('cadastro')

    # Cria a preferência de pagamento
    # IMPORTANTE: Vincula o pagamento ao ID do perfil e ao tipo de plano
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
            "failure": request.build_absolute_uri(reverse('ferver')), # Volta para home em caso de falha
            "pending": request.build_absolute_uri(reverse('ferver')), # Volta para home em caso de pendente
        },
        "external_reference": external_ref
    }

    # Lógica de segurança para evitar erro 400 em localhost com chave de Produção
    # Se estiver usando chave de Produção (APP_USR) em localhost, NÃO ative o auto_return
    is_production_token = not settings.MERCADOPAGO_ACCESS_TOKEN.startswith("TEST")
    is_localhost = "127.0.0.1" in request.get_host() or "localhost" in request.get_host()

    if not (is_production_token and is_localhost):
        preference_data["auto_return"] = "approved"

    preference_response = sdk.preference().create(preference_data)
    preference = preference_response.get("response")

    if not preference or "init_point" not in preference:
        # Log de erro no terminal para debug
        print("!!! ERRO MERCADO PAGO !!! Resposta:", preference_response)
        # Redireciona de volta para evitar tela de erro, mas idealmente mostraria uma mensagem
        # Se estiver em debug, mostra o erro na tela
        return JsonResponse(preference_response or {"error": "Erro ao criar preferência no Mercado Pago"}, status=500)

    print(f"--- REDIRECIONANDO PARA MERCADO PAGO: {preference['init_point']} ---")
    return redirect(preference["init_point"])

def sucesso_pagamento(request):
    return render(request, "ferver/sucesso.html") # Crie este template simples depois

@csrf_exempt
def webhook_mercadopago(request):
    if request.method != "POST":
        return JsonResponse({"status": "error", "message": "Invalid method"}, status=405)

    sdk = mercadopago.SDK(settings.MERCADOPAGO_ACCESS_TOKEN)
    topic = request.GET.get("topic") or request.GET.get("type")
    payment_id = request.GET.get("id") or request.GET.get("data.id")

    if not (topic == "payment" and payment_id):
        return JsonResponse({"status": "ok", "message": "Not a payment notification"})

    try:
        payment_info = sdk.payment().get(payment_id)
    except Exception:
        # Idealmente, logar o erro aqui
        return JsonResponse({"status": "error", "message": "Failed to get payment info"}, status=500)

    if payment_info.get("status") != 200:
        return JsonResponse({"status": "error", "message": "MercadoPago API error"}, status=502)

    dados = payment_info["response"]
    if dados.get("status") != "approved":
        return JsonResponse({"status": "ok", "message": "Payment not approved"})

    external_ref = dados.get("external_reference")
    if not external_ref or '_' not in external_ref:
        return JsonResponse({"status": "error", "message": "Invalid external_reference"}, status=400)

    perfil_id, tipo_plano = external_ref.split('_', 1)

    try:
        perfil = Perfil.objects.get(id=perfil_id)
        
        now = timezone.now()
        
        if tipo_plano == 'destaque':
            perfil.boost = True
            perfil.validade_destaque = now + timedelta(days=7)
        elif tipo_plano == 'premium':
            perfil.premium = True
            perfil.boost = True # Plano Premium também fica em destaque
            perfil.validade_premium = now + timedelta(days=30)
            perfil.validade_destaque = now + timedelta(days=30)
        elif tipo_plano == 'verificado':
            perfil.verificado = True
        
        perfil.pago = True
        perfil.mercadopago_id = str(payment_id)
        perfil.save()
    except Perfil.DoesNotExist:
        return JsonResponse({"status": "error", "message": "Profile not found"}, status=404)
    

    return JsonResponse({"status": "ok"})