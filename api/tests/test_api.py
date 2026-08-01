"""
TEST SUITE - Last Mile Delivery System (Integration Tests)
Ejecutar: pytest tests/test_api.py -v

Usa Flask test client (no requiere servidor corriendo).
"""
import pytest
import sys
import os

# Add parent directory to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from server import app
from db import init_schema, check_empty
from seed import seed

@pytest.fixture(scope='module')
def client():
    """Create test client and initialize DB."""
    app.config['TESTING'] = True
    app.config['DATABASE_URL'] = ''  # Force SQLite for tests
    
    with app.test_client() as client:
        # Initialize schema if needed
        try:
            init_schema()
            if check_empty():
                seed()
        except Exception:
            pass
        yield client


def login(client, user='admin', password='admin123'):
    """Login and return token."""
    r = client.post('/api/auth/login', json={'user': user, 'pass': password})
    data = r.get_json()
    return data.get('token', '')


def auth_headers(token):
    """Create auth headers with token."""
    return {'Authorization': f'Bearer {token}', 'Content-Type': 'application/json'}


# ========================================
# HEALTH
# ========================================
class TestHealth:
    def test_health_ok(self, client):
        r = client.get('/api/health')
        assert r.status_code == 200
        j = r.get_json()
        assert j['status'] in ('OK', 'DEGRADED')
        assert 'timestamp' in j


# ========================================
# AUTH
# ========================================
class TestAuth:
    def test_login_admin(self, client):
        r = client.post('/api/auth/login', json={'user': 'admin', 'pass': 'admin123'})
        assert r.status_code == 200
        j = r.get_json()
        assert 'token' in j
        assert j['rol'] == 'admin'

    def test_login_bad_credentials(self, client):
        r = client.post('/api/auth/login', json={'user': 'admin', 'pass': 'wrong'})
        assert r.status_code == 200
        j = r.get_json()
        assert 'token' not in j or j.get('token') is None

    def test_login_empty_fields(self, client):
        r = client.post('/api/auth/login', json={'user': '', 'pass': ''})
        assert r.status_code == 200
        j = r.get_json()
        assert 'token' not in j or j.get('token') is None

    def test_protected_without_token(self, client):
        r = client.get('/api/pedidos')
        assert r.status_code == 401

    def test_protected_with_token(self, client):
        token = login(client)
        r = client.get('/api/pedidos', headers=auth_headers(token))
        assert r.status_code == 200

    def test_invalid_token(self, client):
        r = client.get('/api/pedidos', headers={'Authorization': 'Bearer invalid_token'})
        assert r.status_code == 401


# ========================================
# MULTI-TENANT
# ========================================
class TestMultiTenant:
    def test_data_isolation(self, client):
        token1 = login(client, 'admin', 'admin123')
        token2 = login(client, 'admin2', 'admin123')
        
        r1 = client.get('/api/pedidos', headers=auth_headers(token1))
        r2 = client.get('/api/pedidos', headers=auth_headers(token2))
        
        assert r1.status_code == 200
        assert r2.status_code == 200
        
        data1 = r1.get_json().get('data', [])
        data2 = r2.get_json().get('data', [])
        
        # Different tenants should have different data
        emp_ids_1 = set(p.get('EMP_ID') for p in data1 if p.get('EMP_ID'))
        emp_ids_2 = set(p.get('EMP_ID') for p in data2 if p.get('EMP_ID'))
        
        # Each should only see their own tenant
        if emp_ids_1:
            assert all(eid == 1 for eid in emp_ids_1)
        if emp_ids_2:
            assert all(eid == 2 for eid in emp_ids_2)


# ========================================
# ZONAS CRUD
# ========================================
class TestZonasCRUD:
    def test_get_zonas(self, client):
        token = login(client)
        r = client.get('/api/zonas', headers=auth_headers(token))
        assert r.status_code == 200
        assert r.get_json().get('success') is True

    def test_create_zona(self, client):
        token = login(client)
        r = client.post('/api/zonas', headers=auth_headers(token), json={
            'nombre': 'Zona Test',
            'descripcion': 'Zona de prueba',
            'coordenadas': '19.4,-99.1'
        })
        assert r.status_code == 200
        assert r.get_json().get('success') is True

    def test_update_zona(self, client):
        token = login(client)
        # Get first zona
        r = client.get('/api/zonas', headers=auth_headers(token))
        zonas = r.get_json().get('data', [])
        if zonas:
            zon_id = zonas[0].get('ZON_ID')
            r = client.put(f'/api/zonas/{zon_id}', headers=auth_headers(token), json={
                'nombre': 'Zona Actualizada'
            })
            assert r.status_code == 200


# ========================================
# COTIZAR
# ========================================
class TestCotizar:
    def test_cotizar_envio(self, client):
        token = login(client)
        r = client.post('/api/zonas/cotizar', headers=auth_headers(token), json={
            'origen': '19.4326,-99.1332',
            'destino': '19.4500,-99.1500',
            'peso': 5,
            'bultos': 1
        })
        assert r.status_code == 200


# ========================================
# PEDIDOS
# ========================================
class TestPedidos:
    def test_create_pedido(self, client):
        token = login(client)
        r = client.post('/api/pedidos', headers=auth_headers(token), json={
            'pedNumero': 'PED-TEST-001',
            'clienteNombre': 'Cliente Test',
            'clienteTelefono': '5551234567',
            'destinoDir': 'Calle Test 123',
            'destinoCol': 'Colonia Test',
            'destinoCiudad': 'CDMX',
            'pesoKg': 2.5,
            'bultos': 1,
            'costoTotal': 150.00,
            'formaPago': 'EFECTIVO',
            'prioridad': 'NORMAL'
        })
        assert r.status_code == 200
        assert r.get_json().get('success') is True

    def test_update_pedido_estado(self, client):
        token = login(client)
        # Get first pedido
        r = client.get('/api/pedidos', headers=auth_headers(token))
        pedidos = r.get_json().get('data', [])
        if pedidos:
            ped_id = pedidos[0].get('PED_ID')
            r = client.put(f'/api/pedidos/{ped_id}/estado', headers=auth_headers(token), json={
                'estado': 'ASIGNADO'
            })
            assert r.status_code == 200


# ========================================
# EDGE CASES
# ========================================
class TestEdgeCases:
    def test_get_nonexistent_pedido(self, client):
        token = login(client)
        r = client.get('/api/pedidos/99999', headers=auth_headers(token))
        # Should return 200 with null data or 404
        assert r.status_code in (200, 404)

    def test_delete_nonexistent_chofer(self, client):
        token = login(client)
        r = client.delete('/api/choferes/99999', headers=auth_headers(token))
        # Should not crash
        assert r.status_code in (200, 404, 500)

    def test_large_limit_capped(self, client):
        token = login(client)
        r = client.get('/api/pedidos?limite=99999', headers=auth_headers(token))
        assert r.status_code == 200
        j = r.get_json()
        assert len(j.get('data', [])) <= 500

    def test_unauthorized_saas_endpoint(self, client):
        token = login(client, 'admin', 'admin123')  # regular admin
        r = client.get('/api/saas/tenants', headers=auth_headers(token))
        assert r.status_code == 403

    def test_health_public(self, client):
        r = client.get('/api/health')
        assert r.status_code == 200
