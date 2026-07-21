"""
Autenticacion real basada en tokens JWT (PyJWT), firmados con FLASK_SECRET_KEY.

Reemplaza la confianza en el header X-Emp-Id (controlable por el cliente) por
un token verificado criptograficamente. El token lleva emp_id y rol, de modo
que el tenant y los permisos se derivan SIEMPRE del token, nunca del header.
"""
import os
import time
from functools import wraps

from flask import request, jsonify, g
import jwt

# Vida del token: 12h por defecto, configurable via AUTH_TOKEN_TTL (segundos).
TOKEN_TTL_SECONDS = int(os.environ.get('AUTH_TOKEN_TTL', 12 * 3600))
ALGORITHM = 'HS256'


def _secret():
    """Clave de firma. Misma que usa Flask (FLASK_SECRET_KEY)."""
    return os.environ.get('FLASK_SECRET_KEY', 'lastmile-dev-key-change-in-prod')


def generate_token(usu_id, emp_id, rol, usuario=''):
    """Emite un JWT firmado con la identidad del usuario autenticado."""
    now = int(time.time())
    payload = {
        'usu_id': usu_id,
        'emp_id': emp_id,
        'rol': rol,
        'usuario': usuario,
        'iat': now,
        'exp': now + TOKEN_TTL_SECONDS,
    }
    return jwt.encode(payload, _secret(), algorithm=ALGORITHM)


def decode_token(token):
    """Devuelve el payload si el token es valido y no expiro, o None."""
    try:
        return jwt.decode(token, _secret(), algorithms=[ALGORITHM])
    except jwt.PyJWTError:
        return None


def _bearer_token():
    """Extrae el token del header Authorization: Bearer <token>."""
    header = request.headers.get('Authorization', '')
    if header.startswith('Bearer '):
        return header[7:].strip()
    return None


def current_identity():
    """Identidad verificada a partir del header Authorization, o None."""
    token = _bearer_token()
    if not token:
        return None
    return decode_token(token)


def _apply_identity(ident):
    """Guarda la identidad verificada en el contexto de la request (flask.g)."""
    g.emp_id = ident.get('emp_id')
    g.rol = ident.get('rol')
    g.usu_id = ident.get('usu_id')
    g.usuario = ident.get('usuario', '')


def requiere_auth(fn):
    """Exige un token valido. Deja la identidad en flask.g."""
    @wraps(fn)
    def wrapper(*args, **kwargs):
        ident = current_identity()
        if not ident:
            return jsonify({'success': False, 'error': 'No autenticado'}), 401
        _apply_identity(ident)
        return fn(*args, **kwargs)
    return wrapper


def requiere_rol(*roles):
    """Exige un token valido cuyo rol este en `roles` (ej. 'admin')."""
    def decorator(fn):
        @wraps(fn)
        def wrapper(*args, **kwargs):
            ident = current_identity()
            if not ident:
                return jsonify({'success': False, 'error': 'No autenticado'}), 401
            if ident.get('rol') not in roles:
                return jsonify({'success': False, 'error': 'No autorizado'}), 403
            _apply_identity(ident)
            return fn(*args, **kwargs)
        return wrapper
    return decorator
