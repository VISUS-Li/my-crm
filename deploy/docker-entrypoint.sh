#!/usr/bin/env bash
# CRM Docker 容器入口：等待 MariaDB → 建站点（首次）→ migrate → bench start
set -euo pipefail

cd /home/frappe/frappe-bench

MARIADB_HOST="${MARIADB_HOST:-mariadb}"
REDIS_HOST="${REDIS_HOST:-redis}"
SITE_NAME="${SITE_NAME:?SITE_NAME required}"
DB_ROOT_PASSWORD="${DB_ROOT_PASSWORD:?DB_ROOT_PASSWORD required}"
ADMIN_PASSWORD="${ADMIN_PASSWORD:-admin}"
SERVER_URL="${SERVER_URL:-https://${SITE_NAME}}"
DEVELOPER_MODE="${DEVELOPER_MODE:-0}"

bench set-mariadb-host "${MARIADB_HOST}"
bench set-config -g db_port 3306
bench set-redis-cache-host "redis://${REDIS_HOST}:6379"
bench set-redis-queue-host "redis://${REDIS_HOST}:6379"
bench set-redis-socketio-host "redis://${REDIS_HOST}:6379"
bench set-config -g webserver_port 8000
bench set-config -g socketio_port 9000

echo "==> Waiting for MariaDB at ${MARIADB_HOST}..."
for _ in $(seq 1 90); do
  if mariadb-admin ping -h"${MARIADB_HOST}" -uroot -p"${DB_ROOT_PASSWORD}" --silent 2>/dev/null; then
    echo "MariaDB is ready"
    break
  fi
  sleep 2
done

if ! grep -qxF crm sites/apps.txt 2>/dev/null; then
  printf 'frappe\ncrm\n' > sites/apps.txt
  python3 - <<'PY'
import json
from pathlib import Path
apps_json = Path("sites/apps.json")
if apps_json.exists():
    data = json.loads(apps_json.read_text())
else:
    data = {}
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
  echo "==> Creating site ${SITE_NAME}..."
  bench new-site "${SITE_NAME}" \
    --mariadb-root-password "${DB_ROOT_PASSWORD}" \
    --admin-password "${ADMIN_PASSWORD}" \
    --mariadb-user-host-login-scope '%'
  bench --site "${SITE_NAME}" install-app crm
else
  echo "==> Site ${SITE_NAME} exists, running migrate..."
fi

bench --site "${SITE_NAME}" set-config developer_mode "${DEVELOPER_MODE}"
bench --site "${SITE_NAME}" set-config host_name "${SERVER_URL}"
bench --site "${SITE_NAME}" set-config mute_emails 1
if [ -n "${TRIPAI_BASE_URL:-}" ]; then
  bench --site "${SITE_NAME}" set-config tripai_base_url "${TRIPAI_BASE_URL}"
  bench --site "${SITE_NAME}" set-config tripai_project_key "${TRIPAI_PROJECT_KEY:-nextdevtpl}"
  bench --site "${SITE_NAME}" set-config tripai_tool_key "${TRIPAI_TOOL_KEY:-my-crm}"
fi
bench use "${SITE_NAME}"

bench --site "${SITE_NAME}" migrate

maybe_bench_build_crm() {
  if [ "${SKIP_BENCH_BUILD:-0}" = "1" ]; then
    echo "==> SKIP_BENCH_BUILD=1, skipping CRM translation compile"
    return 0
  fi
  echo "==> Compiling CRM translations (zh.po -> sites/assets/locale/zh/LC_MESSAGES/crm.mo)..."
  ./env/bin/python apps/crm/scripts/compile_crm_mo.py
}
maybe_bench_build_crm

bench --site "${SITE_NAME}" clear-cache

ln -sfn "$(pwd)/apps/crm/crm/public" sites/assets/crm

sed -i '/watch/d' Procfile
sed -i '/redis/d' Procfile

echo "==> Starting bench (web :8000, socketio :9000)..."
exec bench start
