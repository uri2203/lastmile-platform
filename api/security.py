"""
Hashing de contraseñas con bcrypt, con verificación compatible hacia atrás.

- hash_password(plain)         -> hash bcrypt (str)
- verify_password(plain, hash) -> bool; acepta bcrypt (nuevo) y SHA-256 sin sal (heredado)
- is_legacy_hash(hash)         -> True si el hash es SHA-256 heredado (necesita migrar)

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
