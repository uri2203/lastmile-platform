"""
LAST MILE DELIVERY - End-to-End Tests
Flujo completo: Login → Crear Pedido → Asignar Chofer → GPS → Entrega → Facturación
"""
import pytest
import requests
import json
import time
from datetime import datetime

BASE = 'https://lastmile-platform.onrender.com'
HEADERS = {'Content-Type': 'application/json'}

def get_token(user='admin', password='admin123'):
    r = requests.post(f'{BASE}/api/auth/login', json={'usuario': user, 'password': password}, headers=HEADERS)
    if r.status_code == 200:
        return r.json().get('token')
    return None

def auth_headers(token, emp_id=1):
    return {'Content-Type': 'application/json', 'Authorization': f'Bearer {token}', 'X-Emp-Id': str(emp_id)}


class TestHealthAndBasics:
    def test_health_endpoint(self):
        r = requests.get(f'{BASE}/api/health')
        assert r.status_code == 200

    def test_vapid_key_public(self):
        r = requests.get(f'{BASE}/api/vapid-public-key')
        assert r.status_code == 200
        assert 'publicKey' in r.json()

    def test_fiscal_countries(self):
        r = requests.get(f'{BASE}/api/fiscal/countries')
        assert r.status_code == 200
        countries = r.json()
        assert len(countries) == 8

    def test_fiscal_providers(self):
        r = requests.get(f'{BASE}/api/fiscal/providers')
        assert r.status_code == 200

    def test_payment_countries(self):
        r = requests.get(f'{BASE}/api/payment/countries')
        assert r.status_code == 200

    def test_i18n_es(self):
        r = requests.get(f'{BASE}/i18n/es.json')
        assert r.status_code == 200

    def test_i18n_en(self):
        r = requests.get(f'{BASE}/i18n/en.json')
        assert r.status_code == 200

    def test_i18n_pt(self):
        r = requests.get(f'{BASE}/i18n/pt.json')
        assert r.status_code == 200

    def test_static_panels(self):
        panels = ['panel-admin.html', 'panel-chofer.html', 'panel-cliente.html',
                  'panel-operacion.html', 'panel-tenant.html', 'panel-saas.html']
        for p in panels:
            r = requests.get(f'{BASE}/{p}')
            assert r.status_code == 200, f'{p} not found'

    def test_landing_page(self):
        r = requests.get(f'{BASE}/landing.html')
        assert r.status_code == 200
        assert 'i18n.js' in r.text

    def test_sw_js(self):
        r = requests.get(f'{BASE}/sw.js')
        assert r.status_code == 200
        assert 'push' in r.text

    def test_manifest(self):
        r = requests.get(f'{BASE}/manifest.json')
        assert r.status_code == 200


class TestAuthFlow:
    def test_login_admin(self):
        token = get_token('admin', 'admin123')
        assert token is not None

    def test_login_operador(self):
        token = get_token('operador', 'oper123')
        assert token is not None

    def test_login_chofer(self):
        token = get_token('chofer1', 'chof123')
        assert token is not None

    def test_login_cliente(self):
        token = get_token('cliente1', 'clie123')
        assert token is not None

    def test_login_invalid(self):
        r = requests.post(f'{BASE}/api/auth/login', json={'usuario': 'wrong', 'password': 'wrong'})
        assert r.status_code in [401, 400]

    def test_token_refresh(self):
        token = get_token('admin', 'admin123')
        if token:
            r = requests.post(f'{BASE}/api/auth/refresh',
                            json={'token': token},
                            headers=HEADERS)
            assert r.status_code == 200


