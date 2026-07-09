"""
Last Mile Platform - AI Agent Service
Cascade: Rules → Groq x N accounts → Gemini → OpenAI → Fallback
"""
import os
import json
import time
import re
import hashlib
from datetime import datetime, timedelta
from dotenv import load_dotenv
try:
    import requests as _requests
except ImportError:
    _requests = None

# Load .env from same directory
load_dotenv(os.path.join(os.path.dirname(__file__), '.env'))

# ============================================================
# CONFIGURATION - Groq Multi-Account Cascade
# ============================================================
# Support multiple keys: comma-separated in .env
# Each key = 14,400 req/day + 30 RPM + 6,000 TPM
_groq_keys_raw = os.environ.get('GROQ_API_KEYS', '')
if not _groq_keys_raw:
    _groq_keys_raw = os.environ.get('GROQ_API_KEY', '')

GROQ_KEYS = [k.strip() for k in _groq_keys_raw.split(',') if k.strip()]
GROQ_BASE_URL = 'https://api.groq.com/openai/v1'
GROQ_MODEL = 'llama-3.1-8b-instant'  # Free, fast

# Track which key to use next and error counts
_groq_key_index = 0
_groq_key_errors = {}  # key -> consecutive error count

GEMINI_API_KEY = os.environ.get('GEMINI_API_KEY', '')
OPENAI_API_KEY = os.environ.get('OPENAI_API_KEY', '')

# Simple in-memory cache (production: use Redis)
_cache = {}
CACHE_TTL = 300  # 5 minutes

# ============================================================
# RESPONSE CACHE
# ============================================================
def cache_get(key):
    if key in _cache:
        val, ts = _cache[key]
        if time.time() - ts < CACHE_TTL:
            return val
        del _cache[key]
    return None

def cache_set(key, val):
    _cache[key] = (val, time.time())

def cache_key(text, context=None):
    raw = text.strip().lower()
    if context:
        raw += json.dumps(context, sort_keys=True)
    return hashlib.md5(raw.encode()).hexdigest()

# ============================================================
# RULE-BASED RESPONSES (FREE, instant)
# ============================================================
RULES = {
    # Tracking queries
    r'donde.*(mi pedido|mi envio|paquete|orden)': {
        'response': 'Para rastrear tu pedido, necesito el **numero de guia** o **ID del pedido**. Por favor compartemelo y te doy el estatus actualizado.',
        'quick_replies': ['Tengo el numero de guia', 'No lo tengo']
    },
    r'cuando.*(llega|entrega|recibo|llegar)': {
        'response': 'El tiempo de entrega depende de tu zona y el tipo de servicio. Para darte un **ETA preciso**, comparteme tu numero de pedido y verifico la ruta del chofer en tiempo real.',
        'quick_replies': ['Ver mi pedido', 'Hablar con soporte']
    },
    r'cancelar.*(pedido|envio|orden)': {
        'response': 'Puedes cancelar tu pedido **dentro de los primeros 15 minutos** despues de crearlo. Despues de ese tiempo, puede aplicar una penalizacion del 15-25%.\n\nPara cancelar, ve a **Mis Envios** y selecciona el pedido.',
        'quick_replies': ['Ver mis envios', 'Hablar con agente']
    },
    r'como.*(pagar|pago|cobrar)': {
        'response': 'Aceptamos los siguientes metodos de pago:\n\n- **Efectivo** contra entrega\n- **Transferencia SPEI** (CLABE)\n- **OXXO** (referencia)\n- **Tarjeta** debito/credito\n- **Mercado Pago**\n\nCual prefieres usar?',
        'quick_replies': ['OXXO', 'Transferencia', 'Efectivo']
    },
    r'(hora|horario).*(atencion|soporte|servicio)': {
        'response': 'Nuestro horario de soporte es:\n\n- **Lunes a Viernes**: 8:00 AM - 8:00 PM\n- **Sabados**: 9:00 AM - 5:00 PM\n- **Domingos**: Cerrado\n\nChatbot disponible 24/7.',
        'quick_replies': ['Hablar con agente', 'Enviar email']
    },
    r'(reembolso|devolver|devolver.*dinero)': {
        'response': 'Los reembolsos se procesan dentro de **3-5 dias habiles**. Si tu pedido fue cancelado o fallido, el reembolso es automatico. Para solicitar uno, abre un ticket de soporte.',
        'quick_replies': ['Abrir ticket', 'Ver mis pedidos']
    },
    r'(gracias|muchas gracias|gracias!)': {
        'response': 'De nada! Si necesitas algo mas, estoy aqui para ayudarte. 😊',
        'quick_replies': []
    },
    r'(hola|buenos dias|buenas tardes|buenas noches|hey)': {
        'response': 'Hola! Bienvenido a **Last Mile**. Como puedo ayudarte hoy?',
        'quick_replies': ['Rastrear pedido', 'Hacer un envio', 'Consultar factura', 'Hablar con soporte']
    },
}

