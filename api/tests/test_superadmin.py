"""
TESTS DE SEPARACIÓN SUPERADMIN vs ADMIN.
Ejecutar:  cd api && python -m pytest tests/test_superadmin.py -v

Verifica que la gestión GLOBAL de tenants (/api/saas/*, /api/admin/*) es
exclusiva del rol 'superadmin' (operador de la plataforma), y que el 'admin'
de un tenant cliente queda limitado a SU propio tenant.
"""
import os
import sys

import pytest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
os.environ.pop('ALLOW_SETUP', None)


@pytest.fixture(scope='module')
def client():
    from server import app, limiter
    from create_superadmin import create_or_update_superadmin
    app.config['TESTING'] = True
    limiter.enabled = False
    # Bootstrap del superadmin por comando administrativo (no por HTTP).
    create_or_update_superadmin('superadmin', 'super123')
    return app.test_client()


def _token(client, user, pw):
    r = client.post('/api/auth/login', json={'user': user, 'pass': pw})
    assert r.status_code == 200, r.get_data(as_text=True)
    return r.get_json()['token']


def _auth(tok):
    return {'Authorization': f'Bearer {tok}'}


# ---------------------------------------- ADMIN DE TENANT: BLOQUEADO EN LO GLOBAL

def test_admin_no_puede_listar_tenants(client):
    tok = _token(client, 'admin', 'admin123')          # admin de un tenant cliente
    assert client.get('/api/saas/tenants', headers=_auth(tok)).status_code == 403


def test_admin_no_puede_crear_tenant(client):
    tok = _token(client, 'admin', 'admin123')
    r = client.post('/api/saas/tenants', headers=_auth(tok), json={'nombre': 'Hackeada'})
    assert r.status_code == 403


def test_admin_no_puede_suspender_otro_tenant(client):
    tok = _token(client, 'admin', 'admin123')          # admin de emp 1
    r = client.post('/api/saas/tenants/2/suspend', headers=_auth(tok))
    assert r.status_code == 403


def test_admin_no_puede_ver_ingresos_globales(client):
    tok = _token(client, 'admin', 'admin123')
    assert client.get('/api/admin/tenants-usage', headers=_auth(tok)).status_code == 403


def test_operacion_tampoco_puede_gestion_global(client):
    tok = _token(client, 'operador', 'oper123')
    assert client.get('/api/saas/tenants', headers=_auth(tok)).status_code == 403


# ---------------------------------------- SUPERADMIN: SÍ PUEDE

def test_superadmin_lista_tenants(client):
    tok = _token(client, 'superadmin', 'super123')
    r = client.get('/api/saas/tenants', headers=_auth(tok))
    assert r.status_code == 200
    assert r.get_json()['success'] is True


def test_superadmin_pasa_control_admin_global(client):
    tok = _token(client, 'superadmin', 'super123')
    r = client.get('/api/admin/tenants-usage', headers=_auth(tok))
    # Pasa el control de acceso (no 401/403). El handler usa DATE_TRUNC de PostgreSQL
    # y devuelve 500 en SQLite: bug preexistente ajeno a la autorizacion.
    assert r.status_code not in (401, 403)


def test_superadmin_puede_suspender_tenant(client):
    tok = _token(client, 'superadmin', 'super123')
    r = client.post('/api/saas/tenants/2/suspend', headers=_auth(tok))
    assert r.status_code not in (401, 403)
    # Reactiva para no dejar el tenant 2 suspendido para otros tests.
    client.post('/api/saas/tenants/2/activate', headers=_auth(tok))


# ---------------------------------------- ADMIN SIGUE GESTIONANDO SU PROPIO TENANT

def test_admin_gestiona_usuarios_de_su_tenant(client):
    tok = _token(client, 'admin', 'admin123')          # emp 1
    r = client.get('/api/usuarios', headers=_auth(tok))
    assert r.status_code == 200
    assert r.get_json()['success'] is True


def test_admin_ve_su_propio_dashboard(client):
    tok = _token(client, 'admin', 'admin123')          # emp 1
    assert client.get('/api/dashboard/1', headers=_auth(tok)).status_code == 200


def test_admin_no_ve_dashboard_de_otro_tenant(client):
    tok = _token(client, 'admin', 'admin123')          # emp 1
    assert client.get('/api/dashboard/2', headers=_auth(tok)).status_code == 403
