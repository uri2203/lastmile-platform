"""
LAST MILE DELIVERY SYSTEM - Backend API v3.0 (Python/Flask + SQLite/PostgreSQL)
Migrado desde un sistema legacy a SQLite/PostgreSQL.
Multi-database: SQLite (dev) + PostgreSQL/Supabase (produccion via DATABASE_URL).
Multi-tenant: cada request lleva X-Emp-Id
Produccion-ready: HTTPS, rate limiting, logging, CORS restricciones
"""

from flask import Flask, request, jsonify, send_from_directory, g
from werkzeug.exceptions import HTTPException
from flask_cors import CORS
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
from flask_socketio import SocketIO, emit, join_room, leave_room
from dotenv import load_dotenv
from db import query, execute, init_schema, check_empty, get_db_info, USE_POSTGRES
from auth import generate_token, generate_refresh_token, refresh_access_token, current_identity, requiere_auth, requiere_rol, requiere_superadmin
from security import hash_password, verify_password, is_legacy_hash, validate_password_strength
from webhooks import webhook_bp
from monitoring import init_monitoring
from agents import RouteOptimizer, SmartAssignment, ETAPredictor, SupportChatbot, DemandForecaster, DynamicPricing, FraudDetector, SentimentAnalyzer
import os
import time
import logging
from logging.handlers import RotatingFileHandler
from datetime import datetime

# ========================================
# CARGAR VARIABLES DE ENTORNO
# ========================================
load_dotenv(os.path.join(os.path.dirname(__file__), '.env'))

# Servir archivos estaticos desde /web
app = Flask(__name__, static_folder='web', static_url_path='')
app.register_blueprint(webhook_bp)

# ========================================
# MONITORING: Sentry + metrics
# ========================================
init_monitoring(app)

# Max request body size: 10MB
app.config['MAX_CONTENT_LENGTH'] = 10 * 1024 * 1024

# Validate FLASK_SECRET_KEY in production
_secret_key = os.environ.get('FLASK_SECRET_KEY', '')
if not _secret_key or _secret_key == 'lastmile-dev-key-change-in-prod':
    if os.environ.get('FLASK_ENV') == 'production' or os.environ.get('RENDER'):
        import warnings
        warnings.warn('[SECURITY] FLASK_SECRET_KEY is not set or using default! JWT tokens can be forged.')
        print('[SECURITY] WARNING: Set FLASK_SECRET_KEY env var to a strong random value!')
app.secret_key = _secret_key or 'lastmile-dev-key-change-in-prod'

# ========================================
# CORS: Restringido por origen en produccion
# ========================================
ALLOWED_ORIGINS = os.environ.get('ALLOWED_ORIGINS', '').split(',') if os.environ.get('ALLOWED_ORIGINS') else ['*']
CORS(app, origins=ALLOWED_ORIGINS, supports_credentials=True,
     allow_headers=['Content-Type', 'X-Emp-Id', 'Authorization'],
     methods=['GET', 'POST', 'PUT', 'DELETE', 'OPTIONS'])

# ========================================
# WEBSOCKET: Flask-SocketIO para GPS tiempo real
# ========================================
socketio = SocketIO(app, cors_allowed_origins=ALLOWED_ORIGINS, async_mode='eventlet',
                    ping_timeout=30, ping_interval=25)

# ========================================
# VAPID: Push notifications keys (fallback)
# ========================================
VAPID_PUBLIC_KEY = os.environ.get('VAPID_PUBLIC_KEY', '')
VAPID_PRIVATE_KEY = os.environ.get('VAPID_PRIVATE_KEY', '')
VAPID_SUBJECT = os.environ.get('VAPID_SUBJECT', 'mailto:admin@lastmile.app')

@app.route('/api/vapid-public-key', methods=['GET'])
def get_vapid_key():
    return jsonify({'publicKey': VAPID_PUBLIC_KEY})

@app.route('/api/push/subscribe', methods=['POST'])
def subscribe_push():
    emp_id = get_emp_id()
    data = request.json
    user_id = data.get('user_id')
    subscription = data.get('subscription')
    if not user_id or not subscription:
        return jsonify({'error': 'Missing user_id or subscription'}), 400
    try:
        execute('''CREATE TABLE IF NOT EXISTS PUSH_SUBSCRIPTIONS (
            id SERIAL PRIMARY KEY, emp_id INTEGER, user_id TEXT,
            endpoint TEXT, p256dh TEXT, auth TEXT, created_at TIMESTAMP DEFAULT NOW()
        )''', [])
    except Exception:
        pass
    try:
        keys = subscription.get('keys', {})
        execute(
            'INSERT INTO PUSH_SUBSCRIPTIONS (emp_id, user_id, endpoint, p256dh, auth) VALUES (?, ?, ?, ?, ?)',
            [emp_id, user_id, subscription.get('endpoint', ''), keys.get('p256dh', ''), keys.get('auth', '')]
        )
    except Exception as e:
        app.logger.warning(f'Push subscribe error: {e}')
    return jsonify({'success': True})

def send_push_notification(emp_id, user_id, title, body, url='/panel-chofer.html'):
    try:
        import py_vapid
        from py_vapid import Vapid
        subs = query('SELECT endpoint, p256dh, auth FROM PUSH_SUBSCRIPTIONS WHERE emp_id=? AND user_id=?', [emp_id, user_id])
        if not subs:
            return
        vapid = Vapid()
        vapid.private_key = VAPID_PRIVATE_KEY
        for sub in subs:
            try:
                from webpush import webpush as wp
                wp(subscription_info={'endpoint': sub['endpoint'], 'keys': {'p256dh': sub['p256dh'], 'auth': sub['auth']}},
                   data=json.dumps({'title': title, 'body': body, 'url': url}),
                   vapid_private_key=VAPID_PRIVATE_KEY, vapid_claims={'sub': VAPID_SUBJECT})
            except Exception:
                pass
    except Exception:
        pass

# ========================================
# BACKUP: Exportación de base de datos
# ========================================
@app.route('/api/cron/backup', methods=['POST'])
def cron_backup():
    """Export all tables as JSON for backup. Auth via CRON_API_KEY."""
    key = request.headers.get('X-Cron-Key') or request.args.get('key')
    if key != os.environ.get('CRON_API_KEY', 'lastmile-cron-2026'):
        return jsonify({'error': 'Unauthorized'}), 401
    try:
        import json
        from datetime import datetime
        tables = ['TENANTS', 'USUARIOS', 'CHOFERES', 'VEHICULOS', 'CLIENTES', 'PEDIDOS',
                  'TRACKING', 'FISCAL_CONFIG', 'FISCAL_DOCUMENTS', 'PUSH_SUBSCRIPTIONS']
        backup = {'timestamp': datetime.now().isoformat(), 'tables': {}}
        for table in tables:
            try:
                data = query(f'SELECT * FROM {table} LIMIT 5000', [])
                backup['tables'][table] = data
            except Exception:
                backup['tables'][table] = []
        return jsonify({'success': True, 'backup': backup, 'size': len(json.dumps(backup))})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/cron/backup/download', methods=['GET'])
def cron_backup_download():
    """Download backup as JSON file."""
    key = request.args.get('key')
    if key != os.environ.get('CRON_API_KEY', 'lastmile-cron-2026'):
        return jsonify({'error': 'Unauthorized'}), 401
    try:
        import json
        from datetime import datetime
        from flask import Response
        tables = ['TENANTS', 'USUARIOS', 'CHOFERES', 'VEHICULOS', 'CLIENTES', 'PEDIDOS',
                  'TRACKING', 'FISCAL_CONFIG', 'FISCAL_DOCUMENTS']
        backup = {'timestamp': datetime.now().isoformat(), 'version': '1.0', 'tables': {}}
        for table in tables:
            try:
                data = query(f'SELECT * FROM {table} LIMIT 5000', [])
                backup['tables'][table] = data
            except Exception:
                backup['tables'][table] = []
        filename = f'lastmile_backup_{datetime.now().strftime("%Y%m%d_%H%M%S")}.json'
        return Response(
            json.dumps(backup, default=str, ensure_ascii=False),
            mimetype='application/json',
            headers={'Content-Disposition': f'attachment; filename={filename}'}
        )
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@socketio.on('connect')
def handle_connect():
    print(f'[WS] Client connected: {request.sid}')

@socketio.on('disconnect')
def handle_disconnect():
    print(f'[WS] Client disconnected: {request.sid}')

@socketio.on('subscribe')
def handle_subscribe(data):
    emp_id = data.get('emp_id')
    if emp_id:
        room = f'emp_{emp_id}'
        join_room(room)
        print(f'[WS] Client {request.sid} subscribed to room {room}')

@socketio.on('unsubscribe')
def handle_unsubscribe(data):
    emp_id = data.get('emp_id')
    if emp_id:
        room = f'emp_{emp_id}'
        leave_room(room)

@socketio.on('gps_update')
def handle_gps_update(data):
    emp_id = data.get('emp_id')
    cho_id = data.get('choId')
    if not emp_id or not cho_id:
        return
    try:
        execute(
            '''INSERT INTO TRACKING (EMP_ID, CHO_ID, VEH_ID, TRK_LATITUD, TRK_LONGITUD, TRK_VELOCIDAD, TRK_RUMBO, TRK_BATERIA)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?)''',
            [emp_id, cho_id, data.get('vehId'),
             data.get('latitud'), data.get('longitud'),
             data.get('velocidad', 0), data.get('rumbo', 0), data.get('bateria', 100)]
        )
        room = f'emp_{emp_id}'
        emit('driver_location', {
            'choId': cho_id,
            'nombre': data.get('nombre', ''),
            'apellido': data.get('apellido', ''),
            'lat': data.get('latitud'),
            'lng': data.get('longitud'),
            'speed': data.get('velocidad', 0),
            'heading': data.get('rumbo', 0),
            'battery': data.get('bateria', 100),
            'timestamp': datetime.now().isoformat()
        }, room=room)
    except Exception as e:
        print(f'[WS] GPS update error: {e}')

@socketio.on('client_subscribe_order')
def handle_client_subscribe(data):
    pedido_id = data.get('pedido_id')
    if pedido_id:
        room = f'order_{pedido_id}'
        join_room(room)
        print(f'[WS] Client subscribed to order {room}')

@socketio.on('client_unsubscribe_order')
def handle_client_unsubscribe(data):
    pedido_id = data.get('pedido_id')
    if pedido_id:
        room = f'order_{pedido_id}'
        leave_room(room)

# ========================================
# RATE LIMITING: 200 req/min por IP general, 10/min para auth
# Intenta Redis para multi-worker, fallback a memory
# ========================================
_redis_url = os.environ.get('REDIS_URL', '')
if _redis_url:
    storage_uri = _redis_url
    print(f'[RATELIMIT] Using Redis: {_redis_url[:30]}...')
else:
    storage_uri = "memory://"
    print('[RATELIMIT] Using in-memory (single-worker only). Set REDIS_URL for multi-worker.')
limiter = Limiter(
    get_remote_address,
    app=app,
    default_limits=["200 per minute"],
    storage_uri=storage_uri,
)

# ========================================
# LOGGING: Rotating file + console
# ========================================
LOG_DIR = os.path.join(os.path.dirname(__file__), 'logs')
os.makedirs(LOG_DIR, exist_ok=True)

request_logger = logging.getLogger('request')
request_logger.setLevel(logging.INFO)
req_handler = RotatingFileHandler(
    os.path.join(LOG_DIR, 'requests.log'),
    maxBytes=5*1024*1024, backupCount=5, encoding='utf-8'
)
req_handler.setFormatter(logging.Formatter('%(asctime)s [%(levelname)s] %(message)s'))
request_logger.addHandler(req_handler)

error_logger = logging.getLogger('error')
error_logger.setLevel(logging.ERROR)
err_handler = RotatingFileHandler(
    os.path.join(LOG_DIR, 'errors.log'),
    maxBytes=5*1024*1024, backupCount=5, encoding='utf-8'
)
err_handler.setFormatter(logging.Formatter('%(asctime)s [%(levelname)s] %(message)s'))
error_logger.addHandler(err_handler)

console_handler = logging.StreamHandler()
console_handler.setFormatter(logging.Formatter('%(asctime)s %(message)s', datefmt='%H:%M:%S'))
request_logger.addHandler(console_handler)

# ========================================
# AUDIT LOGGING: Sensitive operations tracking
# ========================================
audit_logger = logging.getLogger('audit')
audit_logger.setLevel(logging.INFO)
audit_handler = RotatingFileHandler(
    os.path.join(LOG_DIR, 'audit.log'),
    maxBytes=5*1024*1024, backupCount=10, encoding='utf-8'
)
audit_handler.setFormatter(logging.Formatter('%(asctime)s [AUDIT] %(message)s'))
audit_logger.addHandler(audit_handler)


def log_audit(action, details=None):
    """Log a sensitive operation for audit trail."""
    user = getattr(g, 'usuario', 'system')
    emp = getattr(g, 'emp_id', '-')
    ip = request.remote_addr or '-'
    msg = f'action={action} user={user} emp={emp} ip={ip}'
    if details:
        msg += f' details={details}'
    audit_logger.info(msg)

# ========================================
# DATABASE: Auto-detect SQLite or PostgreSQL via DATABASE_URL
# ========================================

# Auto-initialize database on first run
db_info = get_db_info()
if db_info['type'] == 'SQLite':
    DATA_DIR = os.environ.get('DATA_DIR', os.path.dirname(os.path.abspath(__file__)))
    DB_PATH = os.path.join(DATA_DIR, 'lastmile.db')

    if not os.path.exists(DB_PATH):
        print(f'[DB] First run - initializing SQLite database at {DB_PATH}')
        try:
            from seed import seed
            seed()
        except Exception as e:
            print(f'[DB] Seed failed ({e}), falling back to schema only')
            from database import init_db
            init_db()
    elif check_empty():
        print('[DB] Database exists but is empty - running seed...')
        try:
            from seed import seed
            seed()
        except Exception as e:
            print(f'[DB] Seed failed: {e}')
else:
    # PostgreSQL: initialize schema, seed if empty
    init_schema()
    if check_empty():
        print('[DB] PostgreSQL empty - running seed via migrate_to_pg.py...')
        try:
            from seed import seed_pg
            seed_pg()
        except Exception as e:
            print(f'[DB] PG seed skipped ({e}). Run: python migrate_to_pg.py DATABASE_URL')

    # Auto-add billing columns if missing
    try:
        from payment_service import ensure_billing_columns
        ensure_billing_columns()
    except Exception as e:
        print(f'[DB] Billing columns check skipped: {e}')

    # Auto-add lockout columns if missing
    try:
        ensure_lockout_columns()
    except Exception as e:
        print(f'[DB] Lockout columns check skipped: {e}')


def ensure_lockout_columns():
    """Add account lockout columns to USUARIOS if they don't exist."""
    if not USE_POSTGRES:
        return
    try:
        execute("ALTER TABLE USUARIOS ADD COLUMN IF NOT EXISTS USU_FAILED_ATTEMPTS INTEGER DEFAULT 0")
    except Exception:
        pass
    try:
        execute("ALTER TABLE USUARIOS ADD COLUMN IF NOT EXISTS USU_LOCKED_UNTIL TIMESTAMP")
    except Exception:
        pass
    try:
        execute("ALTER TABLE USUARIOS ADD COLUMN IF NOT EXISTS USU_LAST_FAILED_AT TIMESTAMP")
    except Exception:
        pass


def get_emp_id():
    """Tenant de la request, derivado del TOKEN verificado (nunca del header)."""
    return getattr(g, 'emp_id', None)


def get_rol():
    """Rol del usuario autenticado, derivado del token."""
    return getattr(g, 'rol', None)


# ========================================
# CONTROL DE ACCESO
# ========================================
# Rutas /api publicas: no requieren token.
PUBLIC_API_PATHS = {
    '/api/health',
    '/api/auth/login',
    '/api/auth/refresh',
    '/api/auth/forgot-password',
    '/api/auth/verify-reset-code',
    '/api/auth/reset-password',
    '/api/docs',
    '/api/onboarding/register',
    '/api/saas/planes',
    '/api/billing/planes',
    '/api/billing/webhook/stripe',
    '/api/billing/webhook/mercadopago',
    '/api/pagos/mercado-pago/webhook',
    '/api/vapid-public-key',
    '/api/push/subscribe',
}
# Prefijos publicos: tracking del cliente final por token opaco en la URL.
PUBLIC_API_PREFIXES = ('/api/cliente-final/', '/api/saas/planes', '/api/webhooks/')
# Endpoint(s) servicio-a-servicio: autenticados por CRON_API_KEY, no por JWT.
CRON_API_PATHS = {'/api/billing/auto-charge', '/api/cron/backup', '/api/cron/backup/download'}
# Prefijos de gestion GLOBAL de la plataforma: solo 'superadmin'.
# El admin de un tenant cliente NO puede gestionar otros tenants ni la plataforma.
SUPERADMIN_API_PREFIXES = ('/api/admin/', '/api/saas/')
SETUP_API_PREFIX = '/api/setup/'


def _is_public_api(path, method):
    if method == 'OPTIONS':
        return True  # preflight CORS
    if path in PUBLIC_API_PATHS:
        return True
    return any(path.startswith(p) for p in PUBLIC_API_PREFIXES)


# ========================================
# REQUEST MIDDLEWARE (gate de autenticacion/autorizacion, fail-closed)
# ========================================
@app.before_request
def before_request():
    request.start_time = time.time()
    path = request.path
    method = request.method

    # Rutas no-/api => paginas estaticas / landing (publicas).
    if not path.startswith('/api/'):
        return

    # Endpoints publicos legitimos.
    if _is_public_api(path, method):
        return

    # Cron: autenticado por CRON_API_KEY dentro del propio handler.
    if path in CRON_API_PATHS:
        return

    # A partir de aqui se EXIGE un token valido.
    ident = current_identity()
    if not ident:
        return jsonify({'success': False, 'error': 'No autenticado'}), 401
    g.emp_id = ident.get('emp_id')
    g.rol = ident.get('rol')
    g.usu_id = ident.get('usu_id')
    g.usuario = ident.get('usuario', '')

    # Endpoints destructivos /api/setup/* (DROP TABLE global): superadmin + ALLOW_SETUP=true.
    if path.startswith(SETUP_API_PREFIX):
        if g.rol != 'superadmin':
            return jsonify({'success': False, 'error': 'No autorizado'}), 403
        if os.environ.get('ALLOW_SETUP', '').lower() != 'true':
            return jsonify({'success': False, 'error': 'Setup deshabilitado (ALLOW_SETUP no activo)'}), 403
    # Gestion global de la plataforma (/api/admin/*, /api/saas/*): solo superadmin.
    elif any(path.startswith(p) for p in SUPERADMIN_API_PREFIXES):
        if g.rol != 'superadmin':
            return jsonify({'success': False, 'error': 'No autorizado'}), 403

    # Anti-IDOR: si la URL trae emp_id, solo el superadmin accede a otros tenants.
    view_args = request.view_args or {}
    if 'emp_id' in view_args and g.rol != 'superadmin':
        try:
            if int(view_args['emp_id']) != int(g.emp_id):
                return jsonify({'success': False, 'error': 'No autorizado'}), 403
        except (ValueError, TypeError):
            return jsonify({'success': False, 'error': 'No autorizado'}), 403

    # Contexto de tenant para RLS (best-effort; no-op en SQLite).
    try:
        if g.emp_id:
            from db import set_tenant_context
            set_tenant_context(int(g.emp_id))
    except (ValueError, TypeError):
        pass


@app.after_request
def after_request(response):
    # Security headers
    response.headers['X-Content-Type-Options'] = 'nosniff'
    response.headers['X-Frame-Options'] = 'DENY'
    response.headers['X-XSS-Protection'] = '1; mode=block'
    response.headers['Referrer-Policy'] = 'strict-origin-when-cross-origin'
    if os.environ.get('FLASK_ENV') == 'production' or os.environ.get('RENDER'):
        response.headers['Strict-Transport-Security'] = 'max-age=31536000; includeSubDomains'
    if request.path.startswith('/api/'):
        response.headers['Content-Security-Policy'] = "default-src 'none'"
    if hasattr(request, 'start_time'):
        elapsed = round((time.time() - request.start_time) * 1000, 1)
        status = response.status_code
        path = request.path
        method = request.method
        emp_id = getattr(g, 'emp_id', '-')
        ip = request.remote_addr or '-'
        request_logger.info(f'{method} {path} => {status} [{elapsed}ms] emp={emp_id} ip={ip}')
    return response


@app.errorhandler(429)
def handle_rate_limit(e):
    return jsonify({'success': False, 'error': 'Demasiados intentos. Espera un momento e intenta de nuevo.'}), 429


@app.errorhandler(404)
def handle_not_found(e):
    if request.path.startswith('/api/'):
        return jsonify({'success': False, 'error': 'Endpoint no encontrado'}), 404
    return e


@app.errorhandler(413)
def handle_too_large(e):
    return jsonify({'success': False, 'error': 'Request demasiado grande. Maximo 10MB.'}), 413


@app.errorhandler(Exception)
def handle_exception(e):
    if isinstance(e, HTTPException):
        return e
    error_logger.error(f'Unhandled: {str(e)}', exc_info=True)
    return jsonify({'success': False, 'error': 'Error interno del servidor'}), 500


# ========================================
# STATIC ROUTES
# ========================================
@app.route('/')
def root():
    return send_from_directory('web', 'landing.html')


@app.route('/login')
def login_page():
    return send_from_directory('web', 'index.html')


@app.route('/saas')
def saas_panel():
    return send_from_directory('web', 'panel-saas.html')


@app.route('/<path:filename>')
def serve_static(filename):
    return send_from_directory('web', filename)


# ========================================
# MODULO: ONBOARDING
# ========================================
@app.route('/register')
def register_page():
    return send_from_directory('web', 'register.html')

@app.route('/terminos')
def terminos_page():
    return send_from_directory('web', 'terminos.html')

@app.route('/privacidad')
def privacidad_page():
    return send_from_directory('web', 'privacidad.html')

@app.route('/pagos')
def pagos_page():
    return send_from_directory('web', 'pagos.html')

@app.route('/deslinde')
def deslinde_page():
    return send_from_directory('web', 'deslinde.html')

@app.route('/sla')
def sla_page():
    return send_from_directory('web', 'sla.html')

@app.route('/cookies')
def cookies_page():
    return send_from_directory('web', 'cookies.html')

@app.route('/demo')
def demo_video():
    return send_from_directory('web', 'demo-video.html')

@app.route('/proteccion-datos')
def proteccion_datos():
    return send_from_directory('web', 'proteccion-datos.html')

@app.route('/regulaciones-ia')
def regulaciones_ia():
    return send_from_directory('web', 'regulaciones-ia.html')

@app.route('/privacidad-eeuu')
def privacidad_eeuu():
    return send_from_directory('web', 'privacidad-eeuu.html')

@app.route('/panel-admin')
def panel_admin():
    return send_from_directory('web', 'panel-admin.html')

@app.route('/panel-ai')
def panel_ai():
    return send_from_directory('web', 'panel-ai.html')

@app.route('/panel-chofer')
def panel_chofer():
    return send_from_directory('web', 'panel-chofer.html')

@app.route('/panel-cliente')
def panel_cliente():
    return send_from_directory('web', 'panel-cliente.html')

@app.route('/panel-operacion')
def panel_operacion():
    return send_from_directory('web', 'panel-operacion.html')

@app.route('/panel-tenant')
def panel_tenant():
    return send_from_directory('web', 'panel-tenant.html')

@app.route('/onboarding')
def onboarding():
    return send_from_directory('web', 'onboarding.html')

@app.route('/tracking')
def tracking_cliente():
    return send_from_directory('web', 'tracking-cliente.html')

@app.route('/ayuda')
def ayuda_cliente():
    return send_from_directory('web', 'ayuda-cliente.html')