# Business query patterns (for tenant assistant)
BUSINESS_RULES = {
    r'(cuantos|cuantas).*(envio|pedido|entrega).*hoy': {
        'sql': "SELECT COUNT(*) as total FROM LM_PEDIDOS WHERE PED_FECHA = CURRENT_DATE",
        'template': 'Hoy tienes **{total} envios** registrados.'
    },
    r'(cuantos|cuantas).*(envio|pedido|entrega).*(semana|esta semana)': {
        'sql': "SELECT COUNT(*) as total FROM LM_PEDIDOS WHERE PED_FECHA >= DATE('now', '-7 days')",
        'template': 'Esta semana tienes **{total} envios**.'
    },
    r'(cuantos|cuantas).*(envio|pedido|entrega).*(mes|este mes)': {
        'sql': "SELECT COUNT(*) as total FROM LM_PEDIDOS WHERE strftime('%Y-%m', PED_FECHA) = strftime('%Y-%m', 'now')",
        'template': 'Este mes tienes **{total} envios**.'
    },
    r'(entregados|exitosos|completados).*hoy': {
        'sql': "SELECT COUNT(*) as total FROM LM_PEDIDOS WHERE PED_ESTADO = 'ENTREGADO' AND PED_FECHA = CURRENT_DATE",
        'template': 'Hoy tienes **{total} entregas exitosas**.'
    },
    r'(pendientes|por entregar|en transito)': {
        'sql': "SELECT COUNT(*) as total FROM LM_PEDIDOS WHERE PED_ESTADO IN ('CREADO','ASIGNADO','EN_TRANSITO')",
        'template': 'Tienes **{total} envios pendientes** (creados, asignados o en transito).'
    },
    r'(fallidos|no entregados|devueltos)': {
        'sql': "SELECT COUNT(*) as total FROM LM_PEDIDOS WHERE PED_ESTADO = 'FALLIDO'",
        'template': 'Tienes **{total} envios fallidos**.'
    },
    r'(cancelados|cancelacion)': {
        'sql': "SELECT COUNT(*) as total FROM LM_PEDIDOS WHERE PED_ESTADO = 'CANCELADO'",
        'template': 'Tienes **{total} envios cancelados**.'
    },
    r'(mejor chofer|mejor.*rendimiento|mas entregas)': {
        'sql': "SELECT CHO_NOMBRE, COUNT(*) as entregas FROM LM_PEDIDOS p JOIN LM_CHOFERES c ON p.CHO_ID = c.CHO_ID WHERE p.PED_ESTADO = 'ENTREGADO' GROUP BY CHO_NOMBRE ORDER BY entregas DESC LIMIT 1",
        'template': 'Tu mejor chofer es **{CHO_NOMBRE}** con **{entregas} entregas**.'
    },
    r'(peor chofer|menos entregas|menor rendimiento)': {
        'sql': "SELECT CHO_NOMBRE, COUNT(*) as entregas FROM LM_PEDIDOS p JOIN LM_CHOFERES c ON p.CHO_ID = c.CHO_ID WHERE p.PED_ESTADO = 'ENTREGADO' GROUP BY CHO_NOMBRE ORDER BY entregas ASC LIMIT 1",
        'template': 'El chofer con menos entregas es **{CHO_NOMBRE}** con **{entregas} entregas**.'
    },
    r'(revenue|ingreso|ganancia|facturado).*(hoy|dia)': {
        'sql': "SELECT COALESCE(SUM(PED_COSTO),0) as total FROM LM_PEDIDOS WHERE PED_FECHA = CURRENT_DATE",
        'template': 'Tu revenue de hoy es **${total:,.2f}** MXN.'
    },
    r'(revenue|ingreso|ganancia|facturado).*(mes|este mes)': {
        'sql': "SELECT COALESCE(SUM(PED_COSTO),0) as total FROM LM_PEDIDOS WHERE strftime('%Y-%m', PED_FECHA) = strftime('%Y-%m', 'now')",
        'template': 'Tu revenue de este mes es **${total:,.2f}** MXN.'
    },
    r'(cuantos chofer|choferes activos|total chofer)': {
        'sql': "SELECT COUNT(*) as total FROM LM_CHOFERES WHERE CHO_ESTATUS = 'ACTIVO'",
        'template': 'Tienes **{total} choferes activos**.'
    },
    r'(cuantos vehiculo|vehiculos activos|total vehiculo)': {
        'sql': "SELECT COUNT(*) as total FROM LM_VEHICULOS WHERE VEH_ESTATUS = 'ACTIVO'",
        'template': 'Tienes **{total} vehiculos activos**.'
    },
}

