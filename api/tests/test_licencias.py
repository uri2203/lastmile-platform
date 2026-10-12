"""
Tests del motor de licencias (anti-hack):
 - login/API bloqueados con licencia suspendida o vencida
 - reactivacion limpia el bloqueo
 - monitor superadmin devuelve el estado global
"""
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from db import query, execute
from billing_service import (
    suspender_licencia, activar_licencia, invalidar_cache_licencia,
    evaluar_licencia, licencia_bloqueo,
)


def _login(client, user='admin', pw='admin123'):
    return client.post('/api/auth/login', json={'user': user, 'pass': pw})


def _emp_id(client):
    res = _login(client)
    data = res.get_json() or {}
    return (data.get('data') or {}).get('emp_id')


def test_login_ok_con_licencia_vigente(client):
    res = _login(client)
    data = res.get_json() or {}
    assert data.get('success') is True, data
    assert data.get('token')


def test_suspender_bloquea_login_y_api(client):
    emp_id = _emp_id(client)
    assert emp_id, 'no se pudo obtener emp_id'
    try:
        # estado inicial: OK
        assert licencia_bloqueo(emp_id) is None

        suspender_licencia(emp_id, 'test')
        assert licencia_bloqueo(emp_id) is not None

        # Login bloqueado
        res = _login(client)
        data = res.get_json() or {}
        assert res.status_code == 403
        assert (data.get('code') or '').startswith('LICENCIA')
    finally:
        activar_licencia(emp_id)
        invalidar_cache_licencia(emp_id)

    res = _login(client)
    assert res.get_json().get('success') is True


def test_api_bloqueada_con_sesion_abierta(client):
    emp_id = _emp_id(client)
    assert emp_id
    token = _login(client).get_json().get('token')
    assert token
    headers = {'Authorization': f'Bearer {token}'}
    # con licencia OK la API responde
    res = client.get('/api/shipments', headers=headers)
    assert res.status_code == 200

    try:
        suspender_licencia(emp_id, 'test_sesion')
        res = client.get('/api/shipments', headers=headers)
        assert res.status_code == 403
        data = res.get_json() or {}
        assert (data.get('code') or '').startswith('LICENCIA')
    finally:
        activar_licencia(emp_id)
        invalidar_cache_licencia(emp_id)

    res = client.get('/api/shipments', headers=headers)
    assert res.status_code == 200


def test_vencimiento_bloquea(client):
    emp_id = _emp_id(client)
    assert emp_id
    execute(
        "UPDATE SAAS_SUSCRIPCIONES SET SUS_ESTADO='ACTIVA', SUS_FECHA_FIN='2000-01-01' "
        "WHERE SUS_ID=(SELECT SUS_ID FROM SAAS_SUSCRIPCIONES WHERE EMP_ID=? ORDER BY SUS_ID DESC LIMIT 1)",
        [emp_id])
    try:
        invalidar_cache_licencia(emp_id)
        ev = evaluar_licencia(emp_id)
        assert ev['ok'] is False
        assert ev['code'] == 'LICENCIA_VENCIDA'
        res = _login(client)
        assert res.status_code == 403
        assert (res.get_json().get('code') or '') == 'LICENCIA_VENCIDA'
    finally:
        execute(
            "UPDATE SAAS_SUSCRIPCIONES SET SUS_FECHA_FIN='2099-12-31' "
            "WHERE SUS_ID=(SELECT SUS_ID FROM SAAS_SUSCRIPCIONES WHERE EMP_ID=? ORDER BY SUS_ID DESC LIMIT 1)",
            [emp_id])
        activar_licencia(emp_id)
        invalidar_cache_licencia(emp_id)
    res = _login(client)
    assert res.get_json().get('success') is True


def test_evaluar_licencia_reglas():
    # empresa inexistente
    ev = evaluar_licencia(999999)
    assert ev['ok'] is False
    # sin empresa
    ev = evaluar_licencia(None)
    assert ev['ok'] is False
