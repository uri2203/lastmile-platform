#!/bin/bash
set -e

# Production entrypoint: creates superadmin if env vars are set, then starts gunicorn
echo "[ENTRYPOINT] Last Mile Delivery - Production Setup"

# Create superadmin if env vars are provided
if [ -n "$SUPERADMIN_USER" ] && [ -n "$SUPERADMIN_PASS" ]; then
    echo "[ENTRYPOINT] Creating superadmin: $SUPERADMIN_USER"
    python create_superadmin.py "$SUPERADMIN_USER" "$SUPERADMIN_PASS"
fi

# Start gunicorn
echo "[ENTRYPOINT] Starting gunicorn..."
exec gunicorn server:app \
    --bind "0.0.0.0:${PORT:-8080}" \
    --workers "${GUNICORN_WORKERS:-4}" \
    --timeout "${GUNICORN_TIMEOUT:-120}" \
    --graceful-timeout 30 \
    --keep-alive 5 \
    --max-requests 1000 \
    --max-requests-jitter 50 \
    --access-logfile - \
    --error-logfile -
