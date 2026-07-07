#!/usr/bin/env bash
set -euo pipefail
export PATH="$HOME/.local/bin:$PATH"
export NVM_DIR="$HOME/.nvm"
source "$NVM_DIR/nvm.sh"
nvm use 20 2>/dev/null || nvm install 20

DB_ROOT_PASSWORD="${DB_ROOT_PASSWORD:-123456}"
ADMIN_PASSWORD="${ADMIN_PASSWORD:-admin}"
SITE_NAME="${SITE_NAME:-crm.localhost}"

cd ~/frappe-bench
source env/bin/activate

echo "==> Linking crm app..."
ln -sfn "$HOME/crm-src" apps/crm

if grep -q frappecrm sites/apps.txt 2>/dev/null || ! grep -qxF crm sites/apps.txt 2>/dev/null; then
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

pip install -e apps/crm -q

if [ ! -d "sites/${SITE_NAME}" ]; then
  echo "==> Creating site..."
  bench new-site "${SITE_NAME}" \
    --mariadb-root-password "${DB_ROOT_PASSWORD}" \
    --admin-password "${ADMIN_PASSWORD}" \
    --mariadb-user-host-login-scope '%'
fi

if ! bench --site "${SITE_NAME}" list-apps 2>/dev/null | grep -qx crm; then
  echo "==> Installing crm app on site..."
  bench --site "${SITE_NAME}" install-app crm
fi

bench --site "${SITE_NAME}" set-config developer_mode 1
bench --site "${SITE_NAME}" set-config ignore_csrf 1
bench --site "${SITE_NAME}" set-config mute_emails 1
bench --site "${SITE_NAME}" set-config host_name "$(hostname -I | awk '{print $1}')"
bench set-config -g webserver_port 8010
bench set-config -g socketio_port 9010
bench use "${SITE_NAME}"
bench --site "${SITE_NAME}" clear-cache

# Socket.IO auth requires hostname === site name; ensure crm.localhost resolves locally.
if ! grep -qE '[[:space:]]crm\.localhost' /etc/hosts 2>/dev/null; then
  echo "127.0.0.1 crm.localhost" | sudo tee -a /etc/hosts >/dev/null || true
fi

sed -i '/watch/d' Procfile
sed -i 's/--port 8000/--port 8010/g' Procfile

echo "==> Building frontend..."
cd ~/crm-src/frontend
export NODE_OPTIONS="${NODE_OPTIONS:---max-old-space-size=4096}"
yarn install
yarn build

cd ~/frappe-bench
ln -sfn "$(pwd)/apps/crm/crm/public" sites/assets/crm

echo "==> Starting bench..."
cd ~/frappe-bench
pkill -f "honcho start" 2>/dev/null || true
sleep 2
nohup bench start > ~/crm-bench.log 2>&1 &
sleep 15
tail -40 ~/crm-bench.log

SERVER_IP=$(hostname -I | awk '{print $1}')
echo ""
echo "CRM URL (recommended): http://crm.localhost:8010/crm"
echo "Add to Windows hosts:  ${SERVER_IP} crm.localhost"
echo "Fallback (no realtime):  http://${SERVER_IP}:8010/crm"
echo "Login: Administrator / ${ADMIN_PASSWORD}"
