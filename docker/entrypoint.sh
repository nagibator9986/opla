#!/usr/bin/env bash
set -euo pipefail

echo "[entrypoint] Waiting for PostgreSQL at db:5432..."
until nc -z db 5432; do sleep 1; done
echo "[entrypoint] Waiting for Redis at redis:6379..."
until nc -z redis 6379; do sleep 1; done
echo "[entrypoint] Waiting for MinIO at minio:9000..."
until nc -z minio 9000; do sleep 1; done

echo "[entrypoint] Running migrations..."
python manage.py migrate --noinput

echo "[entrypoint] Collecting static files..."
python manage.py collectstatic --noinput || true

echo "[entrypoint] Starting gunicorn..."
exec gunicorn baqsy.wsgi:application \
  --bind 0.0.0.0:8000 \
  --workers "${GUNICORN_WORKERS:-2}" \
  --threads "${GUNICORN_THREADS:-2}" \
  --timeout 120 \
  --access-logfile - \
  --error-logfile -
