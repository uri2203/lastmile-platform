"""
Crea o actualiza un usuario SUPERADMIN (operador de la plataforma).

Es un COMANDO ADMINISTRATIVO: se ejecuta a mano en el servidor, NUNCA se expone
por HTTP. El superadmin es el unico rol que puede gestionar tenants globalmente
(/api/saas/*, /api/admin/*). No se puede crear por self-service.

USO:
    cd api
    python create_superadmin.py <usuario> <password>
  o con variables de entorno (util en Render / CI):
    SUPERADMIN_USER=... SUPERADMIN_PASS=... python create_superadmin.py

Usa la misma DATABASE_URL que la app (SQLite local o PostgreSQL/Supabase).
El superadmin se ubica en una empresa-plataforma dedicada ("PLATAFORMA"),
separada de los tenants cliente. Idempotente: si el usuario ya existe, lo
promueve a superadmin y actualiza su contraseña (bcrypt).
"""
import os
import sys

from db import query, execute
from security import hash_password

PLATFORM_NAME = 'PLATAFORMA'


def _platform_emp_id():
    """Devuelve el EMP_ID de la empresa-plataforma, creandola si no existe."""
    rows = query("SELECT EMP_ID FROM EMPRESAS WHERE EMP_NOMBRE = ?", [PLATFORM_NAME])
    if rows:
        return rows[0]['EMP_ID']
    execute(
        "INSERT INTO EMPRESAS (EMP_NOMBRE, EMP_RFC, EMP_EMAIL, EMP_TELEFONO, EMP_ESTATUS, EMP_PLAN, EMP_EMAIL_VERIFIED) "
        "VALUES (?, '', '', '', 'ACTIVA', 'PLATAFORMA', 'S')",
        [PLATFORM_NAME]
    )
    rows = query(
        "SELECT EMP_ID FROM EMPRESAS WHERE EMP_NOMBRE = ? ORDER BY EMP_ID DESC LIMIT 1",
        [PLATFORM_NAME]
    )
    return rows[0]['EMP_ID']


def create_or_update_superadmin(usuario, password):
    """Crea (o promueve) un usuario con rol 'superadmin'. Devuelve (accion, emp_id)."""
    if not usuario or not password:
        raise ValueError('usuario y password son requeridos')
    emp_id = _platform_emp_id()
    pass_hash = hash_password(password)
    existing = query("SELECT USU_ID FROM USUARIOS WHERE UPPER(USU_USUARIO) = UPPER(?)", [usuario])
    if existing:
        execute(
            "UPDATE USUARIOS SET USU_PASS=?, USU_ROL='superadmin', USU_EMP_ID=?, USU_ACTIVO='S' "
            "WHERE USU_ID=?",
            [pass_hash, emp_id, existing[0]['USU_ID']]
        )
        return ('actualizado', emp_id)
    execute(
        "INSERT INTO USUARIOS (USU_EMP_ID, USU_USUARIO, USU_PASS, USU_NOMBRE, USU_EMAIL, USU_ROL, USU_ACTIVO) "
        "VALUES (?, ?, ?, ?, '', 'superadmin', 'S')",
        [emp_id, usuario, pass_hash, f'Superadmin {usuario}']
    )
    return ('creado', emp_id)


if __name__ == '__main__':
    usuario = sys.argv[1] if len(sys.argv) > 1 else os.environ.get('SUPERADMIN_USER', '')
    password = sys.argv[2] if len(sys.argv) > 2 else os.environ.get('SUPERADMIN_PASS', '')
    if not usuario or not password:
        print('Uso: python create_superadmin.py <usuario> <password>')
        print('  (o define las variables de entorno SUPERADMIN_USER y SUPERADMIN_PASS)')
        sys.exit(1)
    accion, emp_id = create_or_update_superadmin(usuario, password)
    print(f'[SUPERADMIN] Usuario "{usuario}" {accion} (rol=superadmin, emp_id={emp_id}).')
