#!/usr/bin/env bash
# 生产环境 Frappe bench 初始化（由 deploy-prod.sh init 调用）
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
CRM_SRC="${CRM_SRC:-$(cd "$SCRIPT_DIR/.." && pwd)}"
BENCH_DIR="${BENCH_DIR:-$HOME/frappe-bench}"
DB_ROOT_PASSWORD="${DB_ROOT_PASSWORD:?set DB_ROOT_PASSWORD}"
ADMIN_PASSWORD="${ADMIN_PASSWORD:?set ADMIN_PASSWORD}"
SITE_NAME="${SITE_NAME:?set SITE_NAME}"
WEB_PORT="${WEB_PORT:-8010}"
SOCKETIO_PORT="${SOCKETIO_PORT:-9010}"
DB_HOST="${DB_HOST:-127.0.0.1}"
DB_PORT="${DB_PORT:-3307}"
SERVER_URL="${SERVER_URL:-https://${SITE_NAME}}"
DEVELOPER_MODE="${DEVELOPER_MODE:-0}"

echo "==> CRM source: $CRM_SRC"
echo "==> Bench dir:  $BENCH_DIR"
echo "==> Site:       $SITE_NAME"

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
bench set-mariadb-host "${DB_HOST}"
bench set-config -g db_port "${DB_PORT}"
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
bench --site "${SITE_NAME}" set-config developer_mode "${DEVELOPER_MODE}"
bench --site "${SITE_NAME}" set-config host_name "${SERVER_URL}"
bench --site "${SITE_NAME}" set-config mute_emails 1
bench --site "${SITE_NAME}" clear-cache
bench use "${SITE_NAME}"

bench set-config -g webserver_port "${WEB_PORT}"
bench set-config -g socketio_port "${SOCKETIO_PORT}"

sed -i '/watch/d' Procfile
sed -i "s/--port 8000/--port ${WEB_PORT}/g" Procfile

echo "==> Building frontend..."
# shellcheck disable=SC1091
source "$NVM_DIR/nvm.sh"
nvm use 20
cd "$CRM_SRC/frontend"
export NODE_OPTIONS="${NODE_OPTIONS:---max-old-space-size=4096}"
yarn install
yarn build

cd "$BENCH_DIR"
ln -sfn "$(pwd)/apps/crm/crm/public" sites/assets/crm

echo "==> Starting bench..."
pkill -f "honcho start" 2>/dev/null || true
sleep 2
nohup bench start > ~/crm-bench.log 2>&1 &
sleep 15
tail -30 ~/crm-bench.log || true

echo "Setup complete: ${SERVER_URL}/crm"
