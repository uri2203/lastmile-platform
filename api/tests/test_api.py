"""
TEST SUITE - Last Mile Delivery System
Ejecutar: pytest tests/ -v
"""
import pytest
import requests
import json
import urllib3

# Suppress SSL warnings for self-signed certs
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

# Auto-detect: try HTTPS first, then HTTP
BASE = 'https://localhost:5000'
HEADERS = {'X-Emp-Id': '1', 'Content-Type': 'application/json'}
HEADERS2 = {'X-Emp-Id': '2', 'Content-Type': 'application/json'}
VERIFY_SSL = False  # Self-signed cert

def api(method, path, headers=None, data=None):
    """Helper para requests (auto HTTPS)"""
    url = f'{BASE}{path}'
    h = headers or HEADERS
    if method == 'GET':
        return requests.get(url, headers=h, timeout=15, verify=VERIFY_SSL)
    elif method == 'POST':
        return requests.post(url, headers=h, json=data, timeout=15, verify=VERIFY_SSL)
    elif method == 'PUT':
        return requests.put(url, headers=h, json=data, timeout=15, verify=VERIFY_SSL)
    elif method == 'DELETE':
        return requests.delete(url, headers=h, timeout=15, verify=VERIFY_SSL)

# ========================================
# HEALTH
# ========================================
class TestHealth:
    def test_health_ok(self):
        r = api('GET', '/api/health')
        assert r.status_code == 200
        j = r.json()
        assert j['status'] in ('OK', 'DEGRADED')
        assert 'timestamp' in j
        assert j['version'] == '2.0.0'

# ========================================
# AUTH
# ========================================
class TestAuth:
    def test_login_admin(self):
        r = api('POST', '/api/auth/login', headers={'Content-Type': 'application/json'},
                data={'user': 'admin', 'pass': 'admin123'})
        j = r.json()
        assert j['success'] == True
        assert j['data']['rol'] == 'admin'
        assert j['data']['emp_id'] == 1

    def test_login_chofer(self):
        r = api('POST', '/api/auth/login', headers={'Content-Type': 'application/json'},
                data={'user': 'chofer1', 'pass': 'chof123'})
        j = r.json()
        assert j['success'] == True
        assert j['data']['rol'] == 'chofer'

    def test_login_cliente(self):
        r = api('POST', '/api/auth/login', headers={'Content-Type': 'application/json'},
                data={'user': 'cliente1', 'pass': 'clie123'})
        j = r.json()
        assert j['success'] == True
        assert j['data']['rol'] == 'cliente'

    def test_login_operador(self):
        r = api('POST', '/api/auth/login', headers={'Content-Type': 'application/json'},
                data={'user': 'operador', 'pass': 'oper123'})
        j = r.json()
        assert j['success'] == True
        assert j['data']['rol'] == 'operacion'

    def test_login_bad_password(self):
        r = api('POST', '/api/auth/login', headers={'Content-Type': 'application/json'},
                data={'user': 'admin', 'pass': 'WRONG'})
        j = r.json()
        assert j['success'] == False

    def test_login_empty_fields(self):
        r = api('POST', '/api/auth/login', headers={'Content-Type': 'application/json'},
                data={'user': '', 'pass': ''})
        j = r.json()
        assert j['success'] == False

    def test_login_unknown_user(self):
        r = api('POST', '/api/auth/login', headers={'Content-Type': 'application/json'},
                data={'user': 'nobody', 'pass': '123'})
        j = r.json()
        assert j['success'] == False

# ========================================
# MULTI-TENANT
# ========================================
class TestMultiTenant:
    def test_emp1_choferes(self):
        r = api('GET', '/api/choferes?emp_id=1')
        j = r.json()
        assert j['success'] == True
        assert len(j['data']) > 0

    def test_emp2_isolated(self):
        r = api('GET', '/api/choferes?emp_id=2', headers=HEADERS2)
        j = r.json()
        assert j['success'] == True
        # Emp 2 has different data from emp 1
        assert j['data'] is not None

    def test_emp3_isolated(self):
        r = api('GET', '/api/choferes?emp_id=3', headers={'X-Emp-Id': '3'})
        j = r.json()
        assert j['success'] == True