# Fallback responses
FALLBACK_RESPONSE = {
    'response': 'No estoy seguro de como ayudarte con eso. Puedo ayudarte con:\n\n- **Rastrear pedidos** - dime tu numero de guia\n- **Consultas de negocio** - envios, revenue, choferes\n- **Soporte** - pagos, cancelaciones, facturacion\n\nO puedes hablar con un agente humano.',
    'quick_replies': ['Rastrear pedido', 'Hablar con agente']
}

# ============================================================
# GROQ API (FREE - 30 RPM, 14,400 req/day)
# ============================================================
def call_groq(messages, system_prompt=''):
    """
    Call Groq API with multi-account cascade.
    Rotates through N API keys. Each key = 14,400 req/day.
    On 429 (rate limit), tries next key automatically.
    """
    global _groq_key_index
    
    if not GROQ_KEYS or not _requests:
        return None
    
    api_messages = []
    if system_prompt:
        api_messages.append({'role': 'system', 'content': system_prompt})
    api_messages.extend(messages)
    
    payload = {
        'model': GROQ_MODEL,
        'messages': api_messages,
        'max_tokens': 500,
        'temperature': 0.7
    }
    
    # Try each key (max one full rotation)
    attempts = 0
    while attempts < len(GROQ_KEYS):
        key = GROQ_KEYS[_groq_key_index % len(GROQ_KEYS)]
        _groq_key_index = (_groq_key_index + 1) % len(GROQ_KEYS)
        attempts += 1
        
        try:
            resp = _requests.post(
                f'{GROQ_BASE_URL}/chat/completions',
                headers={
                    'Content-Type': 'application/json',
                    'Authorization': f'Bearer {key}'
                },
                json=payload,
                timeout=15
            )
            
            if resp.status_code == 200:
                data = resp.json()
                _groq_key_errors[key] = 0  # Reset errors
                return data['choices'][0]['message']['content']
            
            elif resp.status_code == 429:
                # Rate limit on this key, try next
                _groq_key_errors[key] = _groq_key_errors.get(key, 0) + 1
                print(f'Groq key #{_groq_key_index} rate limited (429), trying next...')
                continue
            
            else:
                print(f'Groq error {resp.status_code}: {resp.text[:200]}')
                return None
                
        except Exception as e:
            print(f'Groq error: {e}')
            return None
    
    print(f'Groq: all {len(GROQ_KEYS)} keys exhausted')
    return None

