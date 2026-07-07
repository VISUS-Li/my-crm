#!/usr/bin/env bash
# CRM 生产机一键部署（参考 NextDevTpl/scripts/deploy.sh）
#
# 前置条件:
#   1. DNS: crm.zccmz.cn A 记录 -> 本机公网 IP
#   2. 安全组放行 22 / 80 / 443（勿对外开放 8010/9010/3307）
#   3. 代码已在 ${CRM_SRC:-~/crm-src}（Windows: python scripts/sync_to_server.py）
#   4. cp scripts/release.prod.env.example scripts/release.prod.env 并填写密钥
#
# 子命令:
#   init    新服务器：MariaDB + bench + Nginx + HTTPS
#   nginx   刷新 Nginx 配置 / 证书
#   app     仅构建前端 + migrate + 重启 bench（服务器本地发版）
#   status  查看服务状态

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "${SCRIPT_DIR}/.." && pwd)"
# shellcheck source=deploy-prod-lib.sh
source "${SCRIPT_DIR}/deploy-prod-lib.sh"

usage() {
  sed -n '2,18p' "$0"
  echo ""
  echo "子命令: init | nginx | app | status"
}

log() { printf "[deploy-prod] %s\n" "$*"; }
die() { printf "[deploy-prod] 错误: %s\n" "$*" >&2; exit 1; }

load_prod_vars() {
  CONFIG_FILE="$(resolve_prod_config "${SCRIPT_DIR}")"
  log "配置文件: ${CONFIG_FILE}"
  # shellcheck disable=SC1090
  source "${CONFIG_FILE}"

  DOMAIN="${DOMAIN:-crm.zccmz.cn}"
  SITE_NAME="${SITE_NAME:-${DOMAIN}}"
  SERVER_URL="${SERVER_URL:-https://${DOMAIN}}"
  WEB_PORT="${WEB_PORT:-8010}"
  SOCKETIO_PORT="${SOCKETIO_PORT:-9010}"
  PROD_DIR="${PROD_DIR:-/opt/crm}"
  CRM_SRC="${CRM_SRC:-${HOME}/crm-src}"
  BENCH_DIR="${BENCH_DIR:-${HOME}/frappe-bench}"
  DB_HOST="${DB_HOST:-127.0.0.1}"
  DB_PORT="${DB_PORT:-3307}"
  CERTBOT_EMAIL="${CERTBOT_EMAIL:-}"
  DEVELOPER_MODE="${DEVELOPER_MODE:-0}"

  ensure_prod_secrets "${CONFIG_FILE}"
}

cmd_init() {
  load_prod_vars
  [ -d "${CRM_SRC}" ] || die "未找到源码目录 ${CRM_SRC}，请先 sync 代码"
  [ -n "${CERTBOT_EMAIL}" ] || die "请在 release.prod.env 设置 CERTBOT_EMAIL"

  ensure_docker
  ensure_nginx
  maybe_enable_swap

  log "安装系统依赖..."
  apt-get update -qq
  DEBIAN_FRONTEND=noninteractive apt-get install -y \
    python3-dev python3-pip python3-venv python3-setuptools \
    git curl wget \
    libffi-dev libssl-dev libmariadb-dev \
    xvfb libfontconfig wkhtmltopdf \
    redis-server certbot \
    || true

  systemctl enable redis-server 2>/dev/null || true
  systemctl start redis-server 2>/dev/null || true

  mkdir -p "${PROD_DIR}/scripts" "${PROD_DIR}/nginx"
  install_mariadb_compose "${REPO_ROOT}" "${PROD_DIR}"
  wait_mariadb "${DB_ROOT_PASSWORD}"

  log "初始化 Frappe bench + CRM 站点..."
  export CRM_SRC BENCH_DIR SITE_NAME WEB_PORT SOCKETIO_PORT
  export DB_ROOT_PASSWORD ADMIN_PASSWORD DEVELOPER_MODE SERVER_URL DOMAIN
  export DB_HOST DB_PORT
  bash "${SCRIPT_DIR}/setup-prod-crm.sh"

  log "配置 Nginx + HTTPS..."
  setup_nginx_tls "${REPO_ROOT}"

  wait_bench_ready "${WEB_PORT}"

  log "=========================================="
  log "部署完成!"
  log "  URL:    ${SERVER_URL}/crm"
  log "  登录:   Administrator / ${ADMIN_PASSWORD}"
  log "  Bench:  ${BENCH_DIR}"
  log "  配置:   ${CONFIG_FILE}"
  log "  证书:   ${PROD_DIR}/scripts/renew-certs.sh"
  log "=========================================="
  log "Windows 日常发版: python scripts/sync_to_server.py --deploy"
}

cmd_nginx() {
  load_prod_vars
  ensure_nginx
  setup_nginx_tls "${REPO_ROOT}"
  log "Nginx 已刷新: ${SERVER_URL}"
}

cmd_app() {
  load_prod_vars
  export CRM_SRC BENCH_DIR SITE_NAME
  bash "${SCRIPT_DIR}/deploy-remote.sh"
  log "应用已更新"
}

cmd_status() {
  load_prod_vars
  echo "=== Docker ==="
  docker ps --filter name=crm-mariadb --format 'table {{.Names}}\t{{.Status}}\t{{.Ports}}' 2>/dev/null || true
  echo ""
  echo "=== Bench ==="
  pgrep -af "honcho|bench start" 2>/dev/null || echo "(bench 未运行)"
  echo ""
  echo "=== Nginx ==="
  nginx -t 2>&1 || true
  systemctl is-active nginx 2>/dev/null || true
  echo ""
  echo "=== 端口 ==="
  ss -tlnp 2>/dev/null | grep -E ":(${WEB_PORT}|${SOCKETIO_PORT}|80|443)\s" || netstat -tlnp 2>/dev/null | grep -E ":(${WEB_PORT}|${SOCKETIO_PORT}|80|443)\s" || true
  echo ""
  echo "URL: ${SERVER_URL:-https://${DOMAIN}}/crm"
}

main() {
  local cmd="${1:-}"
  case "${cmd}" in
    init) cmd_init ;;
    nginx) cmd_nginx ;;
    app) cmd_app ;;
    status) cmd_status ;;
    -h|--help|help) usage ;;
    "") die "请指定: init | nginx | app | status" ;;
    *) die "未知子命令: ${cmd}" ;;
  esac
}

main "$@"
