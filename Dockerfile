FROM python:3.11.9-slim

WORKDIR /app

# Install dependencies first (layer cached separately)
COPY api/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Force cache invalidation: use a RUN that changes per-build
# This ensures the COPY layer below is always rebuilt
RUN python3 -c "import secrets; print(secrets.token_hex(8))" > /dev/null

# Copy application code - always fresh due to RUN above
COPY api/ .

# DEBUG: Show what Docker actually has at the problem area
RUN echo "=== DEBUG: Lines 1185-1200 of server.py ===" && sed -n '1185,1200p' server.py && echo "=== DEBUG: Total lines ===" && wc -l server.py && echo "=== DEBUG: MD5 ===" && md5sum server.py && echo "=== DEBUG: file size ===" && ls -la server.py

# Validate syntax at build time - WILL FAIL BUILD if server.py has syntax errors
RUN python3 -c "import py_compile; py_compile.compile('server.py', doraise=True); print('SYNTAX OK: server.py')"

# Create data directory
RUN mkdir -p /data && chmod +x entrypoint.sh

# Set environment
ENV DATA_DIR=/data
ENV FLASK_ENV=production
ENV PORT=5000

EXPOSE 5000

CMD ["./entrypoint.sh"]