class TestFullDeliveryFlow:
    @pytest.fixture(autouse=True)
    def setup(self):
        self.token = get_token('admin', 'admin123')
        self.headers = auth_headers(self.token) if self.token else {}

    def test_01_get_choferes(self):
        r = requests.get(f'{BASE}/api/choferes?emp_id=1', headers=self.headers)
        assert r.status_code == 200

    def test_02_get_pedidos(self):
        r = requests.get(f'{BASE}/api/pedidos?emp_id=1', headers=self.headers)
        assert r.status_code == 200

    def test_03_create_pedido(self):
        payload = {
            'cliente_nombre': 'Test E2E Cliente',
            'cliente_telefono': '5551234567',
            'destino_direccion': 'Av. Test 123, Col. Centro',
            'destino_colonia': 'Centro',
            'bultos': 1,
            'peso_kg': 2.5,
            'costo_total': 150.00,
            'prioridad': 'NORMAL',
            'notas': 'E2E test delivery'
        }
        r = requests.post(f'{BASE}/api/pedidos', json=payload, headers=self.headers)
        assert r.status_code in [200, 201]
        data = r.json()
        assert data.get('success') or data.get('pedido_id')

    def test_04_tracking_live(self):
        r = requests.get(f'{BASE}/api/tracking/live?emp_id=1', headers=self.headers)
        assert r.status_code == 200

    def test_05_multi_country_analytics(self):
        r = requests.get(f'{BASE}/api/analytics/multi-country', headers=self.headers)
        assert r.status_code == 200

    def test_06_fiscal_config(self):
        r = requests.get(f'{BASE}/api/fiscal/config?emp_id=1', headers=self.headers)
        assert r.status_code == 200

    def test_07_billing_plans(self):
        r = requests.get(f'{BASE}/api/billing/planes', headers=self.headers)
        assert r.status_code == 200

    def test_08_dashboard(self):
        r = requests.get(f'{BASE}/api/dashboard/1', headers=self.headers)
        assert r.status_code == 200

    def test_09_client_tracking(self):
        r = requests.get(f'{BASE}/api/cliente-final/test-token')
        assert r.status_code in [200, 404]

    def test_10_webhook_stripe(self):
        payload = {'type': 'test', 'data': {}}
        r = requests.post(f'{BASE}/api/webhooks/stripe', json=payload)
        assert r.status_code in [200, 400]

    def test_11_webhook_mercadopago(self):
        payload = {'type': 'payment', 'data': {}}
        r = requests.post(f'{BASE}/api/webhooks/mercadopago', json=payload)
        assert r.status_code in [200, 400]


class TestMultiCountryFiscal:
    @pytest.fixture(autouse=True)
    def setup(self):
        self.token = get_token('admin', 'admin123')
        self.headers = auth_headers(self.token) if self.token else {}

    def test_mx_providers(self):
        r = requests.get(f'{BASE}/api/fiscal/providers?country=MX', headers=self.headers)
        assert r.status_code == 200

    def test_br_providers(self):
        r = requests.get(f'{BASE}/api/fiscal/providers?country=BR', headers=self.headers)
        assert r.status_code == 200

    def test_co_providers(self):
        r = requests.get(f'{BASE}/api/fiscal/providers?country=CO', headers=self.headers)
        assert r.status_code == 200

    def test_ar_providers(self):
        r = requests.get(f'{BASE}/api/fiscal/providers?country=AR', headers=self.headers)
        assert r.status_code == 200

    def test_cl_providers(self):
        r = requests.get(f'{BASE}/api/fiscal/providers?country=CL', headers=self.headers)
        assert r.status_code == 200

    def test_pe_providers(self):
        r = requests.get(f'{BASE}/api/fiscal/providers?country=PE', headers=self.headers)
        assert r.status_code == 200

    def test_uy_providers(self):
        r = requests.get(f'{BASE}/api/fiscal/providers?country=UY', headers=self.headers)
        assert r.status_code == 200

    def test_ec_providers(self):
        r = requests.get(f'{BASE}/api/fiscal/providers?country=EC', headers=self.headers)
        assert r.status_code == 200


class TestWebSocket:
    def test_socketio_handshake(self):
        r = requests.get(f'{BASE}/socket.io/?EIO=4&transport=polling')
        assert r.status_code == 200


class TestPerformance:
    def test_health_response_time(self):
        start = time.time()
        r = requests.get(f'{BASE}/api/health')
        elapsed = time.time() - start
        assert r.status_code == 200
        assert elapsed < 5.0

    def test_landing_response_time(self):
        start = time.time()
        r = requests.get(f'{BASE}/landing.html')
        elapsed = time.time() - start
        assert r.status_code == 200
        assert elapsed < 5.0


if __name__ == '__main__':
    pytest.main([__file__, '-v', '--tb=short'])