@app.route('/api/onboarding/register', methods=['POST'])
def onboarding_register():
    """Register a new tenant with admin user."""
    data = request.get_json() or {}

    emp_data = data.get('empresa', {})
    usr_data = data.get('usuario', {})
    plan = data.get('plan', 'STARTER')

    # Validate
    if not emp_data.get('nombre'):
        return jsonify({'success': False, 'error': 'Nombre de empresa requerido'}), 400
    if not emp_data.get('rfc'):
        return jsonify({'success': False, 'error': 'RFC requerido'}), 400
    if not usr_data.get('email') or '@' not in usr_data.get('email', ''):
        return jsonify({'success': False, 'error': 'Email inválido'}), 400
    pwd = usr_data.get('password', '')
    pwd_ok, pwd_err = validate_password_strength(pwd)
    if not pwd_ok:
        return jsonify({'success': False, 'error': pwd_err}), 400

    # Check if RFC already exists
    try:
        existing = query("SELECT EMP_ID FROM EMPRESAS WHERE EMP_RFC=?", [emp_data['rfc'].upper()])
        if existing:
            return jsonify({'success': False, 'error': 'Ya existe una empresa con ese RFC'}), 400
    except Exception:
        pass

    # Check if email already exists
    try:
        existing = query("SELECT USU_ID FROM USUARIOS WHERE USU_EMAIL=?", [usr_data['email']])
        if existing:
            return jsonify({'success': False, 'error': 'Ya existe una cuenta con ese email'}), 400
    except Exception:
        pass

    # Create empresa
    import string, random
    plan_config = {'STARTER': 10, 'PRO': 50, 'ENTERPRISE': 9999}
    # Generate unique referral code
    referral_code = ''.join(random.choices(string.ascii_uppercase + string.digits, k=8))
    try:
        existing_code = query("SELECT EMP_ID FROM EMPRESAS WHERE EMP_REFERRAL_CODE=?", [referral_code])
        if existing_code:
            referral_code = ''.join(random.choices(string.ascii_uppercase + string.digits, k=10))
    except Exception:
        pass

    # Process referral if code provided
    referrer_emp_id = None
    input_referral_code = emp_data.get('referral_code', '').strip().upper()
    if input_referral_code:
        try:
            referrer = query("SELECT EMP_ID, EMP_NOMBRE FROM EMPRESAS WHERE EMP_REFERRAL_CODE=?", [input_referral_code])
            if referrer:
                referrer_emp_id = referrer[0].get('EMP_ID', referrer[0].get('emp_id'))
        except Exception:
            pass

    referred_by = referrer_emp_id if referrer_emp_id else None
    try:
        execute(
            "INSERT INTO EMPRESAS (EMP_RFC, EMP_NOMBRE, EMP_EMAIL, EMP_ESTATUS, EMP_PLAN, "
            "EMP_MAX_USUARIOS, EMP_MAX_CHOFERES, EMP_MAX_PEDIDOS_MES, EMP_REFERRAL_CODE, EMP_REFERRED_BY) "
            "VALUES (?, ?, ?, 'ACTIVA', ?, ?, ?, ?, ?, ?)",
            [emp_data['rfc'].upper(), emp_data['nombre'],
             usr_data.get('email', ''),
             plan, 5, plan_config.get(plan, 10), 500,
             referral_code, referred_by]
        )
        r = query("SELECT MAX(EMP_ID) as id FROM EMPRESAS")
        emp_id = r[0].get('ID', r[0].get('id', 1)) if r else 1
    except Exception as e:
        print(f'[ERROR] Creando empresa: {e}')
        return jsonify({'success': False, 'error': 'Error al crear empresa. Intenta de nuevo.'}), 500

    # Record referral relationship
    if referrer_emp_id:
        try:
            execute(
                "INSERT INTO REFERRALS (REF_REFERRER_EMP_ID, REFREFERRED_EMP_ID, REFREFERRED_USR_ID, "
                "REFREFERRED_NAME, REFREFERRED_EMAIL, REF_BONUS_DAYS) "
                "VALUES (?, ?, 0, ?, ?, 14)",
                [referrer_emp_id, emp_id, emp_data['nombre'], usr_data.get('email', '')]
            )
        except Exception:
            pass

    # Create admin user
    password_hash = hash_password(usr_data['password'])
    try:
        execute(
            "INSERT INTO USUARIOS (USU_EMP_ID, USU_USUARIO, USU_PASS, USU_NOMBRE, USU_EMAIL, "
            "USU_TELEFONO, USU_ROL, USU_ACTIVO, USU_CREATED) "
            "VALUES (?, ?, ?, ?, ?, ?, 'admin', 'S', NOW())",
            [emp_id, usr_data.get('usuario', 'admin'), password_hash,
             usr_data['nombre'], usr_data['email'],
             usr_data.get('telefono', '')]
        )
        # Get the newly created user ID
        usr_row = query("SELECT MAX(USR_ID) as id FROM USUARIOS WHERE USU_EMP_ID=?", [emp_id])
        usr_id = usr_row[0].get('ID', usr_row[0].get('id', 0)) if usr_row else 0
    except Exception as e:
        print(f'[ERROR] Creando usuario: {e}')
        return jsonify({'success': False, 'error': 'Error al crear usuario. Intenta de nuevo.'}), 500

    # Record legal acceptance for legal protection
    legal_data = data.get('legal', {})
    client_ip = request.headers.get('X-Forwarded-For', request.remote_addr or 'unknown')
    user_agent = request.headers.get('User-Agent', 'unknown')
    try:
        execute(
            "INSERT INTO LEGAL_ACCEPTANCE (EMP_ID, USR_ID, LA_IP, LA_USER_AGENT, "
            "LA_TERMINOS, LA_PRIVACIDAD, LA_PAGOS, LA_DESLINDE, LA_SLA, LA_COOKIES, "
            "LA_FECHA, LA_ACCEPTED_ALL) "
            "VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, NOW(), 'S')",
            [emp_id, usr_id, client_ip, user_agent,
             'S' if legal_data.get('terminos') else 'N',
             'S' if legal_data.get('privacidad') else 'N',
             'S' if legal_data.get('pagos') else 'N',
             'S' if legal_data.get('deslinde') else 'N',
             'S' if legal_data.get('sla') else 'N',
             'S' if legal_data.get('cookies') else 'N']
        )
    except Exception as e:
        print(f'[ERROR] Legal acceptance: {e}')
    try:
        plan_row = query("SELECT PLAN_ID FROM SAAS_PLANES WHERE PLAN_NOMBRE=? AND PLAN_ACTIVO='S'", [plan])
        if plan_row:
            pid = plan_row[0].get('PLAN_ID', plan_row[0].get('plan_id', 1))
        else:
            pid = 1
        execute(
            "INSERT INTO SAAS_SUSCRIPCIONES (EMP_ID, PLAN_ID, SUS_ESTADO, SUS_FECHA_INICIO) "
            "VALUES (?, ?, 'ACTIVA', CURRENT_TIMESTAMP)",
            [emp_id, pid]
        )
    except Exception as e:
        print(f'[ERROR] Suscripcion: {e}')

    # Seed some sample data for the new tenant
    try:
        _seed_demo_data(emp_id)
    except Exception as e:
        print(f'[ERROR] Seed data: {e}')

    return jsonify({
        'success': True,
        'message': 'Cuenta creada exitosamente',
        'emp_id': emp_id,
        'login': usr_data.get('usuario', 'admin'),
        'referral_code': referral_code
    })


def _seed_demo_data(emp_id):
    """Seed demo data for new tenant."""
    import random

    clients = [
        ('Distribuidora Norte', 'DNO230303', 'Pedro Hernandez', 'pedidos@distnorte.mx', '5551111113', 'CDMX'),
        ('Tienda Express', 'TEX230303', 'Laura Sanchez', 'contacto@tienda.mx', '5551111114', 'CDMX'),
        ('Comercializadora Sur', 'CSU230303', 'Roberto Diaz', 'ventas@sur.mx', '5551111115', 'CDMX'),
    ]
    for rfc, nombre, contacto, email, tel, ciudad in clients:
        try:
            execute(
                "INSERT INTO CLIENTES_LM (EMP_ID, CLI_RAZON_SOCIAL, CLI_RFC, CLI_CONTACTO, "
                "CLI_EMAIL, CLI_TELEFONO, CLI_CIUDAD, CLI_ESTATUS) "
                "VALUES (?, ?, ?, ?, ?, ?, ?, 'ACTIVO')",
                [emp_id, nombre, rfc, contacto, email, tel, ciudad]
            )
        except Exception:
            pass

    choferes = [
        ('Carlos', 'Rodriguez', '5551001001', 'carlos@delivery.mx', 'LIC-001'),
        ('Maria', 'Lopez', '5551001002', 'maria@delivery.mx', 'LIC-002'),
        ('Ana', 'Martinez', '5551001003', 'ana@delivery.mx', 'LIC-003'),
    ]
    for nombre, apellido, tel, email, lic in choferes:
        try:
            execute(
                "INSERT INTO CHOFERES (EMP_ID, CHO_NOMBRE, CHO_APELLIDO, CHO_TELEFONO, "
                "CHO_EMAIL, CHO_LICENCIA, CHO_ESTATUS) "
                "VALUES (?, ?, ?, ?, ?, ?, 'ACTIVO')",
                [emp_id, nombre, apellido, tel, email, lic]
            )
        except Exception:
            pass

    for i in range(5):
        try:
            execute(
                "INSERT INTO PEDIDOS (EMP_ID, PED_CLIENTE_NOMBRE, PED_DESTINO_DIR, "
                "PED_DESTINO_CIUDAD, PED_BULTOS, PED_COSTO_TOTAL, PED_FORMA_PAGO, "
                "PED_ESTADO, PED_FECHA_PEDIDO) "
                "VALUES (?, ?, ?, ?, ?, ?, 'EFECTIVO', 'PENDIENTE', "
                "CURRENT_TIMESTAMP - INTERVAL '1 day' * %s)",
                [emp_id, f'Cliente Demo {i+1}', f'Direccion {i+1}, Col. Centro',
                 'CDMX', random.randint(1, 3), round(random.uniform(150, 800), 2), i]
            )
        except Exception:
            pass


# ========================================
# MODULO: BILLING & USAGE DASHBOARD
# ========================================
@app.route('/api/billing/dashboard', methods=['GET'])
def billing_dashboard():
    """Get billing dashboard data for current tenant."""
    emp_id = get_emp_id()
    try:
        from billing_service import get_billing_dashboard
        data = get_billing_dashboard(emp_id)
        return jsonify({'success': True, 'data': data})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


@app.route('/api/billing/limits', methods=['GET'])
def billing_limits():
    """Check if tenant is within plan limits."""
    emp_id = get_emp_id()
    try:
        from billing_service import check_limits
        result = check_limits(emp_id)
        return jsonify({'success': True, 'data': result})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


@app.route('/api/billing/track', methods=['POST'])
def billing_track():
    """Track usage metric for current tenant."""
    emp_id = get_emp_id()
    data = request.get_json() or {}
    metric = data.get('metric', '')
    count = data.get('count', 1)
    if not metric:
        return jsonify({'success': False, 'error': 'metric required'}), 400
    try:
        from billing_service import track_usage
        track_usage(emp_id, metric, count)
        return jsonify({'success': True})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


@app.route('/api/billing/auto-charge', methods=['POST'])
def auto_charge():
    """Process all due subscription charges. Protected endpoint."""
    # Simple API key protection
    api_key = request.headers.get('X-Cron-Key', '')
    expected = os.environ.get('CRON_API_KEY')
    if not expected or api_key != expected:
        return jsonify({'success': False, 'error': 'Unauthorized'}), 403
    try:
        from billing_service import run_auto_billing
        result = run_auto_billing()
        return jsonify({'success': True, 'data': result})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


@app.route('/api/billing/usage', methods=['GET'])
def billing_usage():
    """Get current month usage for tenant."""
    emp_id = get_emp_id()
    try:
        from billing_service import get_usage
        usage = get_usage(emp_id)
        return jsonify({'success': True, 'data': usage})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


@app.route('/api/admin/tenants-usage', methods=['GET'])
@requiere_superadmin
def admin_tenants_usage():
    """Get usage for all tenants (admin only)."""
    try:
        rows = query(
            "SELECT e.EMP_ID, e.EMP_NOMBRE, e.EMP_PLAN, e.EMP_ESTATUS, "
            "(SELECT COUNT(*) FROM USUARIOS u WHERE u.USU_EMP_ID = e.EMP_ID) as usuarios, "
            "(SELECT COUNT(*) FROM CHOFERES c WHERE c.EMP_ID = e.EMP_ID) as choferes, "
            "(SELECT COUNT(*) FROM PEDIDOS p WHERE p.EMP_ID = e.EMP_ID AND p.PED_FECHA_PEDIDO >= DATE_TRUNC('month', CURRENT_DATE)) as pedidos_mes, "
            "(SELECT COALESCE(SUM(PED_COSTO_TOTAL), 0) FROM PEDIDOS p2 WHERE p2.EMP_ID = e.EMP_ID AND p2.PED_ESTADO='ENTREGADO' AND p2.PED_FECHA_PEDIDO >= DATE_TRUNC('month', CURRENT_DATE)) as ingresos_mes "
            "FROM EMPRESAS e WHERE e.EMP_ESTATUS='ACTIVA' ORDER BY e.EMP_ID"
        )
        return jsonify({'success': True, 'data': rows})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


@app.route('/api/referrals/my-code', methods=['GET'])
def my_referral_code():
    """Get current user's referral code."""
    emp_id = get_emp_id()
    if not emp_id:
        return jsonify({'success': False, 'error': 'Emp ID required'}), 400
    try:
        rows = query("SELECT EMP_REFERRAL_CODE FROM EMPRESAS WHERE EMP_ID=?", [emp_id])
        if rows:
            code = rows[0].get('EMP_REFERRAL_CODE', rows[0].get('emp_referral_code', ''))
            return jsonify({'success': True, 'referral_code': code, 'referral_link': f'/register?ref={code}'})
        return jsonify({'success': False, 'error': 'Empresa no encontrada'}), 404
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


@app.route('/api/referrals/stats', methods=['GET'])
def referral_stats():
    """Get referral statistics for current user's company."""
    emp_id = get_emp_id()
    if not emp_id:
        return jsonify({'success': False, 'error': 'Emp ID required'}), 400
    try:
        # Get referral code
        code_rows = query("SELECT EMP_REFERRAL_CODE FROM EMPRESAS WHERE EMP_ID=?", [emp_id])
        code = code_rows[0].get('EMP_REFERRAL_CODE', '') if code_rows else ''

        # Get referrals made
        referrals = query(
            "SELECT r.*, e.EMP_NOMBRE as referrer_name "
            "FROM REFERRALS r "
            "LEFT JOIN EMPRESAS e ON r.REF_REFERRER_EMP_ID = e.EMP_ID "
            "WHERE r.REF_REFERRER_EMP_ID=? "
            "ORDER BY r.REF_FECHA DESC", [emp_id]
        )

        # Count total referrals and active
        total_referrals = len(referrals) if referrals else 0
        active_referrals = len([r for r in (referrals or []) if r.get('REF_STATUS') == 'ACTIVE'])

        # Check if this company was referred by someone
        referred_by_rows = query(
            "SELECT e.EMP_NOMBRE, e.EMP_REFERRAL_CODE "
            "FROM EMPRESAS e "
            "WHERE e.EMP_ID = (SELECT EMP_REFERRED_BY FROM EMPRESAS WHERE EMP_ID=?)",
            [emp_id]
        )
        referred_by = referred_by_rows[0].get('EMP_NOMBRE', 'N/A') if referred_by_rows else None

        return jsonify({
            'success': True,
            'referral_code': code,
            'referral_link': f'/register?ref={code}',
            'total_referrals': total_referrals,
            'active_referrals': active_referrals,
            'referred_by': referred_by,
            'referrals': referrals or []
        })
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


@app.route('/api/admin/legal-acceptance', methods=['GET'])
@requiere_superadmin
def admin_legal_acceptance():
    """Get all legal acceptance records for legal protection."""
    try:
        emp_id = request.args.get('emp_id')
        if emp_id:
            rows = query(
                "SELECT la.*, u.USU_NOMBRE, u.USU_EMAIL, e.EMP_NOMBRE "
                "FROM LEGAL_ACCEPTANCE la "
                "LEFT JOIN USUARIOS u ON la.USR_ID = u.USR_ID "
                "LEFT JOIN EMPRESAS e ON la.EMP_ID = e.EMP_ID "
                "WHERE la.EMP_ID=? ORDER BY la.LA_FECHA DESC", [emp_id]
            )
        else:
            rows = query(
                "SELECT la.*, u.USU_NOMBRE, u.USU_EMAIL, e.EMP_NOMBRE "
                "FROM LEGAL_ACCEPTANCE la "
                "LEFT JOIN USUARIOS u ON la.USR_ID = u.USR_ID "
                "LEFT JOIN EMPRESAS e ON la.EMP_ID = e.EMP_ID "
                "ORDER BY la.LA_FECHA DESC LIMIT 500"
            )
        return jsonify({'success': True, 'data': rows})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


@app.route('/api/legal/my-acceptance', methods=['GET'])
def my_legal_acceptance():
    """Get current user's legal acceptance records."""
    emp_id = get_emp_id()
    usr_id = request.args.get('usr_id')
    if not emp_id:
        return jsonify({'success': False, 'error': 'Emp ID required'}), 400
    try:
        if usr_id:
            rows = query(
                "SELECT * FROM LEGAL_ACCEPTANCE WHERE EMP_ID=? AND USR_ID=? ORDER BY LA_FECHA DESC",
                [emp_id, usr_id]
            )
        else:
            rows = query(
                "SELECT * FROM LEGAL_ACCEPTANCE WHERE EMP_ID=? ORDER BY LA_FECHA DESC",
                [emp_id]
            )
        return jsonify({'success': True, 'data': rows})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


@app.route('/api/legal/verify/<int:usr_id>', methods=['GET'])
def verify_legal_acceptance(usr_id):
    """Verify if a user has accepted all legal documents."""
    try:
        rows = query(
            "SELECT LA_TERMINOS, LA_PRIVACIDAD, LA_PAGOS, LA_DESLINDE, LA_SLA, LA_COOKIES, "
            "LA_FECHA, LA_IP, LA_ACCEPTED_ALL "
            "FROM LEGAL_ACCEPTANCE WHERE USR_ID=? ORDER BY LA_FECHA DESC LIMIT 1",
            [usr_id]
        )
        if rows:
            r = rows[0]
            all_accepted = all([
                r.get('LA_TERMINOS') == 'S',
                r.get('LA_PRIVACIDAD') == 'S',
                r.get('LA_PAGOS') == 'S',
                r.get('LA_DESLINDE') == 'S',
                r.get('LA_SLA') == 'S',
                r.get('LA_COOKIES') == 'S'
            ])
            return jsonify({
                'success': True,
                'accepted': all_accepted,
                'details': r
            })
        return jsonify({'success': True, 'accepted': False, 'details': None})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


# ========================================
# HEALTH CHECK
# ========================================
@app.route('/api/health', methods=['GET'])
def health():
    checks = {'database': 'UNKNOWN', 'stripe': 'NOT_CONFIGURED', 'mp': 'NOT_CONFIGURED'}

    # DB check
    try:
        start = time.time()
        query("SELECT 1")
        db_ms = round((time.time() - start) * 1000, 1)
        checks['database'] = 'OK'
        db_latency = f'{db_ms}ms'
    except Exception as e:
        checks['database'] = f'ERROR: {str(e)[:60]}'
        db_latency = 'N/A'

    # Stripe check
    if os.environ.get('STRIPE_SECRET_KEY'):
        checks['stripe'] = 'CONFIGURED'

    # MercadoPago check
    if os.environ.get('MP_ACCESS_TOKEN'):
        checks['mp'] = 'CONFIGURED'

    # DB info
    db_info = get_db_info()

    overall = 'OK' if checks['database'] == 'OK' else 'DEGRADED'
    return jsonify({
        'status': overall,
        'timestamp': datetime.now().isoformat(),
        'version': '3.0.0',
        'database': {
            'engine': db_info['type'],
            'status': checks['database'],
            'latency': db_latency,
        },
        'services': {
            'stripe': checks['stripe'],
            'mercadopago': checks['mp'],
            'rate_limit': '200/min',
        }
    })


@app.route('/api/docs', methods=['GET'])
def api_docs():
    """Serve the OpenAPI spec as JSON."""
    import yaml
    docs_path = os.path.join(os.path.dirname(__file__), 'openapi.yaml')
    if os.path.exists(docs_path):
        with open(docs_path, 'r') as f:
            spec = yaml.safe_load(f)
        return jsonify(spec)
    return jsonify({'error': 'API docs not found'}), 404


@app.route('/docs')
def swagger_ui():
    """Serve Swagger UI for API documentation."""
    return send_from_directory('web', 'swagger.html')


# ========================================
# AUTH: Login
# ========================================
LOGIN_MAX_ATTEMPTS = 3
LOGIN_LOCKOUT_MINUTES = 15
_lockout_cols_migrated = False

@app.route('/api/auth/login', methods=['POST'])
@limiter.limit("10 per minute")
def auth_login():
    global _lockout_cols_migrated
    data = request.get_json() or {}
    user = (data.get('user') or '').strip()
    passwd = data.get('pass') or ''
    emp_id_param = data.get('emp_id')

    if not user or not passwd:
        return jsonify({'success': False, 'error': 'Usuario y contrasena requeridos'})

    # Ensure lockout columns exist (run once)
    if not _lockout_cols_migrated:
        try:
            ensure_lockout_columns()
            _lockout_cols_migrated = True
        except Exception:
            pass

    plain = passwd.strip()

    try:
        sql = (
            "SELECT U.USU_ID, U.USU_USUARIO, U.USU_NOMBRE, U.USU_ROL, "
            "U.USU_EMP_ID, U.USU_PASS, E.EMP_NOMBRE, "
            "U.USU_FAILED_ATTEMPTS, U.USU_LOCKED_UNTIL "
            "FROM USUARIOS U "
            "LEFT JOIN EMPRESAS E ON U.USU_EMP_ID = E.EMP_ID "
            "WHERE UPPER(U.USU_USUARIO) = UPPER(?) AND U.USU_ACTIVO = 'S'"
        )
        params = [user]
        if emp_id_param:
            sql += " AND U.USU_EMP_ID = ?"
            params.append(emp_id_param)
        rows = query(sql, params)
    except Exception:
        try:
            sql = (
                "SELECT U.USU_ID, U.USU_USUARIO, U.USU_NOMBRE, U.USU_ROL, "
                "U.USU_EMP_ID, U.USU_PASS, E.EMP_NOMBRE "
                "FROM USUARIOS U "
                "LEFT JOIN EMPRESAS E ON U.USU_EMP_ID = E.EMP_ID "
                "WHERE UPPER(U.USU_USUARIO) = UPPER(?) AND U.USU_ACTIVO = 'S'"
            )
            params = [user]
            if emp_id_param:
                sql += " AND U.USU_EMP_ID = ?"
                params.append(emp_id_param)
            rows = query(sql, params)
        except Exception:
            return jsonify({'success': False, 'error': 'Tabla USUARIOS no existe. Ejecuta el script de setup.'})

    if not rows:
        return jsonify({'success': False, 'error': 'Usuario o contrasena incorrectos'})

    # Check account lockout
    now = datetime.utcnow()
    for row in rows:
        locked_until = row.get('USU_LOCKED_UNTIL')
        if locked_until:
            if isinstance(locked_until, str):
                try:
                    locked_until = datetime.fromisoformat(locked_until.replace('Z', '+00:00'))
                except:
                    locked_until = None
            if locked_until and locked_until > now:
                remaining = int((locked_until - now).total_seconds() / 60) + 1
                return jsonify({
                    'success': False,
                    'error': f'Cuenta bloqueada. Intenta de nuevo en {remaining} minutos'
                }), 429

    # Verifica la contrasena de cada usuario que coincide (usuarios duplicados entre tenants)
    matched = None
    for row in rows:
        db_pass = str(row.get('USU_PASS', '')).strip()
        if verify_password(plain, db_pass):
            matched = row
            break

    if not matched:
        # Increment failed attempts for all matching users
        for row in rows:
            try:
                attempts = (row.get('USU_FAILED_ATTEMPTS') or 0) + 1
                if attempts >= LOGIN_MAX_ATTEMPTS:
                    lock_until = now + timedelta(minutes=LOGIN_LOCKOUT_MINUTES)
                    execute(
                        "UPDATE USUARIOS SET USU_FAILED_ATTEMPTS=?, USU_LOCKED_UNTIL=?, USU_LAST_FAILED_AT=NOW() WHERE USU_ID=?",
                        [attempts, lock_until, row['USU_ID']]
                    )
                else:
                    execute(
                        "UPDATE USUARIOS SET USU_FAILED_ATTEMPTS=?, USU_LAST_FAILED_AT=NOW() WHERE USU_ID=?",
                        [attempts, row['USU_ID']]
                    )
            except Exception:
                pass
        remaining_attempts = LOGIN_MAX_ATTEMPTS - ((rows[0].get('USU_FAILED_ATTEMPTS') or 0) + 1)
        if remaining_attempts <= 0:
            return jsonify({
                'success': False,
                'error': f'Cuenta bloqueada por {LOGIN_LOCKOUT_MINUTES} minutos por múltiples intentos fallidos'
            }), 429
        return jsonify({
            'success': False,
            'error': f'Usuario o contrasena incorrectos. Te quedan {remaining_attempts} intentos'
        })

    # Login exitoso: reset failed attempts
    try:
        execute(
            "UPDATE USUARIOS SET USU_FAILED_ATTEMPTS=0, USU_LOCKED_UNTIL=NULL, USU_LAST_FAILED_AT=NULL WHERE USU_ID=?",
            [matched['USU_ID']]
        )
    except Exception:
        pass

    # Migracion transparente: si el hash almacenado era SHA-256 heredado, re-hashea a bcrypt.
    if is_legacy_hash(str(matched.get('USU_PASS', '')).strip()):
        try:
            execute("UPDATE USUARIOS SET USU_PASS=? WHERE USU_ID=?",
                    [hash_password(plain), matched['USU_ID']])
        except Exception:
            pass

    token = generate_token(
        matched['USU_ID'], matched['USU_EMP_ID'], matched['USU_ROL'], matched['USU_USUARIO']
    )
    refresh = generate_refresh_token(
        matched['USU_ID'], matched['USU_EMP_ID'], matched['USU_ROL'], matched['USU_USUARIO']
    )
    return jsonify({
        'success': True,
        'token': token,
        'refresh_token': refresh,
        'expires_in': 43200,
        'data': {
            'emp_id': matched['USU_EMP_ID'],
            'usuario': matched['USU_USUARIO'],
            'nombre': matched['USU_NOMBRE'],
            'rol': matched['USU_ROL'],
            'empresa': matched.get('EMP_NOMBRE', '')
        }
    })


