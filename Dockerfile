FROM python:3.11-slim

ARG CACHEBUST=1

WORKDIR /app

# Install dependencies
COPY api/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application
COPY api/ .

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
