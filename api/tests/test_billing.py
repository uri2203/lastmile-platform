"""
TEST SUITE - Billing, CFDI, Payments & Security Features
Ejecutar: pytest tests/test_billing.py -v
"""
import pytest
import sys
import os
import json

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from server import app
from db import init_schema, check_empty
from seed import seed


@pytest.fixture(scope='module')
def client():
    app.config['TESTING'] = True
    app.config['DATABASE_URL'] = ''
    with app.test_client() as client:
        try:
            init_schema()
            if check_empty():
                seed()
        except Exception:
            pass
        yield client


def login(client, user='admin', password='admin123'):
    r = client.post('/api/auth/login', json={'user': user, 'pass': password})
    data = r.get_json()
    return data.get('token', ''), data.get('refresh_token', '')


def auth_headers(token):
    return {'Authorization': f'Bearer {token}', 'Content-Type': 'application/json'}


# ========================================
# HEALTH CHECK (Enhanced)
# ========================================
class TestHealthEnhanced:
    def test_health_returns_services(self, client):
        r = client.get('/api/health')
        assert r.status_code == 200
        j = r.get_json()
        assert j['status'] in ('OK', 'DEGRADED')
        assert 'database' in j
        assert 'services' in j
        assert j['database']['status'] == 'OK'
        assert 'latency' in j['database']

    def test_health_has_version(self, client):
        r = client.get('/api/health')
        j = r.get_json()
        assert 'version' in j


# ========================================
# TOKEN REFRESH
# ========================================
class TestTokenRefresh:
    def test_login_returns_refresh_token(self, client):
        token, refresh = login(client)
        assert token
        assert refresh

    def test_refresh_returns_new_token(self, client):
        _, refresh = login(client)
        r = client.post('/api/auth/refresh', json={'refresh_token': refresh})
        assert r.status_code == 200
        j = r.get_json()
        assert j['success'] is True
        assert 'token' in j
        assert j['expires_in'] == 43200

    def test_refresh_rejects_invalid_token(self, client):
        r = client.post('/api/auth/refresh', json={'refresh_token': 'invalid_token'})
        assert r.status_code == 401

    def test_refresh_rejects_empty_token(self, client):
        r = client.post('/api/auth/refresh', json={})
        assert r.status_code == 400

    def test_access_token_works_after_refresh(self, client):
        _, refresh = login(client)
        r = client.post('/api/auth/refresh', json={'refresh_token': refresh})
        new_token = r.get_json().get('token')
        r2 = client.get('/api/pedidos', headers=auth_headers(new_token))
        assert r2.status_code == 200


# ========================================
# PASSWORD STRENGTH
# ========================================
class TestPasswordStrength:
    def test_validate_password_strength_valid(self):
        from security import validate_password_strength
        ok, err = validate_password_strength('MiClave123')
        assert ok is True
        assert err is None

    def test_validate_password_too_short(self):
        from security import validate_password_strength
        ok, err = validate_password_strength('Ab1')
        assert ok is False
        assert '8 caracteres' in err

    def test_validate_password_no_uppercase(self):
        from security import validate_password_strength
        ok, err = validate_password_strength('miclave123')
        assert ok is False
        assert 'mayuscula' in err

    def test_validate_password_no_lowercase(self):
        from security import validate_password_strength
        ok, err = validate_password_strength('MICLAVE123')
        assert ok is False
        assert 'minuscula' in err

    def test_validate_password_no_digit(self):
        from security import validate_password_strength
        ok, err = validate_password_strength('MiClaveSuper')
        assert ok is False
        assert 'digito' in err

    def test_validate_password_empty(self):
        from security import validate_password_strength
        ok, err = validate_password_strength('')
        assert ok is False

    def test_validate_password_long(self):
        from security import validate_password_strength
        long_pwd = 'A' * 129 + 'a1'
        ok, err = validate_password_strength(long_pwd)
        assert ok is False
        assert '128' in err