@app.route('/api/auth/refresh', methods=['POST'])
@limiter.limit("30 per minute")
def auth_refresh():
    """Intercambia un refresh token por un nuevo access token."""
    data = request.get_json() or {}
    refresh_token = data.get('refresh_token') or ''
    if not refresh_token:
        return jsonify({'success': False, 'error': 'refresh_token requerido'}), 400
    new_token, err = refresh_access_token(refresh_token)
    if err:
        return jsonify({'success': False, 'error': err}), 401
    return jsonify({'success': True, 'token': new_token, 'expires_in': 43200})


# ========================================
# AUTH: Password Reset (Forgot Password)
# ========================================
import secrets
import string
from datetime import datetime, timedelta

def _generate_reset_code(length=6):
    """Genera un codigo numerico de 6 digitos para reset de contrasena."""
    return ''.join(secrets.choice(string.digits) for _ in range(length))

def _generate_reset_token():
    """Genera un token unico para el link de reset."""
    return secrets.token_urlsafe(32)

def _get_reset_table_sql():
    """SQL para crear la tabla de tokens si no existe."""
    if USE_POSTGRES:
        return """
            CREATE TABLE IF NOT EXISTS PASSWORD_RESET_TOKENS (
                PRT_ID SERIAL PRIMARY KEY,
                EMP_ID INTEGER NOT NULL,
                USU_ID INTEGER NOT NULL,
                PRT_TOKEN TEXT NOT NULL,
                PRT_CODE TEXT NOT NULL,
                PRT_EXPIRES_AT TIMESTAMP NOT NULL,
                PRT_USED TEXT DEFAULT 'N',
                PRT_CREATED_AT TIMESTAMP DEFAULT NOW(),
                PRT_IP_ADDRESS TEXT,
                UNIQUE(PRT_TOKEN)
            )
        """
    else:
        return """
            CREATE TABLE IF NOT EXISTS PASSWORD_RESET_TOKENS (
                PRT_ID INTEGER PRIMARY KEY AUTOINCREMENT,
                EMP_ID INTEGER NOT NULL,
                USU_ID INTEGER NOT NULL,
                PRT_TOKEN TEXT NOT NULL UNIQUE,
                PRT_CODE TEXT NOT NULL,
                PRT_EXPIRES_AT TIMESTAMP NOT NULL,
                PRT_USED TEXT DEFAULT 'N',
                PRT_CREATED_AT TIMESTAMP DEFAULT (datetime('now')),
                PRT_IP_ADDRESS TEXT
            )
        """


@app.route('/api/auth/forgot-password', methods=['POST'])
@limiter.limit("5 per minute")
def forgot_password():
    """
    Solicita reset de contrasena.
    Envía un codigo de 6 digitos al email del usuario.
    """
    data = request.get_json() or {}
    email = (data.get('email') or '').strip().lower()
    emp_id_param = data.get('emp_id')

    if not email:
        return jsonify({'success': False, 'error': 'Email requerido'}), 400

    try:
        execute(_get_reset_table_sql())
    except Exception:
        pass

    try:
        sql = (
            "SELECT U.USU_ID, U.USU_EMP_ID, U.USU_USUARIO, U.USU_NOMBRE, U.USU_EMAIL "
            "FROM USUARIOS U "
            "WHERE UPPER(U.USU_EMAIL) = UPPER(?) AND U.USU_ACTIVO = 'S'"
        )
        params = [email]
        if emp_id_param:
            sql += " AND U.USU_EMP_ID = ?"
            params.append(emp_id_param)
        rows = query(sql, params)
    except Exception as e:
        return jsonify({'success': False, 'error': 'Error consultando usuario'}), 500

    if not rows:
        return jsonify({
            'success': True,
            'message': 'Si el email existe, recibirás un código de verificación'
        })

    user = rows[0]
    reset_code = _generate_reset_code()
    reset_token = _generate_reset_token()
    expires_at = datetime.utcnow() + timedelta(minutes=15)
    ip_address = request.remote_addr or ''

    try:
        execute(
            "INSERT INTO PASSWORD_RESET_TOKENS (EMP_ID, USU_ID, PRT_TOKEN, PRT_CODE, PRT_EXPIRES_AT, PRT_IP_ADDRESS) "
            "VALUES (?, ?, ?, ?, ?, ?)",
            [user['USU_EMP_ID'], user['USU_ID'], reset_token, reset_code, expires_at, ip_address]
        )
    except Exception as e:
        return jsonify({'success': False, 'error': 'Error generando código'}), 500

    html_body = f"""
    <div style="font-family: Arial, sans-serif; max-width: 500px; margin: 0 auto;">
        <h2 style="color: #1a1a2e;">Recuperación de Contraseña</h2>
        <p>Hola <strong>{user.get('USU_NOMBRE', 'Usuario')}</strong>,</p>
        <p>Recibimos una solicitud para restablecer tu contraseña.</p>
        <div style="background: #f8f9fa; padding: 20px; border-radius: 8px; text-align: center; margin: 20px 0;">
            <p style="margin: 0; color: #666;">Tu código de verificación es:</p>
            <h1 style="margin: 10px 0; color: #1a1a2e; letter-spacing: 5px;">{reset_code}</h1>
            <p style="margin: 0; color: #999; font-size: 12px;">Expira en 15 minutos</p>
        </div>
        <p style="color: #666; font-size: 14px;">Si no solicitaste este cambio, ignora este mensaje.</p>
        <hr style="border: none; border-top: 1px solid #eee; margin: 20px 0;">
        <p style="color: #999; font-size: 12px;">Last Mile Delivery Platform</p>
    </div>
    """

    try:
        from notification_service import email_service
        email_service.send(
            to=email,
            subject='Código de Verificación - Recuperación de Contraseña',
            html_body=html_body
        )
    except Exception:
        pass

    return jsonify({
        'success': True,
        'message': 'Si el email existe, recibirás un código de verificación',
        'debug_code': reset_code if os.environ.get('FLASK_ENV') == 'development' else None
    })


@app.route('/api/auth/verify-reset-code', methods=['POST'])
@limiter.limit("10 per minute")
def verify_reset_code():
    """
    Verifica el código de reset de contraseña.
    Devuelve un token temporal para usar en reset-password.
    """
    data = request.get_json() or {}
    email = (data.get('email') or '').strip().lower()
    code = (data.get('code') or '').strip()

    if not email or not code:
        return jsonify({'success': False, 'error': 'Email y código requeridos'}), 400

    try:
        rows = query(
            "SELECT PRT.*, U.USU_USUARIO, U.USU_NOMBRE "
            "FROM PASSWORD_RESET_TOKENS PRT "
            "JOIN USUARIOS U ON PRT.USU_ID = U.USU_ID "
            "WHERE UPPER(U.USU_EMAIL) = UPPER(?) AND PRT.PRT_CODE = ? AND PRT.PRT_USED = 'N' "
            "AND PRT.PRT_EXPIRES_AT > NOW() "
            "ORDER BY PRT.PRT_ID DESC LIMIT 1",
            [email, code]
        )
    except Exception as e:
        return jsonify({'success': False, 'error': 'Error verificando código'}), 500

    if not rows:
        return jsonify({'success': False, 'error': 'Código inválido o expirado'}), 400

    token_record = rows[0]

    try:
        execute(
            "UPDATE PASSWORD_RESET_TOKENS SET PRT_USED = 'V' WHERE PRT_ID = ?",
            [token_record['PRT_ID']]
        )
    except Exception:
        pass

    return jsonify({
        'success': True,
        'message': 'Código verificado correctamente',
        'reset_token': token_record['PRT_TOKEN'],
        'usuario': token_record.get('USU_USUARIO', ''),
        'expires_in': 900
    })


@app.route('/api/auth/reset-password', methods=['POST'])
@limiter.limit("5 per minute")
def reset_password():
    """
    Restablece la contraseña usando el token de reset.
    """
    data = request.get_json() or {}
    reset_token = (data.get('reset_token') or '').strip()
    new_password = data.get('new_password') or ''

    if not reset_token or not new_password:
        return jsonify({'success': False, 'error': 'Token y nueva contraseña requeridos'}), 400

    pwd_ok, pwd_err = validate_password_strength(new_password)
    if not pwd_ok:
        return jsonify({'success': False, 'error': pwd_err}), 400

    try:
        rows = query(
            "SELECT PRT.* FROM PASSWORD_RESET_TOKENS PRT "
            "WHERE PRT.PRT_TOKEN = ? AND PRT.PRT_USED = 'V' AND PRT.PRT_EXPIRES_AT > NOW()",
            [reset_token]
        )
    except Exception as e:
        return jsonify({'success': False, 'error': 'Error verificando token'}), 500

    if not rows:
        return jsonify({'success': False, 'error': 'Token inválido, expirado o ya utilizado'}), 400

    token_record = rows[0]
    hashed_password = hash_password(new_password)

    try:
        execute(
            "UPDATE USUARIOS SET USU_PASS = ?, USU_UPDATED = NOW() WHERE USU_ID = ?",
            [hashed_password, token_record['USU_ID']]
        )
    except Exception as e:
        return jsonify({'success': False, 'error': 'Error actualizando contraseña'}), 500

    try:
        execute(
            "UPDATE PASSWORD_RESET_TOKENS SET PRT_USED = 'Y' WHERE PRT_ID = ?",
            [token_record['PRT_ID']]
        )
    except Exception:
        pass

    return jsonify({
        'success': True,
        'message': 'Contraseña actualizada correctamente'
    })


# ========================================
# SETUP: Crear tabla USUARIOS (temporal)
# ========================================
@app.route('/api/setup/usuarios', methods=['POST'])
@limiter.limit("2 per hour")
@requiere_superadmin
def setup_usuarios():
    """Crea la tabla USUARIOS y carga datos de prueba."""
    try:
        try:
            execute("DROP TABLE IF EXISTS USUARIOS CASCADE")
        except:
            pass

        if USE_POSTGRES:
            execute("""
                CREATE TABLE USUARIOS (
                    USU_ID SERIAL PRIMARY KEY,
                    USU_EMP_ID INTEGER NOT NULL,
                    USU_USUARIO TEXT NOT NULL,
                    USU_PASS TEXT NOT NULL,
                    USU_NOMBRE TEXT NOT NULL,
                    USU_EMAIL TEXT,
                    USU_TELEFONO TEXT,
                    USU_ROL TEXT NOT NULL DEFAULT 'operacion',
                    USU_ACTIVO TEXT DEFAULT 'S',
                    USU_CREATED TIMESTAMP DEFAULT NOW(),
                    USU_UPDATED TIMESTAMP DEFAULT NOW()
                )
            """)
        else:
            execute("""
                CREATE TABLE USUARIOS (
                    USU_ID INTEGER PRIMARY KEY AUTOINCREMENT,
                    USU_EMP_ID INTEGER NOT NULL,
                    USU_USUARIO TEXT NOT NULL,
                    USU_PASS TEXT NOT NULL,
                    USU_NOMBRE TEXT NOT NULL,
                    USU_EMAIL TEXT,
                    USU_TELEFONO TEXT,
                    USU_ROL TEXT NOT NULL DEFAULT 'operacion',
                    USU_ACTIVO TEXT DEFAULT 'S',
                    USU_CREATED TEXT DEFAULT (datetime('now')),
                    USU_UPDATED TEXT DEFAULT (datetime('now'))
                )
            """)

        try:
            execute("CREATE INDEX IX_USU_USER ON USUARIOS(USU_USUARIO)")
            execute("CREATE INDEX IX_USU_EMP ON USUARIOS(USU_EMP_ID)")
        except:
            pass

        users = [
            (1, 'admin', 'admin123', 'Administrador', 'admin@delivery.mx', 'admin'),
            (1, 'operador', 'oper123', 'Operador General', 'ops@delivery.mx', 'operacion'),
            (1, 'chofer1', 'chof123', 'Carlos Rodriguez', 'carlos@delivery.mx', 'chofer'),
            (1, 'chofer2', 'chof123', 'Maria Lopez', 'maria@delivery.mx', 'chofer'),
            (1, 'cliente1', 'clie123', 'Juan Perez Store', 'juan@perez.mx', 'cliente'),
            (1, 'cliente2', 'clie123', 'Ana Garcia Shop', 'ana@garcia.mx', 'cliente'),
            (2, 'admin2', 'admin123', 'Admin Transporte Rapido', 'admin@transporte.mx', 'admin'),
            (2, 'ops2', 'oper123', 'Operador TR', 'ops@transporte.mx', 'operacion'),
            (2, 'chofer3', 'chof123', 'Pedro Sanchez', 'pedro@transporte.mx', 'chofer'),
            (2, 'cliente3', 'clie123', 'Tienda Rodriguez', 'tienda@rodriguez.mx', 'cliente'),
            (3, 'admin3', 'admin123', 'Admin Logistica Integral', 'admin@logistica.mx', 'admin'),
            (3, 'ops3', 'oper123', 'Operador LI', 'ops@logistica.mx', 'operacion'),
            (3, 'chofer4', 'chof123', 'Roberto Diaz', 'roberto@logistica.mx', 'chofer'),
            (3, 'cliente4', 'clie123', 'Comercial Torres', 'torres@comercial.mx', 'cliente'),
        ]

        for u in users:
            hashed_pass = hash_password(u[2].strip())
            execute(
                "INSERT INTO USUARIOS (USU_EMP_ID, USU_USUARIO, USU_PASS, USU_NOMBRE, USU_EMAIL, USU_ROL) VALUES (?,?,?,?,?,?)",
                [u[0], u[1], hashed_pass, u[3], u[4], u[5]]
            )

        return jsonify({'success': True, 'message': f'Tabla USUARIOS creada con {len(users)} usuarios'})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})


# ========================================
# SETUP: Crear tablas ZONAS y ZONA_TARIFAS
# ========================================
@app.route('/api/setup/zonas', methods=['POST'])
@limiter.limit("2 per hour")
@requiere_superadmin
def setup_zonas():
    """Crea las tablas de zonas y tarifas."""
    try:
        try: execute("DROP TABLE ZONA_TARIFAS")
        except: pass
        try: execute("DROP TABLE ZONAS")
        except: pass

        execute("""
            CREATE TABLE ZONAS (
                ZON_ID INTEGER PRIMARY KEY AUTOINCREMENT,
                ZON_EMP_ID INTEGER NOT NULL,
                ZON_NOMBRE TEXT NOT NULL,
                ZON_DESCRIPCION TEXT,
                ZON_COLOR TEXT DEFAULT '#6366f1',
                ZON_RADIO_KM REAL DEFAULT 5.0,
                ZON_CENTRO_LAT REAL,
                ZON_CENTRO_LNG REAL,
                ZON_ACTIVO TEXT DEFAULT 'S',
                ZON_CREATED TEXT DEFAULT (datetime('now')),
                ZON_UPDATED TEXT DEFAULT (datetime('now'))
            )
        """)

        execute("""
            CREATE TABLE ZONA_TARIFAS (
                ZTA_ID INTEGER PRIMARY KEY AUTOINCREMENT,
                ZTA_ZON_ID INTEGER NOT NULL,
                ZTA_EMP_ID INTEGER NOT NULL,
                ZTA_SERVICIO TEXT DEFAULT 'ESTANDAR',
                ZTA_MONTO_BASE REAL DEFAULT 0,
                ZTA_MONTO_POR_KG REAL DEFAULT 0,
                ZTA_MONTO_POR_KM REAL DEFAULT 0,
                ZTA_MONTO_POR_M3 REAL DEFAULT 0,
                ZTA_PESO_MIN_KG REAL DEFAULT 0.5,
                ZTA_PESO_MAX_KG REAL DEFAULT 30.0,
                ZTA_DISTANCIA_MAX_KM REAL DEFAULT 50.0,
                ZTA_MONTO_MINIMO REAL DEFAULT 35.0,
                ZTA_SEGURO_PCT REAL DEFAULT 0,
                ZTA_ACTIVO TEXT DEFAULT 'S',
                ZTA_CREATED TEXT DEFAULT (datetime('now'))
            )
        """)

        try: execute("CREATE INDEX IX_ZON_EMP ON ZONAS(ZON_EMP_ID)")
        except: pass
        try: execute("CREATE INDEX IX_ZTA_EMP ON ZONA_TARIFAS(ZTA_EMP_ID)")
        except: pass
        try: execute("CREATE INDEX IX_ZTA_ZON ON ZONA_TARIFAS(ZTA_ZON_ID)")
        except: pass

        zones = [
            (1, 'Centro Historico', 'Zona centro historico de CDMX', '#6366f1', 3.0, 19.4326, -99.1332),
            (1, 'Polanco / Reforma', 'Zona premium Polanco y Paseo Reforma', '#10b981', 4.0, 19.4350, -99.1950),
            (1, 'Roma / Condesa', 'Zonas populares Roma Norte y Condesa', '#f59e0b', 3.5, 19.4126, -99.1600),
            (1, 'Coyoacan / San Angel', 'Zona sur artistica y residencial', '#8b5cf6', 5.0, 19.3500, -99.1550),
            (1, 'Santa Fe / Cuajimalpa', 'Zona corporativa y comercial', '#ef4444', 6.0, 19.3600, -99.2700),
            (1, 'Del Valle / Narvarte', 'Zona residencial sur', '#06b6d4', 3.0, 19.3900, -99.1700),
            (1, 'Escandon / Tacubaya', 'Zona mixta poniente', '#ec4899', 2.5, 19.4050, -99.2000),
        ]

        for z in zones:
            execute("INSERT INTO ZONAS (ZON_EMP_ID, ZON_NOMBRE, ZON_DESCRIPCION, ZON_COLOR, ZON_RADIO_KM, ZON_CENTRO_LAT, ZON_CENTRO_LNG) VALUES (?,?,?,?,?,?,?)", list(z))

        tariffs = [
            (1, 1, 'EXPRESS', 45.00, 8.00, 5.00, 0, 0.5, 15.0, 20.0, 45.00, 2.0),
            (1, 1, 'ESTANDAR', 35.00, 5.00, 3.50, 0, 0.5, 30.0, 50.0, 35.00, 0),
            (1, 1, 'ECONOMICO', 25.00, 3.00, 2.00, 0, 1.0, 30.0, 50.0, 25.00, 0),
            (2, 1, 'EXPRESS', 55.00, 10.00, 6.00, 0, 0.5, 15.0, 25.0, 55.00, 3.0),
            (2, 1, 'ESTANDAR', 45.00, 7.00, 4.00, 0, 0.5, 30.0, 50.0, 45.00, 0),
            (2, 1, 'ECONOMICO', 35.00, 4.00, 2.50, 0, 1.0, 30.0, 50.0, 35.00, 0),
        ]

        for t in tariffs:
            execute("INSERT INTO ZONA_TARIFAS (ZTA_ZON_ID, ZTA_EMP_ID, ZTA_SERVICIO, ZTA_MONTO_BASE, ZTA_MONTO_POR_KG, ZTA_MONTO_POR_KM, ZTA_MONTO_POR_M3, ZTA_PESO_MIN_KG, ZTA_PESO_MAX_KG, ZTA_DISTANCIA_MAX_KM, ZTA_MONTO_MINIMO, ZTA_SEGURO_PCT) VALUES (?,?,?,?,?,?,?,?,?,?,?,?)", list(t))

        return jsonify({'success': True, 'message': f'Zonas creadas: {len(zones)} zonas, {len(tariffs)} tarifas'})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})


# ========================================
# CRUD: ZONAS DE COBERTURA
# ========================================
@app.route('/api/zonas', methods=['GET'])
def get_zonas():
    emp_id = get_emp_id()
    zonas = query("SELECT * FROM ZONAS WHERE ZON_EMP_ID = ? AND ZON_ACTIVO = 'S' ORDER BY ZON_NOMBRE", [emp_id])
    for z in zonas:
        z['tarifas'] = query("SELECT * FROM ZONA_TARIFAS WHERE ZTA_ZON_ID = ? AND ZTA_EMP_ID = ? AND ZTA_ACTIVO = 'S' ORDER BY ZTA_MONTO_BASE", [z['ZON_ID'], emp_id])
    return jsonify({'success': True, 'data': zonas})


@app.route('/api/zonas', methods=['POST'])
def create_zona():
    emp_id = get_emp_id()
    data = request.get_json() or {}
    nombre = data.get('nombre', '').strip()
    if not nombre:
        return jsonify({'success': False, 'error': 'Nombre de zona requerido'})

    try:
        execute("INSERT INTO ZONAS (ZON_EMP_ID, ZON_NOMBRE, ZON_DESCRIPCION, ZON_COLOR, ZON_RADIO_KM, ZON_CENTRO_LAT, ZON_CENTRO_LNG) VALUES (?,?,?,?,?,?,?)",
                [emp_id, nombre, data.get('descripcion', ''), data.get('color', '#6366f1'),
                 data.get('radio_km', 5.0), data.get('centro_lat', 19.4326), data.get('centro_lng', -99.1332)])

        rows = query("SELECT ZON_ID FROM ZONAS WHERE ZON_EMP_ID = ? AND ZON_NOMBRE = ? ORDER BY ZON_ID DESC LIMIT 1", [emp_id, nombre])
        zon_id = rows[0]['ZON_ID'] if rows else None

        for t in data.get('tarifas', []):
            execute("INSERT INTO ZONA_TARIFAS (ZTA_ZON_ID, ZTA_EMP_ID, ZTA_SERVICIO, ZTA_MONTO_BASE, ZTA_MONTO_POR_KG, ZTA_MONTO_POR_KM, ZTA_MONTO_POR_M3, ZTA_PESO_MIN_KG, ZTA_PESO_MAX_KG, ZTA_DISTANCIA_MAX_KM, ZTA_MONTO_MINIMO, ZTA_SEGURO_PCT) VALUES (?,?,?,?,?,?,?,?,?,?,?,?)",
                    [zon_id, emp_id, t.get('servicio', 'ESTANDAR'),
                     t.get('monto_base', 0), t.get('monto_por_kg', 0), t.get('monto_por_km', 0),
                     t.get('monto_por_m3', 0), t.get('peso_min_kg', 0.5), t.get('peso_max_kg', 30.0),
                     t.get('distancia_max_km', 50.0), t.get('monto_minimo', 35.0), t.get('seguro_pct', 0)])

        return jsonify({'success': True, 'message': f'Zona "{nombre}" creada', 'zon_id': zon_id})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})


@app.route('/api/zonas/<int:zon_id>', methods=['GET'])
def get_zona(zon_id):
    emp_id = get_emp_id()
    rows = query("SELECT * FROM ZONAS WHERE ZON_ID = ? AND ZON_EMP_ID = ?", [zon_id, emp_id])
    if not rows:
        return jsonify({'success': False, 'error': 'Zona no encontrada'}), 404
    zona = rows[0]
    zona['tarifas'] = query("SELECT * FROM ZONA_TARIFAS WHERE ZTA_ZON_ID = ? AND ZTA_EMP_ID = ? ORDER BY ZTA_SERVICIO", [zon_id, emp_id])
    return jsonify({'success': True, 'data': zona})


@app.route('/api/zonas/<int:zon_id>', methods=['PUT'])
def update_zona(zon_id):
    emp_id = get_emp_id()
    data = request.get_json() or {}
    try:
        execute("UPDATE ZONAS SET ZON_NOMBRE=?, ZON_DESCRIPCION=?, ZON_COLOR=?, ZON_RADIO_KM=?, ZON_CENTRO_LAT=?, ZON_CENTRO_LNG=?, ZON_UPDATED=datetime('now') WHERE ZON_ID=? AND ZON_EMP_ID=?",
                [data.get('nombre', ''), data.get('descripcion', ''), data.get('color', '#6366f1'),
                 data.get('radio_km', 5.0), data.get('centro_lat', 19.4326), data.get('centro_lng', -99.1332),
                 zon_id, emp_id])

        for t in data.get('tarifas', []):
            zta_id = t.get('id')
            if zta_id:
                execute("UPDATE ZONA_TARIFAS SET ZTA_SERVICIO=?, ZTA_MONTO_BASE=?, ZTA_MONTO_POR_KG=?, ZTA_MONTO_POR_KM=?, ZTA_MONTO_POR_M3=?, ZTA_PESO_MIN_KG=?, ZTA_PESO_MAX_KG=?, ZTA_DISTANCIA_MAX_KM=?, ZTA_MONTO_MINIMO=?, ZTA_SEGURO_PCT=? WHERE ZTA_ID=? AND ZTA_EMP_ID=?",
                        [t.get('servicio', 'ESTANDAR'), t.get('monto_base', 0), t.get('monto_por_kg', 0),
                         t.get('monto_por_km', 0), t.get('monto_por_m3', 0), t.get('peso_min_kg', 0.5),
                         t.get('peso_max_kg', 30.0), t.get('distancia_max_km', 50.0), t.get('monto_minimo', 35.0),
                         t.get('seguro_pct', 0), zta_id, emp_id])
            else:
                execute("INSERT INTO ZONA_TARIFAS (ZTA_ZON_ID, ZTA_EMP_ID, ZTA_SERVICIO, ZTA_MONTO_BASE, ZTA_MONTO_POR_KG, ZTA_MONTO_POR_KM, ZTA_MONTO_POR_M3, ZTA_PESO_MIN_KG, ZTA_PESO_MAX_KG, ZTA_DISTANCIA_MAX_KM, ZTA_MONTO_MINIMO, ZTA_SEGURO_PCT) VALUES (?,?,?,?,?,?,?,?,?,?,?,?)",
                        [zon_id, emp_id, t.get('servicio', 'ESTANDAR'), t.get('monto_base', 0), t.get('monto_por_kg', 0),
                         t.get('monto_por_km', 0), t.get('monto_por_m3', 0), t.get('peso_min_kg', 0.5),
                         t.get('peso_max_kg', 30.0), t.get('distancia_max_km', 50.0), t.get('monto_minimo', 35.0),
                         t.get('seguro_pct', 0)])

        return jsonify({'success': True, 'message': 'Zona actualizada'})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})