# ============================================================
# GEMINI API (FREE TIER)
# ============================================================
def call_gemini(messages, system_prompt=''):
    """Call Google Gemini API (free tier: 15 req/min)"""
    if not GEMINI_API_KEY:
        return None
    
    try:
        import urllib.request
        import urllib.parse
        
        url = f'https://generativelanguage.googleapis.com/v1beta/models/gemini-2.0-flash:generateContent?key={GEMINI_API_KEY}'
        
        # Build content
        contents = []
        if system_prompt:
            contents.append({'role': 'user', 'parts': [{'text': system_prompt}]})
            contents.append({'role': 'model', 'parts': [{'text': 'Entendido. Respondere como asistente de Last Mile Platform.'}]})
        
        for msg in messages:
            role = 'user' if msg['role'] == 'user' else 'model'
            contents.append({'role': role, 'parts': [{'text': msg['content']}]})
        
        payload = json.dumps({'contents': contents}).encode('utf-8')
        
        req = urllib.request.Request(url, data=payload, headers={
            'Content-Type': 'application/json'
        })
        
        with urllib.request.urlopen(req, timeout=10) as resp:
            data = json.loads(resp.read().decode())
            if 'candidates' in data and data['candidates']:
                return data['candidates'][0]['content']['parts'][0]['text']
    except Exception as e:
        print(f'Gemini error: {e}')
    return None

# ============================================================
# OPENAI API (FREE CREDIT)
# ============================================================
def call_openai(messages, system_prompt=''):
    """Call OpenAI API (free $5 credit for new accounts)"""
    if not OPENAI_API_KEY:
        return None
    
    try:
        import urllib.request
        
        url = 'https://api.openai.com/v1/chat/completions'
        
        api_messages = []
        if system_prompt:
            api_messages.append({'role': 'system', 'content': system_prompt})
        api_messages.extend(messages)
        
        payload = json.dumps({
            'model': 'gpt-4o-mini',
            'messages': api_messages,
            'max_tokens': 500,
            'temperature': 0.7
        }).encode('utf-8')
        
        req = urllib.request.Request(url, data=payload, headers={
            'Content-Type': 'application/json',
            'Authorization': f'Bearer {OPENAI_API_KEY}'
        })
        
        with urllib.request.urlopen(req, timeout=15) as resp:
            data = json.loads(resp.read().decode())
            return data['choices'][0]['message']['content']
    except Exception as e:
        print(f'OpenAI error: {e}')
    return None

# ============================================================
# SYSTEM PROMPTS
# ============================================================
SUPPORT_SYSTEM_PROMPT = """Eres un asistente de soporte de Last Mile Platform, una plataforma SaaS de delivery en Mexico.

Tu trabajo es ayudar a clientes con:
- Rastreo de pedidos (necesitan numero de guia)
- Informacion sobre tiempos de entrega
- Metodos de pago aceptados
- Proceso de cancelacion y politicas
- Facturacion CFDI
- Problemas con entregas

Reglas:
- Responde en espanol, se amable y profesional
- Si no tienes info especifica del pedido, pide el numero de guia
- Manten respuestas cortas (2-3 parrafos max)
- Ofrece acciones concretas cuando sea posible
- Si el cliente esta molesto, muestra empatia y ofrece escalar a agente humano
- NO inventes informacion que no tengas"""

BUSINESS_SYSTEM_PROMPT = """Eres un asistente de negocio para la plataforma Last Mile. Ayudas a los clientes a entender sus metricas de delivery.

Puedes consultar:
- Numero de envios (hoy, semana, mes)
- Entregas exitosas, fallidas, canceladas
- Revenue e ingresos
- Rendimiento de choferes
- Estado de la flota

Reglas:
- Responde en espanol con datos concretos
- Usa formato de moneda mexicana ($XX,XXX.XX MXN)
- Si la consulta es ambigua, pide clarificacion
- Muestra tendencias cuando sea posible (↑ 12% vs semana pasada)
- Manten respuestas concisas y accionables"""

