"""
Tests de autenticacion (JWT).
Ejecutar: cd api && python -m pytest tests/test_auth.py -v
"""
import pytest
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from auth import decode_token


def test_login_success(client, _seed):
    r = client.post('/api/auth/login', json={'user': 'admin', 'pass': 'admin123'})
    assert r.status_code == 200
    body = r.get_json()
    assert body['success'] is True
    assert 'token' in body and body['token']
    payload = decode_token(body['token'])
    assert payload is not None
    assert payload['emp_id'] == 1
    assert payload['rol'] == 'admin'


def test_login_invalid_credentials(client, _seed):
    r = client.post('/api/auth/login', json={'user': 'admin', 'pass': 'wrongpassword'})
    body = r.get_json()
    assert body['success'] is False
    assert 'token' not in body


def test_login_empty_fields(client, _seed):
    r = client.post('/api/auth/login', json={'user': '', 'pass': ''})
    body = r.get_json()
    assert body['success'] is False


def test_protected_route_without_token(client, _seed):
    r = client.get('/api/pedidos')
    assert r.status_code == 401


def test_protected_route_with_token(client, _seed):
    res = client.post('/api/auth/login', json={'user': 'admin', 'pass': 'admin123'})
    token = res.get_json()['token']
    r = client.get('/api/pedidos', headers={'Authorization': f'Bearer {token}'})
    assert r.status_code == 200
    assert r.get_json()['success'] is True


def test_invalid_token_rejected(client, _seed):
    r = client.get('/api/pedidos', headers={'Authorization': 'Bearer not.a.valid.token'})
    assert r.status_code == 401


def test_refresh_token(client, _seed):
    res = client.post('/api/auth/login', json={'user': 'admin', 'pass': 'admin123'})
    refresh = res.get_json().get('refresh_token', '')
    assert refresh
    r = client.post('/api/auth/refresh', json={'refresh_token': refresh})
    assert r.status_code == 200
    body = r.get_json()
    assert body['success'] is True
    assert 'token' in body


def test_refresh_invalid_token(client, _seed):
    r = client.post('/api/auth/refresh', json={'refresh_token': 'garbage'})
    assert r.status_code == 401


def test_header_x_emp_id_ignored(client, _seed):
    res = client.post('/api/auth/login', json={'user': 'operador', 'pass': 'oper123'})
    token = res.get_json()['token']
    r = client.get('/api/usuarios', headers={
        'Authorization': f'Bearer {token}',
        'X-Emp-Id': '2',
    })
    assert r.status_code == 200
    data = r.get_json()['data']
    assert all(u['USU_EMP_ID'] == 1 for u in data)


def test_admin_only_rechaza_no_admin(client, _seed):
    res = client.post('/api/auth/login', json={'user': 'operador', 'pass': 'oper123'})
    token = res.get_json()['token']
    r = client.get('/api/admin/tenants-usage', headers={'Authorization': f'Bearer {token}'})
    assert r.status_code == 403


def test_health_public(client, _seed):
    r = client.get('/api/health')
    assert r.status_code == 200
    assert r.get_json()['status'] in ('OK', 'DEGRADED')