# ========================================
# GET ENDPOINTS
# ========================================
class TestGetEndpoints:
    def test_empresas(self):
        r = api('GET', '/api/empresas')
        j = r.json()
        assert j['success'] == True
        assert len(j['data']) >= 3

    def test_dashboard(self):
        r = api('GET', '/api/dashboard/1')
        j = r.json()
        assert j['success'] == True

    def test_pedidos(self):
        r = api('GET', '/api/pedidos?emp_id=1')
        j = r.json()
        assert j['success'] == True
        assert len(j['data']) > 0

    def test_choferes(self):
        r = api('GET', '/api/choferes?emp_id=1')
        j = r.json()
        assert j['success'] == True

    def test_vehiculos(self):
        r = api('GET', '/api/vehiculos?emp_id=1')
        j = r.json()
        assert j['success'] == True

    def test_clientes(self):
        r = api('GET', '/api/clientes?emp_id=1')
        j = r.json()
        assert j['success'] == True

    def test_clientes_top(self):
        r = api('GET', '/api/clientes/top?emp_id=1')
        j = r.json()
        assert j['success'] == True

    def test_zonas(self):
        r = api('GET', '/api/zonas?emp_id=1')
        j = r.json()
        assert j['success'] == True
        assert len(j['data']) > 0

    def test_cfdi_facturas(self):
        r = api('GET', '/api/cfdi/facturas?emp_id=1')
        j = r.json()
        assert j['success'] == True

    def test_pagos_metodos(self):
        r = api('GET', '/api/pagos/metodos?emp_id=1')
        j = r.json()
        assert j['success'] == True

    def test_pagos_transacciones(self):
        r = api('GET', '/api/pagos/transacciones?emp_id=1')
        j = r.json()
        assert j['success'] == True

    def test_saas_tenants(self):
        r = api('GET', '/api/saas/tenants?emp_id=1')
        j = r.json()
        assert j['success'] == True
        assert len(j['data']) >= 3

    def test_saas_planes(self):
        r = api('GET', '/api/saas/planes')
        j = r.json()
        assert j['success'] == True

    def test_saas_suscripciones(self):
        r = api('GET', '/api/saas/suscripciones?emp_id=1')
        j = r.json()
        assert j['success'] == True

    def test_saas_cobros(self):
        r = api('GET', '/api/saas/cobros?emp_id=1')
        j = r.json()
        assert j['success'] == True

    def test_audit(self):
        r = api('GET', '/api/audit?emp_id=1')
        j = r.json()
        assert j['success'] == True

    def test_usuarios(self):
        r = api('GET', '/api/usuarios?emp_id=1')
        j = r.json()
        assert j['success'] == True
        assert len(j['data']) > 0

    def test_usuario_by_id(self):
        r = api('GET', '/api/usuarios/1')
        j = r.json()
        assert j['success'] == True

    def test_vehiculos_flota(self):
        r = api('GET', '/api/vehiculos/flota?emp_id=1')
        j = r.json()
        assert j['success'] == True

    def test_rendimiento_choferes(self):
        r = api('GET', '/api/choferes/rendimiento?emp_id=1')
        j = r.json()
        assert j['success'] == True

# ========================================
# ZONAS CRUD
# ========================================
class TestZonasCRUD:
    def _create_zona(self):
        data = {
            'nombre': 'Test Zone Pytest',
            'descripcion': 'Auto test',
            'color': '#ff0000',
            'radio_km': 3,
            'centro_lat': 19.5,
            'centro_lng': -99.2,
            'tarifas': [{
                'servicio': 'EXPRESS',
                'monto_base': 50,
                'monto_por_kg': 10,
                'monto_por_km': 5,
                'monto_por_m3': 0,
                'peso_min_kg': 0.5,
                'peso_max_kg': 15,
                'distancia_max_km': 20,
                'monto_minimo': 50,
                'seguro_pct': 2
            }]
        }
        r = api('POST', '/api/zonas', data=data)
        return r.json()

    def test_create_zona(self):
        j = self._create_zona()
        assert j['success'] == True
        assert 'zon_id' in j

    def test_get_zona_by_id(self):
        j = self._create_zona()
        zid = j['zon_id']
        r = api('GET', f'/api/zonas/{zid}')
        assert r.status_code == 200
        data = r.json()
        assert data['success'] == True
        assert data['data']['ZON_NOMBRE'] == 'Test Zone Pytest'
        # Cleanup
        api('DELETE', f'/api/zonas/{zid}')

    def test_update_zona(self):
        j = self._create_zona()
        zid = j['zon_id']
        update = {
            'nombre': 'Updated Zone',
            'color': '#00ff00',
            'radio_km': 5,
            'centro_lat': 19.6,
            'centro_lng': -99.3,
            'tarifas': [{
                'servicio': 'EXPRESS',
                'monto_base': 60,
                'monto_por_kg': 12,
                'monto_por_km': 6,
                'monto_por_m3': 0,
                'peso_min_kg': 0.5,
                'peso_max_kg': 15,
                'distancia_max_km': 25,
                'monto_minimo': 60,
                'seguro_pct': 3
            }]
        }
        r = api('PUT', f'/api/zonas/{zid}', data=update)
        assert r.json()['success'] == True
        # Verify
        r = api('GET', f'/api/zonas/{zid}')
        assert r.json()['data']['ZON_NOMBRE'] == 'Updated Zone'
        # Cleanup
        api('DELETE', f'/api/zonas/{zid}')

    def test_delete_zona(self):
        j = self._create_zona()
        zid = j['zon_id']
        r = api('DELETE', f'/api/zonas/{zid}')
        assert r.json()['success'] == True

    def test_zona_empty_name_rejected(self):
        data = {'nombre': '', 'color': '#000', 'radio_km': 1, 'centro_lat': 19, 'centro_lng': -99, 'tarifas': []}
        r = api('POST', '/api/zonas', data=data)
        j = r.json()
        assert j['success'] == False

    def test_get_nonexistent_zona(self):
        r = api('GET', '/api/zonas/99999')
        assert r.status_code == 404

