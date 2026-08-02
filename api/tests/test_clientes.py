"""
Tests del modulo de clientes.
Ejecutar: cd api && python -m pytest tests/test_clientes.py -v
"""
import pytest


def test_get_clientes(client, auth_headers, _seed):
    r = client.get('/api/clientes', headers=auth_headers)
    assert r.status_code == 200
    body = r.get_json()
    assert body['success'] is True
    assert isinstance(body['data'], list)


def test_create_cliente(client, auth_headers, _seed):
    r = client.post('/api/clientes', headers=auth_headers, json={
        'razon_social': 'Cliente Test SA',
        'rfc': 'CTE230303XYZ',
        'contacto': 'Juan Perez',
        'telefono': '5551234567',
        'email': 'juan@test.mx',
        'estatus': 'ACTIVO',
    })
    assert r.status_code == 200
    assert r.get_json()['success'] is True


def test_create_cliente_missing_razon(client, auth_headers, _seed):
    r = client.post('/api/clientes', headers=auth_headers, json={
        'rfc': 'SINRAZON',
    })
    assert r.status_code == 400


def test_create_cliente_no_data(client, auth_headers, _seed):
    r = client.post('/api/clientes', headers=auth_headers, json=None)
    assert r.status_code == 400


def test_get_top_clientes(client, auth_headers, _seed):
    r = client.get('/api/clientes/top', headers=auth_headers)
    assert r.status_code == 200
    body = r.get_json()
    assert body['success'] is True


def test_update_cliente(client, auth_headers, _seed):
    r = client.get('/api/clientes', headers=auth_headers)
    clientes = r.get_json().get('data', [])
    if clientes:
        cli_id = clientes[0].get('CLI_ID')
        r2 = client.put(f'/api/clientes/{cli_id}', headers=auth_headers, json={
            'razon_social': 'Cliente Actualizado',
            'rfc': 'ACT230303',
            'contacto': 'Ana Garcia',
            'telefono': '5559876543',
            'email': 'ana@actualizado.mx',
            'estatus': 'ACTIVO',
        })
        assert r2.status_code == 200
        assert r2.get_json()['success'] is True


def test_delete_cliente(client, auth_headers, _seed):
    r = client.post('/api/clientes', headers=auth_headers, json={
        'razon_social': 'Para Eliminar',
        'rfc': 'DEL230303',
    })
    r2 = client.get('/api/clientes', headers=auth_headers)
    cli_id = None
    for c in r2.get_json().get('data', []):
        if c.get('CLI_RAZON_SOCIAL') == 'Para Eliminar':
            cli_id = c['CLI_ID']
            break
    if cli_id:
        r3 = client.delete(f'/api/clientes/{cli_id}', headers=auth_headers)
        assert r3.status_code == 200
        assert r3.get_json()['success'] is True
