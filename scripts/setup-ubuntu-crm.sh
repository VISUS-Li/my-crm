#!/usr/bin/env bash
# One-time CRM backend setup on Ubuntu.
# Run on the server: bash ~/crm-src/scripts/setup-ubuntu-crm.sh
#
# Uses an isolated MariaDB container (port 3307) and existing Redis (6379).
# CRM web port defaults to 8010 (8000 is occupied by casdoor on this server).

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
CRM_SRC="${CRM_SRC:-$(cd "$SCRIPT_DIR/.." && pwd)}"
BENCH_DIR="${BENCH_DIR:-$HOME/frappe-bench}"
DB_ROOT_PASSWORD="${DB_ROOT_PASSWORD:-crm123456}"
ADMIN_PASSWORD="${ADMIN_PASSWORD:-admin}"
SITE_NAME="${SITE_NAME:-crm.localhost}"
WEB_PORT="${WEB_PORT:-8010}"
SOCKETIO_PORT="${SOCKETIO_PORT:-9010}"
SUDO_PASSWORD="${SUDO_PASSWORD:-123456}"

sudo_cmd() {
  echo "${SUDO_PASSWORD}" | sudo -S "$@"
}

echo "==> CRM source: $CRM_SRC"
echo "==> Bench dir:  $BENCH_DIR"

echo "==> Installing system packages..."
sudo_cmd apt-get update -qq
sudo_cmd DEBIAN_FRONTEND=noninteractive apt-get install -y \
  python3-dev python3-pip python3-venv python3-setuptools \
  git curl wget \
  libffi-dev libssl-dev libmariadb-dev \
  xvfb libfontconfig wkhtmltopdf \
  redis-tools

echo "==> Starting CRM MariaDB container..."
docker compose -f "$SCRIPT_DIR/docker-compose.crm.yml" up -d

echo "==> Waiting for MariaDB..."
for i in $(seq 1 30); do
  if docker exec crm-mariadb mariadb-admin ping -h127.0.0.1 -uroot -p"${DB_ROOT_PASSWORD}" --silent 2>/dev/null; then
    break
  fi
  sleep 2
done

echo "==> Installing Node 20 via nvm..."
export NVM_DIR="$HOME/.nvm"
if [ ! -s "$NVM_DIR/nvm.sh" ]; then
  curl -o- https://raw.githubusercontent.com/nvm-sh/nvm/v0.40.1/install.sh | bash
fi
# shellcheck disable=SC1091
source "$NVM_DIR/nvm.sh"
nvm install 20
nvm alias default 20
npm install -g yarn

echo "==> Installing frappe-bench..."
export PATH="$HOME/.local/bin:$PATH"
if ! command -v bench >/dev/null 2>&1; then
  pip3 install --user frappe-bench || pip3 install frappe-bench
fi

if [ ! -d "$BENCH_DIR/apps/frappe" ]; then
  echo "==> Initializing bench..."
  bench init "$BENCH_DIR" --frappe-branch version-15 --python python3
fi

cd "$BENCH_DIR"
bench set-mariadb-host 127.0.0.1
bench set-config -g db_port 3307
bench set-redis-cache-host 127.0.0.1:6379
bench set-redis-queue-host 127.0.0.1:6379
bench set-redis-socketio-host 127.0.0.1:6379

if ! grep -qxF crm sites/apps.txt 2>/dev/null; then
  ln -sfn "$CRM_SRC" apps/crm
  printf 'frappe\ncrm\n' > sites/apps.txt
  python3 - <<'PY'
import json
from pathlib import Path
apps_json = Path("sites/apps.json")
data = json.loads(apps_json.read_text())
if "crm" not in data:
    data["crm"] = {
        "is_repo": True,
        "resolution": {"commit_hash": None, "branch": None},
        "required": [],
        "idx": 2,
        "version": "2.0.0.dev0",
    }
    apps_json.write_text(json.dumps(data, indent=4) + "\n")
PY
fi
source env/bin/activate
pip install -e apps/crm -q

if [ ! -d "sites/${SITE_NAME}" ]; then
  bench new-site "${SITE_NAME}" \
    --mariadb-root-password "${DB_ROOT_PASSWORD}" \
    --admin-password "${ADMIN_PASSWORD}" \
    --mariadb-user-host-login-scope '%'
fi

bench --site "${SITE_NAME}" install-app crm || true
bench --site "${SITE_NAME}" set-config developer_mode 1
bench --site "${SITE_NAME}" set-config ignore_csrf 1
bench --site "${SITE_NAME}" set-config mute_emails 1
bench --site "${SITE_NAME}" clear-cache
bench use "${SITE_NAME}"

bench set-config -g webserver_port "${WEB_PORT}"
bench set-config -g socketio_port "${SOCKETIO_PORT}"

# Production deploy builds frontend manually; disable watch (needs yarn in PATH)
sed -i '/watch/d' Procfile
sed -i "s/--port 8000/--port ${WEB_PORT}/g" Procfile

# Build frontend once
# shellcheck disable=SC1091
source "$NVM_DIR/nvm.sh"
nvm use 20
cd apps/crm/frontend
export NODE_OPTIONS="${NODE_OPTIONS:---max-old-space-size=4096}"
yarn install
yarn build

ln -sfn "$(pwd)/apps/crm/crm/public" sites/assets/crm

SERVER_IP="$(hostname -I | awk '{print $1}')"
echo ""
echo "=========================================="
echo "Setup complete!"
echo "  Site:   ${SITE_NAME}"
echo "  URL:    http://${SERVER_IP}:${WEB_PORT}/crm"
echo "  Login:  Administrator / ${ADMIN_PASSWORD}"
echo ""
echo "Start backend:"
echo "  cd ${BENCH_DIR} && bench start"
echo ""
echo "After editing on Windows, sync & deploy:"
echo "  python scripts/sync_to_server.py --deploy"
echo "=========================================="
