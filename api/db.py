"""
LAST MILE DELIVERY - Database Abstraction Layer
Soporte dual: SQLite (desarrollo/local) y PostgreSQL (Supabase/produccion).
Detecta automaticamente via variable de entorno DATABASE_URL.
Connection pooling para PostgreSQL. Thread-local connections.
"""

import os
import re
import threading

DATABASE_URL = os.environ.get('DATABASE_URL', '')

# ========================================
# DETECCION DE MOTOR
# ========================================
USE_POSTGRES = DATABASE_URL.startswith('postgres://') or DATABASE_URL.startswith('postgresql://')

if USE_POSTGRES:
    import psycopg2
    import psycopg2.extras
    import psycopg2.pool
    print(f'[DB] Using PostgreSQL (Supabase)')
else:
    import sqlite3
    DATA_DIR = os.environ.get('DATA_DIR', os.path.dirname(os.path.abspath(__file__)))
    DB_PATH = os.path.join(DATA_DIR, 'lastmile.db')
    print(f'[DB] Using SQLite ({DB_PATH})')


# ========================================
# CONNECTION POOLING (PostgreSQL)
# ========================================
_pool = None
_pool_lock = threading.Lock()

def _get_pool():
    """Get or create the connection pool (thread-safe, lazy init)."""
    global _pool
    if _pool is None:
        with _pool_lock:
            if _pool is None:
                try:
                    url = DATABASE_URL
                    if 'sslmode' not in url:
                        url += '&sslmode=require' if '?' in url else '?sslmode=require'
                    _pool = psycopg2.pool.ThreadedConnectionPool(
                        minconn=2,
                        maxconn=10,
                        dsn=url,
                        connect_timeout=10
                    )
                    print('[DB] Connection pool created (2-10 connections)')
                except Exception as e:
                    print(f'[DB] WARNING: Pool creation failed: {e}. Falling back to direct connections.')
                    _pool = None
    return _pool


# ========================================
# THREAD-LOCAL CONNECTIONS
# ========================================
_thread_local = threading.local()

def get_db():
    """Get database connection (PostgreSQL or SQLite).
    For PostgreSQL: uses connection pooling with thread-local connections.
    Each thread gets its own connection that persists for the request lifecycle.
    """
    if USE_POSTGRES:
        # Check if current thread already has an open connection
        conn = getattr(_thread_local, 'pg_conn', None)
        if conn and not conn.closed:
            # Check if connection is in a usable state (not in an aborted transaction)
            try:
                conn.isolation_level  # simple validity check
            except Exception:
                # Connection is broken, close and get a new one
                try:
                    conn.close()
                except Exception:
                    pass
                _thread_local.pg_conn = None
                conn = None
            if conn:
                return conn

        # Get from pool or create direct
        pool = _get_pool()
        if pool:
            conn = pool.getconn()
            # Reset connection state to clear any stale aborted transactions
            try:
                conn.rollback()
            except Exception:
                pass
        else:
            url = DATABASE_URL
            if 'sslmode' not in url:
                url += '&sslmode=require' if '?' in url else '?sslmode=require'
            conn = psycopg2.connect(url, connect_timeout=10)

        conn.autocommit = False
        _thread_local.pg_conn = conn
        return conn
    else:
        conn = sqlite3.connect(DB_PATH)
        conn.row_factory = sqlite3.Row
        conn.execute("PRAGMA journal_mode=WAL")
        conn.execute("PRAGMA busy_timeout=5000")
        conn.execute("PRAGMA foreign_keys=ON")
        return conn


def set_tenant_context(emp_id):
    """Set the current tenant ID for Row-Level Security (PostgreSQL only).
    Sets the session variable on the SAME connection used for subsequent queries.
    Prefers the SQL function set_current_tenant() (migration 004) when available,
    falls back to raw SET for backward compatibility.
    """
    if not USE_POSTGRES or emp_id is None:
        return
    try:
        conn = get_db()
        cursor = conn.cursor()
        try:
            cursor.execute("SELECT set_current_tenant(%s)", [int(emp_id)])
        except Exception:
            cursor.execute("SET app.current_emp_id = %s", [str(emp_id)])
        conn.commit()
        cursor.close()
    except Exception:
        pass  # RLS not enabled or SQLite


def _release_conn():
    """Release the current thread's PostgreSQL connection back to the pool."""
    conn = getattr(_thread_local, 'pg_conn', None)
    if conn is None or conn.closed:
        return
    pool = _get_pool()
    if pool:
        try:
            pool.putconn(conn)
        except Exception:
            pass
    else:
        try:
            conn.close()
        except Exception:
            pass
    _thread_local.pg_conn = None


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
        if USE_POSTGRES:
            _release_conn()
        else:
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
        if USE_POSTGRES:
            _release_conn()
        else:
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
        _release_conn()


def init_schema():
    """Initialize database schema. Creates all tables if they don't exist."""
    if USE_POSTGRES:
        _init_postgres_schema()
    else:
        from database import init_db
        init_db()


def _init_postgres_schema():
    """Create all tables and views in PostgreSQL.
    Uses a dedicated connection that is ALWAYS closed after init (never returned to pool).
    This avoids poisoning the pool with aborted transactions."""
    schema_path = os.path.join(os.path.dirname(__file__), 'schema_postgres.sql')
    if not os.path.exists(schema_path):
        print('[DB] WARNING: schema_postgres.sql not found')
        return

    with open(schema_path, 'r') as f:
        schema_sql = f.read()

    # Use a DEDICATED connection, not the pool — close it regardless of success/failure.
    url = DATABASE_URL
    if 'sslmode' not in url:
        url += '&sslmode=require' if '?' in url else '?sslmode=require'
    conn = None
    try:
        conn = psycopg2.connect(url, connect_timeout=10)
        conn.autocommit = False
        cursor = conn.cursor()
        cursor.execute(schema_sql)
        conn.commit()
        cursor.close()
        print('[DB] PostgreSQL schema initialized')
    except Exception as e:
        if conn:
            try:
                conn.rollback()
            except Exception:
                pass
        print(f'[DB] Schema init error (rolled back): {e}')
    finally:
        if conn:
            try:
                conn.close()
            except Exception:
                pass


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
            'path': 'Supabase Cloud',
            'pool_active': _pool is not None
        }
    else:
        return {
            'type': 'SQLite',
            'path': DB_PATH,
            'size_kb': round(os.path.getsize(DB_PATH) / 1024, 1) if os.path.exists(DB_PATH) else 0
        }
