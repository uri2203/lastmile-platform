#!/bin/bash
# Last Mile Delivery - Database Backup Script
# Run via cron: 0 2 * * * /path/to/backup.sh
# Or manually: ./backup.sh

BACKUP_DIR="/data/backups"
URL="https://lastmile-platform.onrender.com/api/cron/backup/download"
KEY="${CRON_API_KEY:-lastmile-cron-2026}"
DATE=$(date +%Y%m%d_%H%M%S)
FILE="$BACKUP_DIR/lastmile_backup_$DATE.json"

mkdir -p "$BACKUP_DIR"

echo "[BACKUP] Starting backup at $(date)"
curl -s -o "$FILE" "$URL?key=$KEY"

if [ -f "$FILE" ] && [ -s "$FILE" ]; then
    SIZE=$(wc -c < "$FILE")
    echo "[BACKUP] Success: $FILE ($SIZE bytes)"
    # Keep only last 7 backups
    ls -t "$BACKUP_DIR"/lastmile_backup_*.json 2>/dev/null | tail -n +8 | xargs rm -f 2>/dev/null
    echo "[BACKUP] Cleanup done"
else
    echo "[BACKUP] FAILED"
    rm -f "$FILE"
fi