@app.route('/api/zonas/<int:zon_id>', methods=['DELETE'])
def delete_zona(zon_id):
    emp_id = get_emp_id()
    try:
        execute("UPDATE ZONAS SET ZON_ACTIVO='N', ZON_UPDATED=datetime('now') WHERE ZON_ID=? AND ZON_EMP_ID=?", [zon_id, emp_id])
        execute("UPDATE ZONA_TARIFAS SET ZTA_ACTIVO='N' WHERE ZTA_ZON_ID=? AND ZTA_EMP_ID=?", [zon_id, emp_id])
        log_audit('zona_deleted', f'zon_id={zon_id}')
        return jsonify({'success': True, 'message': 'Zona eliminada'})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})


@app.route('/api/zonas/cotizar', methods=['POST'])
def cotizar_envio():
    emp_id = get_emp_id()
    data = request.get_json() or {}
    zon_id = data.get('zona_id')
    servicio = data.get('servicio', 'ESTANDAR')
    peso_kg = float(data.get('peso_kg', 1.0))
    largo_cm = float(data.get('largo_cm', 0))
    ancho_cm = float(data.get('ancho_cm', 0))
    alto_cm = float(data.get('alto_cm', 0))
    distancia_km = float(data.get('distancia_km', 0))
    valor_declarado = float(data.get('valor_declarado', 0))

    if not zon_id:
        return jsonify({'success': False, 'error': 'zona_id requerido'})

    rows = query("SELECT * FROM ZONA_TARIFAS WHERE ZTA_ZON_ID=? AND ZTA_EMP_ID=? AND ZTA_SERVICIO=? AND ZTA_ACTIVO='S'",
                 [zon_id, emp_id, servicio])
    if not rows:
        return jsonify({'success': False, 'error': f'No hay tarifa para servicio {servicio} en esta zona'})

    t = rows[0]
    peso_vol = (largo_cm * ancho_cm * alto_cm) / 5000.0 if all([largo_cm, ancho_cm, alto_cm]) else 0
    peso_cobrar = max(peso_kg, peso_vol)

    monto_base = float(t.get('ZTA_MONTO_BASE', 0))
    costo_kg = peso_cobrar * float(t.get('ZTA_MONTO_POR_KG', 0))
    costo_km = distancia_km * float(t.get('ZTA_MONTO_POR_KM', 0))
    costo_vol = 0
    if peso_vol > peso_kg:
        m3 = (largo_cm * ancho_cm * alto_cm) / 1000000.0
        costo_vol = m3 * float(t.get('ZTA_MONTO_POR_M3', 0))

    subtotal = monto_base + costo_kg + costo_km + costo_vol
    seguro = valor_declarado * float(t.get('ZTA_SEGURO_PCT', 0)) / 100.0 if valor_declarado > 0 else 0
    total = subtotal + seguro
    monto_min = float(t.get('ZTA_MONTO_MINIMO', 0))
    if total < monto_min:
        total = monto_min

    return jsonify({
        'success': True,
        'data': {
            'peso_real_kg': peso_kg,
            'peso_volumetrico_kg': round(peso_vol, 2),
            'peso_cobrar_kg': round(peso_cobrar, 2),
            'monto_base': monto_base,
            'costo_peso': round(costo_kg, 2),
            'costo_distancia': round(costo_km, 2),
            'costo_volumen': round(costo_vol, 2),
            'seguro': round(seguro, 2),
            'subtotal': round(subtotal, 2),
            'monto_minimo': monto_min,
            'total': round(max(total, monto_min), 2)
        }
    })


# ========================================
# MODULO: EMPRESAS
# ========================================
@app.route('/api/empresas', methods=['GET'])
def get_empresas():
    return jsonify({'success': True, 'data': query('SELECT * FROM EMPRESAS ORDER BY EMP_ID')})


@app.route('/api/empresas/<int:emp_id>', methods=['GET'])
def get_empresa(emp_id):
    data = query('SELECT * FROM EMPRESAS WHERE EMP_ID = ?', [emp_id])
    return jsonify({'success': True, 'data': data[0] if data else None})


# ========================================
# MODULO: DASHBOARD
# ========================================
@app.route('/api/dashboard/<int:emp_id>', methods=['GET'])
def get_dashboard(emp_id):
    data = query('SELECT * FROM V_DASHBOARD_RESUMEN WHERE EMP_ID = ?', [emp_id])
    return jsonify({'success': True, 'data': data[0] if data else {}})


@app.route('/api/dashboard/<int:emp_id>/charts', methods=['GET'])
def get_dashboard_charts(emp_id):
    """Get real chart data for dashboard."""
    result = {'pedidos_semana': [], 'ingresos_semana': [], 'estados_pie': {}, 'top_choferes': []}

    # Pedidos by day of week (last 7 days)
    try:
        rows = query(
            "SELECT PED_FECHA_PEDIDO::date as dia, COUNT(*) as total "
            "FROM PEDIDOS WHERE EMP_ID=? AND PED_FECHA_PEDIDO >= CURRENT_DATE - INTERVAL '7 days' "
            "GROUP BY dia ORDER BY dia",
            [emp_id]
        )
        result['pedidos_semana'] = [{'dia': str(r.get('DIA', '')), 'total': r.get('TOTAL', 0)} for r in (rows or [])]
    except Exception:
        pass

    # Ingresos by day (last 7 days)
    try:
        rows = query(
            "SELECT PED_FECHA_PEDIDO::date as dia, SUM(PED_COSTO_TOTAL) as total "
            "FROM PEDIDOS WHERE EMP_ID=? AND PED_FECHA_PEDIDO >= CURRENT_DATE - INTERVAL '7 days' "
            "AND PED_ESTADO='ENTREGADO' "
            "GROUP BY dia ORDER BY dia",
            [emp_id]
        )
        result['ingresos_semana'] = [{'dia': str(r.get('DIA', '')), 'total': float(r.get('TOTAL', 0) or 0)} for r in (rows or [])]
    except Exception:
        pass

    # Order status distribution
    try:
        rows = query(
            "SELECT PED_ESTADO, COUNT(*) as total FROM PEDIDOS WHERE EMP_ID=? "
            "GROUP BY PED_ESTADO",
            [emp_id]
        )
        result['estados_pie'] = {r.get('PED_ESTADO', ''): r.get('TOTAL', 0) for r in (rows or [])}
    except Exception:
        pass

    # Top choferes by deliveries
    try:
        rows = query(
            "SELECT c.CHO_NOMBRE, c.CHO_APELLIDO, COUNT(p.PED_ID) as entregas "
            "FROM CHOFERES c LEFT JOIN PEDIDOS p ON c.CHO_ID = p.CHO_ID AND p.PED_ESTADO = 'ENTREGADO' "
            "WHERE c.EMP_ID=? GROUP BY c.CHO_ID, c.CHO_NOMBRE, c.CHO_APELLIDO "
            "ORDER BY entregas DESC LIMIT 5",
            [emp_id]
        )
        result['top_choferes'] = [
            {'nombre': f"{r.get('CHO_NOMBRE', '') or ''} {r.get('CHO_APELLIDO', '') or ''}".strip(), 'entregas': r.get('ENTREGAS', 0)}
            for r in (rows or [])
        ]
    except Exception:
        pass

    return jsonify({'success': True, 'data': result})


# ========================================
# MODULO: PEDIDOS
# ========================================
@app.route('/api/pedidos', methods=['GET'])
def get_pedidos():
    emp_id = get_emp_id()
    estado = request.args.get('estado')
    limite = request.args.get('limite', '100')
    try:
        limite_int = min(int(limite), 500)
    except (ValueError, TypeError):
        limite_int = 100

    sql = 'SELECT * FROM V_PEDIDOS_COMPLETO WHERE EMP_ID = ?'
    params = [emp_id]
    if estado:
        sql += ' AND PED_ESTADO = ?'
        params.append(estado)
    sql += f' ORDER BY PED_FECHA_PEDIDO DESC LIMIT {limite_int}'

    data = query(sql, params)
    return jsonify({'success': True, 'data': data, 'total': len(data)})


@app.route('/api/pedidos/<int:ped_id>', methods=['GET'])
def get_pedido(ped_id):
    emp_id = get_emp_id()
    data = query('SELECT * FROM V_PEDIDOS_COMPLETO WHERE PED_ID = ? AND EMP_ID = ?', [ped_id, emp_id])
    return jsonify({'success': True, 'data': data[0] if data else None})


@app.route('/api/pedidos', methods=['POST'])
def create_pedido():
    emp_id = get_emp_id()
    p = request.json
    if not p:
        return jsonify({'success': False, 'error': 'Datos requeridos'}), 400
    execute(
        '''INSERT INTO PEDIDOS (EMP_ID, PED_NUMERO, CLI_ID, PED_CLIENTE_NOMBRE,
           PED_CLIENTE_TELEFONO, PED_DESTINO_DIR, PED_DESTINO_COL, PED_DESTINO_CIUDAD,
           PED_PESO_KG, PED_BULTOS, PED_COSTO_TOTAL, PED_FORMA_PAGO, PED_ESTADO, PED_PRIORIDAD)
           VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 'PENDIENTE', ?)''',
        [emp_id, p.get('pedNumero'), p.get('cliId'), p.get('clienteNombre'),
         p.get('clienteTelefono'), p.get('destinoDir'), p.get('destinoCol'),
         p.get('destinoCiudad'), p.get('pesoKg', 0), p.get('bultos', 1),
         p.get('costoTotal', 0), p.get('formaPago', 'EFECTIVO'), p.get('prioridad', 'NORMAL')]
    )
    # Get the new pedido ID
    try:
        last = query("SELECT MAX(PED_ID) as id FROM PEDIDOS WHERE EMP_ID=?", [emp_id])
        new_id = last[0]['id'] if last else None
        # Send notification
        try:
            if notification_service:
                notification_service.send('pedido_creado', new_id, emp_id,
                                         cli_id=p.get('cliId'),
                                         extra={'destino': p.get('destinoDir', '')})
        except Exception:
            pass
    except Exception:
        pass
    return jsonify({'success': True, 'message': 'Pedido creado'})


@app.route('/api/pedidos/<int:ped_id>/asignar', methods=['POST'])
def asignar_pedido(ped_id):
    emp_id = get_emp_id()
    data = request.json or {}
    cho_id = data.get('cho_id')
    veh_id = data.get('veh_id')
    notas = data.get('notas', '')
    try:
        updates = ["CHO_ID=?"]
        params = [cho_id]
        if veh_id:
            updates.append("VEH_ID=?")
            params.append(veh_id)
        if cho_id:
            ch = query("SELECT CHO_NOMBRE, CHO_APELLIDO FROM CHOFERES WHERE CHO_ID=? AND EMP_ID=?", [cho_id, emp_id])
            if ch:
                nombre = (ch[0].get('CHO_NOMBRE', '') or '') + ' ' + (ch[0].get('CHO_APELLIDO', '') or '')
                updates.append("CHOFER_ASIGNADO=?")
                params.append(nombre.strip())
        params.extend([ped_id, emp_id])
        execute(f"UPDATE PEDIDOS SET {', '.join(updates)} WHERE PED_ID=? AND EMP_ID=?", params)
        execute("INSERT INTO PEDIDO_HISTORIAL (PED_ID, HIS_ESTADO, HIS_USUARIO, HIS_OBSERVACIONES) VALUES (?, 'ASIGNADO', ?, ?)",
                [ped_id, data.get('usuario', 'SYSTEM'), notas])
        return jsonify({'success': True, 'message': 'Chofer asignado al pedido'})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


@app.route('/api/pedidos/<int:ped_id>/estado', methods=['PUT', 'POST'])
def update_estado_pedido(ped_id):
    emp_id = get_emp_id()
    data = request.json or {}
    estado = data.get('estado')
    usuario = data.get('usuario', 'SYSTEM')

    execute('UPDATE PEDIDOS SET PED_ESTADO = ? WHERE PED_ID = ? AND EMP_ID = ?', [estado, ped_id, emp_id])
    execute('INSERT INTO PEDIDO_HISTORIAL (PED_ID, HIS_ESTADO, HIS_USUARIO) VALUES (?, ?, ?)', [ped_id, estado, usuario])

    # Send notification based on status change
    try:
        # Get chofer and client info
        pedido = query("SELECT CHO_ID, CLI_ID, PED_CLIENTE_NOMBRE, PED_DESTINO_DIR FROM PEDIDOS WHERE PED_ID=?", [ped_id])
        chofer_id = pedido[0].get('CHO_ID') if pedido else None
        cli_id = pedido[0].get('CLI_ID') if pedido else None

        if estado == 'EN_RUTA':
            ch = query("SELECT CHO_NOMBRE FROM CHOFERES WHERE CHO_ID=?", [chofer_id]) if chofer_id else None
            chofer_name = ch[0].get('CHO_NOMBRE', 'Chofer') if ch else 'Chofer'
            # Notify client that order is on the way
            if notification_service:
                notification_service.send('pedido_en_ruta', ped_id, emp_id,
                                         cli_id=cli_id,
                                         extra={'chofer': chofer_name,
                                                'destino': pedido[0].get('PED_DESTINO_DIR', '') if pedido else ''})
                # Notify chofer
                if chofer_id:
                    notification_service.send('pedido_asignado_chofer', ped_id, emp_id,
                                             chofer_id=chofer_id, cli_id=cli_id,
                                             extra={'cliente': pedido[0].get('PED_CLIENTE_NOMBRE', '') if pedido else '',
                                                    'origen': '', 'destino': pedido[0].get('PED_DESTINO_DIR', '') if pedido else ''})

        elif estado == 'ENTREGADO':
            if notification_service:
                notification_service.send('pedido_entregado', ped_id, emp_id,
                                         cli_id=cli_id,
                                         extra={'fecha_entrega': datetime.now().strftime('%d/%m/%Y %H:%M'),
                                                'destino': pedido[0].get('PED_DESTINO_DIR', '') if pedido else ''})

        elif estado == 'CANCELADO':
            if notification_service:
                notification_service.send('pedido_cancelado', ped_id, emp_id,
                                         cli_id=cli_id,
                                         extra={'razon': request.json.get('razon', 'Sin especificar')})
    except Exception as e:
        app.logger.warning(f'Notification error: {str(e)}')

    return jsonify({'success': True, 'message': f'Estado actualizado a {estado}'})


@app.route('/api/pedidos/<int:ped_id>', methods=['PUT'])
def update_pedido(ped_id):
    emp_id = get_emp_id()
    p = request.json
    if not p:
        return jsonify({'success': False, 'error': 'Datos requeridos'}), 400
    try:
        execute(
            "UPDATE PEDIDOS SET PED_CLIENTE_NOMBRE=?, PED_CLIENTE_TELEFONO=?, PED_DESTINO_DIR=?, PED_DESTINO_COL=?, PED_DESTINO_CIUDAD=?, PED_PESO_KG=?, PED_BULTOS=?, PED_COSTO_TOTAL=?, PED_FORMA_PAGO=?, PED_ESTADO=?, PED_PRIORIDAD=? WHERE PED_ID=? AND EMP_ID=?",
            [p.get('clienteNombre', p.get('PED_CLIENTE_NOMBRE', '')),
             p.get('clienteTelefono', p.get('PED_CLIENTE_TELEFONO', '')),
             p.get('destinoDir', p.get('PED_DESTINO_DIR', '')),
             p.get('destinoCol', p.get('PED_DESTINO_COL', '')),
             p.get('destinoCiudad', p.get('PED_DESTINO_CIUDAD', '')),
             p.get('pesoKg', p.get('PED_PESO_KG', 0)),
             p.get('bultos', p.get('PED_BULTOS', 1)),
             p.get('costoTotal', p.get('PED_COSTO_TOTAL', 0)),
             p.get('formaPago', p.get('PED_FORMA_PAGO', 'EFECTIVO')),
             p.get('estado', p.get('PED_ESTADO', 'PENDIENTE')),
             p.get('prioridad', p.get('PED_PRIORIDAD', 'NORMAL')),
             ped_id, emp_id]
        )
        return jsonify({'success': True, 'message': 'Pedido actualizado'})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})


@app.route('/api/pedidos/estadisticas', methods=['GET'])
def get_pedidos_estadisticas():
    emp_id = get_emp_id()
    data = query(
        "SELECT COUNT(*) as total, SUM(CASE WHEN PED_ESTADO = 'PENDIENTE' THEN 1 ELSE 0 END) as pendientes, "
        "SUM(CASE WHEN PED_ESTADO = 'EN_RUTA' THEN 1 ELSE 0 END) as en_ruta, "
        "SUM(CASE WHEN PED_ESTADO = 'ENTREGADO' THEN 1 ELSE 0 END) as entregados, "
        "SUM(CASE WHEN PED_ESTADO = 'CANCELADO' THEN 1 ELSE 0 END) as cancelados, "
        "COALESCE(SUM(PED_COSTO_TOTAL), 0) as ingresos_totales "
        "FROM PEDIDOS WHERE EMP_ID = ?", [emp_id])
    return jsonify({'success': True, 'data': data[0] if data else {}})


@app.route('/api/tarifas', methods=['GET'])
def get_tarifas():
    emp_id = get_emp_id()
    data = query("SELECT * FROM ZONA_TARIFAS WHERE ZTA_EMP_ID = ? AND ZTA_ACTIVO = 'S' ORDER BY ZTA_SERVICIO", [emp_id])
    return jsonify({'success': True, 'data': data})


# ========================================
# MODULO: CHOFERES
# ========================================
@app.route('/api/choferes', methods=['GET'])
def get_choferes():
    emp_id = get_emp_id()
    return jsonify({'success': True, 'data': query('SELECT * FROM CHOFERES WHERE EMP_ID = ? ORDER BY CHO_NOMBRE', [emp_id])})


@app.route('/api/choferes/rendimiento', methods=['GET'])
def get_rendimiento_choferes():
    emp_id = get_emp_id()
    limit = min(int(request.args.get('limit', 50)), 200)
    offset = max(int(request.args.get('offset', 0)), 0)
    total = query('SELECT COUNT(*) as cnt FROM V_RENDIMIENTO_CHOFERES WHERE EMP_ID = ?', [emp_id])
    total_count = total[0].get('cnt', 0) if total else 0
    data = query('SELECT * FROM V_RENDIMIENTO_CHOFERES WHERE EMP_ID = ? ORDER BY TASA_EXITO DESC LIMIT ? OFFSET ?', [emp_id, limit, offset])
    resp = jsonify({'success': True, 'data': data, 'total': total_count})
    resp.headers['X-Total-Count'] = str(total_count)
    resp.headers['Link'] = f'</api/choferes/rendimiento?limit={limit}&offset={offset}>; rel="self"'
    return resp


@app.route('/api/choferes/<int:cho_id>', methods=['DELETE'])
def delete_chofer(cho_id):
    emp_id = get_emp_id()
    try:
        execute("UPDATE CHOFERES SET CHO_ESTATUS='INACTIVO' WHERE CHO_ID = ? AND EMP_ID = ?", [cho_id, emp_id])
        log_audit('chofer_soft_deleted', f'cho_id={cho_id}')
        return jsonify({'success': True, 'message': 'Chofer desactivado'})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})


@app.route('/api/choferes', methods=['POST'])
def create_chofer():
    emp_id = get_emp_id()
    c = request.json
    if not c:
        return jsonify({'success': False, 'error': 'Datos requeridos'}), 400
    nombre = (c.get('nombre') or c.get('CHO_NOMBRE') or '').strip()
    if not nombre:
        return jsonify({'success': False, 'error': 'Nombre del chofer requerido'}), 400
    try:
        execute(
            "INSERT INTO CHOFERES (EMP_ID, CHO_NOMBRE, CHO_APELLIDO, CHO_TELEFONO, CHO_LICENCIA, CHO_EMAIL, CHO_ESTATUS, CHO_RFC) VALUES (?,?,?,?,?,?,?,?)",
            [emp_id, nombre, c.get('apellido', c.get('CHO_APELLIDO', '')),
             c.get('telefono', c.get('CHO_TELEFONO', '')), c.get('licencia', c.get('CHO_LICENCIA', '')),
             c.get('email', c.get('CHO_EMAIL', '')), c.get('estatus', c.get('CHO_ESTATUS', 'ACTIVO')),
             c.get('rfc', c.get('CHO_RFC', ''))]
        )
        return jsonify({'success': True, 'message': 'Chofer creado'})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})


@app.route('/api/choferes/<int:cho_id>', methods=['PUT'])
def update_chofer(cho_id):
    emp_id = get_emp_id()
    c = request.json
    if not c:
        return jsonify({'success': False, 'error': 'Datos requeridos'}), 400
    try:
        execute(
            "UPDATE CHOFERES SET CHO_NOMBRE=?, CHO_APELLIDO=?, CHO_TELEFONO=?, CHO_LICENCIA=?, CHO_EMAIL=?, CHO_ESTATUS=?, CHO_RFC=? WHERE CHO_ID=? AND EMP_ID=?",
            [c.get('nombre', c.get('CHO_NOMBRE', '')), c.get('apellido', c.get('CHO_APELLIDO', '')),
             c.get('telefono', c.get('CHO_TELEFONO', '')), c.get('licencia', c.get('CHO_LICENCIA', '')),
             c.get('email', c.get('CHO_EMAIL', '')), c.get('estatus', c.get('CHO_ESTATUS', 'ACTIVO')),
             c.get('rfc', c.get('CHO_RFC', '')), cho_id, emp_id]
        )
        return jsonify({'success': True, 'message': 'Chofer actualizado'})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})


# ========================================
# MODULO: VEHICULOS
# ========================================
@app.route('/api/vehiculos', methods=['GET'])
def get_vehiculos():
    emp_id = get_emp_id()
    return jsonify({'success': True, 'data': query('SELECT * FROM VEHICULOS WHERE EMP_ID = ? ORDER BY VEH_UNIDAD', [emp_id])})


@app.route('/api/vehiculos/flota', methods=['GET'])
def get_flota():
    emp_id = get_emp_id()
    return jsonify({'success': True, 'data': query('SELECT * FROM V_ESTADO_FLOTA WHERE EMP_ID = ?', [emp_id])})


@app.route('/api/vehiculos/<int:veh_id>', methods=['DELETE'])
def delete_vehiculo(veh_id):
    emp_id = get_emp_id()
    try:
        execute("DELETE FROM VEHICULOS WHERE VEH_ID = ? AND EMP_ID = ?", [veh_id, emp_id])
        log_audit('vehiculo_deleted', f'veh_id={veh_id}')
        return jsonify({'success': True, 'message': 'Vehiculo eliminado'})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})


@app.route('/api/vehiculos', methods=['POST'])
def create_vehiculo():
    emp_id = get_emp_id()
    v = request.json
    if not v:
        return jsonify({'success': False, 'error': 'Datos requeridos'}), 400
    unidad = (v.get('unidad') or v.get('VEH_UNIDAD') or '').strip()
    if not unidad:
        return jsonify({'success': False, 'error': 'Nombre de unidad requerido'}), 400
    try:
        execute(
            "INSERT INTO VEHICULOS (EMP_ID, VEH_UNIDAD, VEH_MARCA, VEH_MODELO, VEH_ANIO, VEH_PLACAS, VEH_TIPO, VEH_COLOR, VEH_ESTATUS, VEH_CAPACIDAD_KG) VALUES (?,?,?,?,?,?,?,?,?,?)",
            [emp_id, unidad, v.get('marca', v.get('VEH_MARCA', '')),
             v.get('modelo', v.get('VEH_MODELO', '')), v.get('anio', v.get('VEH_ANIO', '')),
             v.get('placas', v.get('VEH_PLACAS', '')), v.get('tipo', v.get('VEH_TIPO', 'CAMIONETA')),
             v.get('color', v.get('VEH_COLOR', '')), v.get('estatus', v.get('VEH_ESTATUS', 'DISPONIBLE')),
             v.get('capacidad_kg', v.get('VEH_CAPACIDAD_KG', 0))]
        )
        return jsonify({'success': True, 'message': 'Vehiculo creado'})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})