# ============================================================
# MAIN CHAT FUNCTION
# ============================================================
def chat(user_message, context=None, chat_history=None):
    """
    Main chat function with cascade:
    1. Check cache
    2. Try rule-based response
    3. Try Gemini (free)
    4. Try OpenAI (free credit)
    5. Fallback template
    """
    context = context or {}
    chat_history = chat_history or []
    
    # 1. Check cache
    ckey = cache_key(user_message, context)
    cached = cache_get(ckey)
    if cached:
        return cached
    
    # 2. Try rule-based response
    msg_lower = user_message.lower().strip()
    
    # Check if it's a business query
    is_business = context.get('panel') in ('tenant', 'admin', 'operacion')
    
    if is_business:
        for pattern, rule in BUSINESS_RULES.items():
            if re.search(pattern, msg_lower):
                # In real app, execute SQL and format
                # For demo, return template with mock data
                try:
                    result = rule['template'].format(
                        total=47,  # Mock data
                        CHO_NOMBRE='Carlos Lopez',
                        entregas=23
                    )
                    response = {
                        'response': result,
                        'type': 'data',
                        'quick_replies': ['Ver reporte completo', 'Actualizar datos'],
                        'sql': rule.get('sql')
                    }
                    cache_set(ckey, response)
                    return response
                except:
                    pass
    
    # Check general rules
    for pattern, rule in RULES.items():
        if re.search(pattern, msg_lower):
            response = {
                'response': rule['response'],
                'type': 'info',
                'quick_replies': rule.get('quick_replies', [])
            }
            cache_set(ckey, response)
            return response
    
    # 3. Try Groq (free, fast, no credit card)
    messages = chat_history + [{'role': 'user', 'content': user_message}]
    system = BUSINESS_SYSTEM_PROMPT if is_business else SUPPORT_SYSTEM_PROMPT
    
    groq_resp = call_groq(messages, system)
    if groq_resp:
        response = {
            'response': groq_resp,
            'type': 'ai',
            'provider': 'groq',
            'quick_replies': []
        }
        cache_set(ckey, response)
        return response
    
    # 4. Try Gemini (free)
    gemini_resp = call_gemini(messages, system)
    if gemini_resp:
        response = {
            'response': gemini_resp,
            'type': 'ai',
            'provider': 'gemini',
            'quick_replies': []
        }
        cache_set(ckey, response)
        return response
    
    # 5. Try OpenAI (free credit)
    openai_resp = call_openai(messages, system)
    if openai_resp:
        response = {
            'response': openai_resp,
            'type': 'ai',
            'provider': 'openai',
            'quick_replies': []
        }
        cache_set(ckey, response)
        return response
    
    # 6. Fallback
    response = {
        'response': FALLBACK_RESPONSE['response'],
        'type': 'fallback',
        'quick_replies': FALLBACK_RESPONSE['quick_replies']
    }
    cache_set(ckey, response)
    return response

