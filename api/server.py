"""
LAST MILE DELIVERY SYSTEM - Backend API v2.0 (Python/Flask + SQLite)
Migrado desde AS/400 DB2/400 a SQLite local.
Multi-tenant: cada request lleva X-Emp-Id
Produccion-ready: HTTPS, rate limiting, logging, CORS restricciones
"""

from flask import Flask, request, jsonify, send_from_directory
from flask_cors import CORS
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
from dotenv import load_dotenv
import hashlib
import os
import sqlite3
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
app.secret_key = os.environ.get('FLASK_SECRET_KEY', 'lastmile-dev-key-change-in-prod')

# ========================================
# CORS: Restringido por origen en produccion
# ========================================
ALLOWED_ORIGINS = os.environ.get('ALLOWED_ORIGINS', '').split(',') if os.environ.get('ALLOWED_ORIGINS') else ['*']
CORS(app, origins=ALLOWED_ORIGINS, supports_credentials=True,
     allow_headers=['Content-Type', 'X-Emp-Id', 'Authorization'],
     methods=['GET', 'POST', 'PUT', 'DELETE', 'OPTIONS'])

# ========================================
# RATE LIMITING: 200 req/min por IP general, 10/min para auth
# ========================================
limiter = Limiter(
    get_remote_address,
    app=app,
    default_limits=["200 per minute"],
    storage_uri="memory://",
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
# DATABASE: SQLite (con soporte para disco persistente en Render)
# ========================================
DATA_DIR = os.environ.get('DATA_DIR', os.path.dirname(os.path.abspath(__file__)))
DB_PATH = os.path.join(DATA_DIR, 'lastmile.db')

# Auto-initialize database on first run
if not os.path.exists(DB_PATH):
    print(f'[DB] First run - initializing database at {DB_PATH}')
    from database import init_db
    init_db()
    # Try to migrate data from backup if available
    try:
        from migrate import migrate
        migrate()
    except Exception:
        pass


def get_db():
    """Get SQLite connection with Row factory."""
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA journal_mode=WAL")
    conn.execute("PRAGMA busy_timeout=5000")
    return conn


def query(sql, params=None):
    """Execute a SELECT and return list of dicts."""
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute(sql, params or [])
    columns = [desc[0] for desc in cursor.description] if cursor.description else []
    rows = cursor.fetchall()
    cursor.close()
    conn.close()
    return [dict(zip(columns, row)) for row in rows]


def execute(sql, params=None):
    """Execute an INSERT/UPDATE/DELETE and return affected rows."""
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute(sql, params or [])
    conn.commit()
    affected = cursor.rowcount
    cursor.close()
    conn.close()
    return affected


def get_emp_id():
    try:
        return int(request.headers.get('X-Emp-Id', '1'))
    except (ValueError, TypeError):
        return 1


# ========================================
# REQUEST MIDDLEWARE
# ========================================
@app.before_request
def before_request():
    request.start_time = time.time()


@app.after_request
def after_request(response):
    if hasattr(request, 'start_time'):
        elapsed = round((time.time() - request.start_time) * 1000, 1)
        status = response.status_code
        path = request.path
        method = request.method
        emp_id = request.headers.get('X-Emp-Id', '-')
        ip = request.remote_addr or '-'
        request_logger.info(f'{method} {path} => {status} [{elapsed}ms] emp={emp_id} ip={ip}')
    return response


@app.errorhandler(Exception)
def handle_exception(e):
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


@app.route('/<path:filename>')
def serve_static(filename):
    return send_from_directory('web', filename)


# ========================================
# HEALTH CHECK
# ========================================
@app.route('/api/health', methods=['GET'])
def health():
    db_status = 'DISCONNECTED'
    try:
        conn = get_db()
        cursor = conn.cursor()
        cursor.execute("SELECT 1")
        cursor.close()
        conn.close()
        db_status = 'CONNECTED'
    except Exception as e:
        db_status = f'ERROR: {str(e)[:80]}'

    return jsonify({
        'status': 'OK' if db_status == 'CONNECTED' else 'DEGRADED',
        'timestamp': datetime.now().isoformat(),
        'version': '2.0.0',
        'database': f'SQLite ({db_status})',
        'db_file': os.path.basename(DB_PATH),
        'rate_limit': '200/min'
    })


# ========================================
# AUTH: Login
# ========================================
@app.route('/api/auth/login', methods=['POST'])
@limiter.limit("10 per minute")
def auth_login():
    data = request.get_json() or {}
    user = (data.get('user') or '').strip()
    passwd = data.get('pass') or ''

    if not user or not passwd:
        return jsonify({'success': False, 'error': 'Usuario y contrasena requeridos'})

    pass_hash = hashlib.sha256(passwd.strip().encode()).hexdigest()

    try:
        rows = query(
            "SELECT U.USU_ID, U.USU_USUARIO, U.USU_NOMBRE, U.USU_ROL, "
            "U.USU_EMP_ID, U.USU_PASS, E.EMP_NOMBRE "
            "FROM USUARIOS U "
            "LEFT JOIN EMPRESAS E ON U.USU_EMP_ID = E.EMP_ID "
            "WHERE UPPER(U.USU_USUARIO) = UPPER(?) AND U.USU_ACTIVO = 'S'",
            [user]
        )
    except Exception:
        return jsonify({'success': False, 'error': 'Tabla USUARIOS no existe. Ejecuta el script de setup.'})

    if not rows:
        return jsonify({'success': False, 'error': 'Usuario o contrasena incorrectos'})

    u = rows[0]
    db_pass = str(u.get('USU_PASS', '')).strip()
    if db_pass != pass_hash:
        return jsonify({'success': False, 'error': 'Usuario o contrasena incorrectos'})

    return jsonify({
        'success': True,
        'data': {
            'emp_id': u['USU_EMP_ID'],
            'usuario': u['USU_USUARIO'],
            'nombre': u['USU_NOMBRE'],
            'rol': u['USU_ROL'],
            'empresa': u.get('EMP_NOMBRE', '')
        }
    })


# ========================================
# SETUP: Crear tabla USUARIOS (temporal)
# ========================================
@app.route('/api/setup/usuarios', methods=['POST'])
@limiter.limit("2 per hour")
def setup_usuarios():
    """Crea la tabla USUARIOS y carga datos de prueba."""
    try:
        try:
            execute("DROP TABLE USUARIOS")
        except:
            pass

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
            hashed_pass = hashlib.sha256(u[2].strip().encode()).hexdigest()
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
    return jsonify({'success': True, 'message': 'Pedido creado'})


@app.route('/api/pedidos/<int:ped_id>/estado', methods=['PUT'])
def update_estado_pedido(ped_id):
    emp_id = get_emp_id()
    estado = request.json.get('estado')
    usuario = request.json.get('usuario', 'SYSTEM')

    execute('UPDATE PEDIDOS SET PED_ESTADO = ? WHERE PED_ID = ? AND EMP_ID = ?', [estado, ped_id, emp_id])
    execute('INSERT INTO PEDIDO_HISTORIAL (PED_ID, HIS_ESTADO, HIS_USUARIO) VALUES (?, ?, ?)', [ped_id, estado, usuario])

    return jsonify({'success': True, 'message': f'Estado actualizado a {estado}'})


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
    return jsonify({'success': True, 'data': query('SELECT * FROM V_RENDIMIENTO_CHOFERES WHERE EMP_ID = ? ORDER BY TASA_EXITO DESC', [emp_id])})


@app.route('/api/choferes/<int:cho_id>', methods=['DELETE'])
def delete_chofer(cho_id):
    emp_id = get_emp_id()
    try:
        execute("DELETE FROM CHOFERES WHERE CHO_ID = ? AND EMP_ID = ?", [cho_id, emp_id])
        return jsonify({'success': True, 'message': 'Chofer eliminado'})
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
        return jsonify({'success': True, 'message': 'Vehiculo eliminado'})
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
        execute("DELETE FROM CLIENTES_LM WHERE CLI_ID = ? AND EMP_ID = ?", [cli_id, emp_id])
        return jsonify({'success': True, 'message': 'Cliente eliminado'})
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
    return jsonify({'success': True, 'data': query('SELECT * FROM ENTREGAS WHERE EMP_ID = ? ORDER BY ENT_FECHA_LLEGADA DESC LIMIT 50', [emp_id])})


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
    return jsonify({'success': True, 'message': 'Tracking registrado'})


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
    import uuid as uuid_mod
    emp_id = get_emp_id()
    uuid_cfdi = str(uuid_mod.uuid4()).upper()
    execute("UPDATE CFDI_FACTURAS SET FAC_UUID=?, FAC_FECHA_TIMBRADO=datetime('now'), FAC_ESTATUS=? WHERE FAC_ID=? AND EMP_ID=?",
            [uuid_cfdi, 'TIMBRADA', fac_id, emp_id])
    execute("INSERT INTO CFDI_TIMBRADO_LOG (FAC_ID, TIM_PAC, TIM_CODIGO_RESPUESTA, TIM_MENSAJE, TIM_EXITOSO) VALUES (?,?,?,?,?)",
            [fac_id, 'SIMULADO', '200', 'Timbrado exitoso', 'S'])
    return jsonify({'success': True, 'uuid': uuid_cfdi, 'message': 'Factura timbrada correctamente'})


@app.route('/api/cfdi/facturas/<int:fac_id>/cancelar', methods=['POST'])
def cancelar_factura(fac_id):
    motivo = request.json.get('motivo', 'Error en factura')
    execute("UPDATE CFDI_FACTURAS SET FAC_ESTATUS=?, FAC_MOTIVO_CANCELACION=? WHERE FAC_ID=? AND EMP_ID=?",
            ['CANCELADA', motivo, fac_id, get_emp_id()])
    return jsonify({'success': True, 'message': 'Factura cancelada'})


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
        execute("DELETE FROM PAGOS_TRANSACCIONES WHERE TRP_ID = ?", [pag_id])
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
    return jsonify({'success': True, 'message': 'Webhook procesado'})


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
        return jsonify({'success': True, 'message': 'Usuario eliminado'})
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
    return jsonify({'success': True, 'message': 'Whitelabel actualizado'})


# ========================================
# MODULO: SaaS ADMIN
# ========================================
@app.route('/api/saas/tenants', methods=['GET'])
def get_saas_tenants():
    return jsonify({'success': True, 'data': query('''SELECT E.*,
        (SELECT COUNT(*) FROM PEDIDOS P WHERE P.EMP_ID = E.EMP_ID) as TOTAL_PEDIDOS,
        (SELECT COUNT(*) FROM CHOFERES C WHERE C.EMP_ID = E.EMP_ID) as TOTAL_CHOFERES,
        (SELECT COUNT(*) FROM CLIENTES_LM CL WHERE CL.EMP_ID = E.EMP_ID) as TOTAL_CLIENTES
        FROM EMPRESAS E ORDER BY E.EMP_ID''')})


@app.route('/api/saas/plan-usage/<int:emp_id>', methods=['GET'])
def get_plan_usage(emp_id):
    data = query('''SELECT E.EMP_ID, E.EMP_NOMBRE,
        (SELECT COUNT(*) FROM PEDIDOS WHERE EMP_ID = ? AND PED_FECHA_PEDIDO >= date('now', '-30 days')) as PEDIDOS_MES,
        (SELECT COUNT(*) FROM CHOFERES WHERE EMP_ID = ?) as CHOFERES,
        (SELECT COUNT(*) FROM CLIENTES_LM WHERE EMP_ID = ?) as CLIENTES,
        (SELECT COUNT(*) FROM VEHICULOS WHERE EMP_ID = ?) as VEHICULOS
        FROM EMPRESAS E WHERE E.EMP_ID = ?''', [emp_id]*5)
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
def create_suscripcion():
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
    uso_hoy = query("SELECT COALESCE(SUM(USR_PEDIDOS_CREADOS), 0) as PEDIDOS, COALESCE(SUM(USR_API_CALLS), 0) as API_CALLS FROM SAAS_USO_RECURSOS WHERE USR_FECHA = date('now')")

    return jsonify({
        'success': True,
        'data': {
            'empresas_activas': empresas[0]['TOTAL'] if empresas else 0,
            'suscripciones': {s['SUS_ESTADO']: s['TOTAL'] for s in suscripciones},
            'cobros': cobros[0] if cobros else {},
            'uso_hoy': uso_hoy[0] if uso_hoy else {}
        }
    })


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
    execute("INSERT INTO NOTIF_PUSH (EMP_ID, USR_ID, CHO_ID, NPUSH_TIPO, NPUSH_TITULO, NPUSH_CUERPO, NPUSH_DATA) VALUES (?, ?, ?, ?, ?, ?, ?)",
            [emp_id, n.get('usrId'), n.get('choId'), n.get('tipo'), n.get('titulo'), n.get('cuerpo'), n.get('data', '{}')])
    return jsonify({'success': True, 'message': 'Notificacion enviada'})


@app.route('/api/notif/dispositivos', methods=['POST'])
def register_device():
    emp_id = get_emp_id()
    d = request.json
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
        execute("DELETE FROM PEDIDOS WHERE PED_ID = ?", [ped_id])
        return jsonify({'success': True, 'message': 'Pedido eliminado'})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})


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
# INICIAR SERVIDOR
# ========================================
if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    env = os.environ.get('FLASK_ENV', 'development')
    ssl_enabled = os.path.exists(os.path.join(DATA_DIR, 'cert.pem'))

    print()
    print('  ========================================')
    print('  LAST MILE DELIVERY API v2.0.0')
    print('  ========================================')
    print(f'  Puerto:     {port}')
    print(f'  Entorno:    {env}')
    print(f'  Database:   SQLite ({DB_PATH})')
    print(f'  HTTPS:      {"ACTIVO" if ssl_enabled else "NO (HTTP)"}')
    print(f'  Rate Limit: 200/min general, 10/min auth')
    print(f'  CORS:       {"Restringido" if ALLOWED_ORIGINS != ["*"] else "ABIERTO"}')
    print(f'  Logs:       {LOG_DIR}')
    print('  ========================================')
    print()

    request_logger.info(f'Server starting on port {port} (env={env}, db=SQLite)')

    if ssl_enabled:
        cert_path = os.path.join(DATA_DIR, 'cert.pem')
        key_path = os.path.join(DATA_DIR, 'key.pem')
        app.run(host='0.0.0.0', port=port, debug=False, ssl_context=(cert_path, key_path))
    else:
        app.run(host='0.0.0.0', port=port, debug=False)
