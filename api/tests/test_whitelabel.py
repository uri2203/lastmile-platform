"""
Tests del modulo de whitelabel.
Ejecutar: cd api && python -m pytest tests/test_whitelabel.py -v
"""
import pytest


def test_get_whitelabel_config(client, auth_headers, _seed):
    r = client.get('/api/whitelabel/1', headers=auth_headers)
    assert r.status_code == 200
    body = r.get_json()
    assert body['success'] is True
    assert 'data' in body


def test_get_whitelabel_config_nonexistent(client, auth_headers, _seed):
    r = client.get('/api/whitelabel/99999', headers=auth_headers)
    assert r.status_code == 200
    body = r.get_json()
    assert body['success'] is True


def test_update_whitelabel_config(client, auth_headers, _seed):
    r = client.post('/api/whitelabel/config', headers=auth_headers, json={
        'nombre': 'Mi Empresa WhiteLabel',
        'logo_url': 'https://example.com/logo.png',
        'color_primary': '#FF5733',
        'color_secondary': '#33FF57',
        'color_bg': '#FFFFFF',
        'dominio': 'midominio.com',
        'footer_text': 'Powered by Last Mile',
        'custom_css': 'body { font-family: Arial; }',
        'custom_js': '',
        'features': '{}',
    })
    assert r.status_code == 200
    body = r.get_json()
    assert body['success'] is True


def test_update_whitelabel_config_defaults(client, auth_headers, _seed):
    r = client.post('/api/whitelabel/config', headers=auth_headers, json={})
    assert r.status_code == 200
    body = r.get_json()
    assert body['success'] is True


def test_update_whitelabel_without_auth(client, _seed):
    r = client.post('/api/whitelabel/config', json={
        'nombre': 'Sin Auth',
    })
    assert r.status_code == 401
