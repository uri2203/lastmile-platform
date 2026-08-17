"""
Tests del modulo de pedidos.
Ejecutar: cd api && python -m pytest tests/test_pedidos.py -v
"""
import pytest


def test_get_pedidos(client, auth_headers, _seed):
    r = client.get('/api/pedidos', headers=auth_headers)
    assert r.status_code == 200
    body = r.get_json()
    assert body['success'] is True
    assert isinstance(body['data'], list)
    assert 'total' in body


def test_get_pedidos_with_estado_filter(client, auth_headers, _seed):
    r = client.get('/api/pedidos?estado=PENDIENTE', headers=auth_headers)
    assert r.status_code == 200
    body = r.get_json()
    assert body['success'] is True
    for p in body['data']:
        assert p.get('PED_ESTADO') == 'PENDIENTE'


def test_get_pedidos_limit_capped(client, auth_headers, _seed):
    r = client.get('/api/pedidos?limite=99999', headers=auth_headers)
    assert r.status_code == 200
    body = r.get_json()
    assert len(body['data']) <= 500


def test_create_pedido(client, auth_headers, _seed):
    r = client.post('/api/pedidos', headers=auth_headers, json={
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
        'prioridad': 'NORMAL',
    })
    assert r.status_code == 200
    assert r.get_json()['success'] is True


def test_create_pedido_missing_data(client, auth_headers, _seed):
    r = client.post('/api/pedidos', headers=auth_headers, json=None)
    assert r.status_code == 400


def test_get_pedido_by_id(client, auth_headers, _seed):
    r = client.get('/api/pedidos', headers=auth_headers)
    pedidos = r.get_json().get('data', [])
    if pedidos:
        ped_id = pedidos[0].get('PED_ID')
        r2 = client.get(f'/api/pedidos/{ped_id}', headers=auth_headers)
        assert r2.status_code == 200
        body = r2.get_json()
        assert body['success'] is True
        if body['data']:
            assert body['data']['PED_ID'] == ped_id


def test_get_nonexistent_pedido(client, auth_headers, _seed):
    r = client.get('/api/pedidos/99999', headers=auth_headers)
    assert r.status_code == 200
    body = r.get_json()
    assert body['data'] is None


def test_update_pedido_status(client, auth_headers, _seed):
    r = client.get('/api/pedidos', headers=auth_headers)
    pedidos = r.get_json().get('data', [])
    if pedidos:
        ped_id = pedidos[0].get('PED_ID')
        r2 = client.put(f'/api/pedidos/{ped_id}/estado', headers=auth_headers, json={
            'estado': 'EN_RUTA',
            'usuario': 'TEST',
        })
        assert r2.status_code == 200
        assert r2.get_json()['success'] is True


def test_update_pedido_full(client, auth_headers, _seed):
    r = client.get('/api/pedidos', headers=auth_headers)
    pedidos = r.get_json().get('data', [])
    if pedidos:
        ped_id = pedidos[0].get('PED_ID')
        r2 = client.put(f'/api/pedidos/{ped_id}', headers=auth_headers, json={
            'clienteNombre': 'Cliente Actualizado',
            'clienteTelefono': '5559999999',
            'destinoDir': 'Nueva Direccion 456',
            'destinoCol': 'Nueva Colonia',
            'destinoCiudad': 'Guadalajara',
            'pesoKg': 5.0,
            'bultos': 2,
            'costoTotal': 300.00,
            'formaPago': 'TARJETA',
            'estado': 'PENDIENTE',
            'priorIDAD': 'URGENTE',
        })
        assert r2.status_code == 200


def test_pedido_estadisticas(client, auth_headers, _seed):
    r = client.get('/api/pedidos/estadisticas', headers=auth_headers)
    assert r.status_code == 200
    body = r.get_json()
    assert body['success'] is True
    assert 'TOTAL' in body['data']


def test_delete_pedido(client, auth_headers, _seed):
    r = client.post('/api/pedidos', headers=auth_headers, json={
        'pedNumero': 'PED-DEL-001',
        'clienteNombre': 'Para Eliminar',
        'destinoDir': 'Calle X',
        'destinoCiudad': 'CDMX',
        'costoTotal': 50,
    })
    ped_id = None
    r2 = client.get('/api/pedidos', headers=auth_headers)
    for p in r2.get_json().get('data', []):
        if p.get('PED_NUMERO') == 'PED-DEL-001':
            ped_id = p['PED_ID']
            break
    if ped_id:
        r3 = client.delete(f'/api/pedidos/{ped_id}', headers=auth_headers)
        assert r3.status_code == 200
        assert r3.get_json()['success'] is True