# ============================================================
# ROUTE OPTIMIZER (No AI needed - pure algorithm)
# ============================================================
def optimize_routes(orders, drivers, start_location=None):
    """
    Optimize delivery routes using nearest neighbor + 2-opt improvement.
    
    Args:
        orders: list of {id, lat, lng, time_window_start, time_window_end, priority}
        drivers: list of {id, lat, lng, capacity, current_orders}
        start_location: {lat, lng} - depot location
    
    Returns:
        Optimized routes for each driver
    """
    import math
    
    if not start_location:
        start_location = {'lat': 19.4326, 'lng': -99.1332}  # Mexico City default
    
    def distance(a, b):
        """Haversine distance in km"""
        R = 6371
        lat1, lon1 = math.radians(a['lat']), math.radians(a['lng'])
        lat2, lon2 = math.radians(b['lat']), math.radians(b['lng'])
        dlat = lat2 - lat1
        dlon = lon2 - lon1
        a_val = math.sin(dlat/2)**2 + math.cos(lat1) * math.cos(lat2) * math.sin(dlon/2)**2
        return R * 2 * math.asin(math.sqrt(a_val))
    
    def total_distance(route):
        total = 0
        for i in range(len(route) - 1):
            total += distance(route[i], route[i+1])
        return total
    
    def two_opt_improve(route):
        """2-opt local search improvement"""
        improved = True
        best = route[:]
        while improved:
            improved = False
            for i in range(1, len(best) - 1):
                for j in range(i + 1, len(best)):
                    new_route = best[:i] + best[i:j+1][::-1] + best[j+1:]
                    if total_distance(new_route) < total_distance(best):
                        best = new_route
                        improved = True
        return best
    
    # Sort orders by priority (urgent first)
    priority_order = {'urgente': 0, 'express': 1, 'normal': 2}
    sorted_orders = sorted(orders, key=lambda o: priority_order.get(o.get('priority', 'normal'), 2))
    
    # Assign orders to drivers (nearest driver first)
    unassigned = sorted_orders[:]
    routes = {}
    
    for driver in drivers:
        if not unassigned:
            break
        
        driver_start = {'lat': driver['lat'], 'lng': driver['lng']}
        capacity = driver.get('capacity', 10)
        current = len(driver.get('current_orders', []))
        available = capacity - current
        
        if available <= 0:
            continue
        
        # Greedy nearest neighbor
        route = [driver_start]
        remaining = unassigned[:]
        
        while remaining and len(route) - 1 < available:
            current_pos = route[-1]
            nearest = min(remaining, key=lambda o: distance(current_pos, o))
            route.append(nearest)
            remaining.remove(nearest)
        
        route.append(driver_start)  # Return to start
        
        # Improve with 2-opt
        if len(route) > 3:
            route = two_opt_improve(route)
        
        # Calculate metrics
        total_dist = total_distance(route)
        estimated_time = total_dist * 3  # ~3 min per km in city
        
        routes[driver['id']] = {
            'driver_id': driver['id'],
            'driver_name': driver.get('name', f'Driver {driver["id"]}'),
            'stops': len(route) - 2,  # Exclude start/end
            'route': route,
            'total_distance_km': round(total_dist, 2),
            'estimated_time_min': round(estimated_time),
            'estimated_fuel_cost': round(total_dist * 2.5, 2),  # ~$2.5/km
            'efficiency_score': round((len(route) - 2) / max(total_dist, 1) * 10, 1)
        }
        
        # Remove assigned orders
        assigned_ids = {o['id'] for o in route if 'id' in o}
        unassigned = [o for o in unassigned if o['id'] not in assigned_ids]
    
    # Summary
    total_orders_assigned = sum(r['stops'] for r in routes.values())
    total_distance = sum(r['total_distance_km'] for r in routes.values())
    total_fuel = sum(r['estimated_fuel_cost'] for r in routes.values())
    
    return {
        'routes': routes,
        'summary': {
            'total_orders': len(orders),
            'orders_assigned': total_orders_assigned,
            'orders_unassigned': len(orders) - total_orders_assigned,
            'drivers_used': len(routes),
            'total_distance_km': round(total_distance, 2),
            'total_estimated_time_min': round(total_distance * 3),
            'total_estimated_fuel_cost': round(total_fuel, 2),
            'avg_efficiency': round(sum(r['efficiency_score'] for r in routes.values()) / max(len(routes), 1), 1)
        }
    }

# ============================================================
# QUICK SUGGESTIONS
# ============================================================
def get_suggestions(panel_type='tenant'):
    """Get contextual quick action suggestions"""
    if panel_type == 'tenant':
        return [
            {'icon': '📦', 'text': 'Cuántos envíos llevo hoy?', 'action': 'query', 'query': 'cuantos envios hoy'},
            {'icon': '🚚', 'text': 'Cuáles están en tránsito?', 'action': 'query', 'query': 'envios en transito'},
            {'icon': '💰', 'text': 'Cuánto facturé este mes?', 'action': 'query', 'query': 'revenue este mes'},
            {'icon': '⭐', 'text': 'Quién es mi mejor chofer?', 'action': 'query', 'query': 'mejor chofer'},
        ]
    elif panel_type == 'support':
        return [
            {'icon': '📍', 'text': 'Rastrear mi pedido', 'action': 'query', 'query': 'donde esta mi pedido'},
            {'icon': '❌', 'text': 'Cómo cancelo?', 'action': 'query', 'query': 'como cancelar pedido'},
            {'icon': '💳', 'text': 'Métodos de pago', 'action': 'query', 'query': 'como pagar'},
            {'icon': '👤', 'text': 'Hablar con agente', 'action': 'escalate'},
        ]
    return []