@app.route('/api/vehiculos/<int:veh_id>', methods=['PUT'])
def update_vehiculo(veh_id):
    emp_id = get_emp_id()
    v = request.json
    if not v:
        return jsonify({'success': False, 'error': 'Datos requeridos'}), 400
    try:
        execute(
            "UPDATE VEHICULOS SET VEH_UNIDAD=?, VEH_MARCA=?, VEH_MODELO=?, VEH_ANIO=?, VEH_PLACAS=?, VEH_TIPO=?, VEH_COLOR=?, VEH_ESTATUS=?, VEH_CAPACIDAD_KG=? WHERE VEH_ID=? AND EMP_ID=?",
            [v.get('unidad', v.get('VEH_UNIDAD', '')), v.get('marca', v.get('VEH_MARCA', '')),
             v.get('modelo', v.get('VEH_MODELO', '')), v.get('anio', v.get('VEH_ANIO', '')),
             v.get('placas', v.get('VEH_PLACAS', '')), v.get('tipo', v.get('VEH_TIPO', 'CAMIONETA')),
             v.get('color', v.get('VEH_COLOR', '')), v.get('estatus', v.get('VEH_ESTATUS', 'DISPONIBLE')),
             v.get('capacidad_kg', v.get('VEH_CAPACIDAD_KG', 0)), veh_id, emp_id]
        )
        return jsonify({'success': True, 'message': 'Vehiculo actualizado'})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})


# ========================================
# MODULO: CLIENTES
# ========================================
@app.route('/api/clientes', methods=['GET'])
def get_clientes():
    emp_id = get_emp_id()
    return jsonify({'success': True, 'data': query('SELECT * FROM CLIENTES_LM WHERE EMP_ID = ? ORDER BY CLI_RAZON_SOCIAL', [emp_id])})


@app.route('/api/clientes/top', methods=['GET'])
def get_top_clientes():
    emp_id = get_emp_id()
    return jsonify({'success': True, 'data': query('SELECT * FROM V_TOP_CLIENTES WHERE EMP_ID = ? ORDER BY TOTAL_GASTADO DESC LIMIT 10', [emp_id])})


@app.route('/api/clientes/<int:cli_id>', methods=['DELETE'])
def delete_cliente(cli_id):
    emp_id = get_emp_id()
    try:
        execute("UPDATE CLIENTES_LM SET CLI_ESTATUS='INACTIVO' WHERE CLI_ID = ? AND EMP_ID = ?", [cli_id, emp_id])
        log_audit('cliente_soft_deleted', f'cli_id={cli_id}')
        return jsonify({'success': True, 'message': 'Cliente desactivado'})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})


@app.route('/api/clientes', methods=['POST'])
def create_cliente():
    emp_id = get_emp_id()
    c = request.json
    if not c:
        return jsonify({'success': False, 'error': 'Datos requeridos'}), 400
    razon = (c.get('razon_social') or c.get('nombre') or c.get('CLI_RAZON_SOCIAL') or '').strip()
    if not razon:
        return jsonify({'success': False, 'error': 'Razon social requerida'}), 400
    try:
        execute(
            "INSERT INTO CLIENTES_LM (EMP_ID, CLI_RAZON_SOCIAL, CLI_RFC, CLI_CONTACTO, CLI_TELEFONO, CLI_EMAIL, CLI_ESTATUS) VALUES (?,?,?,?,?,?,?)",
            [emp_id, razon, c.get('rfc', c.get('CLI_RFC', '')),
             c.get('contacto', c.get('CLI_CONTACTO', '')),
             c.get('telefono', c.get('CLI_TELEFONO', '')),
             c.get('email', c.get('CLI_EMAIL', '')),
             c.get('estatus', c.get('CLI_ESTATUS', 'ACTIVO'))]
        )
        return jsonify({'success': True, 'message': 'Cliente creado'})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})


@app.route('/api/clientes/<int:cli_id>', methods=['PUT'])
def update_cliente(cli_id):
    emp_id = get_emp_id()
    c = request.json
    if not c:
        return jsonify({'success': False, 'error': 'Datos requeridos'}), 400
    try:
        execute(
            "UPDATE CLIENTES_LM SET CLI_RAZON_SOCIAL=?, CLI_RFC=?, CLI_CONTACTO=?, CLI_TELEFONO=?, CLI_EMAIL=?, CLI_ESTATUS=? WHERE CLI_ID=? AND EMP_ID=?",
            [c.get('razon_social', c.get('CLI_RAZON_SOCIAL', '')),
             c.get('rfc', c.get('CLI_RFC', '')),
             c.get('contacto', c.get('CLI_CONTACTO', '')),
             c.get('telefono', c.get('CLI_TELEFONO', '')),
             c.get('email', c.get('CLI_EMAIL', '')),
             c.get('estatus', c.get('CLI_ESTATUS', 'ACTIVO')),
             cli_id, emp_id]
        )
        return jsonify({'success': True, 'message': 'Cliente actualizado'})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})


# ========================================
# MODULO: RUTAS / ENTREGAS
# ========================================
@app.route('/api/rutas', methods=['GET'])
def get_rutas():
    emp_id = get_emp_id()
    return jsonify({'success': True, 'data': query('SELECT * FROM V_COSTOS_RUTA WHERE EMP_ID = ? ORDER BY PED_FECHA_PEDIDO DESC', [emp_id])})


@app.route('/api/entregas', methods=['GET'])
def get_entregas():
    emp_id = get_emp_id()
    limit = min(int(request.args.get('limit', 50)), 200)
    offset = max(int(request.args.get('offset', 0)), 0)
    total = query('SELECT COUNT(*) as cnt FROM ENTREGAS WHERE EMP_ID = ?', [emp_id])
    total_count = total[0].get('cnt', 0) if total else 0
    data = query('SELECT * FROM ENTREGAS WHERE EMP_ID = ? ORDER BY ENT_FECHA_LLEGADA DESC LIMIT ? OFFSET ?', [emp_id, limit, offset])
    resp = jsonify({'success': True, 'data': data, 'total': total_count})
    resp.headers['X-Total-Count'] = str(total_count)
    resp.headers['Link'] = f'</api/entregas?limit={limit}&offset={offset}>; rel="self"'
    if offset + limit < total_count:
        resp.headers['Link'] += f', </api/entregas?limit={limit}&offset={offset + limit}>; rel="next"'
    if offset > 0:
        resp.headers['Link'] += f', </api/entregas?limit={limit}&offset={max(offset - limit, 0)}>; rel="prev"'
    return resp


@app.route('/api/entregas/chofer/<int:cho_id>', methods=['GET'])
def get_entregas_chofer(cho_id):
    emp_id = get_emp_id()
    return jsonify({'success': True, 'data': query(
        '''SELECT E.*, P.PED_NUMERO, P.PED_CLIENTE_NOMBRE, P.PED_DESTINO_DIR
           FROM ENTREGAS E JOIN PEDIDOS P ON E.PED_ID = P.PED_ID
           WHERE E.CHO_ID = ? AND E.EMP_ID = ? ORDER BY E.ENT_FECHA_LLEGADA DESC''',
        [cho_id, emp_id])})


# ========================================
# MODULO: KPIs
# ========================================
@app.route('/api/kpis', methods=['GET'])
def get_kpis():
    emp_id = get_emp_id()
    data = query('SELECT * FROM V_KPI_CONSOLIDADO WHERE EMP_ID = ?', [emp_id])
    return jsonify({'success': True, 'data': data[0] if data else {}})


@app.route('/api/kpis/diario', methods=['GET'])
def get_kpis_diario():
    emp_id = get_emp_id()
    return jsonify({'success': True, 'data': query('SELECT * FROM KPI_DIARIO WHERE EMP_ID = ? ORDER BY KPI_FECHA DESC LIMIT 30', [emp_id])})


# ========================================
# MODULO: INCIDENCIAS
# ========================================
@app.route('/api/incidencias', methods=['GET'])
def get_incidencias():
    emp_id = get_emp_id()
    return jsonify({'success': True, 'data': query('SELECT * FROM INCIDENCIAS WHERE EMP_ID = ? ORDER BY INC_FECHA DESC', [emp_id])})


@app.route('/api/incidencias/resumen', methods=['GET'])
def get_incidencias_resumen():
    emp_id = get_emp_id()
    return jsonify({'success': True, 'data': query('SELECT * FROM V_INCIDENCIAS_RESUMEN WHERE EMP_ID = ?', [emp_id])})


# ========================================
# MODULO: TRACKING GPS
# ========================================
@app.route('/api/tracking/<int:cho_id>', methods=['GET'])
def get_tracking(cho_id):
    emp_id = get_emp_id()
    return jsonify({'success': True, 'data': query('SELECT * FROM TRACKING WHERE CHO_ID = ? AND EMP_ID = ? ORDER BY TRK_FECHA DESC LIMIT 10', [cho_id, emp_id])})


@app.route('/api/tracking', methods=['POST'])
def post_tracking():
    emp_id = get_emp_id()
    t = request.json
    execute(
        '''INSERT INTO TRACKING (EMP_ID, CHO_ID, VEH_ID, TRK_LATITUD, TRK_LONGITUD, TRK_VELOCIDAD, TRK_RUMBO, TRK_BATERIA)
           VALUES (?, ?, ?, ?, ?, ?, ?, ?)''',
        [emp_id, t.get('choId'), t.get('vehId'), t.get('latitud'), t.get('longitud'),
         t.get('velocidad', 0), t.get('rumbo', 0), t.get('bateria', 100)]
    )
    room = f'emp_{emp_id}'
    socketio.emit('driver_location', {
        'choId': t.get('choId'),
        'nombre': t.get('nombre', ''),
        'apellido': t.get('apellido', ''),
        'lat': t.get('latitud'),
        'lng': t.get('longitud'),
        'speed': t.get('velocidad', 0),
        'heading': t.get('rumbo', 0),
        'battery': t.get('bateria', 100),
        'timestamp': datetime.now().isoformat()
    }, room=room)
    return jsonify({'success': True, 'message': 'Tracking registrado'})


@app.route('/api/tracking/live', methods=['GET'])
def get_live_tracking():
    """Get latest position of all active choferes for real-time map."""
    emp_id = get_emp_id()
    try:
        data = query(
            "SELECT t.CHO_ID, t.TRK_LATITUD, t.TRK_LONGITUD, t.TRK_VELOCIDAD, t.TRK_RUMBO, t.TRK_BATERIA, t.TRK_FECHA, "
            "c.CHO_NOMBRE, c.CHO_APELLIDO, c.CHO_TELEFONO "
            "FROM TRACKING t "
            "JOIN CHOFERES c ON t.CHO_ID = c.CHO_ID "
            "WHERE t.EMP_ID = ? "
            "AND t.TRK_FECHA = (SELECT MAX(T2.TRK_FECHA) FROM TRACKING T2 WHERE T2.CHO_ID = t.CHO_ID AND T2.EMP_ID = t.EMP_ID) "
            "ORDER BY t.TRK_FECHA DESC",
            [emp_id]
        )
        return jsonify({'success': True, 'data': data or []})
    except Exception as e:
        app.logger.warning(f'Live tracking error: {str(e)}')
        return jsonify({'success': True, 'data': []})


@app.route('/api/tracking/route/<int:cho_id>', methods=['GET'])
def get_chofer_route(cho_id):
    """Get route history for a chofer (last 24 hours)."""
    emp_id = get_emp_id()
    try:
        data = query(
            "SELECT TRK_LATITUD, TRK_LONGITUD, TRK_VELOCIDAD, TRK_FECHA "
            "FROM TRACKING WHERE CHO_ID=? AND EMP_ID=? "
            "AND TRK_FECHA >= NOW() - INTERVAL '24 hours' "
            "ORDER BY TRK_FECHA ASC",
            [cho_id, emp_id]
        )
        return jsonify({'success': True, 'data': data})
    except Exception:
        return jsonify({'success': True, 'data': []})


# ========================================
# MODULO: AUDITORIA
# ========================================
@app.route('/api/audit', methods=['GET'])
def get_audit():
    emp_id = get_emp_id()
    return jsonify({'success': True, 'data': query('SELECT * FROM AUDIT_LOG WHERE EMP_ID = ? ORDER BY AUD_FECHA DESC LIMIT 100', [emp_id])})


# ========================================
# MODULO: CFDI 4.0 (Facturacion)
# ========================================
@app.route('/api/cfdi/facturas', methods=['GET'])
def get_cfdi_facturas():
    emp_id = get_emp_id()
    return jsonify({'success': True, 'data': query('SELECT * FROM CFDI_FACTURAS WHERE EMP_ID = ? ORDER BY FAC_FECHA_EMISION DESC LIMIT 50', [emp_id])})


@app.route('/api/cfdi/facturas', methods=['POST'])
def create_cfdi_factura():
    emp_id = get_emp_id()
    f = request.json
    folio_data = query("SELECT FOL_SERIE, FOL_SIGUIENTE FROM CFDI_FOLIOS WHERE EMP_ID = ? AND FOL_ESTATUS = 'ACTIVO' LIMIT 1", [emp_id])
    if not folio_data:
        return jsonify({'success': False, 'error': 'No hay folios disponibles'}), 400
    serie = folio_data[0]['FOL_SERIE']
    folio = folio_data[0]['FOL_SIGUIENTE']
    execute('UPDATE CFDI_FOLIOS SET FOL_SIGUIENTE = FOL_SIGUIENTE + 1 WHERE EMP_ID = ? AND FOL_SERIE = ?', [emp_id, serie])

    execute('''INSERT INTO CFDI_FACTURAS (EMP_ID, FAC_SERIE, FAC_FOLIO, FAC_FORMA_PAGO, FAC_METODO_PAGO,
        FAC_SUBTOTAL, FAC_TOTAL_IVA, FAC_TOTAL, FAC_RECEPTOR_RFC, FAC_RECEPTOR_RAZON,
        FAC_RECEPTOR_REGIMEN, FAC_RECEPTOR_CP, FAC_RECEPTOR_USO_CFDI, FAC_RECEPTOR_EMAIL, FAC_PED_ID, FAC_ESTATUS)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 'PENDIENTE')''',
        [emp_id, serie, str(folio), f.get('formaPago', '01'), f.get('metodoPago', 'PUE'),
         f.get('subtotal', 0), f.get('iva', 0), f.get('total', 0),
         f.get('receptorRfc', ''), f.get('receptorRazon', ''),
         f.get('receptorRegimen', '601'), f.get('receptorCp', '00000'),
         f.get('receptorUsoCfdi', 'G03'), f.get('receptorEmail', ''),
         f.get('pedId')])

    return jsonify({'success': True, 'message': f'Factura {serie}-{folio} creada', 'serie': serie, 'folio': folio})


@app.route('/api/cfdi/facturas/<int:fac_id>/timbrar', methods=['POST'])
def timbrar_factura(fac_id):
    emp_id = get_emp_id()
    from cfdi_service import cfdi_service
    fac_rows = query("SELECT FAC_PED_ID FROM CFDI_FACTURAS WHERE FAC_ID=? AND EMP_ID=?", [fac_id, emp_id])
    if not fac_rows:
        return jsonify({'success': False, 'error': 'Factura no encontrada'}), 404
    pedido_id = fac_rows[0].get('FAC_PED_ID')
    if not pedido_id:
        return jsonify({'success': False, 'error': 'Factura sin pedido asociado'}), 400
    result = cfdi_service.create_invoice(pedido_id, emp_id)
    if result.get('success'):
        execute("UPDATE CFDI_FACTURAS SET FAC_UUID=?, FAC_ESTATUS='TIMBRADA' WHERE FAC_ID=? AND EMP_ID=?",
                [result.get('uuid'), fac_id, emp_id])
        return jsonify({'success': True, 'uuid': result.get('uuid'), 'message': 'Factura timbrada correctamente'})
    else:
        return jsonify({'success': False, 'error': result.get('error', 'Error al timbrar')}), 400


@app.route('/api/cfdi/facturas/<int:fac_id>/cancelar', methods=['POST'])
def cancelar_factura(fac_id):
    emp_id = get_emp_id()
    motivo = request.json.get('motivo', 'Error en factura')
    from cfdi_service import cfdi_service
    result = cfdi_service.cancel_invoice(fac_id, emp_id, motivo)
    if result.get('success'):
        log_audit('factura_cancelled', f'fac_id={fac_id} motivo={motivo[:50]}')
        return jsonify({'success': True, 'message': 'Factura cancelada'})
    else:
        return jsonify({'success': False, 'error': result.get('error', 'Error al cancelar')}), 400


@app.route('/api/cfdi/status', methods=['GET'])
def cfdi_status():
    from cfdi_service import cfdi_service
    return jsonify({'success': True, 'data': cfdi_service.get_status()})


@app.route('/api/cfdi/catalogo', methods=['GET'])
def get_cfdi_catalogo():
    return jsonify({'success': True, 'data': query("SELECT * FROM CFDI_CONCEPTOS_CATALOGO WHERE EMP_ID = ? AND COC_ESTATUS = 'ACTIVO'", [get_emp_id()])})


@app.route('/api/cfdi/empresa-fiscal', methods=['GET'])
def get_empresa_fiscal():
    data = query('SELECT * FROM CFDI_EMPRESA_FISCAL WHERE EMP_ID = ?', [get_emp_id()])
    return jsonify({'success': True, 'data': data[0] if data else None})


@app.route('/api/cfdi/empresa-fiscal', methods=['PUT'])
def update_empresa_fiscal():
    emp_id = get_emp_id()
    f = request.json
    if not f:
        return jsonify({'success': False, 'error': 'Datos requeridos'}), 400
    existing = query('SELECT FISC_ID FROM CFDI_EMPRESA_FISCAL WHERE EMP_ID = ?', [emp_id])
    if existing:
        execute('''UPDATE CFDI_EMPRESA_FISCAL SET FISC_RFC=?, FISC_RAZON_SOCIAL=?, FISC_REGIMEN_FISCAL=?,
            FISC_CODIGO_POSTAL=?, FISC_COLONIA=?, FISC_CALLE=?, FISC_NUMERO_EXTERIOR=?,
            FISC_MUNICIPIO=?, FISC_ESTADO=?, FISC_TELEFONO=?, FISC_EMAIL=? WHERE EMP_ID = ?''',
            [f.get('rfc'), f.get('razonSocial'), f.get('regimenFiscal'),
             f.get('codigoPostal'), f.get('colonia'), f.get('calle'),
             f.get('numeroExterior'), f.get('municipio'), f.get('estado'),
             f.get('telefono'), f.get('email'), emp_id])
    else:
        execute('''INSERT INTO CFDI_EMPRESA_FISCAL (EMP_ID, FISC_RFC, FISC_RAZON_SOCIAL,
            FISC_REGIMEN_FISCAL, FISC_CODIGO_POSTAL, FISC_COLONIA, FISC_CALLE,
            FISC_NUMERO_EXTERIOR, FISC_MUNICIPIO, FISC_ESTADO, FISC_TELEFONO, FISC_EMAIL, FISC_TIPO_PERSONA)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)''',
            [emp_id, f.get('rfc'), f.get('razonSocial'), f.get('regimenFiscal'),
             f.get('codigoPostal'), f.get('colonia'), f.get('calle'),
             f.get('numeroExterior'), f.get('municipio'), f.get('estado'),
             f.get('telefono'), f.get('email'), f.get('tipoPersona', 'M')])
    return jsonify({'success': True, 'message': 'Datos fiscales actualizados'})


@app.route('/api/cfdi/folios', methods=['GET'])
def get_folios():
    return jsonify({'success': True, 'data': query('SELECT * FROM CFDI_FOLIOS WHERE EMP_ID = ?', [get_emp_id()])})


@app.route('/api/cfdi/timbrado-log', methods=['GET'])
def get_timbrado_log():
    return jsonify({'success': True, 'data': query(
        "SELECT T.*, F.FAC_SERIE, F.FAC_FOLIO FROM CFDI_TIMBRADO_LOG T JOIN CFDI_FACTURAS F ON T.FAC_ID = F.FAC_ID WHERE F.EMP_ID = ? ORDER BY T.TIM_FECHA DESC LIMIT 20",
        [get_emp_id()])})


# ========================================
# MODULO: PAGOS
# ========================================
@app.route('/api/pagos/metodos', methods=['GET'])
def get_pagos_metodos():
    return jsonify({'success': True, 'data': query("SELECT * FROM PAGOS_METODOS WHERE EMP_ID = ? AND PMT_ACTIVO = 'S'", [get_emp_id()])})


@app.route('/api/pagos/transacciones', methods=['GET'])
def get_pagos_transacciones():
    return jsonify({'success': True, 'data': query('SELECT * FROM PAGOS_TRANSACCIONES WHERE EMP_ID = ? ORDER BY TRP_FECHA_REGISTRO DESC LIMIT 50', [get_emp_id()])})


@app.route('/api/pagos/transacciones', methods=['POST'])
def create_pago_transaccion():
    emp_id = get_emp_id()
    p = request.json
    if not p:
        return jsonify({'success': False, 'error': 'Datos requeridos'}), 400
    execute('''INSERT INTO PAGOS_TRANSACCIONES (EMP_ID, PED_ID, FAC_ID, TRP_NUM_REFERENCIA,
        TRP_MONTO, TRP_MONEDA, TRP_METODO, TRP_ESTATUS)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)''',
        [emp_id, p.get('pedId'), p.get('facId'), p.get('numReferencia'),
         p.get('monto'), p.get('moneda', 'MXN'), p.get('metodo'), p.get('estatus', 'PENDIENTE')])
    return jsonify({'success': True, 'message': 'Pago registrado'})


@app.route('/api/pagos/resumen', methods=['GET'])
def get_pagos_resumen():
    return jsonify({'success': True, 'data': query('''SELECT TRP_METODO, COUNT(*) as TOTAL, SUM(TRP_MONTO) as MONTO_TOTAL,
        SUM(CASE WHEN TRP_ESTATUS = 'PAGADO' THEN TRP_MONTO ELSE 0 END) as COBRADO,
        SUM(CASE WHEN TRP_ESTATUS = 'PENDIENTE' THEN TRP_MONTO ELSE 0 END) as PENDIENTE
        FROM PAGOS_TRANSACCIONES WHERE EMP_ID = ? GROUP BY TRP_METODO ORDER BY MONTO_TOTAL DESC''', [get_emp_id()])})


@app.route('/api/pagos/transacciones/<int:pag_id>', methods=['DELETE'])
def delete_pago(pag_id):
    try:
        emp_id = get_emp_id()
        execute("DELETE FROM PAGOS_TRANSACCIONES WHERE TRP_ID = ? AND EMP_ID = ?", [pag_id, emp_id])
        log_audit('pago_deleted', f'pag_id={pag_id}')
        return jsonify({'success': True, 'message': 'Pago eliminado'})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})


@app.route('/api/pagos/oxxo', methods=['POST'])
def create_oxxo():
    import random, string
    p = request.json
    ref = 'OXXO' + ''.join(random.choices(string.digits, k=12))
    execute("INSERT INTO PAGOS_TRANSACCIONES (EMP_ID, PED_ID, TRP_NUM_REFERENCIA, TRP_MONTO, TRP_METODO, TRP_ESTATUS) VALUES (?, ?, ?, ?, 'OXXO', 'PENDIENTE')",
            [get_emp_id(), p.get('pedId'), ref, p.get('monto')])
    return jsonify({'success': True, 'referencia': ref, 'message': f'Referencia OXXO: {ref}'})


@app.route('/api/pagos/mercado-pago/webhook', methods=['POST'])
def mp_webhook():
    data = request.get_json() or {}
    action = data.get('action', '')
    payment_id = data.get('data', {}).get('id')

    if action == 'payment.created' and payment_id:
        payment = mp_service.get_payment(payment_id)
        if payment.get('status') == 'approved':
            ext_ref = payment.get('external_reference', '')
            if ext_ref.startswith('emp_'):
                parts = ext_ref.split('_')
                emp_id = int(parts[1]) if len(parts) > 1 else 0
                plan_name = parts[2] if len(parts) > 2 else 'STARTER'
                if emp_id:
                    create_suscripcion(emp_id, plan_name, 'mercadopago', str(payment_id))
                    create_pago(emp_id, payment.get('transaction_amount', 0), 'MERCADOPAGO', str(payment_id))

    return jsonify({'received': True})


# ========================================
# MODULO: USUARIOS
# ========================================
@app.route('/api/usuarios', methods=['GET'])
def get_usuarios():
    emp_id = get_emp_id()
    return jsonify({'success': True, 'data': query('SELECT USU_ID, USU_EMP_ID, USU_USUARIO, USU_NOMBRE, USU_EMAIL, USU_TELEFONO, USU_ROL, USU_ACTIVO, USU_CREATED FROM USUARIOS WHERE USU_EMP_ID = ? ORDER BY USU_NOMBRE', [emp_id])})


@app.route('/api/usuarios/<int:usu_id>', methods=['GET'])
def get_usuario(usu_id):
    emp_id = get_emp_id()
    data = query('SELECT USU_ID, USU_EMP_ID, USU_USUARIO, USU_NOMBRE, USU_EMAIL, USU_TELEFONO, USU_ROL, USU_ACTIVO, USU_CREATED FROM USUARIOS WHERE USU_ID = ? AND USU_EMP_ID = ?', [usu_id, emp_id])
    return jsonify({'success': True, 'data': data[0] if data else None})


