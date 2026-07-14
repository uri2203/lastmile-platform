"""
LAST MILE DELIVERY - Database Abstraction Layer
Soporte dual: SQLite (desarrollo/local) y PostgreSQL (Supabase/produccion).
Detecta automaticamente via variable de entorno DATABASE_URL.
"""

import os
import re

DATABASE_URL = os.environ.get('DATABASE_URL', '')

# ========================================
# DETECCION DE MOTOR
# ========================================
USE_POSTGRES = DATABASE_URL.startswith('postgres://') or DATABASE_URL.startswith('postgresql://')

if USE_POSTGRES:
    import psycopg2
    import psycopg2.extras
    print(f'[DB] Using PostgreSQL (Supabase)')
else:
    import sqlite3
    DATA_DIR = os.environ.get('DATA_DIR', os.path.dirname(os.path.abspath(__file__)))
    DB_PATH = os.path.join(DATA_DIR, 'lastmile.db')
    print(f'[DB] Using SQLite ({DB_PATH})')


def get_db():
    """Get database connection (PostgreSQL or SQLite)."""
    if USE_POSTGRES:
        url = DATABASE_URL
        if 'sslmode' not in url:
            url += '&sslmode=require' if '?' in url else '?sslmode=require'
        conn = psycopg2.connect(url, connect_timeout=10)
        conn.autocommit = False
        return conn
    else:
        conn = sqlite3.connect(DB_PATH)
        conn.row_factory = sqlite3.Row
        conn.execute("PRAGMA journal_mode=WAL")
        conn.execute("PRAGMA busy_timeout=5000")
        conn.execute("PRAGMA foreign_keys=ON")
        return conn


def _translate_sql(sql):
    """
    Translate SQLite-specific SQL to PostgreSQL-compatible SQL.
    - ? placeholders -> %s
    - datetime('now') -> NOW()
    - date('now') -> CURRENT_DATE
    - date('now', '-30 days') -> CURRENT_DATE - INTERVAL '30 days'
    - julianday(...) -> EXTRACT(EPOCH FROM (...::timestamp))
    - AUTOINCREMENT -> (removed, SERIAL handles it)
    """
    if not USE_POSTGRES:
        return sql

    # Replace ? with %s for psycopg2
    result = sql
    result = result.replace('?', '%s')

    # SQLite date functions -> PostgreSQL
    result = re.sub(r"datetime\('now'\)", "NOW()", result)
    result = re.sub(r"date\('now'\)", "CURRENT_DATE", result)
    result = re.sub(
        r"date\('now',\s*'([-+]\d+)\s+(day|month|year)s?\)",
        r"CURRENT_DATE - INTERVAL '\1 \2'",
        result
    )
    # Handle julianday subtraction: (julianday(x) - julianday(y)) * 24
    result = re.sub(
        r"\(julianday\(([^)]+)\)\s*-\s*julianday\(([^)]+)\)\)\s*\*\s*24",
        r"EXTRACT(EPOCH FROM (\1::timestamp - \2::timestamp)) / 3600",
        result
    )

    return result


def _row_to_dict(cursor, row):
    """Convert a database row to a dictionary (uppercase keys for consistency)."""
    if USE_POSTGRES:
        columns = [desc[0].upper() for desc in cursor.description]
        return dict(zip(columns, row))
    else:
        return dict(row)


def query(sql, params=None):
    """Execute a SELECT and return list of dicts."""
    sql_translated = _translate_sql(sql)
    conn = get_db()
    try:
        cursor = conn.cursor()
        cursor.execute(sql_translated, params or [])
        rows = cursor.fetchall()
        result = [_row_to_dict(cursor, row) for row in rows]
        cursor.close()
        return result
    finally:
        conn.close()


def execute(sql, params=None):
    """Execute an INSERT/UPDATE/DELETE and return affected rows."""
    sql_translated = _translate_sql(sql)
    conn = get_db()
    try:
        cursor = conn.cursor()
        cursor.execute(sql_translated, params or [])
        conn.commit()
        affected = cursor.rowcount
        cursor.close()
        return affected
    finally:
        conn.close()


def execute_returning(sql, params=None):
    """Execute INSERT with RETURNING clause (PostgreSQL only)."""
    if not USE_POSTGRES:
        execute(sql, params)
        return None

    sql_translated = _translate_sql(sql)
    conn = get_db()
    try:
        cursor = conn.cursor()
        cursor.execute(sql_translated, params or [])
        result = cursor.fetchone()
        conn.commit()
        cursor.close()
        return result[0] if result else None
    finally:
        conn.close()


def init_schema():
    """Initialize database schema. Creates all tables if they don't exist."""
    if USE_POSTGRES:
        _init_postgres_schema()
    else:
        from database import init_db
        init_db()


def _init_postgres_schema():
    """Create all tables and views in PostgreSQL."""
    schema_path = os.path.join(os.path.dirname(__file__), 'schema_postgres.sql')
    if os.path.exists(schema_path):
        with open(schema_path, 'r') as f:
            schema_sql = f.read()
        conn = get_db()
        try:
            cursor = conn.cursor()
            cursor.execute(schema_sql)
            conn.commit()
            cursor.close()
            print('[DB] PostgreSQL schema initialized')
        finally:
            conn.close()
    else:
        print('[DB] WARNING: schema_postgres.sql not found')


def check_empty():
    """Check if the database has data (empresas table)."""
    try:
        rows = query("SELECT COUNT(*) as TOTAL FROM EMPRESAS")
        return rows[0]['TOTAL'] == 0
    except Exception:
        return True


def get_db_info():
    """Return database info for health checks."""
    if USE_POSTGRES:
        return {
            'type': 'PostgreSQL',
            'url': DATABASE_URL.split('@')[-1] if '@' in DATABASE_URL else 'connected',
            'path': 'Supabase Cloud'
        }
    else:
        return {
            'type': 'SQLite',
            'path': DB_PATH,
            'size_kb': round(os.path.getsize(DB_PATH) / 1024, 1) if os.path.exists(DB_PATH) else 0
        }
