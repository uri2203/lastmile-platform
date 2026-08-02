import pytest
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

os.environ.pop('ALLOW_SETUP', None)

from server import app as flask_app
from server import limiter


@pytest.fixture(scope='session')
def app():
    flask_app.config['TESTING'] = True
    limiter.enabled = False
    yield flask_app


@pytest.fixture(scope='session')
def client(app):
    return app.test_client()


@pytest.fixture(scope='session')
def _seed(client):
    from db import check_empty
    from seed import seed
    if check_empty():
        try:
            seed()
        except Exception:
            pass


@pytest.fixture(scope='session')
def auth_headers(client, _seed):
    res = client.post('/api/auth/login', json={'user': 'admin', 'pass': 'admin123'})
    data = res.get_json()
    token = data.get('token', '')
    return {'Authorization': f'Bearer {token}', 'Content-Type': 'application/json'}


@pytest.fixture(scope='session')
def auth_headers_operador(client, _seed):
    res = client.post('/api/auth/login', json={'user': 'operador', 'pass': 'oper123'})
    data = res.get_json()
    token = data.get('token', '')
    return {'Authorization': f'Bearer {token}', 'Content-Type': 'application/json'}