@app.route('/api/usuarios/<int:usu_id>', methods=['DELETE'])
def delete_usuario(usu_id):
    emp_id = get_emp_id()
    try:
        execute("DELETE FROM USUARIOS WHERE USU_ID = ? AND USU_EMP_ID = ?", [usu_id, emp_id])
        log_audit('usuario_deleted', f'usu_id={usu_id}')
        return jsonify({'success': True, 'message': 'Usuario eliminado'})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})


@app.route('/api/usuarios', methods=['POST'])
def create_usuario():
    emp_id = get_emp_id()
    u = request.json
    if not u:
        return jsonify({'success': False, 'error': 'Datos requeridos'}), 400
    usuario = (u.get('usuario') or u.get('USU_USUARIO') or u.get('email', '') or '').strip()
    nombre = (u.get('nombre') or u.get('USU_NOMBRE') or '').strip()
    password = u.get('password', u.get('USU_PASS', ''))
    if not usuario or not nombre:
        return jsonify({'success': False, 'error': 'Usuario y nombre requeridos'}), 400
    if not password:
        return jsonify({'success': False, 'error': 'Password requerido'}), 400
    pass_hash = hash_password(password)
    try:
        execute(
            "INSERT INTO USUARIOS (USU_EMP_ID, USU_USUARIO, USU_PASS, USU_NOMBRE, USU_EMAIL, USU_TELEFONO, USU_ROL, USU_ACTIVO) VALUES (?,?,?,?,?,?,?,?)",
            [emp_id, usuario, pass_hash, nombre,
             u.get('email', u.get('USU_EMAIL', '')),
             u.get('telefono', u.get('USU_TELEFONO', '')),
             u.get('rol', u.get('USU_ROL', 'operacion')),
             u.get('activo', u.get('USU_ACTIVO', 'S'))]
        )
        return jsonify({'success': True, 'message': 'Usuario creado'})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})


@app.route('/api/usuarios/<int:usu_id>', methods=['PUT'])
def update_usuario(usu_id):
    emp_id = get_emp_id()
    u = request.json
    if not u:
        return jsonify({'success': False, 'error': 'Datos requeridos'}), 400
    password = u.get('password', u.get('USU_PASS', ''))
    try:
        if password:
            pass_hash = hash_password(password)
            execute(
                "UPDATE USUARIOS SET USU_USUARIO=?, USU_PASS=?, USU_NOMBRE=?, USU_EMAIL=?, USU_TELEFONO=?, USU_ROL=?, USU_ACTIVO=? WHERE USU_ID=? AND USU_EMP_ID=?",
                [u.get('usuario', u.get('USU_USUARIO', '')), pass_hash,
                 u.get('nombre', u.get('USU_NOMBRE', '')),
                 u.get('email', u.get('USU_EMAIL', '')),
                 u.get('telefono', u.get('USU_TELEFONO', '')),
                 u.get('rol', u.get('USU_ROL', 'operacion')),
                 u.get('activo', u.get('USU_ACTIVO', 'S')),
                 usu_id, emp_id]
            )
        else:
            execute(
                "UPDATE USUARIOS SET USU_USUARIO=?, USU_NOMBRE=?, USU_EMAIL=?, USU_TELEFONO=?, USU_ROL=?, USU_ACTIVO=? WHERE USU_ID=? AND USU_EMP_ID=?",
                [u.get('usuario', u.get('USU_USUARIO', '')),
                 u.get('nombre', u.get('USU_NOMBRE', '')),
                 u.get('email', u.get('USU_EMAIL', '')),
                 u.get('telefono', u.get('USU_TELEFONO', '')),
                 u.get('rol', u.get('USU_ROL', 'operacion')),
                 u.get('activo', u.get('USU_ACTIVO', 'S')),
                 usu_id, emp_id]
            )
        return jsonify({'success': True, 'message': 'Usuario actualizado'})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})


@app.route('/api/usuarios/<int:usu_id>/unlock', methods=['POST'])
@requiere_rol('admin', 'superadmin')
def unlock_usuario(usu_id):
    """Desbloquea una cuenta bloqueada por intentos fallidos."""
    emp_id = get_emp_id()
    try:
        execute(
            "UPDATE USUARIOS SET USU_FAILED_ATTEMPTS=0, USU_LOCKED_UNTIL=NULL, USU_LAST_FAILED_AT=NULL WHERE USU_ID=? AND USU_EMP_ID=?",
            [usu_id, emp_id]
        )
        return jsonify({'success': True, 'message': 'Cuenta desbloqueada'})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})


@app.route('/api/usuarios/lock-status', methods=['GET'])
@requiere_rol('admin', 'superadmin')
def lock_status():
    """Lista usuarios bloqueados en el tenant."""
    emp_id = get_emp_id()
    try:
        rows = query(
            "SELECT USU_ID, USU_USUARIO, USU_NOMBRE, USU_FAILED_ATTEMPTS, USU_LOCKED_UNTIL, USU_LAST_FAILED_AT "
            "FROM USUARIOS WHERE USU_EMP_ID=? AND (USU_FAILED_ATTEMPTS > 0 OR USU_LOCKED_UNTIL IS NOT NULL) "
            "ORDER BY USU_LAST_FAILED_AT DESC",
            [emp_id]
        )
        return jsonify({'success': True, 'data': rows})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})


# ========================================
# MODULO: WHITELABEL
# ========================================
@app.route('/api/whitelabel/<int:emp_id>', methods=['GET'])
def get_whitelabel(emp_id):
    data = query('''SELECT E.EMP_ID, E.EMP_NOMBRE,
        COALESCE(F.FISC_RFC, '') as RFC,
        COALESCE(F.FISC_RAZON_SOCIAL, '') as RAZON_SOCIAL
        FROM EMPRESAS E LEFT JOIN CFDI_EMPRESA_FISCAL F ON E.EMP_ID = F.EMP_ID WHERE E.EMP_ID = ?''', [emp_id])
    return jsonify({'success': True, 'data': data[0] if data else {}})


@app.route('/api/whitelabel/config', methods=['POST'])
def update_whitelabel():
    try:
        emp_id = get_emp_id()
        if not emp_id:
            return jsonify({'success': False, 'error': 'No autenticado'}), 401
        data = request.json or {}
        execute('''CREATE TABLE IF NOT EXISTS TENANT_CONFIG (
            TC_ID INTEGER PRIMARY KEY AUTOINCREMENT,
            EMP_ID INTEGER NOT NULL UNIQUE,
            TC_NOMBRE TEXT DEFAULT '',
            TC_LOGO_URL TEXT DEFAULT '',
            TC_COLOR_PRIMARY TEXT DEFAULT '#4F46E5',
            TC_COLOR_SECONDARY TEXT DEFAULT '#7C3AED',
            TC_COLOR_BG TEXT DEFAULT '#F9FAFB',
            TC_DOMINIO TEXT DEFAULT '',
            TC_FOOTER_TEXT TEXT DEFAULT '',
            TC_CUSTOM_CSS TEXT DEFAULT '',
            TC_CUSTOM_JS TEXT DEFAULT '',
            TC_FEATURES TEXT DEFAULT '{}',
            TC_FECHA_REGISTRO TEXT DEFAULT (datetime('now')),
            TC_FECHA_ACTUALIZACION TEXT DEFAULT (datetime('now'))
        )''')
        existing = query('SELECT TC_ID FROM TENANT_CONFIG WHERE EMP_ID = ?', [emp_id])
        if existing:
            execute('''UPDATE TENANT_CONFIG SET
                TC_NOMBRE=?, TC_LOGO_URL=?, TC_COLOR_PRIMARY=?, TC_COLOR_SECONDARY=?,
                TC_COLOR_BG=?, TC_DOMINIO=?, TC_FOOTER_TEXT=?, TC_CUSTOM_CSS=?,
                TC_CUSTOM_JS=?, TC_FEATURES=?, TC_FECHA_ACTUALIZACION=datetime('now')
                WHERE EMP_ID=?''',
                [data.get('nombre', ''), data.get('logo_url', ''),
                 data.get('color_primary', '#4F46E5'), data.get('color_secondary', '#7C3AED'),
                 data.get('color_bg', '#F9FAFB'), data.get('dominio', ''),
                 data.get('footer_text', ''), data.get('custom_css', ''),
                 data.get('custom_js', ''), data.get('features', '{}'), emp_id])
        else:
            execute('''INSERT INTO TENANT_CONFIG
                (EMP_ID, TC_NOMBRE, TC_LOGO_URL, TC_COLOR_PRIMARY, TC_COLOR_SECONDARY,
                 TC_COLOR_BG, TC_DOMINIO, TC_FOOTER_TEXT, TC_CUSTOM_CSS, TC_CUSTOM_JS, TC_FEATURES)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)''',
                [emp_id, data.get('nombre', ''), data.get('logo_url', ''),
                 data.get('color_primary', '#4F46E5'), data.get('color_secondary', '#7C3AED'),
                 data.get('color_bg', '#F9FAFB'), data.get('dominio', ''),
                 data.get('footer_text', ''), data.get('custom_css', ''),
                 data.get('custom_js', ''), data.get('features', '{}')])
        return jsonify({'success': True, 'message': 'Whitelabel actualizado'})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})


# ========================================
# MODULO: EXPORTACION CSV/PDF
# ========================================
try:
    from export_service import export_service, EXPORT_CONFIGS
except Exception as _export_err:
    export_service = None
    EXPORT_CONFIGS = {}
    print(f'[WARN] Export service disabled: {_export_err}')


@app.route('/api/export/<entity>', methods=['GET'])
def export_entity(entity):
    if not export_service:
        return jsonify({'success': False, 'error': 'Export service not configured'}), 503
    emp_id = get_emp_id()
    fmt = request.args.get('format', 'csv')

    config = EXPORT_CONFIGS.get(entity)
    if not config:
        return jsonify({'success': False, 'error': f'Entidad {entity} no soportada'}), 400

    # Query data
    table_map = {
        'pedidos': 'PEDIDOS', 'clientes': 'CLIENTES_LM', 'choferes': 'CHOFERES',
        'vehiculos': 'VEHICULOS', 'usuarios': 'USUARIOS',
        'pagos': 'PAGOS_TRANSACCIONES', 'facturas': 'CFDI_FACTURAS'
    }
    table = table_map.get(entity)
    if not table:
        return jsonify({'success': False, 'error': f'Entidad {entity} no soportada'}), 400

    try:
        data = query(f"SELECT * FROM {table} WHERE EMP_ID=? ORDER BY 1 DESC LIMIT 5000", [emp_id])
    except Exception:
        data = query(f"SELECT * FROM {table} ORDER BY 1 DESC LIMIT 5000")

    if fmt == 'pdf':
        result = export_service.to_pdf(data, config['columns'], title=config['title'])
    else:
        result = export_service.to_csv(data, list(config['columns'].keys()),
                                       filename=f'{entity}_{datetime.now().strftime("%Y%m%d")}.csv')

    if not result.get('success'):
        return jsonify({'success': False, 'error': result.get('error')}), 400

    from flask import Response
    return Response(
        result['content'],
        mimetype=result['content_type'],
        headers={'Content-Disposition': f'attachment; filename={result["filename"]}'}
    )


@app.route('/api/export/custom', methods=['POST'])
def export_custom():
    if not export_service:
        return jsonify({'success': False, 'error': 'Export service not configured'}), 503
    data = request.json or {}
    report_type = data.get('report_type', '')
    params = data.get('params', {})
    columns = data.get('columns', {})
    title = data.get('title', 'Reporte')
    fmt = data.get('format', 'csv')
    emp_id = get_emp_id()

    ALLOWED_REPORTS = {
        'pedidos_por_estado': "SELECT PED_ESTADO, COUNT(*) as TOTAL, SUM(PED_COSTO_TOTAL) as MONTO FROM PEDIDOS WHERE EMP_ID=? GROUP BY PED_ESTADO",
        'choferes_por_empresa': "SELECT C.CHO_NOMBRE, C.CHO_TELEFONO, C.CHO_ESTATUS FROM CHOFERES C WHERE C.EMP_ID=?",
        'pagos_por_metodo': "SELECT TRP_METODO, COUNT(*) as TOTAL, SUM(TRP_MONTO) as MONTO FROM PAGOS_TRANSACCIONES WHERE EMP_ID=? GROUP BY TRP_METODO",
        'clientes_top': "SELECT PED_CLIENTE_NOMBRE, COUNT(*) as PEDIDOS, SUM(PED_COSTO_TOTAL) as GASTO FROM PEDIDOS WHERE EMP_ID=? GROUP BY PED_CLIENTE_NOMBRE ORDER BY GASTO DESC LIMIT 10",
        'ingresos_mensuales': "SELECT strftime('%Y-%m', PED_FECHA_PEDIDO) as MES, SUM(PED_COSTO_TOTAL) as INGRESOS, COUNT(*) as PEDIDOS FROM PEDIDOS WHERE EMP_ID=? GROUP BY MES ORDER BY MES DESC LIMIT 12",
    }

    if not report_type:
        return jsonify({'success': False, 'error': 'report_type requerido', 'available': list(ALLOWED_REPORTS.keys())}), 400

    sql_template = ALLOWED_REPORTS.get(report_type)
    if not sql_template:
        return jsonify({'success': False, 'error': f'Reporte no valido. Disponibles: {list(ALLOWED_REPORTS.keys())}'}), 400

    try:
        result_data = query(sql_template, [emp_id])
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 400

    if fmt == 'pdf':
        result = export_service.to_pdf(result_data, columns, title=title)
    else:
        result = export_service.to_csv(result_data, list(columns.keys()) if columns else None)

    if not result.get('success'):
        return jsonify({'success': False, 'error': result.get('error')}), 400

    from flask import Response
    return Response(
        result['content'],
        mimetype=result['content_type'],
        headers={'Content-Disposition': f'attachment; filename={result["filename"]}'}
    )


# ========================================
# MODULO: SaaS ADMIN
# ========================================
@app.route('/api/saas/tenants', methods=['GET'])
@requiere_superadmin
def get_saas_tenants():
    return jsonify({'success': True, 'data': query('''SELECT E.*,
        (SELECT COUNT(*) FROM PEDIDOS P WHERE P.EMP_ID = E.EMP_ID) as TOTAL_PEDIDOS,
        (SELECT COUNT(*) FROM CHOFERES C WHERE C.EMP_ID = E.EMP_ID) as TOTAL_CHOFERES,
        (SELECT COUNT(*) FROM CLIENTES_LM CL WHERE CL.EMP_ID = E.EMP_ID) as TOTAL_CLIENTES
        FROM EMPRESAS E ORDER BY E.EMP_ID''')})


@app.route('/api/saas/plan-usage/<int:emp_id>', methods=['GET'])
def get_plan_usage(emp_id):
    data = query('''SELECT E.EMP_ID, E.EMP_NOMBRE,
        (SELECT COUNT(*) FROM PEDIDOS P WHERE P.EMP_ID = E.EMP_ID AND P.PED_FECHA_PEDIDO >= CURRENT_DATE - INTERVAL '30 days') as PEDIDOS_MES,
        (SELECT COUNT(*) FROM CHOFERES C WHERE C.EMP_ID = E.EMP_ID) as CHOFERES,
        (SELECT COUNT(*) FROM CLIENTES_LM CL WHERE CL.EMP_ID = E.EMP_ID) as CLIENTES,
        (SELECT COUNT(*) FROM VEHICULOS V WHERE V.EMP_ID = E.EMP_ID) as VEHICULOS
        FROM EMPRESAS E WHERE E.EMP_ID = ?''', [emp_id])
    return jsonify({'success': True, 'data': data[0] if data else {}})


@app.route('/api/saas/health', methods=['GET'])
def saas_health():
    empresas = query('SELECT COUNT(*) as TOTAL FROM EMPRESAS')
    pedidos = query('SELECT COUNT(*) as TOTAL FROM PEDIDOS')
    return jsonify({'success': True, 'empresas_activas': empresas[0]['TOTAL'] if empresas else 0, 'pedidos_total': pedidos[0]['TOTAL'] if pedidos else 0})


@app.route('/api/saas/planes', methods=['GET'])
def get_saas_planes():
    return jsonify({'success': True, 'data': query("SELECT * FROM SAAS_PLANES WHERE PLAN_ACTIVO = 'S' ORDER BY PLAN_ORDEN")})


@app.route('/api/saas/planes/<int:plan_id>', methods=['GET'])
def get_saas_plan(plan_id):
    data = query('SELECT * FROM SAAS_PLANES WHERE PLAN_ID = ?', [plan_id])
    return jsonify({'success': True, 'data': data[0] if data else None})


@app.route('/api/saas/suscripciones', methods=['GET'])
def get_suscripciones():
    return jsonify({'success': True, 'data': query('''SELECT S.*, P.PLAN_NOMBRE, P.PLAN_PRECIO_MENSUAL, E.EMP_NOMBRE
        FROM SAAS_SUSCRIPCIONES S JOIN SAAS_PLANES P ON S.PLAN_ID = P.PLAN_ID JOIN EMPRESAS E ON S.EMP_ID = E.EMP_ID
        ORDER BY S.SUS_FECHA_REGISTRO DESC''')})


@app.route('/api/saas/suscripciones', methods=['POST'])
def create_suscripcion_manual():
    emp_id = get_emp_id()
    s = request.json
    from datetime import date, timedelta
    hoy = date.today()
    proximo = hoy + timedelta(days=30)
    execute("INSERT INTO SAAS_SUSCRIPCIONES (EMP_ID, PLAN_ID, SUS_ESTADO, SUS_FECHA_INICIO, SUS_FECHA_FIN, SUS_FECHA_PROXIMO_COBRO) VALUES (?, ?, 'TRIAL', ?, ?, ?)",
            [emp_id, s.get('planId'), hoy.isoformat(), proximo.isoformat(), proximo.isoformat()])
    return jsonify({'success': True, 'message': 'Suscripcion creada'})


@app.route('/api/saas/cobros', methods=['GET'])
def get_cobros():
    return jsonify({'success': True, 'data': query('''SELECT C.*, P.PLAN_NOMBRE, E.EMP_NOMBRE
        FROM SAAS_COBROS C JOIN SAAS_SUSCRIPCIONES S ON C.SUS_ID = S.SUS_ID
        JOIN SAAS_PLANES P ON S.PLAN_ID = P.PLAN_ID JOIN EMPRESAS E ON C.EMP_ID = E.EMP_ID
        ORDER BY C.COB_FECHA_COBRO DESC LIMIT 20''')})


@app.route('/api/saas/cobros/resumen', methods=['GET'])
def get_cobros_resumen():
    data = query('''SELECT
        COUNT(*) as TOTAL_COBROS,
        COALESCE(SUM(COB_MONTO), 0) as MONTO_TOTAL,
        COALESCE(SUM(CASE WHEN COB_ESTATUS = 'PAGADO' THEN COB_MONTO ELSE 0 END), 0) as COBRADO,
        COALESCE(SUM(CASE WHEN COB_ESTATUS = 'PENDIENTE' THEN COB_MONTO ELSE 0 END), 0) as PENDIENTE,
        0 as VENCIDO
        FROM SAAS_COBROS''')
    return jsonify({'success': True, 'data': data[0] if data else {'TOTAL_COBROS': 0, 'MONTO_TOTAL': 0, 'COBRADO': 0, 'PENDIENTE': 0, 'VENCIDO': 0}})


@app.route('/api/saas/uso/<int:emp_id>', methods=['GET'])
def get_uso_recursos(emp_id):
    return jsonify({'success': True, 'data': query('SELECT * FROM SAAS_USO_RECURSOS WHERE EMP_ID = ? ORDER BY USR_FECHA DESC LIMIT 30', [emp_id])})


@app.route('/api/saas/uso', methods=['POST'])
def registrar_uso():
    emp_id = get_emp_id()
    u = request.json
    if not u:
        return jsonify({'success': False, 'error': 'Datos requeridos'}), 400
    execute("INSERT INTO SAAS_USO_RECURSOS (EMP_ID, USR_PEDIDOS_CREADOS, USR_PEDIDOS_ENTREGADOS, USR_ENVIOS_SMS, USR_ENVIOS_EMAIL, USR_API_CALLS) VALUES (?, ?, ?, ?, ?, ?)",
            [emp_id, u.get('pedidosCreados', 0), u.get('pedidosEntregados', 0), u.get('enviosSms', 0), u.get('enviosEmail', 0), u.get('apiCalls', 0)])
    return jsonify({'success': True, 'message': 'Uso registrado'})


@app.route('/api/saas/dashboard-billing', methods=['GET'])
def get_billing_dashboard():
    empresas = query('SELECT COUNT(*) as TOTAL FROM EMPRESAS')
    suscripciones = query('SELECT SUS_ESTADO, COUNT(*) as TOTAL FROM SAAS_SUSCRIPCIONES GROUP BY SUS_ESTADO')
    cobros = query('''SELECT SUM(COB_MONTO) as TOTAL,
        SUM(CASE WHEN COB_ESTATUS = 'PAGADO' THEN COB_MONTO ELSE 0 END) as COBRADO,
        SUM(CASE WHEN COB_ESTATUS = 'PENDIENTE' THEN COB_MONTO ELSE 0 END) as PENDIENTE
        FROM SAAS_COBROS''')
    uso_hoy = query("SELECT COALESCE(SUM(USR_PEDIDOS_CREADOS), 0) as PEDIDOS, COALESCE(SUM(USR_API_CALLS), 0) as API_CALLS FROM SAAS_USO_RECURSOS WHERE USR_FECHA = CURRENT_DATE")

    return jsonify({
        'success': True,
        'data': {
            'empresas_activas': empresas[0]['TOTAL'] if empresas else 0,
            'suscripciones': {s['SUS_ESTADO']: s['TOTAL'] for s in suscripciones},
            'cobros': cobros[0] if cobros else {},
            'uso_hoy': uso_hoy[0] if uso_hoy else {}
        }
    })


@app.route('/api/saas/global-stats', methods=['GET'])
def saas_global_stats():
    result = {
        'empresas_total': 0, 'empresas_activas': 0, 'pedidos_hoy': 0, 'pedidos_mes': 0,
        'choferes_total': 0, 'usuarios_total': 0, 'clientes_total': 0,
        'revenue_mes': 0, 'mrr': 0, 'pagos_pendientes': 0, 'pagos_pend_monto': 0,
        'sus_activas': 0, 'sus_trial': 0, 'sus_canceladas': 0,
    }
    try:
        r = query('SELECT COUNT(*) as total, COUNT(CASE WHEN EMP_ESTATUS=\'ACTIVA\' THEN 1 END) as activas FROM EMPRESAS')
        if r: result['empresas_total'] = r[0].get('TOTAL', 0); result['empresas_activas'] = r[0].get('ACTIVAS', 0)
    except Exception: pass
    try:
        r = query("SELECT COUNT(*) as total FROM PEDIDOS WHERE PED_FECHA_PEDIDO >= CURRENT_DATE")
        if r: result['pedidos_hoy'] = r[0].get('TOTAL', 0)
    except Exception: pass
    try:
        r = query("SELECT COUNT(*) as total FROM PEDIDOS WHERE PED_FECHA_PEDIDO >= CURRENT_DATE - INTERVAL '30 days'")
        if r: result['pedidos_mes'] = r[0].get('TOTAL', 0)
    except Exception: pass
    try:
        r = query('SELECT COUNT(*) as total FROM CHOFERES')
        if r: result['choferes_total'] = r[0].get('TOTAL', 0)
    except Exception: pass
    try:
        r = query('SELECT COUNT(*) as total FROM USUARIOS')
        if r: result['usuarios_total'] = r[0].get('TOTAL', 0)
    except Exception: pass
    try:
        r = query('SELECT COUNT(*) as total FROM CLIENTES_LM')
        if r: result['clientes_total'] = r[0].get('TOTAL', 0)
    except Exception: pass
    try:
        r = query("SELECT COALESCE(SUM(COB_MONTO), 0) as total FROM SAAS_COBROS WHERE COB_FECHA_COBRO >= CURRENT_DATE - INTERVAL '30 days'")
        if r: result['revenue_mes'] = float(r[0].get('TOTAL', 0) or 0)
    except Exception: pass
    try:
        r = query("SELECT COALESCE(SUM(P.PLAN_PRECIO_MENSUAL), 0) as total FROM SAAS_SUSCRIPCIONES S JOIN SAAS_PLANES P ON S.PLAN_ID = P.PLAN_ID WHERE S.SUS_ESTADO = 'ACTIVA'")
        if r: result['mrr'] = float(r[0].get('TOTAL', 0) or 0)
    except Exception: pass
    try:
        r = query("SELECT COUNT(*) as total, COALESCE(SUM(COB_MONTO), 0) as monto FROM SAAS_COBROS WHERE COB_ESTATUS = 'PENDIENTE'")
        if r: result['pagos_pendientes'] = r[0].get('TOTAL', 0); result['pagos_pend_monto'] = float(r[0].get('MONTO', 0) or 0)
    except Exception: pass
    try:
        sus = query("SELECT SUS_ESTADO, COUNT(*) as total FROM SAAS_SUSCRIPCIONES GROUP BY SUS_ESTADO")
        for s in (sus or []):
            key = s.get('SUS_ESTADO', '').lower()
            if key == 'activa': result['sus_activas'] = s.get('TOTAL', 0)
            elif key == 'trial': result['sus_trial'] = s.get('TOTAL', 0)
            elif key == 'cancelada': result['sus_canceladas'] = s.get('TOTAL', 0)
    except Exception: pass

    return jsonify({'success': True, 'data': result})


