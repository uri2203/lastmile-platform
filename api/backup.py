"""
BACKUP AUTOMATIZADO - Last Mile Delivery System
Exporta datos criticos de DB2/400 TESTLIB a JSON diariamente.

Uso:
  python backup.py              # Backup completo
  python backup.py --tables     # Solo tablas especificas
  
Cron (Linux): 0 2 * * * cd /path/to/api && python backup.py
Task Scheduler (Windows): C:\Python314\python.exe backup.py
"""
import jaydebeapi
import json
import os
import sys
from datetime import datetime
from dotenv import load_dotenv

load_dotenv(os.path.join(os.path.dirname(__file__), '.env'))

BACKUP_DIR = os.path.join(os.path.dirname(__file__), 'backups')
os.makedirs(BACKUP_DIR, exist_ok=True)

# Tablas criticas para backup
CRITICAL_TABLES = [
    'EMPRESAS', 'USUARIOS', 'PEDIDOS', 'PEDIDO_HISTORIAL',
    'CHOFERES', 'VEHICULOS', 'CLIENTES_LM', 'CLIENTE_FINAL',
    'ZONAS', 'ZONA_TARIFAS',
    'CFDI_FACTURAS', 'CFDI_FOLIOS', 'CFDI_TIMBRADO_LOG',
    'PAGOS_TRANSACCIONES', 'PAGOS_METODOS',
    'AUDIT_LOG', 'TRACKING',
    'SAAS_PLANES', 'SAAS_SUSCRIPCIONES', 'SAAS_COBROS',
    'NOTIF_PUSH', 'EMAIL_ENVIADOS', 'SMS_ENVIADOS',
]

def get_db():
    return jaydebeapi.connect(
        os.environ.get('DB_DRIVER_CLASS', 'com.ibm.as400.access.AS400JDBCDriver'),
        os.environ.get('DB_URL', 'jdbc:as400://192.168.0.240;errors=full'),
        [os.environ.get('DB_USER', 'AYUDATX'), os.environ.get('DB_PASS', '')],
        os.path.join(os.path.dirname(__file__), '..', '..', 'BOOT-INF', 'lib', 'jt400-21.0.6.jar')
    )

def backup_table(conn, table_name, emp_id_filter=None):
    """Export a single table to JSON"""
    cursor = conn.cursor()
    sql = f"SELECT * FROM TESTLIB.{table_name}"
    params = []
    if emp_id_filter and table_name not in ('EMPRESAS', 'SAAS_PLANES'):
        try:
            sql += " WHERE EMP_ID = ?"
            params = [emp_id_filter]
        except:
            pass
    sql += " FETCH FIRST 5000 ROWS ONLY"
    
    cursor.execute(sql, params)
    columns = [desc[0] for desc in cursor.description] if cursor.description else []
    rows = []
    for row in cursor.fetchall():
        rows.append(dict(zip(columns, [str(c) if c is not None else None for c in row])))
    cursor.close()
    return rows

def run_backup(emp_id=None):
    """Run full backup"""
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    backup_path = os.path.join(BACKUP_DIR, f'backup_{timestamp}')
    os.makedirs(backup_path, exist_ok=True)
    
    print(f'\n  BACKUP INICIADO: {timestamp}')
    print(f'  Directorio: {backup_path}\n')
    
    conn = get_db()
    manifest = {
        'timestamp': timestamp,
        'tables': {},
        'errors': []
    }
    
    for table in CRITICAL_TABLES:
        try:
            data = backup_table(conn, table, emp_id)
            filename = f'{table.lower()}.json'
            filepath = os.path.join(backup_path, filename)
            with open(filepath, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2, ensure_ascii=False, default=str)
            
            manifest['tables'][table] = {
                'rows': len(data),
                'file': filename,
                'size_bytes': os.path.getsize(filepath)
            }
            print(f'  [OK]  {table}: {len(data)} registros')
        except Exception as e:
            manifest['errors'].append({'table': table, 'error': str(e)})
            print(f'  [ERR] {table}: {str(e)[:60]}')
    
    # Save manifest
    with open(os.path.join(backup_path, 'manifest.json'), 'w') as f:
        json.dump(manifest, f, indent=2)
    
    total_tables = len(manifest['tables'])
    total_errors = len(manifest['errors'])
    total_size = sum(t['size_bytes'] for t in manifest['tables'].values())
    
    print(f'\n  BACKUP COMPLETADO')
    print(f'  Tablas: {total_tables}/{len(CRITICAL_TABLES)} OK')
    if total_errors:
        print(f'  Errores: {total_errors}')
    print(f'  Tamano total: {total_size/1024:.1f} KB')
    print(f'  Ruta: {backup_path}\n')
    
    conn.close()
    return manifest

if __name__ == '__main__':
    emp_id = None
    if '--emp' in sys.argv:
        idx = sys.argv.index('--emp')
        if idx + 1 < len(sys.argv):
            emp_id = int(sys.argv[idx + 1])
    
    run_backup(emp_id)
