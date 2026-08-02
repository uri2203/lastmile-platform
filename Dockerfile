# syntax=docker/dockerfile:1

FROM python:3.11.8-slim

WORKDIR /app

# Install dependencies
COPY api/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application
COPY --link api/ .

# DEBUG: Show exact content Docker sees at the problem area
RUN echo "=== FILE SIZE ===" && wc -l server.py && echo "=== MD5 ===" && md5sum server.py && echo "=== LINES 1185-1200 ===" && cat -n server.py | sed -n '1185,1200p' && echo "=== SEARCH except without try ===" && grep -n "except" server.py | head -5 && echo "=== AREA AROUND 1192 ===" && python3 -c "
with open('server.py','r') as f:
    lines = f.readlines()
print(f'Total lines: {len(lines)}')
for i in range(1185, min(1200, len(lines))):
    print(f'{i+1}: {repr(lines[i])}')" && echo "=== END DEBUG ==="

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