@app.route('/api/saas/tenants/<int:emp_id>', methods=['GET'])
def get_saas_tenant(emp_id):
    data = query('''SELECT E.*,
        (SELECT COUNT(*) FROM PEDIDOS P WHERE P.EMP_ID = E.EMP_ID) as TOTAL_PEDIDOS,
        (SELECT COUNT(*) FROM CHOFERES C WHERE C.EMP_ID = E.EMP_ID) as TOTAL_CHOFERES,
        (SELECT COUNT(*) FROM CLIENTES_LM CL WHERE CL.EMP_ID = E.EMP_ID) as TOTAL_CLIENTES,
        (SELECT COUNT(*) FROM VEHICULOS V WHERE V.EMP_ID = E.EMP_ID) as TOTAL_VEHICULOS,
        (SELECT COUNT(*) FROM USUARIOS U WHERE U.USU_EMP_ID = E.EMP_ID) as TOTAL_USUARIOS
        FROM EMPRESAS E WHERE E.EMP_ID = ?''', [emp_id])
    if not data:
        return jsonify({'success': False, 'error': 'Tenant no encontrado'}), 404

    tenant = data[0]
    tenant['suscripcion'] = query('''SELECT S.*, P.PLAN_NOMBRE, P.PLAN_PRECIO_MENSUAL
        FROM SAAS_SUSCRIPCIONES S JOIN SAAS_PLANES P ON S.PLAN_ID = P.PLAN_ID
        WHERE S.EMP_ID = ? AND S.SUS_ESTADO = 'ACTIVA' ORDER BY S.SUS_FECHA_INICIO DESC LIMIT 1''', [emp_id])
    tenant['suscripcion'] = tenant['suscripcion'][0] if tenant['suscripcion'] else None
    tenant['pagos_recientes'] = query('''SELECT * FROM SAAS_COBROS WHERE EMP_ID = ? ORDER BY COB_FECHA_COBRO DESC LIMIT 5''', [emp_id])
    tenant['usuarios'] = query('SELECT USU_ID, USU_USUARIO, USU_NOMBRE, USU_ROL, USU_ACTIVO FROM USUARIOS WHERE USU_EMP_ID = ?', [emp_id])
    tenant['uso_reciente'] = query('SELECT * FROM SAAS_USO_RECURSOS WHERE EMP_ID = ? ORDER BY USR_FECHA DESC LIMIT 7', [emp_id])

    return jsonify({'success': True, 'data': tenant})


@app.route('/api/saas/tenants', methods=['POST'])
@requiere_superadmin
def create_saas_tenant():
    data = request.json or {}
    nombre = data.get('nombre', '').strip()
    if not nombre:
        return jsonify({'success': False, 'error': 'Nombre requerido'})

    execute("INSERT INTO EMPRESAS (EMP_NOMBRE, EMP_RFC, EMP_EMAIL, EMP_TELEFONO, EMP_ESTATUS, EMP_PLAN) VALUES (?, ?, ?, ?, 'ACTIVA', ?)",
            [nombre, data.get('rfc', ''), data.get('email', ''), data.get('telefono', ''), data.get('plan', 'STARTER')])

    emp = query("SELECT EMP_ID FROM EMPRESAS WHERE EMP_NOMBRE = ? ORDER BY EMP_ID DESC LIMIT 1", [nombre])
    emp_id = emp[0]['EMP_ID'] if emp else 0

    if emp_id:
        admin_user = data.get('admin_user', 'admin')
        admin_pass = data.get('admin_pass', 'admin123')
        pass_hash = hash_password(admin_pass.strip())
        execute("INSERT INTO USUARIOS (USU_EMP_ID, USU_USUARIO, USU_PASS, USU_NOMBRE, USU_EMAIL, USU_ROL) VALUES (?, ?, ?, ?, ?, 'admin')",
                [emp_id, admin_user, pass_hash, f'Admin {nombre}', data.get('email', '')])

    return jsonify({'success': True, 'message': f'Tenant "{nombre}" creado', 'emp_id': emp_id})


@app.route('/api/saas/tenants/<int:emp_id>', methods=['PUT'])
@requiere_superadmin
def update_saas_tenant(emp_id):
    data = request.json or {}
    execute("UPDATE EMPRESAS SET EMP_NOMBRE=?, EMP_RFC=?, EMP_EMAIL=?, EMP_TELEFONO=?, EMP_ESTATUS=?, EMP_PLAN=? WHERE EMP_ID=?",
            [data.get('nombre', ''), data.get('rfc', ''), data.get('email', ''), data.get('telefono', ''),
             data.get('estatus', 'ACTIVA'), data.get('plan', 'STARTER'), emp_id])
    return jsonify({'success': True, 'message': 'Tenant actualizado'})


@app.route('/api/saas/tenants/<int:emp_id>/suspend', methods=['POST'])
@requiere_superadmin
def suspend_saas_tenant(emp_id):
    execute("UPDATE EMPRESAS SET EMP_ESTATUS='SUSPENDIDA' WHERE EMP_ID=?", [emp_id])
    try:
        execute("UPDATE SAAS_SUSCRIPCIONES SET SUS_ESTADO='SUSPENDIDA' WHERE EMP_ID=? AND SUS_ESTADO='ACTIVA'", [emp_id])
    except Exception:
        pass
    log_audit('tenant_suspended', f'emp_id={emp_id}')
    return jsonify({'success': True, 'message': 'Tenant suspendido'})


@app.route('/api/saas/tenants/<int:emp_id>/activate', methods=['POST'])
@requiere_superadmin
def activate_saas_tenant(emp_id):
    execute("UPDATE EMPRESAS SET EMP_ESTATUS='ACTIVA' WHERE EMP_ID=?", [emp_id])
    log_audit('tenant_activated', f'emp_id={emp_id}')
    return jsonify({'success': True, 'message': 'Tenant activado'})


@app.route('/api/saas/all-users', methods=['GET'])
def get_saas_all_users():
    return jsonify({'success': True, 'data': query('''SELECT U.*, E.EMP_NOMBRE
        FROM USUARIOS U JOIN EMPRESAS E ON U.USU_EMP_ID = E.EMP_ID
        ORDER BY U.USU_ID DESC''')})


@app.route('/api/saas/all-pedidos', methods=['GET'])
def get_saas_all_pedidos():
    return jsonify({'success': True, 'data': query('''SELECT P.*, E.EMP_NOMBRE
        FROM PEDIDOS P JOIN EMPRESAS E ON P.EMP_ID = E.EMP_ID
        ORDER BY P.PED_FECHA_PEDIDO DESC LIMIT 100''')})


@app.route('/api/saas/audit', methods=['GET'])
def get_saas_audit():
    return jsonify({'success': True, 'data': query('''SELECT A.*, E.EMP_NOMBRE
        FROM AUDIT_LOG A LEFT JOIN EMPRESAS E ON A.EMP_ID = E.EMP_ID
        ORDER BY A.AUD_FECHA DESC LIMIT 100''')})


@app.route('/api/saas/audit', methods=['POST'])
def create_saas_audit():
    emp_id = get_emp_id()
    a = request.json or {}
    execute("INSERT INTO AUDIT_LOG (EMP_ID, AUD_USUARIO, AUD_ACCION, AUD_TABLA, AUD_REGISTRO_ID, AUD_DETALLE, AUD_IP) VALUES (?, ?, ?, ?, ?, ?, ?)",
            [emp_id, a.get('usuario', 'SYSTEM'), a.get('accion', ''), a.get('tabla', ''), a.get('registro_id', 0), a.get('detalle', ''), a.get('ip', '')])
    return jsonify({'success': True})


@app.route('/api/saas/revenue-chart', methods=['GET'])
def saas_revenue_chart():
    try:
        data = query('''SELECT
            TO_CHAR(COB_FECHA_COBRO, 'YYYY-MM') as mes,
            SUM(COB_MONTO) as total,
            SUM(CASE WHEN COB_ESTATUS = 'PAGADO' THEN COB_MONTO ELSE 0 END) as cobrado
            FROM SAAS_COBROS
            WHERE COB_FECHA_COBRO >= CURRENT_DATE - INTERVAL '12 months'
            GROUP BY TO_CHAR(COB_FECHA_COBRO, 'YYYY-MM')
            ORDER BY mes''')
    except Exception:
        data = []
    return jsonify({'success': True, 'data': data or []})


@app.route('/api/saas/tenants-chart', methods=['GET'])
def saas_tenants_chart():
    try:
        data = query('''SELECT
            PLAN_ID, COUNT(*) as total
            FROM SAAS_SUSCRIPCIONES
            WHERE SUS_ESTADO IN ('ACTIVA', 'TRIAL')
            GROUP BY PLAN_ID''')
    except Exception:
        data = []
    return jsonify({'success': True, 'data': data or []})


@app.route('/api/saas/config', methods=['GET'])
def get_saas_config():
    return jsonify({'success': True, 'data': {
        'platform_name': 'Last Mile Delivery SaaS',
        'currency': 'MXN',
        'timezone': 'America/Mexico_City',
        'trial_days': 14,
        'max_free_tenants': 3,
        'maintenance_mode': False,
    }})


# ========================================
# MODULO: NOTIFICACIONES
# ========================================
@app.route('/api/notif/push', methods=['GET'])
def get_notif_push():
    return jsonify({'success': True, 'data': query('SELECT * FROM NOTIF_PUSH WHERE EMP_ID = ? ORDER BY NPUSH_FECHA_REGISTRO DESC LIMIT 20', [get_emp_id()])})


@app.route('/api/notif/push', methods=['POST'])
def send_notif_push():
    emp_id = get_emp_id()
    n = request.json
    if not n:
        return jsonify({'success': False, 'error': 'Datos requeridos'}), 400
    execute("INSERT INTO NOTIF_PUSH (EMP_ID, USR_ID, CHO_ID, NPUSH_TIPO, NPUSH_TITULO, NPUSH_CUERPO, NPUSH_DATA) VALUES (?, ?, ?, ?, ?, ?, ?)",
            [emp_id, n.get('usrId'), n.get('choId'), n.get('tipo'), n.get('titulo'), n.get('cuerpo'), n.get('data', '{}')])
    return jsonify({'success': True, 'message': 'Notificacion enviada'})


@app.route('/api/notif/dispositivos', methods=['POST'])
def register_device():
    emp_id = get_emp_id()
    d = request.json
    if not d:
        return jsonify({'success': False, 'error': 'Datos requeridos'}), 400
    execute("INSERT INTO NOTIF_DISPOSITIVOS (EMP_ID, USR_ID, CHO_ID, DISP_TOKEN, DISP_PLATAFORMA) VALUES (?, ?, ?, ?, ?)",
            [emp_id, d.get('usrId'), d.get('choId'), d.get('token'), d.get('plataforma', 'WEB')])
    return jsonify({'success': True, 'message': 'Dispositivo registrado'})


@app.route('/api/notif/stats', methods=['GET'])
def get_notif_stats():
    return jsonify({'success': True, 'data': query('''SELECT NPUSH_TIPO, COUNT(*) as TOTAL,
        SUM(CASE WHEN NPUSH_ENVIADO = 'S' THEN 1 ELSE 0 END) as ENVIADOS,
        SUM(CASE WHEN NPUSH_LEIDO = 'S' THEN 1 ELSE 0 END) as LEIDOS
        FROM NOTIF_PUSH WHERE EMP_ID = ? GROUP BY NPUSH_TIPO''', [get_emp_id()])})


# ========================================
# MODULO: EMAIL / SMS
# ========================================
@app.route('/api/email/enviados', methods=['GET'])
def get_emails():
    return jsonify({'success': True, 'data': query('SELECT * FROM EMAIL_ENVIADOS WHERE EMP_ID = ? ORDER BY EMAIL_FECHA_REGISTRO DESC LIMIT 20', [get_emp_id()])})


@app.route('/api/email/enviar', methods=['POST'])
def send_email():
    emp_id = get_emp_id()
    e = request.json
    if not e:
        return jsonify({'success': False, 'error': 'Datos requeridos'}), 400
    execute("INSERT INTO EMAIL_ENVIADOS (EMP_ID, PED_ID, EMAIL_DESTINATARIO, EMAIL_ASUNTO, EMAIL_TIPO, EMAIL_BODY_HTML, EMAIL_ENVIADO) VALUES (?, ?, ?, ?, ?, ?, 'S')",
            [emp_id, e.get('pedId'), e.get('destinatario'), e.get('asunto'), e.get('tipo'), e.get('bodyHtml')])
    return jsonify({'success': True, 'message': 'Email enviado'})


@app.route('/api/email/stats', methods=['GET'])
def get_email_stats():
    return jsonify({'success': True, 'data': query('''SELECT EMAIL_TIPO, COUNT(*) as TOTAL,
        SUM(CASE WHEN EMAIL_ENVIADO = 'S' THEN 1 ELSE 0 END) as ENVIADOS
        FROM EMAIL_ENVIADOS WHERE EMP_ID = ? GROUP BY EMAIL_TIPO''', [get_emp_id()])})


@app.route('/api/sms/enviados', methods=['GET'])
def get_sms():
    return jsonify({'success': True, 'data': query('SELECT * FROM SMS_ENVIADOS WHERE EMP_ID = ? ORDER BY SMS_FECHA_REGISTRO DESC LIMIT 20', [get_emp_id()])})


@app.route('/api/sms/enviar', methods=['POST'])
def send_sms():
    emp_id = get_emp_id()
    s = request.json
    if not s:
        return jsonify({'success': False, 'error': 'Datos requeridos'}), 400
    execute("INSERT INTO SMS_ENVIADOS (EMP_ID, PED_ID, SMS_TELEFONO, SMS_MENSAJE, SMS_PLATAFORMA, SMS_ENVIADO) VALUES (?, ?, ?, ?, ?, 'S')",
            [emp_id, s.get('pedId'), s.get('telefono'), s.get('mensaje'), s.get('plataforma', 'SMS')])
    return jsonify({'success': True, 'message': 'SMS enviado'})


@app.route('/api/sms/stats', methods=['GET'])
def get_sms_stats():
    return jsonify({'success': True, 'data': query('''SELECT SMS_PLATAFORMA, COUNT(*) as TOTAL,
        SUM(SMS_COSTO) as COSTO_TOTAL
        FROM SMS_ENVIADOS WHERE EMP_ID = ? GROUP BY SMS_PLATAFORMA''', [get_emp_id()])})


# ========================================
# MODULO: REPORTES
# ========================================
@app.route('/api/reportes', methods=['GET'])
def get_reportes():
    return jsonify({'success': True, 'data': query('SELECT * FROM REPORTES_GENERADOS WHERE EMP_ID = ? ORDER BY RPT_FECHA_GENERACION DESC LIMIT 20', [get_emp_id()])})


@app.route('/api/reportes/generar', methods=['POST'])
def generar_reporte():
    emp_id = get_emp_id()
    r = request.json
    tipo = r.get('tipo', 'ENTREGAS')
    execute("INSERT INTO REPORTES_GENERADOS (EMP_ID, RPT_TIPO, RPT_NOMBRE, RPT_PARAMETROS, RPT_GENERADO_POR) VALUES (?, ?, ?, ?, ?)",
            [emp_id, tipo, f'Reporte {tipo}', r.get('parametros', '{}'), r.get('usuario', 'ADMIN')])
    return jsonify({'success': True, 'message': f'Reporte {tipo} generado'})


@app.route('/api/reportes/entregas', methods=['GET'])
def reporte_entregas():
    return jsonify({'success': True, 'data': query('''SELECT P.PED_NUMERO, P.PED_CLIENTE_NOMBRE, P.PED_DESTINO_DIR, P.PED_DESTINO_COL,
        P.PED_BULTOS, P.PED_COSTO_TOTAL, P.PED_ESTADO, P.PED_FECHA_PEDIDO,
        C.CHO_NOMBRE, C.CHO_APELLIDO, V.VEH_UNIDAD
        FROM PEDIDOS P LEFT JOIN CHOFERES C ON P.CHO_ID = C.CHO_ID LEFT JOIN VEHICULOS V ON P.VEH_ID = V.VEH_ID
        WHERE P.EMP_ID = ? ORDER BY P.PED_FECHA_PEDIDO DESC LIMIT 50''', [get_emp_id()])})


@app.route('/api/reportes/rendimiento-choferes', methods=['GET'])
def reporte_rendimiento():
    return jsonify({'success': True, 'data': query('SELECT * FROM V_RENDIMIENTO_CHOFERES WHERE EMP_ID = ? ORDER BY TASA_EXITO DESC', [get_emp_id()])})


@app.route('/api/reportes/costos-rutas', methods=['GET'])
def reporte_costos():
    return jsonify({'success': True, 'data': query('SELECT * FROM V_COSTOS_RUTA WHERE EMP_ID = ? ORDER BY PED_COSTO_TOTAL DESC', [get_emp_id()])})


# ========================================
# MODULO: APP CLIENTE (Tracking)
# ========================================
@app.route('/api/cliente-final/<token>', methods=['GET'])
def get_cliente_tracking(token):
    data = query('''SELECT CF.CLIF_NOMBRE, CF.CLIF_TELEFONO, CF.CLIF_EMAIL, CF.PED_ID,
        P.PED_NUMERO, P.PED_ESTADO, P.PED_DESTINO_DIR, P.PED_DESTINO_COL,
        P.PED_BULTOS, P.PED_FECHA_PEDIDO, P.CHOFER_ASIGNADO, P.UNIDAD_ASIGNADA
        FROM CLIENTE_FINAL CF
        JOIN V_PEDIDOS_COMPLETO P ON CF.PED_ID = P.PED_ID AND P.EMP_ID = CF.EMP_ID
        WHERE CF.CLIF_TOKEN_TRACKING = ?''', [token])
    if not data:
        return jsonify({'success': False, 'error': 'Token no encontrado'}), 404
    return jsonify({'success': True, 'data': data[0]})


@app.route('/api/cliente-final/<token>/timeline', methods=['GET'])
def get_cliente_timeline(token):
    pedido = query('SELECT PED_ID FROM CLIENTE_FINAL WHERE CLIF_TOKEN_TRACKING = ?', [token])
    if not pedido:
        return jsonify({'success': False, 'error': 'Token invalido'}), 404
    ped_id = pedido[0]['PED_ID']

    timeline = []
    p = query('SELECT * FROM PEDIDOS WHERE PED_ID = ?', [ped_id])
    if p:
        timeline.append({'estado': 'Creado', 'fecha': str(p[0].get('PED_FECHA_PEDIDO', '')), 'icono': 'package'})
    hist = query('SELECT * FROM PEDIDO_HISTORIAL WHERE PED_ID = ? ORDER BY HIS_FECHA DESC', [ped_id])
    for h in hist:
        timeline.append({'estado': h.get('HIS_ESTADO', ''), 'fecha': str(h.get('HIS_FECHA', '')), 'usuario': h.get('HIS_USUARIO', '')})

    return jsonify({'success': True, 'data': timeline})


@app.route('/api/cliente-final', methods=['POST'])
def create_cliente_final():
    emp_id = get_emp_id()
    import secrets
    c = request.json
    token = secrets.token_hex(32)
    execute("INSERT INTO CLIENTE_FINAL (EMP_ID, PED_ID, CLIF_NOMBRE, CLIF_TELEFONO, CLIF_EMAIL, CLIF_TOKEN_TRACKING) VALUES (?, ?, ?, ?, ?, ?)",
            [emp_id, c.get('pedId'), c.get('nombre'), c.get('telefono'), c.get('email'), token])
    return jsonify({'success': True, 'token': token, 'message': 'Tracking link generado'})


# ========================================
# PEDIDOS DELETE
# ========================================
@app.route('/api/pedidos/<int:ped_id>', methods=['DELETE'])
def delete_pedido(ped_id):
    try:
        emp_id = get_emp_id()
        execute("UPDATE PEDIDOS SET PED_ESTADO='ELIMINADO' WHERE PED_ID = ? AND EMP_ID = ?", [ped_id, emp_id])
        execute("INSERT INTO PEDIDO_HISTORIAL (PED_ID, HIS_ESTADO, HIS_USUARIO) VALUES (?, 'ELIMINADO', 'SYSTEM')", [ped_id])
        log_audit('pedido_soft_deleted', f'ped_id={ped_id}')
        return jsonify({'success': True, 'message': 'Pedido eliminado'})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})


# ========================================
# MODULO: BILLING / SUSCRIPCIONES
# ========================================
from payment_service import (
    stripe_service, mp_service, get_plan_config, PLANS,
    get_empresa_billing, create_suscripcion, create_pago,
    cancel_suscripcion, get_suscripcion_activa, get_billing_stats
)


# ========================================
# MODULO: NOTIFICACIONES
# ========================================
try:
    from notification_service import notification_service
except Exception as _notif_err:
    notification_service = None
    print(f'[WARN] Notification service disabled: {_notif_err}')


try:
    from ai_endpoints import ai_bp
    app.register_blueprint(ai_bp)
except Exception as _ai_err:
    print(f'[WARN] AI endpoints disabled: {_ai_err}')


@app.route('/api/notifications/send', methods=['POST'])
def send_notification():
    if not notification_service:
        return jsonify({'success': False, 'error': 'Notification service not configured'}), 503
    data = request.get_json() or {}
    template = data.get('template')
    pedido_id = data.get('pedido_id')
    emp_id = get_emp_id()
    chofer_id = data.get('chofer_id')
    cli_id = data.get('cli_id')
    extra = data.get('extra', {})

    if not template:
        return jsonify({'success': False, 'error': 'Template requerido'}), 400

    result = notification_service.send(template, pedido_id, emp_id, chofer_id, cli_id, extra)
    return jsonify({'success': True, 'data': result})


@app.route('/api/notifications/custom', methods=['POST'])
def send_custom_notification():
    if not notification_service:
        return jsonify({'success': False, 'error': 'Notification service not configured'}), 503
    data = request.get_json() or {}
    result = notification_service.send_custom(
        to_email=data.get('to_email'),
        to_phone=data.get('to_phone'),
        subject=data.get('subject'),
        html=data.get('html'),
        sms_text=data.get('sms_text')
    )
    return jsonify({'success': True, 'data': result})


@app.route('/api/notifications/test', methods=['POST'])
def test_notification():
    if not notification_service:
        return jsonify({'success': False, 'error': 'Notification service not configured'}), 503
    data = request.get_json() or {}
    test_type = data.get('type', 'email')
    to = data.get('to')

    if test_type == 'email':
        result = notification_service.email.send(to, 'Test - Last Mile', '<h1>Funciona!</h1><p>El sistema de email esta configurado correctamente.</p>')
    elif test_type == 'sms':
        result = notification_service.sms.send(to, 'Last Mile: SMS configurado correctamente.')
    else:
        return jsonify({'success': False, 'error': 'Tipo invalido'}), 400

    return jsonify({'success': True, 'data': result})


@app.route('/api/notifications/config', methods=['GET'])
def get_notification_config():
    if not notification_service:
        return jsonify({'success': True, 'data': {'email_enabled': False, 'sms_enabled': False, 'email_provider': 'None', 'sms_provider': 'None'}})
    return jsonify({
        'success': True,
        'data': {
            'email_enabled': notification_service.email.enabled,
            'sms_enabled': notification_service.sms.enabled,
            'email_provider': 'Resend' if notification_service.email.enabled else 'None',
            'sms_provider': 'Twilio' if notification_service.sms.enabled else 'None',
        }
    })


@app.route('/api/billing/planes', methods=['GET'])
def get_planes():
    planes = []
    for key, plan in PLANS.items():
        planes.append({
            'id': key,
            'name': plan['name'],
            'price_mxn': plan['price_mxn'],
            'max_usuarios': plan['max_usuarios'],
            'max_choferes': plan['max_choferes'],
            'max_pedidos_mes': plan['max_pedidos_mes'],
            'features': plan['features'],
            'stripe_available': bool(plan['stripe_price_id']),
            'mp_available': bool(plan['mp_plan_id']),
        })
    return jsonify({'success': True, 'data': planes})


@app.route('/api/billing/estado', methods=['GET'])
def get_billing_estado():
    emp_id = get_emp_id()
    try:
        stats = get_billing_stats(emp_id)
        stats['stripe_enabled'] = stripe_service.enabled
        stats['mp_enabled'] = mp_service.enabled
        return jsonify({'success': True, 'data': stats})
    except Exception as e:
        error_logger.error(f'Billing estado error: {str(e)}', exc_info=True)
        plan = get_plan_config('STARTER')
        return jsonify({'success': True, 'data': {
            'plan_actual': 'STARTER',
            'plan_nombre': plan['name'],
            'precio_mensual': plan['price_mxn'],
            'suscripcion_activa': False,
            'suscripcion_inicio': None,
            'total_pagos': 0,
            'monto_total': 0,
            'monto_completado': 0,
            'limite_usuarios': plan['max_usuarios'],
            'limite_choferes': plan['max_choferes'],
            'limite_pedidos_mes': plan['max_pedidos_mes'],
            'stripe_enabled': stripe_service.enabled,
            'mp_enabled': mp_service.enabled,
        }})


