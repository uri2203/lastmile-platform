# syntax=docker/dockerfile:1

FROM python:3.11.8-slim

RUN apt-get update && apt-get install -y dos2unix && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Install dependencies
COPY api/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application
COPY api/ .

# Normalize line endings - fix any CRLF from Windows git
RUN find . -name "*.py" -exec dos2unix {} + 2>/dev/null; echo "Line endings normalized"

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
