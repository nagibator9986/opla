#!/bin/bash
set -euo pipefail

# Configuration from environment
DB_HOST="${POSTGRES_HOST:-db}"
DB_PORT="${POSTGRES_PORT:-5432}"
DB_NAME="${POSTGRES_DB:-baqsy}"
DB_USER="${POSTGRES_USER:-baqsy}"
MINIO_ALIAS="${MINIO_ALIAS:-local}"
MINIO_BUCKET="${MINIO_BUCKET:-baqsy}"
BACKUP_PREFIX="backups/db"
RETENTION_DAYS="${BACKUP_RETENTION_DAYS:-7}"

TIMESTAMP=$(date +%Y-%m-%d_%H-%M-%S)
FILENAME="${DB_NAME}_${TIMESTAMP}.sql.gz"
REMOTE_PATH="${MINIO_ALIAS}/${MINIO_BUCKET}/${BACKUP_PREFIX}/${FILENAME}"

echo "[backup] Starting PostgreSQL backup: ${FILENAME}"

# Dump and compress
PGPASSWORD="${POSTGRES_PASSWORD}" pg_dump \
    -h "${DB_HOST}" \
    -p "${DB_PORT}" \
    -U "${DB_USER}" \
    -d "${DB_NAME}" \
    --no-owner \
    --no-acl \
    | gzip > "/tmp/${FILENAME}"

FILESIZE=$(du -h "/tmp/${FILENAME}" | cut -f1)
echo "[backup] Dump complete: ${FILESIZE}"

# Upload to MinIO
mc cp "/tmp/${FILENAME}" "${REMOTE_PATH}"
echo "[backup] Uploaded to ${REMOTE_PATH}"

# Clean up local file
rm -f "/tmp/${FILENAME}"

# Remove old backups (older than RETENTION_DAYS)
echo "[backup] Cleaning backups older than ${RETENTION_DAYS} days..."
mc find "${MINIO_ALIAS}/${MINIO_BUCKET}/${BACKUP_PREFIX}/" \
    --older-than "${RETENTION_DAYS}d" \
    --exec "mc rm {}" 2>/dev/null || true

echo "[backup] Done."