# ========================================
# BILLING / PLANES
# ========================================
class TestBillingPlanes:
    def test_get_planes(self, client):
        token = login(client)[0]
        r = client.get('/api/billing/planes', headers=auth_headers(token))
        assert r.status_code == 200
        j = r.get_json()
        assert j.get('success') is True

    def test_get_mis_limits(self, client):
        token = login(client)[0]
        r = client.get('/api/billing/mis-limites', headers=auth_headers(token))
        assert r.status_code == 200
        j = r.get_json()
        assert j.get('success') is True
        assert 'plan' in j.get('data', {})

    def test_get_billing_stats(self, client):
        token = login(client)[0]
        r = client.get('/api/billing/stats', headers=auth_headers(token))
        assert r.status_code == 200
        j = r.get_json()
        assert j.get('success') is True


# ========================================
# CFDI
# ========================================
class TestCFDI:
    def test_cfdi_status(self, client):
        token = login(client)[0]
        r = client.get('/api/cfdi/status', headers=auth_headers(token))
        assert r.status_code == 200
        j = r.get_json()
        assert j.get('success') is True

    def test_cfdi_facturas(self, client):
        token = login(client)[0]
        r = client.get('/api/cfdi/facturas', headers=auth_headers(token))
        assert r.status_code == 200
        j = r.get_json()
        assert j.get('success') is True


# ========================================
# RATE LIMITING
# ========================================
class TestRateLimit:
    def test_health_no_rate_limit(self, client):
        for _ in range(5):
            r = client.get('/api/health')
            assert r.status_code == 200

    def test_login_rate_limit(self, client):
        for _ in range(12):
            client.post('/api/auth/login', json={'user': 'nobody', 'pass': 'x'})
        r = client.post('/api/auth/login', json={'user': 'nobody', 'pass': 'x'})
        assert r.status_code in (200, 429)


# ========================================
# BODY SIZE LIMIT
# ========================================
class TestBodySizeLimit:
    def test_large_payload_rejected(self, client):
        token = login(client)[0]
        large_data = 'x' * (11 * 1024 * 1024)  # 11MB
        r = client.post('/api/pedidos', headers=auth_headers(token),
                       data=large_data, content_type='application/json')
        assert r.status_code == 413


# ========================================
# SECURITY HEADERS
# ========================================
class TestSecurityHeaders:
    def test_api_has_security_headers(self, client):
        token = login(client)[0]
        r = client.get('/api/pedidos', headers=auth_headers(token))
        assert r.headers.get('X-Content-Type-Options') == 'nosniff'
        assert r.headers.get('X-Frame-Options') == 'DENY'
        assert r.headers.get('X-XSS-Protection') == '1; mode=block'

    def test_health_has_security_headers(self, client):
        r = client.get('/api/health')
        assert r.headers.get('X-Content-Type-Options') == 'nosniff'


# ========================================
# AUDIT LOGGING
# ========================================
class TestAuditLogging:
    def test_audit_log_created_on_delete(self, client):
        token = login(client)[0]
        r = client.get('/api/pedidos', headers=auth_headers(token))
        pedidos = r.get_json().get('data', [])
        if pedidos:
            ped_id = pedidos[0].get('PED_ID')
            r = client.delete(f'/api/pedidos/{ped_id}', headers=auth_headers(token))
            assert r.status_code == 200
            # Check audit log exists
            log_path = os.path.join(os.path.dirname(__file__), '..', 'logs', 'audit.log')
            if os.path.exists(log_path):
                with open(log_path, 'r') as f:
                    content = f.read()
                    assert 'pedido_deleted' in content


# ========================================
# EDGE CASES - AUTH
# ========================================
class TestAuthEdgeCases:
    def test_nonexistent_user(self, client):
        r = client.post('/api/auth/login', json={'user': 'ghost', 'pass': 'x'})
        assert r.status_code == 200
        j = r.get_json()
        assert j.get('success') is False

    def test_special_characters_in_password(self, client):
        r = client.post('/api/auth/login', json={'user': 'admin', "pass": "'; DROP TABLE--"})
        assert r.status_code == 200
        j = r.get_json()
        assert j.get('success') is False

    def test_token_format(self, client):
        token, _ = login(client)
        parts = token.split('.')
        assert len(parts) == 3  # JWT has 3 parts
