"""
Tests del modulo de choferes.
Ejecutar: cd api && python -m pytest tests/test_choferes.py -v
"""
import pytest


def test_get_choferes(client, auth_headers, _seed):
    r = client.get('/api/choferes', headers=auth_headers)
    assert r.status_code == 200
    body = r.get_json()
    assert body['success'] is True
    assert isinstance(body['data'], list)


def test_create_chofer(client, auth_headers, _seed):
    r = client.post('/api/choferes', headers=auth_headers, json={
        'nombre': 'Carlos',
        'apellido': 'Rodriguez',
        'telefono': '5551001001',
        'email': 'carlos@test.mx',
        'licencia': 'LIC-TEST-001',
        'estatus': 'ACTIVO',
    })
    assert r.status_code == 200
    assert r.get_json()['success'] is True


def test_create_chofer_missing_nombre(client, auth_headers, _seed):
    r = client.post('/api/choferes', headers=auth_headers, json={
        'apellido': 'SinNombre',
    })
    assert r.status_code == 400


def test_create_chofer_no_data(client, auth_headers, _seed):
    r = client.post('/api/choferes', headers=auth_headers, json=None)
    assert r.status_code == 400


def test_get_chofer_by_id(client, auth_headers, _seed):
    r = client.get('/api/choferes', headers=auth_headers)
    choferes = r.get_json().get('data', [])
    if choferes:
        cho_id = choferes[0].get('CHO_ID')
        r2 = client.get(f'/api/choferes/{cho_id}', headers=auth_headers)
        assert r2.status_code in (200, 405)


def test_update_chofer(client, auth_headers, _seed):
    r = client.get('/api/choferes', headers=auth_headers)
    choferes = r.get_json().get('data', [])
    if choferes:
        cho_id = choferes[0].get('CHO_ID')
        r2 = client.put(f'/api/choferes/{cho_id}', headers=auth_headers, json={
            'nombre': 'Carlos',
            'apellido': 'Rodriguez Updated',
            'telefono': '5559999999',
            'licencia': 'LIC-001',
            'email': 'carlos@test.mx',
            'estatus': 'ACTIVO',
        })
        assert r2.status_code == 200
        assert r2.get_json()['success'] is True


def test_delete_chofer(client, auth_headers, _seed):
    r = client.post('/api/choferes', headers=auth_headers, json={
        'nombre': 'ParaEliminar',
        'apellido': 'Chofer',
    })
    r2 = client.get('/api/choferes', headers=auth_headers)
    cho_id = None
    for c in r2.get_json().get('data', []):
        if c.get('CHO_NOMBRE') == 'ParaEliminar':
            cho_id = c['CHO_ID']
            break
    if cho_id:
        r3 = client.delete(f'/api/choferes/{cho_id}', headers=auth_headers)
        assert r3.status_code == 200
        assert r3.get_json()['success'] is True


def test_choferes_rendimiento(client, auth_headers, _seed):
    r = client.get('/api/choferes/rendimiento', headers=auth_headers)
    assert r.status_code == 200
    body = r.get_json()
    assert body['success'] is True
    assert 'total' in body
