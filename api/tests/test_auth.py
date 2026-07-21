"""
TESTS DE AUTENTICACION REAL (JWT).
Ejecutar:  cd api && python -m pytest tests/test_auth.py -v

Usa el test_client de Flask en proceso (no requiere servidor vivo).
Verifica: login emite token, endpoint protegido rechaza sin token (401),
el IDOR por header X-Emp-Id ya no funciona, el IDOR por URL se bloquea (403),
y los endpoints admin/destructivos rechazan a los no-admin.
"""
import os
import sys

import pytest

# Asegura que 'api/' este en el path para importar server/auth.
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Los endpoints destructivos deben estar deshabilitados por defecto en tests.
os.environ.pop('ALLOW_SETUP', None)

from server import app          # noqa: E402
from auth import decode_token   # noqa: E402


@pytest.fixture(scope='module')
def client():
    app.config['TESTING'] = True
    from server import limiter
    limiter.enabled = False   # evita el rate-limit del login durante los tests
    return app.test_client()


def login(client, user, passwd):
    r = client.post('/api/auth/login', json={'user': user, 'pass': passwd})
    return r


def token_for(client, user, passwd):
    r = login(client, user, passwd)
    assert r.status_code == 200, r.get_data(as_text=True)
    return r.get_json()['token']


# ---------------------------------------------------------------- LOGIN

def test_login_devuelve_token(client):
    r = login(client, 'admin', 'admin123')
    assert r.status_code == 200
    body = r.get_json()
    assert body['success'] is True
    assert 'token' in body and body['token']
    payload = decode_token(body['token'])
    assert payload is not None
    assert payload['emp_id'] == 1
    assert payload['rol'] == 'admin'


def test_login_credenciales_malas_sin_token(client):
    r = login(client, 'admin', 'password-incorrecto')
    body = r.get_json()
    assert body['success'] is False
    assert 'token' not in body


# ---------------------------------------------------------- AUTH REQUERIDA

def test_endpoint_protegido_sin_token_401(client):
    r = client.get('/api/usuarios')
    assert r.status_code == 401


def test_endpoint_protegido_con_token_ok(client):
    tok = token_for(client, 'admin', 'admin123')
    r = client.get('/api/usuarios', headers={'Authorization': f'Bearer {tok}'})
    assert r.status_code == 200
    assert r.get_json()['success'] is True


def test_token_invalido_401(client):
    r = client.get('/api/usuarios', headers={'Authorization': 'Bearer no.es.un.token'})
    assert r.status_code == 401


# --------------------------------------------------- IDOR YA NO FUNCIONA

def test_header_x_emp_id_ignorado(client):
    """El tenant sale del token; el header X-Emp-Id spoofeado se ignora."""
    tok = token_for(client, 'operador', 'oper123')   # emp 1, rol operacion
    r = client.get('/api/usuarios', headers={
        'Authorization': f'Bearer {tok}',
        'X-Emp-Id': '2',      # intento de leer datos de la empresa 2
    })
    assert r.status_code == 200
    data = r.get_json()['data']
    # Todos los usuarios devueltos son de la empresa 1 (la del token), no la 2.
    assert all(u['USU_EMP_ID'] == 1 for u in data)


def test_idor_por_url_bloqueado(client):
    """Un no-admin no puede acceder a datos de otra empresa por la URL."""
    tok = token_for(client, 'operador', 'oper123')   # emp 1
    r = client.get('/api/dashboard/2', headers={'Authorization': f'Bearer {tok}'})
    assert r.status_code == 403


def test_acceso_a_su_propia_empresa_ok(client):
    tok = token_for(client, 'operador', 'oper123')   # emp 1
    r = client.get('/api/dashboard/1', headers={'Authorization': f'Bearer {tok}'})
    assert r.status_code == 200


# --------------------------------------------------------- SOLO ADMIN

def test_admin_only_rechaza_no_admin(client):
    tok = token_for(client, 'operador', 'oper123')   # rol operacion
    r = client.get('/api/admin/tenants-usage', headers={'Authorization': f'Bearer {tok}'})
    assert r.status_code == 403


def test_admin_only_permite_admin(client):
    tok = token_for(client, 'admin', 'admin123')     # rol admin
    r = client.get('/api/admin/tenants-usage', headers={'Authorization': f'Bearer {tok}'})
    # El admin pasa el control de acceso (no 401/403). El handler usa DATE_TRUNC
    # (sintaxis PostgreSQL) y devuelve 500 en SQLite: bug preexistente ajeno al auth.
    assert r.status_code not in (401, 403)


def test_saas_prefijo_rechaza_no_admin(client):
    tok = token_for(client, 'operador', 'oper123')
    r = client.get('/api/saas/tenants', headers={'Authorization': f'Bearer {tok}'})
    assert r.status_code == 403


# ----------------------------------------------- DESTRUCTIVO (SETUP)

def test_setup_destructivo_bloqueado_sin_allow_setup(client):
    """DROP TABLE via /api/setup/* debe fallar aunque seas admin, si ALLOW_SETUP no esta activo."""
    tok = token_for(client, 'admin', 'admin123')
    r = client.post('/api/setup/usuarios', headers={'Authorization': f'Bearer {tok}'})
    assert r.status_code == 403


def test_setup_destructivo_sin_token_401(client):
    r = client.post('/api/setup/usuarios')
    assert r.status_code == 401


# ------------------------------------------------------------ PUBLICOS

def test_health_publico(client):
    assert client.get('/api/health').status_code == 200


def test_planes_publico(client):
    # El catalogo de planes es publico (landing / registro).
    assert client.get('/api/saas/planes').status_code == 200
