"""Verify all data migrated from AS/400 to SQLite"""
import sqlite3, os

DB = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'lastmile.db')
conn = sqlite3.connect(DB)
c = conn.cursor()

c.execute("SELECT name FROM sqlite_master WHERE type='table' ORDER BY name")
tables = [r[0] for r in c.fetchall()]

print(f'=== TABLAS EN SQLite ({len(tables)} total) ===')
print()
total = 0
for t in tables:
    c.execute(f'SELECT COUNT(*) FROM [{t}]')
    count = c.fetchone()[0]
    total += count
    status = 'OK' if count > 0 else 'VACIA'
    print(f'  {t:30s} {count:>6,} registros  [{status}]')

print(f'  {"":30s} {"-------":>6s}')
print(f'  {"TOTAL":30s} {total:>6,} registros')

c.execute("SELECT name FROM sqlite_master WHERE type='view' ORDER BY name")
views = [r[0] for r in c.fetchall()]
print(f'\n  Vistas: {len(views)}')
for v in views:
    print(f'    {v}')

conn.close()