@app.route('/api/billing/checkout', methods=['POST'])
def create_checkout():
    emp_id = get_emp_id()
    data = request.get_json() or {}
    plan_name = data.get('plan', 'STARTER')
    provider = data.get('provider', 'stripe')
    country_code = data.get('country_code', 'MX').upper()

    empresa = query("SELECT * FROM EMPRESAS WHERE EMP_ID=?", [emp_id])
    if not empresa:
        return jsonify({'success': False, 'error': 'Empresa no encontrada'}), 404
    empresa = empresa[0]

    base_url = request.host_url.rstrip('/')
    success_url = f'{base_url}/panel-admin.html?billing=success'
    cancel_url = f'{base_url}/panel-admin.html?billing=cancel'

    if provider == 'stripe':
        result = stripe_service.create_checkout_session(emp_id, plan_name, success_url, cancel_url, country_code)
        if 'error' in result:
            return jsonify({'success': False, 'error': result['error']}), 400
        return jsonify({'success': True, 'checkout_url': result.get('url'), 'session_id': result.get('id')})
    elif provider == 'mercadopago':
        result = mp_service.create_preference(
            emp_id, plan_name,
            success_url, cancel_url, success_url
        )
        if 'error' in result:
            return jsonify({'success': False, 'error': result['error']}), 400
        return jsonify({'success': True, 'checkout_url': result.get('init_point'), 'preference_id': result.get('id')})
    else:
        return jsonify({'success': False, 'error': f'Proveedor no soportado: {provider}'}), 400


@app.route('/api/billing/suscripcion', methods=['POST'])
def activate_suscripcion():
    emp_id = get_emp_id()
    data = request.get_json() or {}
    plan_name = data.get('plan', 'STARTER')
    provider = data.get('provider', 'manual')
    external_id = data.get('external_id', '')

    create_suscripcion(emp_id, plan_name, provider, external_id)
    return jsonify({'success': True, 'message': f'Suscripcion {plan_name} activada'})


@app.route('/api/billing/cancelar', methods=['POST'])
def cancelar_suscripcion():
    emp_id = get_emp_id()
    sus = get_suscripcion_activa(emp_id)
    if not sus:
        return jsonify({'success': False, 'error': 'No hay suscripcion activa'})

    if sus.get('SUS_PROVEEDOR') == 'stripe' and sus.get('SUS_EXTERNAL_ID'):
        stripe_service.cancel_subscription(sus['SUS_EXTERNAL_ID'])

    cancel_suscripcion(emp_id)
    log_audit('subscription_cancelled', f'emp_id={emp_id} plan={sus.get("SUS_PLAN", "")}')
    return jsonify({'success': True, 'message': 'Suscripcion cancelada, plan revertido a Starter'})


@app.route('/api/billing/pagos', methods=['GET'])
def get_pagos():
    emp_id = get_emp_id()
    pagos = query(
        "SELECT * FROM PAGOS_TRANSACCIONES WHERE EMP_ID = ? ORDER BY TRP_FECHA_REGISTRO DESC LIMIT 50",
        [emp_id]
    )
    return jsonify({'success': True, 'data': pagos})


@app.route('/api/billing/pago', methods=['POST'])
def record_pago():
    emp_id = get_emp_id()
    data = request.get_json() or {}
    monto = float(data.get('monto', 0))
    metodo = data.get('metodo', 'EFECTIVO')
    referencia = data.get('referencia', '')
    notas = data.get('notas', '')

    if monto <= 0:
        return jsonify({'success': False, 'error': 'Monto debe ser mayor a 0'}), 400

    create_pago(emp_id, monto, metodo, referencia, notas)
    return jsonify({'success': True, 'message': 'Pago registrado'})


@app.route('/api/billing/webhook/stripe', methods=['POST'])
@limiter.limit("100 per minute")
def stripe_webhook():
    payload = request.get_data(as_text=True)
    sig_header = request.headers.get('Stripe-Signature', '')

    event = stripe_service.verify_webhook(payload, sig_header)
    if not event:
        return jsonify({'error': 'Invalid webhook'}), 400

    if event['type'] == 'checkout.session.completed':
        session = event['data']['object']
        emp_id = int(session.get('metadata', {}).get('emp_id', 0))
        plan_name = session.get('metadata', {}).get('plan', 'STARTER')
        if emp_id:
            create_suscripcion(emp_id, plan_name, 'stripe', session.get('subscription'))
            create_pago(emp_id, PLANS.get(plan_name, {}).get('price_mxn', 0), 'STRIPE', session.get('payment_intent'))
    elif event['type'] == 'invoice.paid':
        invoice = event['data']['object']
        emp_id = int(invoice.get('metadata', {}).get('emp_id', 0))
        if emp_id:
            create_pago(emp_id, invoice.get('amount_paid', 0) / 100, 'STRIPE', invoice.get('payment_intent'), 'Renovacion automatica')
    elif event['type'] == 'invoice.payment_failed':
        invoice = event['data']['object']
        emp_id = int(invoice.get('metadata', {}).get('emp_id', 0))
        if emp_id:
            create_pago(emp_id, invoice.get('amount_due', 0) / 100, 'STRIPE', invoice.get('payment_intent'), 'Pago fallido')
    elif event['type'] == 'customer.subscription.deleted':
        sub = event['data']['object']
        sub_id = sub.get('id')
        rows = query("SELECT EMP_ID FROM SAAS_SUSCRIPCIONES WHERE SUS_EXTERNAL_ID=? AND SUS_ESTADO='ACTIVA'", [sub_id])
        if rows:
            cancel_suscripcion(rows[0]['EMP_ID'])

    return jsonify({'received': True})


@app.route('/api/billing/webhook/mercadopago', methods=['POST'])
@limiter.limit("100 per minute")
def mercadopago_webhook():
    data = request.get_json() or {}
    if data.get('type') == 'payment':
        payment_id = data.get('data', {}).get('id')
        if payment_id:
            payment = mp_service.get_payment(payment_id)
            if payment.get('status') == 'approved':
                ext_ref = payment.get('external_reference', '')
                if ext_ref.startswith('emp_'):
                    parts = ext_ref.split('_')
                    emp_id = int(parts[1]) if len(parts) > 1 else 0
                    plan_name = parts[2] if len(parts) > 2 else 'STARTER'
                    if emp_id:
                        create_suscripcion(emp_id, plan_name, 'mercadopago', str(payment_id))
                        create_pago(emp_id, payment.get('transaction_amount', 0), 'MERCADOPAGO', str(payment_id))
    return jsonify({'received': True})


@app.route('/api/billing/stats-all', methods=['GET'])
def billing_stats_all():
    stats = query('''
        SELECT E.EMP_ID, E.EMP_NOMBRE, E.EMP_PLAN,
            (SELECT COUNT(*) FROM SAAS_SUSCRIPCIONES S WHERE S.EMP_ID = E.EMP_ID AND S.SUS_ESTADO = 'ACTIVA') as activas,
            (SELECT COALESCE(SUM(C.COB_MONTO), 0) FROM SAAS_COBROS C WHERE C.EMP_ID = E.EMP_ID AND C.COB_ESTATUS = 'COMPLETADO') as ingresos
        FROM EMPRESAS E
        ORDER BY E.EMP_ID
    ''')
    return jsonify({'success': True, 'data': stats})


# ========================================
# MULTI-COUNTRY FISCAL
# ========================================

@app.route('/api/fiscal/countries', methods=['GET'])
def get_fiscal_countries():
    from fiscal_providers import MultiCountryFiscalService
    service = MultiCountryFiscalService()
    return jsonify({'success': True, 'data': service.get_available_countries()})


@app.route('/api/fiscal/config', methods=['GET'])
def get_fiscal_config():
    emp_id = g.emp_id
    config = query("SELECT * FROM TENANT_FISCAL_CONFIG WHERE EMP_ID=?", [emp_id])
    fiscal_data = query("SELECT * FROM TENANT_FISCAL_DATA WHERE EMP_ID=?", [emp_id])
    return jsonify({'success': True, 'config': config[0] if config else None, 'fiscal_data': fiscal_data[0] if fiscal_data else None})


@app.route('/api/fiscal/config', methods=['PUT'])
def update_fiscal_config():
    emp_id = g.emp_id
    data = request.get_json()
    cc = data.get('country_code', 'MX')
    provider = data.get('provider', 'MEXICO')
    api_key = data.get('api_key', '')
    base_url = data.get('base_url', '')
    test_mode = data.get('test_mode', 'S')
    existing = query("SELECT * FROM TENANT_FISCAL_CONFIG WHERE EMP_ID=?", [emp_id])
    if existing:
        execute("UPDATE TENANT_FISCAL_CONFIG SET TFC_COUNTRY_CODE=?, TFC_PROVIDER=?, TFC_API_KEY=?, TFC_BASE_URL=?, TFC_TEST_MODE=?, TFC_FECHA_ACTUALIZACION=NOW() WHERE EMP_ID=?", [cc, provider, api_key, base_url, test_mode, emp_id])
    else:
        execute("INSERT INTO TENANT_FISCAL_CONFIG (EMP_ID, TFC_COUNTRY_CODE, TFC_PROVIDER, TFC_API_KEY, TFC_BASE_URL, TFC_TEST_MODE) VALUES (?, ?, ?, ?, ?, ?)", [emp_id, cc, provider, api_key, base_url, test_mode])
    log_audit('FISCAL_CONFIG_UPDATED')
    return jsonify({'success': True})


@app.route('/api/fiscal/providers', methods=['GET'])
def get_fiscal_providers():
    from fiscal_providers import FiscalProviderRegistry
    return jsonify({'success': True, 'data': FiscalProviderRegistry.get_available_countries()})


@app.route('/api/fiscal/test-connection', methods=['POST'])
def test_fiscal_connection():
    emp_id = g.emp_id
    data = request.get_json() or {}
    country_code = data.get('country_code')
    from fiscal_providers import FiscalProviderRegistry
    if country_code:
        provider = FiscalProviderRegistry.get_provider(country_code, {'api_key': 'test', 'base_url': ''})
        if provider: return jsonify(provider.test_connection())
        return jsonify({'success': False, 'error': f'Provider {country_code} not found'})
    config = query("SELECT * FROM TENANT_FISCAL_CONFIG WHERE EMP_ID=?", [emp_id])
    if not config: return jsonify({'success': False, 'error': 'No config for this tenant'})
    cfg = config[0]
    provider = FiscalProviderRegistry.get_provider(cfg['TFC_COUNTRY_CODE'], {'api_key': cfg.get('TFC_API_KEY', ''), 'base_url': cfg.get('TFC_BASE_URL', '')})
    if provider: return jsonify(provider.test_connection())
    return jsonify({'success': False, 'error': 'Provider not found'})


@app.route('/api/fiscal/emit', methods=['POST'])
def emit_fiscal_document():
    emp_id = g.emp_id
    from fiscal_providers import MultiCountryFiscalService
    service = MultiCountryFiscalService()
    config = query("SELECT * FROM TENANT_FISCAL_CONFIG WHERE EMP_ID=?", [emp_id])
    if not config: return jsonify({'success': False, 'error': 'No config'})
    cfg = config[0]
    service.configure_tenant(emp_id, cfg['TFC_COUNTRY_CODE'], {'api_key': cfg.get('TFC_API_KEY', ''), 'base_url': cfg.get('TFC_BASE_URL', '')})
    result = service.emit_invoice(emp_id, request.get_json())
    if result.get('success'):
        log_audit('FISCAL_INVOICE_EMITTED')
    return jsonify(result)


@app.route('/api/fiscal/cancel', methods=['POST'])
def cancel_fiscal_document():
    emp_id = g.emp_id
    from fiscal_providers import MultiCountryFiscalService
    service = MultiCountryFiscalService()
    config = query("SELECT * FROM TENANT_FISCAL_CONFIG WHERE EMP_ID=?", [emp_id])
    if not config: return jsonify({'success': False, 'error': 'No config'})
    cfg = config[0]
    service.configure_tenant(emp_id, cfg['TFC_COUNTRY_CODE'], {'api_key': cfg.get('TFC_API_KEY', ''), 'base_url': cfg.get('TFC_BASE_URL', '')})
    data = request.get_json()
    result = service.cancel_invoice(emp_id, data.get('document_id', ''), data.get('reason', ''))
    return jsonify(result)


@app.route('/api/payment/countries', methods=['GET'])
def get_payment_countries():
    rows = query("SELECT DISTINCT PMC_COUNTRY_CODE FROM PAYMENT_METHODS_COUNTRY WHERE PMC_ACTIVO='S' ORDER BY PMC_COUNTRY_CODE")
    return jsonify({'success': True, 'data': [r['PMC_COUNTRY_CODE'] for r in rows]})


@app.route('/api/payment/methods/<country_code>', methods=['GET'])
def get_payment_methods(country_code):
    rows = query("SELECT * FROM PAYMENT_METHODS_COUNTRY WHERE PMC_COUNTRY_CODE=? AND PMC_ACTIVO='S'", [country_code.upper()])
    return jsonify({'success': True, 'data': rows})


@app.route('/api/system/migrate', methods=['POST'])
def run_migration():
    from auth import decode_token
    auth_header = request.headers.get('Authorization', '')
    if not auth_header.startswith('Bearer '):
        return jsonify({'error': 'Unauthorized'}), 401
    token = auth_header.split(' ')[1]
    payload = decode_token(token)
    if not payload:
        return jsonify({'error': 'Invalid token'}), 401
    if payload.get('usuario') != 'admin' and payload.get('rol') != 'admin':
        return jsonify({'error': 'Admin only'}), 401

    stmts = [
        "CREATE TABLE IF NOT EXISTS TENANT_FISCAL_CONFIG (TFC_ID SERIAL PRIMARY KEY, EMP_ID INTEGER NOT NULL UNIQUE REFERENCES EMPRESAS(EMP_ID), TFC_COUNTRY_CODE TEXT NOT NULL DEFAULT 'MX', TFC_PROVIDER TEXT NOT NULL DEFAULT 'MEXICO', TFC_API_KEY TEXT, TFC_API_SECRET TEXT, TFC_BASE_URL TEXT, TFC_ENABLED TEXT DEFAULT 'N', TFC_TEST_MODE TEXT DEFAULT 'S', TFC_CUSTOM_CONFIG TEXT DEFAULT '{}', TFC_FECHA_REGISTRO TIMESTAMP DEFAULT NOW(), TFC_FECHA_ACTUALIZACION TIMESTAMP DEFAULT NOW())",
        "CREATE TABLE IF NOT EXISTS TENANT_FISCAL_DATA (TFD_ID SERIAL PRIMARY KEY, EMP_ID INTEGER NOT NULL UNIQUE REFERENCES EMPRESAS(EMP_ID), TFD_RFC TEXT, TFD_RAZON_SOCIAL TEXT, TFD_REGIMEN_FISCAL TEXT, TFD_CODIGO_POSTAL TEXT, TFD_CALLE TEXT, TFD_MUNICIPIO TEXT, TFD_ESTADO TEXT, TFD_TELEFONO TEXT, TFD_EMAIL TEXT, TFD_CNPJ TEXT, TFD_IE TEXT, TFD_NIT TEXT, TFD_CUIT TEXT, TFD_CONDICION_IVA TEXT, TFD_RUT TEXT, TFD_GIRO TEXT, TFD_COMUNA TEXT, TFD_CIUDAD TEXT, TFD_REGION TEXT, TFD_TIPO_PERSONA TEXT DEFAULT 'M', TFD_FECHA_REGISTRO TIMESTAMP DEFAULT NOW())",
        "CREATE TABLE IF NOT EXISTS FISCAL_DOCUMENTS (FD_ID SERIAL PRIMARY KEY, EMP_ID INTEGER NOT NULL REFERENCES EMPRESAS(EMP_ID), FD_DOCUMENT_ID TEXT, FD_DOCUMENT_TYPE TEXT DEFAULT 'FACTURA', FD_COUNTRY_CODE TEXT NOT NULL, FD_UUID TEXT, FD_SERIE TEXT, FD_NUMERO TEXT, FD_FECHA_EMISION TIMESTAMP DEFAULT NOW(), FD_MONEDA TEXT DEFAULT 'MXN', FD_SUBTOTAL REAL DEFAULT 0, FD_TOTAL REAL DEFAULT 0, FD_RECEPTOR_NOMBRE TEXT, FD_ESTATUS TEXT DEFAULT 'PENDIENTE', FD_FECHA_REGISTRO TIMESTAMP DEFAULT NOW())",
        "CREATE TABLE IF NOT EXISTS PAYMENT_METHODS_COUNTRY (PMC_ID SERIAL PRIMARY KEY, PMC_COUNTRY_CODE TEXT NOT NULL, PMC_METHOD_CODE TEXT NOT NULL, PMC_METHOD_NAME TEXT NOT NULL, PMC_PROVIDER TEXT, PMC_ACTIVO TEXT DEFAULT 'S', UNIQUE(PMC_COUNTRY_CODE, PMC_METHOD_CODE))",
        "CREATE INDEX IF NOT EXISTS IX_TFC_EMP ON TENANT_FISCAL_CONFIG(EMP_ID)",
        "CREATE INDEX IF NOT EXISTS IX_FD_EMP ON FISCAL_DOCUMENTS(EMP_ID)",
    ]
    results = []
    for s in stmts:
        try:
            execute(s)
            results.append({'status': 'OK', 'preview': s[:50]})
        except Exception as e:
            results.append({'status': 'ERROR', 'error': str(e)[:200], 'preview': s[:50]})

    pms = [
        ('MX','EFECTIVO','Efectivo',None),('MX','TARJETA','Tarjeta','stripe'),('MX','OXXO','OXXO','stripe'),('MX','MERCADOPAGO','MercadoPago','mercadopago'),
        ('BR','PIX','PIX','mercadopago'),('BR','BOLETO','Boleto','mercadopago'),('BR','CARTAO','Cartao','stripe'),
        ('CO','PSE','PSE','mercadopago'),('CO','NEQUI','Nequi',None),('CO','TARJETA','Tarjeta','stripe'),
        ('AR','MERCADOPAGO','MercadoPago','mercadopago'),('AR','TARJETA','Tarjeta','stripe'),('AR','EFECTIVO','Rapipago',None),
        ('CL','WEBPAY','Webpay','stripe'),('CL','TARJETA','Tarjeta','stripe'),
        ('PE','YAPE','Yape',None),('PE','PLIN','Plin',None),('PE','TARJETA','Tarjeta','stripe'),
        ('UY','MERCADOPAGO','MercadoPago','mercadopago'),('UY','TARJETA','Tarjeta','stripe'),
        ('EC','TARJETA','Tarjeta','stripe'),('EC','PICHINCHA','Pichincha',None),
    ]
    pm_ok = 0
    for pm in pms:
        try:
            execute("INSERT INTO PAYMENT_METHODS_COUNTRY (PMC_COUNTRY_CODE, PMC_METHOD_CODE, PMC_METHOD_NAME, PMC_PROVIDER) VALUES (?, ?, ?, ?) ON CONFLICT (PMC_COUNTRY_CODE, PMC_METHOD_CODE) DO NOTHING", list(pm))
            pm_ok += 1
        except Exception:
            pass

    log_audit('MIGRATION_RUN')
    return jsonify({'success': True, 'ddl_ok': sum(1 for r in results if r['status'] == 'OK'), 'payment_methods': pm_ok, 'details': results})


# ========================================
# MANTENIMIENTO (EDGAR data - simulado)
# ========================================
@app.route('/api/mantenimiento/unidades', methods=['GET'])
def get_unidades_mantto():
    return jsonify({'success': True, 'data': []})


@app.route('/api/mantenimiento/ots', methods=['GET'])
def get_ots_mantto():
    return jsonify({'success': True, 'data': []})


# ========================================
# AGENTES INTELIGENTES (AI)
# ========================================
route_optimizer = RouteOptimizer()
smart_assignment = SmartAssignment()
eta_predictor = ETAPredictor()
support_chatbot = SupportChatbot()
demand_forecaster = DemandForecaster()
dynamic_pricing = DynamicPricing()
fraud_detector = FraudDetector()
sentiment_analyzer = SentimentAnalyzer()


@app.route('/api/ai/route', methods=['POST'])
def ai_optimize_route():
    """Agente 1: Optimiza ruta para múltiples entregas"""
    data = request.json
    origin = data.get('origin', {})
    deliveries = data.get('deliveries', [])
    constraints = data.get('constraints', {})
    if not origin or not deliveries:
        return jsonify({'error': 'origin y deliveries requeridos'}), 400
    result = route_optimizer.optimize_route(origin, deliveries, constraints)
    return jsonify({'success': True, 'result': result})


@app.route('/api/ai/assign', methods=['POST'])
def ai_smart_assign():
    """Agente 2: Asigna pedido al chofer óptimo"""
    data = request.json
    order = data.get('order', {})
    drivers = data.get('drivers', [])
    if not order or not drivers:
        return jsonify({'error': 'order y drivers requeridos'}), 400
    result = smart_assignment.assign_order(order, drivers)
    return jsonify({'success': True, 'result': result})


@app.route('/api/ai/eta', methods=['POST'])
def ai_predict_eta():
    """Agente 3: Predice tiempo real de llegada"""
    data = request.json
    origin = data.get('origin', {})
    destination = data.get('destination', {})
    context = data.get('context', {})
    if not origin or not destination:
        return jsonify({'error': 'origin y destination requeridos'}), 400
    result = eta_predictor.predict_eta(origin, destination, context)
    return jsonify({'success': True, 'result': result})


@app.route('/api/ai/chat', methods=['POST'])
def ai_chatbot():
    """Agente 4: Chatbot de soporte 24/7"""
    data = request.json
    message = data.get('message', '')
    context = data.get('context', {})
    if not message:
        return jsonify({'error': 'message requerido'}), 400
    result = support_chatbot.get_response(message, context)
    return jsonify({'success': True, 'result': result})


@app.route('/api/ai/demand', methods=['POST'])
def ai_demand_forecast():
    """Agente 5: Predice volumen de pedidos"""
    data = request.json
    zone = data.get('zone', '')
    hours_ahead = data.get('hours_ahead', 24)
    if not zone:
        return jsonify({'error': 'zone requerido'}), 400
    # Use hourly prediction + recommendations
    hourly = demand_forecaster.predict_hourly_volume(zone)
    now = datetime.now()
    recommendations = demand_forecaster.get_recommendations(zone, now.hour)
    result = {'hourly_forecast': hourly, 'recommendations': recommendations}
    return jsonify({'success': True, 'result': result})


@app.route('/api/ai/pricing', methods=['POST'])
def ai_dynamic_pricing():
    """Agente 6: Calcula precio dinámico"""
    data = request.json
    order = data.get('order', {})
    demand_level = data.get('demand_level', 'medium')
    if not order:
        return jsonify({'error': 'order requerido'}), 400
    result = dynamic_pricing.calculate_price(order, demand_level)
    return jsonify({'success': True, 'result': result})


@app.route('/api/ai/fraud', methods=['POST'])
def ai_fraud_detect():
    """Agente 7: Detecta pedidos sospechosos"""
    data = request.json
    order = data.get('order', {})
    customer_history = data.get('customer_history', {})
    if not order:
        return jsonify({'error': 'order requerido'}), 400
    result = fraud_detector.analyze_order(order, customer_history)
    return jsonify({'success': True, 'result': result})


@app.route('/api/ai/sentiment', methods=['POST'])
def ai_sentiment():
    """Agente 8: Analiza sentimiento de feedback"""
    data = request.json
    text = data.get('text', '')
    if not text:
        return jsonify({'error': 'text requerido'}), 400
    result = sentiment_analyzer.analyze(text)
    return jsonify({'success': True, 'result': result})


# ========================================
# INICIAR SERVIDOR
# ========================================
if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    env = os.environ.get('FLASK_ENV', 'development')
    ssl_enabled = os.path.exists(os.path.join(DATA_DIR, 'cert.pem')) if 'DATA_DIR' in dir() else False
    db_info = get_db_info()

    print()
    print('  ========================================')
    print('  LAST MILE DELIVERY API v3.0.0')
    print('  ========================================')
    print(f'  Puerto:     {port}')
    print(f'  Entorno:    {env}')
    print(f'  Database:   {db_info["type"]} ({db_info.get("path", db_info.get("url", ""))})')
    print(f'  HTTPS:      {"ACTIVO" if ssl_enabled else "NO (HTTP)"}')
    print(f'  Rate Limit: 200/min general, 10/min auth')
    print(f'  CORS:       {"Restringido" if ALLOWED_ORIGINS != ["*"] else "ABIERTO"}')
    print(f'  Logs:       {LOG_DIR}')
    print('  ========================================')
    print()

    request_logger.info(f'Server starting on port {port} (env={env}, db={db_info["type"]})')

    if ssl_enabled:
        cert_path = os.path.join(DATA_DIR, 'cert.pem')
        key_path = os.path.join(DATA_DIR, 'key.pem')
        socketio.run(app, host='0.0.0.0', port=port, debug=False, ssl_context=(cert_path, key_path))
    else:
        socketio.run(app, host='0.0.0.0', port=port, debug=False)
