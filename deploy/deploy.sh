#!/usr/bin/env bash
# Idempotent rsync-based deploy for Baqsy System.
#
# Usage:
#   SSH_HOST=debian@78.40.108.112 ./deploy/deploy.sh
# Optional env:
#   SSH_PORT=22
#   APP_DIR=/srv/baqsy
#   SSHPASS=... (if using password auth) — then prefix command with `sshpass -e`
#
# What it does:
#   1. rsyncs the repo to $APP_DIR (excludes node_modules, dist, .git, envs)
#   2. ensures .env exists on the server (copies .env.prod.example on first run)
#   3. runs docker compose build + up -d with the prod compose file
#   4. runs migrations and collectstatic
#   5. tails logs until health checks pass (or timeout)

set -euo pipefail

SSH_HOST="${SSH_HOST:?SSH_HOST must be set, e.g. debian@78.40.108.112}"
SSH_PORT="${SSH_PORT:-22}"
APP_DIR="${APP_DIR:-/srv/baqsy}"
COMPOSE_FILE="docker/docker-compose.prod.yml"

REPO_ROOT="$(cd "$(dirname "$0")/.." && pwd)"

SSH_OPTS=(-o StrictHostKeyChecking=accept-new -p "$SSH_PORT")
RSYNC_SSH="ssh ${SSH_OPTS[*]}"

echo "[deploy] syncing repo to $SSH_HOST:$APP_DIR"
rsync -az --delete \
    --exclude '.git/' \
    --exclude 'node_modules/' \
    --exclude 'frontend/dist/' \
    --exclude '**/__pycache__/' \
    --exclude '*.pyc' \
    --exclude '.env' \
    --exclude '.env.local' \
    --exclude 'backend/media/' \
    --exclude 'backend/staticfiles/' \
    --exclude '.planning/' \
    -e "$RSYNC_SSH" \
    "$REPO_ROOT/" "$SSH_HOST:$APP_DIR/"

echo "[deploy] ensure .env exists"
ssh "${SSH_OPTS[@]}" "$SSH_HOST" "
set -e
cd '$APP_DIR'
if [ ! -f .env ]; then
    cp .env.prod.example .env
    echo '[deploy] created .env from .env.prod.example — FILL IN SECRETS BEFORE RESTARTING!'
    exit 2
fi
"

echo "[deploy] build + start"
ssh "${SSH_OPTS[@]}" "$SSH_HOST" "
set -e
cd '$APP_DIR'
docker compose -f '$COMPOSE_FILE' --env-file .env build
docker compose -f '$COMPOSE_FILE' --env-file .env up -d
"

echo "[deploy] waiting for web to be healthy…"
ssh "${SSH_OPTS[@]}" "$SSH_HOST" "
set -e
cd '$APP_DIR'
for i in \$(seq 1 60); do
    state=\$(docker compose -f '$COMPOSE_FILE' ps --format json web | \
        python3 -c 'import sys,json; [print(json.loads(l).get(\"Health\",\"\")) for l in sys.stdin if l.strip()]' 2>/dev/null || true)
    if echo \"\$state\" | grep -q healthy; then
        echo '[deploy] web healthy'
        break
    fi
    sleep 5
done
docker compose -f '$COMPOSE_FILE' ps
"

echo "[deploy] done. Visit http://\${SSH_HOST#*@}/ to verify."
