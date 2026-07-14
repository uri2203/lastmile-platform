"""
MIGRATION SCRIPT: AS/400 (JSON backup) -> SQLite
Importa todos los datos del backup JSON a la base SQLite.
"""
import sqlite3
import json
import os
from datetime import datetime

DATA_DIR = os.environ.get('DATA_DIR', os.path.dirname(os.path.abspath(__file__)))
BACKUP_DIR = os.path.join(DATA_DIR, 'backups', 'backup_20260714_095601')
DB_PATH = os.path.join(DATA_DIR, 'lastmile.db')

# Map backup JSON filenames to SQLite table names
TABLE_MAP = {
    'empresas': 'EMPRESAS',
    'usuarios': 'USUARIOS',
    'choferes': 'CHOFERES',
    'vehiculos': 'VEHICULOS',
    'clientes_lm': 'CLIENTES_LM',
    'pedidos': 'PEDIDOS',
    'pedido_historial': 'PEDIDO_HISTORIAL',
    'tracking': 'TRACKING',
    'zonas': 'ZONAS',
    'zona_tarifas': 'ZONA_TARIFAS',
    'cfdi_facturas': 'CFDI_FACTURAS',
    'cfdi_folios': 'CFDI_FOLIOS',
    'cfdi_timbrado_log': 'CFDI_TIMBRADO_LOG',
    'pagos_metodos': 'PAGOS_METODOS',
    'pagos_transacciones': 'PAGOS_TRANSACCIONES',
    'audit_log': 'AUDIT_LOG',
    'cliente_final': 'CLIENTE_FINAL',
    'saas_planes': 'SAAS_PLANES',
    'saas_suscripciones': 'SAAS_SUSCRIPCIONES',
    'saas_cobros': 'SAAS_COBROS',
    'notif_push': 'NOTIF_PUSH',
    'email_enviados': 'EMAIL_ENVIADOS',
    'sms_enviados': 'SMS_ENVIADOS',
}

# Columns to skip (will be auto-generated or not in SQLite)
SKIP_COLS = set()


def clean_value(v):
    """Clean a value for SQLite insertion."""
    if v is None:
        return None
    if isinstance(v, str):
        v = v.strip()
        # Handle DB2/400 specific values
        if v == '':
            return None
        # Handle numeric strings that came from DB2
        # Try to preserve as-is, SQLite is flexible
    # Handle dict/list (JSON fields)
    if isinstance(v, (dict, list)):
        return json.dumps(v)
    return v


def migrate():
    """Run the full migration."""
    if not os.path.exists(BACKUP_DIR):
        print(f"Backup directory not found: {BACKUP_DIR}")
        print("Run backup.py first to export data from AS/400")
        return

    conn = sqlite3.connect(DB_PATH)
    conn.execute("PRAGMA journal_mode=WAL")
    conn.execute("PRAGMA foreign_keys=OFF")  # Disable during migration
    cursor = conn.cursor()

    total_rows = 0
    errors = []

    for json_file, table_name in TABLE_MAP.items():
        json_path = os.path.join(BACKUP_DIR, f'{json_file}.json')
        if not os.path.exists(json_path):
            print(f"  [SKIP] {json_file}.json not found")
            continue

        with open(json_path, 'r', encoding='utf-8') as f:
            data = json.load(f)

        if not data:
            print(f"  [SKIP] {json_file}: 0 records")
            continue

        # Get column names from first record
        columns = list(data[0].keys())

        # Filter out columns that don't exist in SQLite table
        cursor.execute(f"PRAGMA table_info({table_name})")
        existing_cols = {row[1] for row in cursor.fetchall()}

        valid_cols = [col for col in columns if col in existing_cols]
        if not valid_cols:
            print(f"  [SKIP] {json_file}: no matching columns for {table_name}")
            continue

        placeholders = ','.join(['?' for _ in valid_cols])
        col_names = ','.join(valid_cols)

        inserted = 0
        for row in data:
            values = []
            for col in valid_cols:
                val = row.get(col)
                values.append(clean_value(val))

            try:
                cursor.execute(
                    f'INSERT OR IGNORE INTO {table_name} ({col_names}) VALUES ({placeholders})',
                    values
                )
                inserted += 1
            except sqlite3.IntegrityError as e:
                pass  # Skip duplicates
            except Exception as e:
                errors.append(f"{table_name}: {str(e)[:80]}")

        total_rows += inserted
        print(f"  [OK]  {table_name}: {inserted}/{len(data)} rows imported")

    conn.execute("PRAGMA foreign_keys=ON")
    conn.commit()
    conn.close()

    print(f"\n  MIGRATION COMPLETE: {total_rows} total rows")
    if errors:
        print(f"  Errors: {len(errors)}")
        for e in errors[:5]:
            print(f"    - {e}")
    print(f"  Database: {DB_PATH}")
    print(f"  Size: {os.path.getsize(DB_PATH)/1024:.1f} KB")


if __name__ == '__main__':
    migrate()
