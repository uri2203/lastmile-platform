"""
MIGRATION: SQLite -> PostgreSQL (Supabase)
Lee datos del lastmile.db local y los inserta en PostgreSQL.
Uso: python migrate_to_pg.py postgresql://user:pass@host/dbname
"""

import sqlite3
import os
import sys
import psycopg2
import psycopg2.extras

SQLITE_PATH = os.environ.get('SQLITE_PATH', os.path.join(os.path.dirname(__file__), 'lastmile.db'))

# Tables in order (respecting foreign keys)
TABLES = [
    'EMPRESAS', 'USUARIOS', 'CHOFERES', 'VEHICULOS', 'CLIENTES_LM',
    'PEDIDOS', 'PEDIDO_HISTORIAL', 'TRACKING', 'ZONAS', 'ZONA_TARIFAS',
    'CFDI_EMPRESA_FISCAL', 'CFDI_FOLIOS', 'CFDI_FACTURAS', 'CFDI_TIMBRADO_LOG',
    'CFDI_CONCEPTOS_CATALOGO', 'PAGOS_METODOS', 'PAGOS_TRANSACCIONES',
    'AUDIT_LOG', 'CLIENTE_FINAL', 'SAAS_PLANES', 'SAAS_SUSCRIPCIONES',
    'SAAS_COBROS', 'SAAS_USO_RECURSOS', 'NOTIF_PUSH', 'NOTIF_DISPOSITIVOS',
    'EMAIL_ENVIADOS', 'SMS_ENVIADOS', 'REPORTES_GENERADOS', 'ENTREGAS',
    'INCIDENCIAS', 'KPI_DIARIO'
]


def get_sqlite_data(table_name):
    """Read all rows from a SQLite table."""
    conn = sqlite3.connect(SQLITE_PATH)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    try:
        cursor.execute(f'SELECT * FROM {table_name}')
        rows = cursor.fetchall()
        columns = [desc[0] for desc in cursor.description] if cursor.description else []
        return columns, [dict(zip(columns, row)) for row in rows]
    except Exception as e:
        print(f'  SKIP {table_name}: {e}')
        return [], []
    finally:
        conn.close()


def insert_postgres(pg_conn, table_name, columns, rows):
    """Insert rows into PostgreSQL table."""
    if not rows:
        return 0

    cursor = pg_conn.cursor()

    # Build INSERT statement with %s placeholders
    placeholders = ', '.join(['%s'] * len(columns))
    col_names = ', '.join(columns)
    sql = f'INSERT INTO {table_name} ({col_names}) VALUES ({placeholders})'

    count = 0
    for row in rows:
        try:
            values = [row.get(col) for col in columns]
            cursor.execute(sql, values)
            count += 1
        except psycopg2.errors.UniqueViolation:
            pg_conn.rollback()
            continue
        except Exception as e:
            pg_conn.rollback()
            print(f'  ERROR on {table_name}: {e}')
            continue

    pg_conn.commit()
    return count


def migrate(pg_url):
    """Run full migration from SQLite to PostgreSQL."""
    if not os.path.exists(SQLITE_PATH):
        print(f'ERROR: SQLite database not found at {SQLITE_PATH}')
        sys.exit(1)

    print(f'[MIGRATE] SQLite: {SQLITE_PATH}')
    print(f'[MIGRATE] PostgreSQL: {pg_url.split("@")[-1] if "@" in pg_url else pg_url}')
    print()

    # Connect to PostgreSQL
    pg_conn = psycopg2.connect(pg_url)
    pg_conn.autocommit = False

    # First, run schema creation
    schema_path = os.path.join(os.path.dirname(__file__), 'schema_postgres.sql')
    if os.path.exists(schema_path):
        print('[MIGRATE] Creating PostgreSQL schema...')
        cursor = pg_conn.cursor()
        with open(schema_path, 'r') as f:
            cursor.execute(f.read())
        pg_conn.commit()
        print('[MIGRATE] Schema created OK')

    print()
    print('[MIGRATE] Migrating data...')
    print('=' * 60)

    total_rows = 0
    for table in TABLES:
        columns, rows = get_sqlite_data(table)
        if rows:
            inserted = insert_postgres(pg_conn, table, columns, rows)
            total_rows += inserted
            print(f'  {table:30s} -> {inserted:5d} rows (of {len(rows)})')
        else:
            print(f'  {table:30s} -> empty')

    pg_conn.close()

    print()
    print('=' * 60)
    print(f'[MIGRATE] DONE! Total: {total_rows} rows migrated')
    print(f'[MIGRATE] Run `python server.py` to test')


if __name__ == '__main__':
    if len(sys.argv) < 2:
        print('Usage: python migrate_to_pg.py postgresql://user:pass@host:port/dbname')
        print()
        print('For Supabase, get the URL from: Settings > Database > Connection string > URI')
        sys.exit(1)

    migrate(sys.argv[1])
