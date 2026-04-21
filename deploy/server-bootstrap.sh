#!/usr/bin/env bash
# One-time VPS bootstrap. Run AS root OR with sudo.
#
#   curl -fsSL https://<your-repo>/raw/main/deploy/server-bootstrap.sh | sudo bash
# or copy this file to the server and:
#   sudo bash server-bootstrap.sh
#
# Installs Docker Engine + Compose plugin, creates the /srv/baqsy dir, opens
# ports 80/443, and leaves an idle server ready for rsync-based deploys.

set -euo pipefail

APP_DIR="${APP_DIR:-/srv/baqsy}"
DEPLOY_USER="${DEPLOY_USER:-debian}"

echo "[bootstrap] apt update + base tools"
apt-get update -y
apt-get install -y --no-install-recommends \
    ca-certificates curl gnupg lsb-release ufw rsync

if ! command -v docker >/dev/null 2>&1; then
    echo "[bootstrap] installing Docker Engine"
    install -m 0755 -d /etc/apt/keyrings
    curl -fsSL https://download.docker.com/linux/debian/gpg \
        | gpg --dearmor -o /etc/apt/keyrings/docker.gpg
    chmod a+r /etc/apt/keyrings/docker.gpg
    echo "deb [arch=$(dpkg --print-architecture) signed-by=/etc/apt/keyrings/docker.gpg] \
https://download.docker.com/linux/debian $(lsb_release -cs) stable" \
        > /etc/apt/sources.list.d/docker.list
    apt-get update -y
    apt-get install -y docker-ce docker-ce-cli containerd.io docker-buildx-plugin docker-compose-plugin
    systemctl enable --now docker
fi

echo "[bootstrap] adding $DEPLOY_USER to docker group"
usermod -aG docker "$DEPLOY_USER" || true

echo "[bootstrap] creating app dir at $APP_DIR"
mkdir -p "$APP_DIR"
chown -R "$DEPLOY_USER":"$DEPLOY_USER" "$APP_DIR"

echo "[bootstrap] firewall"
ufw allow OpenSSH >/dev/null 2>&1 || true
ufw allow 80/tcp  >/dev/null 2>&1 || true
ufw allow 443/tcp >/dev/null 2>&1 || true
yes | ufw enable >/dev/null 2>&1 || true

echo "[bootstrap] docker version:"
docker --version
docker compose version

echo "[bootstrap] done. App dir: $APP_DIR"
