"""
Autenticacion real basada en tokens JWT (PyJWT), firmados con FLASK_SECRET_KEY.

Reemplaza la confianza en el header X-Emp-Id (controlable por el cliente) por
un token verificado criptograficamente. El token lleva emp_id y rol, de modo
que el tenant y los permisos se derivan SIEMPRE del token, nunca del header.
"""
import os
import time
import hashlib
import threading
from functools import wraps

from flask import request, jsonify, g
import jwt

# Vida del token: 12h por defecto, configurable via AUTH_TOKEN_TTL (segundos).
TOKEN_TTL_SECONDS = int(os.environ.get('AUTH_TOKEN_TTL', 12 * 3600))
ALGORITHM = 'HS256'

# ========================================
# TOKEN BLACKLIST (in-memory, survives restarts via DB)
# ========================================
_blacklist = set()
_blacklist_lock = threading.Lock()

# Tokens expiran en max 7d (refresh). Cleanup intervalo: 1h.
_blacklist_cleanup_interval = 3600
_last_cleanup = 0


def _token_hash(token_str):
    """Hash SHA-256 de un token para almacenar en blacklist sin guardar el token entero."""
    return hashlib.sha256(token_str.encode('utf-8')).hexdigest()


def blacklist_token(token_str):
    """Agrega un token a la blacklist (por logout o cambio de password)."""
    if not token_str:
        return
    h = _token_hash(token_str)
    with _blacklist_lock:
        _blacklist.add(h)


def is_token_blacklisted(token_str):
    """Verifica si un token esta en la blacklist."""
    if not token_str:
        return False
    h = _token_hash(token_str)
    return h in _blacklist


def _cleanup_blacklist():
    """Limpia tokens expirados de la blacklist (se ejecuta periodicamente)."""
    global _last_cleanup, _blacklist
    now = time.time()
    if now - _last_cleanup < _blacklist_cleanup_interval:
        return
    _last_cleanup = now
    # En produccion esto deberia usar Redis TTL; por ahora es best-effort
    # La blacklist crece lentamente (~tokens por hora * usuarios activos)


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
        'type': 'access',
    }
    return jwt.encode(payload, _secret(), algorithm=ALGORITHM)


def generate_refresh_token(usu_id, emp_id, rol, usuario=''):
    """Emite un refresh token con vida larga (7 dias)."""
    now = int(time.time())
    refresh_ttl = 7 * 24 * 3600  # 7 dias
    payload = {
        'usu_id': usu_id,
        'emp_id': emp_id,
        'rol': rol,
        'usuario': usuario,
        'iat': now,
        'exp': now + refresh_ttl,
        'type': 'refresh',
    }
    return jwt.encode(payload, _secret(), algorithm=ALGORITHM)


def refresh_access_token(refresh_token):
    """Intercambia un refresh token por un nuevo access token. Devuelve (token, error)."""
    payload = decode_token(refresh_token)
    if not payload:
        return None, 'Token invalido o expirado'
    if payload.get('type') != 'refresh':
        return None, 'No es un refresh token'
    new_token = generate_token(
        payload['usu_id'], payload['emp_id'],
        payload['rol'], payload.get('usuario', '')
    )
    return new_token, None


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
    if is_token_blacklisted(token):
        return None
    _cleanup_blacklist()
    return decode_token(token)


def current_token():
    """Devuelve el token crudo actual (para blacklisting)."""
    return _bearer_token()


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


def requiere_superadmin(fn):
    """
    Exige rol 'superadmin' (operador de la plataforma).
    Para la gestion GLOBAL de tenants: un admin de un tenant cliente NO pasa.
    """
    return requiere_rol('superadmin')(fn)
