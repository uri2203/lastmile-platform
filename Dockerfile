# syntax=docker/dockerfile:1

FROM python:3.11.8-slim

WORKDIR /app

# Install dependencies
COPY api/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application
COPY api/ .

# Fix line endings using Python (always available)
RUN python3 -c "
import os, glob
for f in glob.glob('**/*.py', recursive=True):
    with open(f, 'rb') as fh:
        data = fh.read()
    cr = data.count(b'\r')
    lf = data.count(b'\n')
    print(f'{f}: {len(data)} bytes, CR={cr}, LF={lf}')
    if b'\r' in data:
        print(f'  -> Fixing CRLF in {f}')
        data = data.replace(b'\r\n', b'\n').replace(b'\r', b'\n')
        with open(f, 'wb') as fh:
            fh.write(data)
        print(f'  -> Fixed: {len(data)} bytes after fix')
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
