# syntax=docker/dockerfile:1

FROM python:3.11.8-slim

WORKDIR /app

# Install dependencies
COPY api/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application
COPY --link api/ .

# DEBUG: Show exact bytes Docker sees
RUN python3 -c "
with open('server.py', 'rb') as f:
    data = f.read()
lines = data.split(b'\n')
print(f'Total lines: {len(lines)}')
print(f'Total bytes: {len(data)}')
print(f'CR count: {data.count(b\"\\r\")}')
print(f'LF count: {data.count(b\"\\n\")}')
print()
print(f'Line 1190 bytes: {lines[1189][:80].hex()}')
print(f'Line 1190 text: {lines[1189][:80]}')
print(f'Line 1191 bytes: {lines[1190][:80].hex()}')
print(f'Line 1191 text: {lines[1190][:80]}')
print(f'Line 1192 bytes: {lines[1191][:80].hex()}')
print(f'Line 1192 text: {lines[1191][:80]}')
print(f'Line 1193 bytes: {lines[1192][:80].hex()}')
print(f'Line 1193 text: {lines[1192][:80]}')
print(f'Line 1194 bytes: {lines[1193][:80].hex()}')
print(f'Line 1194 text: {lines[1193][:80]}')
# Find which line has 'except Exception:' that is not inside a try block
print()
print('=== Structural check: try/except balance per function ===')
in_function = None
try_count = 0
except_count = 0
for i, line in enumerate(lines):
    stripped = line.strip()
    if stripped.startswith('def '):
        if in_function and try_count != except_count:
            print(f'  MISMATCH in {in_function}: try={try_count} except={except_count}')
        in_function = stripped.split('(')[0].replace('def ', '')
        try_count = 0
        except_count = 0
    if stripped == 'try:':
        try_count += 1
    if stripped.startswith('except'):
        except_count += 1
if in_function and try_count != except_count:
    print(f'  MISMATCH in {in_function}: try={try_count} except={except_count}')
"

# Validate syntax at build time
RUN python3 -c "import py_compile; py_compile.compile('server.py', doraise=True); print('SYNTAX OK: server.py')"

# Create data directory
RUN mkdir -p /data && chmod +x entrypoint.sh

# Set environment
ENV DATA_DIR=/data
ENV FLASK_ENV=production
ENV PORT=5000

EXPOSE 5000

CMD ["./entrypoint.sh"]
