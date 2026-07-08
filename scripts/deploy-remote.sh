#!/usr/bin/env bash
set -euo pipefail
export PATH="$HOME/.local/bin:$PATH"
export NVM_DIR="$HOME/.nvm"
[ -s "$NVM_DIR/nvm.sh" ] || {
  echo "nvm not found at $NVM_DIR; install Node 20 before deploying" >&2
  exit 1
}
source "$NVM_DIR/nvm.sh"
nvm use 20 2>/dev/null || nvm install 20

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
CRM_SRC="${CRM_SRC:-$(cd "$SCRIPT_DIR/.." && pwd)}"
BENCH_DIR="${BENCH_DIR:-$HOME/frappe-bench}"
SITE_NAME="${SITE_NAME:-crm.localhost}"
WEB_PORT="${WEB_PORT:-8010}"

echo "==> Building frontend..."
cd "$CRM_SRC/frontend"
export NODE_OPTIONS="${NODE_OPTIONS:---max-old-space-size=4096}"
yarn install --frozen-lockfile 2>/dev/null || yarn install
yarn build

echo "==> Linking CRM static assets..."
cd "$BENCH_DIR"
ln -sfn "$(pwd)/apps/crm/crm/public" sites/assets/crm

echo "==> Running migrations..."
cd "$BENCH_DIR"
bench --site "$SITE_NAME" migrate

echo "==> Compiling CRM translations (zh.po -> .mo)..."
cd "$BENCH_DIR"
./env/bin/python apps/crm/scripts/compile_crm_mo.py

echo "==> Clearing cache..."
cd "$BENCH_DIR"
bench --site "$SITE_NAME" enable-scheduler
bench --site "$SITE_NAME" clear-cache

sed -i '/watch/d' Procfile
sed -i "s/--port 8000/--port ${WEB_PORT}/g" Procfile

echo "==> Restarting bench..."
cd "$BENCH_DIR"
if pgrep -f "honcho start" >/dev/null 2>&1; then
  bench restart
  echo "Bench restarted."
else
  pkill -f "honcho start" 2>/dev/null || true
  sleep 2
  nohup bench start > ~/crm-bench.log 2>&1 &
  sleep 12
  echo "Bench started in background (log: ~/crm-bench.log)"
  tail -20 ~/crm-bench.log || true
fi

WEB_PORT="$(bench --site "$SITE_NAME" get-config webserver_port 2>/dev/null || echo "${WEB_PORT}")"
HOST_NAME="$(bench --site "$SITE_NAME" get-config host_name 2>/dev/null || true)"
echo ""
if [ -n "${HOST_NAME}" ]; then
  echo "Done. Open: ${HOST_NAME}/crm"
else
  SERVER_IP="$(hostname -I | awk '{print $1}')"
  echo "Done. Open: http://${SERVER_IP}:${WEB_PORT}/crm"
fi