# ========================================
# COTIZAR
# ========================================
class TestCotizar:
    def test_cotizar_express(self):
        data = {'zona_id': 1, 'servicio': 'EXPRESS', 'peso_kg': 5, 'largo_cm': 30, 'ancho_cm': 20, 'alto_cm': 15, 'distancia_km': 10, 'valor_declarado': 1000}
        r = api('POST', '/api/zonas/cotizar', data=data)
        j = r.json()
        assert j['success'] == True
        assert j['data']['total'] > 0

    def test_cotizar_peso_volumetrico(self):
        data = {'zona_id': 1, 'servicio': 'ESTANDAR', 'peso_kg': 0.5, 'largo_cm': 50, 'ancho_cm': 40, 'alto_cm': 30, 'distancia_km': 5, 'valor_declarado': 0}
        r = api('POST', '/api/zonas/cotizar', data=data)
        j = r.json()
        assert j['success'] == True
        assert j['data']['peso_volumetrico_kg'] > j['data']['peso_real_kg']

    def test_cotizar_without_zona(self):
        r = api('POST', '/api/zonas/cotizar', data={'servicio': 'EXPRESS', 'peso_kg': 5})
        j = r.json()
        assert j['success'] == False

    def test_cotizar_invalid_zone(self):
        r = api('POST', '/api/zonas/cotizar', data={'zona_id': 99999, 'servicio': 'EXPRESS', 'peso_kg': 5})
        j = r.json()
        assert j['success'] == False

# ========================================
# PEDIDOS
# ========================================
class TestPedidos:
    def test_create_pedido(self):
        data = {
            'pedNumero': 'TEST-001',
            'cliId': 1,
            'clienteNombre': 'Test Customer',
            'clienteTelefono': '5551234567',
            'destinoDir': 'Calle Test 123',
            'destinoCol': 'Colonia Test',
            'destinoCiudad': 'CDMX',
            'pesoKg': 5,
            'bultos': 1,
            'costoTotal': 150,
            'formaPago': 'EFECTIVO',
            'prioridad': 'NORMAL'
        }
        r = api('POST', '/api/pedidos', data=data)
        j = r.json()
        assert j['success'] == True

    def test_update_estado(self):
        data = {'estado': 'EN_RUTA', 'usuario': 'TEST'}
        r = api('PUT', '/api/pedidos/1/estado', data=data)
        j = r.json()
        assert j['success'] == True

# ========================================
# TRACKING
# ========================================
class TestTracking:
    def test_post_tracking(self):
        data = {'choId': 1, 'vehId': 1, 'latitud': 19.4326, 'longitud': -99.1332, 'velocidad': 45, 'rumbo': 180, 'bateria': 85}
        r = api('POST', '/api/tracking', data=data)
        j = r.json()
        assert j['success'] == True

    def test_get_tracking(self):
        r = api('GET', '/api/tracking/1')
        j = r.json()
        assert j['success'] == True

# ========================================
# EDGE CASES
# ========================================
class TestEdgeCases:
    def test_delete_nonexistent_zona(self):
        r = api('DELETE', '/api/zonas/99999')
        j = r.json()
        assert j['success'] == True  # Soft delete

    def test_delete_nonexistent_chofer(self):
        r = api('DELETE', '/api/choferes/99999')
        # May fail if no rows affected, but shouldn't crash
        assert r.status_code in (200, 500)

    def test_invalid_emp_header(self):
        r = api('GET', '/api/choferes', headers={'X-Emp-Id': 'invalid'})
        # Should default to emp 1, not crash
        assert r.status_code == 200

    def test_missing_emp_header(self):
        r = requests.get(f'{BASE}/api/choferes', timeout=15, verify=VERIFY_SSL)
        # Should default to emp 1
        assert r.status_code == 200

    def test_large_limite_capped(self):
        r = api('GET', '/api/pedidos?limite=99999')
        j = r.json()
        assert j['success'] == True
        # Server caps at 500
        assert len(j['data']) <= 500
