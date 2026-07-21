"""
TEST DEL RATE-LIMIT DEL LOGIN.
Ejecutar:  cd api && python -m pytest tests/test_ratelimit.py -v

Confirma que al superar el limite de intentos de login se devuelve 429
(Too Many Requests) con un mensaje claro, y NO 500 (antes el errorhandler
generico enmascaraba el 429 como 500).
"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
os.environ.pop('ALLOW_SETUP', None)


def test_login_rate_limit_devuelve_429_no_500():
    from server import app, limiter
    app.config['TESTING'] = True

    limiter.enabled = True                       # el login limita a 10/min
    try:
        limiter.reset()                          # limpia contadores previos
    except Exception:
        pass

    client = app.test_client()
    statuses = []
    body = None
    try:
        # Con 15 intentos (limite = 10/min) forzamos el rate-limit.
        for _ in range(15):
            r = client.post('/api/auth/login', json={'user': 'nadie', 'pass': 'x'})
            statuses.append(r.status_code)
            if r.status_code == 429:
                body = r.get_json()
                break
    finally:
        limiter.enabled = False                  # no afecta a otras suites

    assert 429 in statuses, f'esperaba un 429 tras superar el limite, hubo: {statuses}'
    assert 500 not in statuses, f'el 429 se enmascaro como 500: {statuses}'
    assert body is not None
    assert body.get('success') is False
    assert 'error' in body
