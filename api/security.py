"""
Hashing de contraseñas con bcrypt, con verificación compatible hacia atrás.

- hash_password(plain)         -> hash bcrypt (str)
- verify_password(plain, hash) -> bool; acepta bcrypt (nuevo) y SHA-256 sin sal (heredado)
- is_legacy_hash(hash)         -> True si el hash es SHA-256 heredado (necesita migrar)
- validate_password_strength(plain) -> (ok, error_msg)

Los usuarios existentes tienen hashes SHA-256 sin sal. verify_password los sigue
validando; el llamador (login) re-hashea a bcrypt tras un login correcto para
migrar de forma transparente. Ver [[migracion-transparente]].
"""
import hashlib
import hmac
import re

import bcrypt

# SHA-256 hexdigest = 64 caracteres hex. bcrypt empieza por $2a$/$2b$/$2y$.
_SHA256_RE = re.compile(r'^[0-9a-fA-F]{64}$')

# Password policy: min 8 chars, at least 1 uppercase, 1 lowercase, 1 digit
_PASSWORD_MIN_LENGTH = 8
_PASSWORD_MAX_LENGTH = 128


def validate_password_strength(plain: str) -> tuple:
    """
    Valida que la contrasena cumpla politicas de seguridad.
    Retorna (True, None) si es valida, o (False, mensaje_error) si no.
    """
    if not plain:
        return False, 'La contrasena no puede estar vacia'
    if len(plain) < _PASSWORD_MIN_LENGTH:
        return False, f'La contrasena debe tener al menos {_PASSWORD_MIN_LENGTH} caracteres'
    if len(plain) > _PASSWORD_MAX_LENGTH:
        return False, f'La contrasena no puede exceder {_PASSWORD_MAX_LENGTH} caracteres'
    if not re.search(r'[A-Z]', plain):
        return False, 'La contrasena debe contener al menos una letra mayuscula'
    if not re.search(r'[a-z]', plain):
        return False, 'La contrasena debe contener al menos una letra minuscula'
    if not re.search(r'[0-9]', plain):
        return False, 'La contrasena debe contener al menos un digito'
    return True, None


def hash_password(plain: str) -> str:
    """Devuelve un hash bcrypt (con sal) de la contraseña en claro."""
    if plain is None:
        plain = ''
    return bcrypt.hashpw(plain.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')


def is_legacy_hash(stored: str) -> bool:
    """True si `stored` es un hash SHA-256 heredado (64 hex), no bcrypt."""
    return bool(stored) and bool(_SHA256_RE.match(stored.strip()))


def _sha256(plain: str) -> str:
    return hashlib.sha256(plain.encode('utf-8')).hexdigest()


def verify_password(plain: str, stored: str) -> bool:
    """
    Verifica la contraseña contra el hash almacenado.
    Soporta bcrypt (nuevo) y SHA-256 sin sal (heredado).
    """
    if not stored or plain is None:
        return False
    stored = stored.strip()

    if is_legacy_hash(stored):
        # Hash heredado SHA-256: comparación en tiempo constante.
        return hmac.compare_digest(_sha256(plain), stored.lower())

    # bcrypt
    try:
        return bcrypt.checkpw(plain.encode('utf-8'), stored.encode('utf-8'))
    except (ValueError, TypeError):
        return False
