#!/bin/bash
# ESPAlert Database Backup Script

set -e

BACKUP_DIR="/home/$USER/backups/espalert"
TIMESTAMP=$(date +"%Y%m%d_%H%M%S")
FILENAME="espalert_db_backup_$TIMESTAMP.sql.gz"
GPG_RECIPIENT="${BACKUP_GPG_RECIPIENT:-}"

mkdir -p $BACKUP_DIR

echo "💾 Starting database backup: $FILENAME"

# Performance backup from Docker container
docker compose -f /home/$USER/espalert/docker-compose.prod.yml exec -t db pg_dump -U espalert espalert | gzip > "$BACKUP_DIR/$FILENAME"

# Encrypt with GPG if a recipient is configured
if [ -n "$GPG_RECIPIENT" ]; then
    gpg --batch --yes --recipient "$GPG_RECIPIENT" --encrypt "$BACKUP_DIR/$FILENAME"
    rm -f "$BACKUP_DIR/$FILENAME"
    FILENAME="${FILENAME}.gpg"
    echo "🔒 Backup encrypted with GPG"
fi

# Retention: Delete backups older than 30 days
find $BACKUP_DIR -name "espalert_db_backup_*" -mtime +30 -delete

echo "✅ Backup complete. Stored in $BACKUP_DIR"

# Optional: Sync to S3 or remote storage here
# rclone copy $BACKUP_DIR remote:bucket/espalert/backups
