"""
TESTS DE HASHING DE CONTRASEÑAS (bcrypt + migración transparente).
Ejecutar:  cd api && python -m pytest tests/test_password.py -v

Verifica: hash bcrypt y verify OK; contraseña incorrecta falla; un hash
SHA-256 heredado sigue validando; y al hacer login con un hash heredado,
el registro se re-hashea a bcrypt (migración transparente).
"""
import hashlib
import os
import sys

import pytest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
os.environ.pop('ALLOW_SETUP', None)

from security import hash_password, verify_password, is_legacy_hash  # noqa: E402


def _sha256(p):
    return hashlib.sha256(p.encode('utf-8')).hexdigest()


# ------------------------------------------------ UNIT: bcrypt

def test_hash_es_bcrypt():
    h = hash_password('secret123')
    assert h.startswith('$2')          # prefijo bcrypt ($2b$)
    assert is_legacy_hash(h) is False


def test_hash_es_salado_y_distinto_cada_vez():
    assert hash_password('misma') != hash_password('misma')  # sal aleatoria


def test_verify_correcto():
    h = hash_password('secret123')
    assert verify_password('secret123', h) is True


def test_verify_incorrecto():
    h = hash_password('secret123')
    assert verify_password('mala', h) is False


# ------------------------------------------------ UNIT: heredado SHA-256

def test_detecta_hash_heredado():
    assert is_legacy_hash(_sha256('admin123')) is True
    assert is_legacy_hash(hash_password('admin123')) is False


def test_hash_heredado_sigue_validando():
    legacy = _sha256('admin123')
    assert verify_password('admin123', legacy) is True
    assert verify_password('incorrecta', legacy) is False


def test_rehash_de_heredado_a_bcrypt():
    legacy = _sha256('clave')
    assert verify_password('clave', legacy)      # valida el viejo
    nuevo = hash_password('clave')               # se re-hashea
    assert not is_legacy_hash(nuevo)
    assert verify_password('clave', nuevo)


# ------------------------ INTEGRACIÓN: migración transparente en el login

@pytest.fixture(scope='module')
def ctx():
    from server import app, limiter
    from db import query, execute
    app.config['TESTING'] = True
    limiter.enabled = False   # evita el rate-limit del login durante los tests
    return app.test_client(), query, execute


def test_login_migra_hash_heredado_a_bcrypt(ctx):
    client, query, execute = ctx
    # Forzamos a 'operador' (emp 1) a tener un hash SHA-256 heredado.
    execute("UPDATE USUARIOS SET USU_PASS=? WHERE USU_USUARIO='operador' AND USU_EMP_ID=1",
            [_sha256('oper123')])
    antes = query("SELECT USU_PASS FROM USUARIOS WHERE USU_USUARIO='operador' AND USU_EMP_ID=1")[0]['USU_PASS']
    assert is_legacy_hash(antes)                  # está en formato viejo

    # Login correcto con la contraseña de siempre.
    r = client.post('/api/auth/login', json={'user': 'operador', 'pass': 'oper123'})
    assert r.status_code == 200
    assert r.get_json()['success'] is True

    # Tras el login, el hash almacenado ya es bcrypt (migrado).
    despues = query("SELECT USU_PASS FROM USUARIOS WHERE USU_USUARIO='operador' AND USU_EMP_ID=1")[0]['USU_PASS']
    assert despues.startswith('$2')
    assert not is_legacy_hash(despues)
    # Y sigue validando la misma contraseña con el hash nuevo.
    assert verify_password('oper123', despues)
