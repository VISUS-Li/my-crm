#!/bin/bash
# CRM 生产机部署：compose 栈（mariadb + redis + crm-app [+ nginx + certbot]）
#
# 全新服务器（一次性，含 Nginx + HTTPS）:
#   cp scripts/release.env.example scripts/release.env
#   # 填写 DOMAIN、镜像仓库、DB 密码等
#   ./scripts/deploy.sh init [version]
#
# 仅更新应用镜像（不动数据库/站点卷）:
#   ./scripts/deploy.sh app [version]
#
# 已有栈补装 / 刷新 Nginx 与证书:
#   ./scripts/deploy.sh nginx
#
# 危险：清空部署目录并停止栈（默认保留 crm-mariadb-data / crm-sites）:
#   CONFIRM_RESET=yes ./scripts/deploy.sh reset

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "${SCRIPT_DIR}/.." && pwd)"
COMPOSE_SRC="${REPO_ROOT}/deploy/docker-compose.prod-ip.yml"
# shellcheck source=deploy-lib.sh
source "${SCRIPT_DIR}/deploy-lib.sh"

usage() {
  sed -n '2,18p' "$0"
  echo ""
  echo "子命令:"
  echo "  init [version]  新服务器：mariadb + redis + crm-app + Nginx + HTTPS"
  echo "  app  [version]  已部署：仅 pull 并重建 crm-app"
  echo "  nginx           Docker Nginx + HTTPS（ENABLE_NGINX=true 时）"
  echo "  nginx-host      宿主机 Nginx 反代 + HTTPS（HOST_NGINX=true 时）"
  echo "  reset           停止栈并删除 ${PROD_DIR:-/opt/crm}（需 CONFIRM_RESET=yes）"
}

log() { printf "[deploy] %s\n" "$*"; }
die() { printf "[deploy] 错误: %s\n" "$*" >&2; exit 1; }

load_release_vars() {
  CONFIG_FILE="$(resolve_release_config "${SCRIPT_DIR}")"
  log "配置文件: ${CONFIG_FILE}"
  # shellcheck disable=SC1090
  source "${CONFIG_FILE}"

  REGISTRY_DOMAIN="${REGISTRY_DOMAIN:-crpi-dwpdx29dne1d4tyy.cn-chengdu.personal.cr.aliyuncs.com}"
  REGISTRY_USER="${REGISTRY_USER:-}"
  REGISTRY_PASSWORD="${REGISTRY_PASSWORD:-}"
  NAMESPACE="${NAMESPACE:-visus}"
  IMAGE_NAME="${IMAGE_NAME:-my-crm}"
  SERVER_URL="${SERVER_URL:-http://127.0.0.1:8000}"
  PROD_DIR="${PROD_DIR:-/opt/crm}"
  APP_PUBLISH_PORT="${APP_PUBLISH_PORT:-8000}"
  APP_PUBLISH_HOST="${APP_PUBLISH_HOST:-0.0.0.0}"
  SOCKETIO_PUBLISH_PORT="${SOCKETIO_PUBLISH_PORT:-9000}"
  DB_ROOT_PASSWORD="${DB_ROOT_PASSWORD:-}"
  ADMIN_PASSWORD="${ADMIN_PASSWORD:-}"
  DOMAIN="${DOMAIN:-}"
  SITE_NAME="${SITE_NAME:-${DOMAIN}}"
  WWW_DOMAIN="${WWW_DOMAIN:-}"
  CERTBOT_EMAIL="${CERTBOT_EMAIL:-}"
  CERT_PROVIDER="${CERT_PROVIDER:-acme-dns-ali}"
  APP_UPSTREAM_HOST="${APP_UPSTREAM_HOST:-crm-app}"
  APP_PORT="${APP_PORT:-8000}"
  SOCKETIO_PORT="${SOCKETIO_PORT:-9000}"
  SKIP_LOGIN="${SKIP_LOGIN:-false}"
  SKIP_PULL="${SKIP_PULL:-false}"
  ENABLE_SWAP="${ENABLE_SWAP:-false}"
  SWAP_SIZE_GB="${SWAP_SIZE_GB:-2}"
  KEEP_DB_VOLUME="${KEEP_DB_VOLUME:-true}"
  DEVELOPER_MODE="${DEVELOPER_MODE:-0}"
  HOST_NGINX="${HOST_NGINX:-false}"
  HOST_NGINX_CONF="${HOST_NGINX_CONF:-/etc/nginx/conf.d/crm.conf}"
  TRIPAI_BASE_URL="${TRIPAI_BASE_URL:-}"
  TRIPAI_PROJECT_KEY="${TRIPAI_PROJECT_KEY:-nextdevtpl}"
  TRIPAI_TOOL_KEY="${TRIPAI_TOOL_KEY:-my-crm}"

  if [ -z "${DOMAIN}" ]; then
    case "${SERVER_URL}" in
      https://*)
        DOMAIN="${SERVER_URL#https://}"
        DOMAIN="${DOMAIN%%/*}"
        ;;
    esac
  fi
  [ -n "${SITE_NAME}" ] || SITE_NAME="${DOMAIN}"

  # 47.95.2.50 等已有宿主机 Nginx：复用 /etc/nginx，容器只绑定 127.0.0.1
  if [ "${HOST_NGINX}" = "true" ]; then
    COMPOSE_SRC="${REPO_ROOT}/deploy/docker-compose.prod-ip.yml"
    APP_PUBLISH_HOST="127.0.0.1"
    APP_UPSTREAM_HOST="127.0.0.1"
    ENABLE_NGINX="false"
    case "${SERVER_URL}" in
      http://*) SERVER_URL="https://${DOMAIN}" ;;
    esac
    SERVER_URL="${SERVER_URL:-https://${DOMAIN}}"
    log "模式: 宿主机 Nginx（${HOST_NGINX_CONF}）→ 127.0.0.1:${APP_PUBLISH_PORT}"
    return 0
  fi

  ENABLE_NGINX="$(resolve_enable_nginx)"
  if [ "${ENABLE_NGINX}" = "true" ]; then
    [ -n "${DOMAIN}" ] || die "启用 Nginx 时请在 release.env 设置 DOMAIN"
    [ -n "${CERTBOT_EMAIL}" ] || die "启用 Nginx 时请在 release.env 设置 CERTBOT_EMAIL"
    case "${SERVER_URL}" in
      http://*)
        log "检测到 HTTP 地址，自动切换为 https://${DOMAIN}"
        SERVER_URL="https://${DOMAIN}"
        ;;
    esac
    SERVER_URL="${SERVER_URL:-https://${DOMAIN}}"
    COMPOSE_SRC="${REPO_ROOT}/deploy/docker-compose.prod.yml"
    APP_PUBLISH_HOST="127.0.0.1"
  else
    COMPOSE_SRC="${REPO_ROOT}/deploy/docker-compose.prod-ip.yml"
    APP_PUBLISH_HOST="${APP_PUBLISH_HOST:-0.0.0.0}"
  fi
}

full_image() {
  local version="$1"
  echo "${REGISTRY_DOMAIN}/${NAMESPACE}/${IMAGE_NAME}:${version}"
}

read_env_value() {
  local file="$1"
  local key="$2"
  grep -E "^${key}=" "${file}" 2>/dev/null | head -n1 | cut -d= -f2- || true
}

write_compose_dotenv() {
  local version="$1"
  local image
  local env_file="${PROD_DIR}/.env"
  image="$(full_image "${version}")"

  if [ -z "${DB_ROOT_PASSWORD}" ] && [ -f "${env_file}" ]; then
    DB_ROOT_PASSWORD="$(read_env_value "${env_file}" "DB_ROOT_PASSWORD")"
  fi
  if [ -z "${DB_ROOT_PASSWORD}" ]; then
    DB_ROOT_PASSWORD="$(gen_db_password)"
    log "已生成 DB_ROOT_PASSWORD（保存在 ${env_file}）"
  fi

  cat > "${env_file}" <<EOF
DB_ROOT_PASSWORD=${DB_ROOT_PASSWORD}
CRM_IMAGE=${image}
APP_PUBLISH_HOST=${APP_PUBLISH_HOST:-127.0.0.1}
APP_PUBLISH_PORT=${APP_PUBLISH_PORT:-8000}
SOCKETIO_PUBLISH_PORT=${SOCKETIO_PUBLISH_PORT:-9000}
EOF
  chmod 600 "${env_file}" 2>/dev/null || true
}

update_compose_image_tag() {
  local version="$1"
  local env_file="${PROD_DIR}/.env"
  local image
  [ -f "${env_file}" ] || die "缺少 ${env_file}，请先 deploy.sh init"
  image="$(full_image "${version}")"
  if grep -q "^CRM_IMAGE=" "${env_file}"; then
    sed -i.bak "s|^CRM_IMAGE=.*|CRM_IMAGE=${image}|" "${env_file}" && rm -f "${env_file}.bak"
  else
    echo "CRM_IMAGE=${image}" >> "${env_file}"
  fi
}

write_env_release() {
  local mode="$1"
  local release_file="${PROD_DIR}/.env.release"
  local existing_admin db_pass

  if [ -z "${ADMIN_PASSWORD}" ] && [ -f "${release_file}" ]; then
    ADMIN_PASSWORD="$(read_env_value "${release_file}" "ADMIN_PASSWORD")"
  fi
  if [ -z "${ADMIN_PASSWORD}" ]; then
    ADMIN_PASSWORD="$(gen_db_password)"
    log "已生成 ADMIN_PASSWORD（保存在 ${release_file}）"
  fi

  if [ "${mode}" = "app" ] && [ -f "${release_file}" ]; then
    log "保留已有 ${release_file}（不覆盖 ADMIN_PASSWORD）"
    if grep -q "^SERVER_URL=" "${release_file}"; then
      sed -i.bak "s|^SERVER_URL=.*|SERVER_URL=${SERVER_URL}|" "${release_file}" && rm -f "${release_file}.bak"
    fi
    return 0
  fi

  cat > "${release_file}" <<EOF
SITE_NAME=${SITE_NAME}
SERVER_URL=${SERVER_URL}
ADMIN_PASSWORD=${ADMIN_PASSWORD}
DEVELOPER_MODE=${DEVELOPER_MODE}
MARIADB_HOST=mariadb
REDIS_HOST=redis
DB_ROOT_PASSWORD=${DB_ROOT_PASSWORD}
TRIPAI_BASE_URL=${TRIPAI_BASE_URL}
TRIPAI_PROJECT_KEY=${TRIPAI_PROJECT_KEY}
TRIPAI_TOOL_KEY=${TRIPAI_TOOL_KEY}
EOF
  chmod 600 "${release_file}" 2>/dev/null || true
  log "已写入 ${release_file}"
}

install_compose_project() {
  [ -f "${COMPOSE_SRC}" ] || die "缺少 compose 模板: ${COMPOSE_SRC}"
  mkdir -p "${PROD_DIR}/nginx/conf.d" "${PROD_DIR}/certbot/conf" "${PROD_DIR}/certbot/www" "${PROD_DIR}/scripts"
  cp "${COMPOSE_SRC}" "${PROD_DIR}/docker-compose.yml"
  cp "${REPO_ROOT}/deploy/nginx/render-nginx-crm.sh" "${PROD_DIR}/scripts/render-nginx-crm.sh"
  cp "${REPO_ROOT}/scripts/deploy-lib.sh" "${PROD_DIR}/scripts/deploy-lib.sh"
  cp "${REPO_ROOT}/scripts/import-aliyun-cert.sh" "${PROD_DIR}/scripts/import-aliyun-cert.sh"
  chmod +x "${PROD_DIR}/scripts/render-nginx-crm.sh" "${PROD_DIR}/scripts/import-aliyun-cert.sh"
  log "已安装 compose: ${PROD_DIR}/docker-compose.yml"
}

compose_in_prod_dir() {
  compose_in_dir "${PROD_DIR}" "$@"
}

wait_for_public_site() {
  if [ "${ENABLE_NGINX}" != "true" ] && [ "${HOST_NGINX}" != "true" ]; then
    return 0
  fi
  local url="https://${DOMAIN}/api/method/ping"
  log "等待 HTTPS 站点就绪: ${url}"
  for _ in $(seq 1 30); do
    if curl -fsS "${url}" >/dev/null 2>&1; then
      log "HTTPS 站点已就绪"
      return 0
    fi
    sleep 3
  done
  log "警告：HTTPS 探活未通过，请检查 DNS / 安全组 / certbot 日志"
}

run_host_nginx_setup() {
  log "配置宿主机 Nginx（${HOST_NGINX_CONF}）..."
  setup_host_nginx_tls \
    "${REPO_ROOT}" \
    "${PROD_DIR}" \
    "${DOMAIN}" \
    "${SITE_NAME}" \
    "${HOST_NGINX_CONF}" \
    "${APP_PUBLISH_PORT}" \
    "${SOCKETIO_PUBLISH_PORT}" \
    "${CERTBOT_EMAIL}" \
    "${CERT_PROVIDER:-acme-dns-ali}"
  wait_for_public_site
  log "宿主机 Nginx 已启用: https://${DOMAIN}/crm"
}

run_nginx_setup() {
  local skip_nginx_up="${1:-false}"
  log "配置 Nginx + HTTPS（DOMAIN=${DOMAIN}）..."
  if [ "${skip_nginx_up}" = "true" ]; then
    setup_nginx_tls "${REPO_ROOT}" "${PROD_DIR}" "${CERTBOT_EMAIL}" "true"
  else
    setup_nginx_tls "${REPO_ROOT}" "${PROD_DIR}" "${CERTBOT_EMAIL}" "false"
  fi
  wait_for_public_site
  log "Nginx 已启用: https://${DOMAIN}/crm"
}

cmd_init() {
  local version="${1:-latest}"
  load_release_vars
  ensure_docker
  maybe_enable_swap
  install_compose_project
  write_compose_dotenv "${version}"
  write_env_release "init"
  registry_login "${REGISTRY_DOMAIN}" "${REGISTRY_USER}" "${REGISTRY_PASSWORD}" "${SKIP_LOGIN}"

  if [ "${ENABLE_NGINX}" = "true" ]; then
    ensure_nginx_dirs "${PROD_DIR}"
    render_nginx_configs "${REPO_ROOT}" "${PROD_DIR}" "http"
  fi

  if [ "${SKIP_PULL}" != "true" ]; then
    log "拉取镜像: $(full_image "${version}")"
    docker pull "$(full_image "${version}")"
    if [ "${ENABLE_NGINX}" = "true" ]; then
      docker pull nginx:1.27-alpine
    fi
  fi

  log "启动 compose 栈..."
  compose_in_prod_dir up -d
  sleep 5
  compose_in_prod_dir ps

  wait_app_ready "${APP_PUBLISH_PORT}" || {
    docker logs crm-app --tail 100 2>&1 || true
    exit 1
  }
  verify_crm_container crm-app
  docker logs crm-app --tail 50 2>&1 || true

  if [ "${HOST_NGINX}" = "true" ]; then
    run_host_nginx_setup
  elif [ "${ENABLE_NGINX}" = "true" ]; then
    run_nginx_setup "true"
  fi

  log "初始化完成: ${SERVER_URL}/crm"
  log "登录: Administrator / ${ADMIN_PASSWORD}"
  log "配置目录: ${PROD_DIR}"
}

cmd_app() {
  local version="${1:-latest}"
  load_release_vars
  ensure_docker
  [ -d "${PROD_DIR}" ] && [ -f "${PROD_DIR}/docker-compose.yml" ] \
    || die "未找到 ${PROD_DIR}，请先 deploy.sh init"
  install_compose_project
  update_compose_image_tag "${version}"
  write_env_release "app"
  registry_login "${REGISTRY_DOMAIN}" "${REGISTRY_USER}" "${REGISTRY_PASSWORD}" "${SKIP_LOGIN}"

  if [ "${SKIP_PULL}" != "true" ]; then
    log "拉取应用镜像..."
    compose_in_prod_dir pull crm-app
  fi

  log "仅重建 crm-app（mariadb / redis / nginx / 数据卷不变）..."
  compose_in_prod_dir up -d --no-deps crm-app
  sleep 5
  compose_in_prod_dir ps

  wait_app_ready "${APP_PUBLISH_PORT}" || {
    docker logs crm-app --tail 100 2>&1 || true
    exit 1
  }
  verify_crm_container crm-app
  log "应用已更新: $(full_image "${version}")"
}

cmd_nginx_host() {
  load_release_vars
  [ "${HOST_NGINX}" = "true" ] || die "请在 release.env 设置 HOST_NGINX=true"
  [ -d "${PROD_DIR}" ] || die "未找到 ${PROD_DIR}，请先 deploy.sh init"
  wait_app_ready "${APP_PUBLISH_PORT}" || die "crm-app 未就绪（127.0.0.1:${APP_PUBLISH_PORT}）"
  run_host_nginx_setup
}

cmd_nginx() {
  load_release_vars
  ensure_docker
  [ "${ENABLE_NGINX}" = "true" ] || die "release.env 未启用 Nginx（请设置 DOMAIN 与 CERTBOT_EMAIL）"
  [ -d "${PROD_DIR}" ] && [ -f "${PROD_DIR}/docker-compose.yml" ] \
    || die "未找到 ${PROD_DIR}，请先 deploy.sh init"
  install_compose_project
  write_env_release "nginx"
  compose_in_prod_dir up -d
  wait_app_ready "${APP_PUBLISH_PORT}" || die "crm-app 未就绪"
  run_nginx_setup "false"
}

cmd_reset() {
  load_release_vars
  [ "${CONFIRM_RESET:-}" = "yes" ] || die "危险操作：请设置 CONFIRM_RESET=yes"
  ensure_docker
  if [ -d "${PROD_DIR}" ] && [ -f "${PROD_DIR}/docker-compose.yml" ]; then
    compose_in_prod_dir down --remove-orphans 2>/dev/null || true
  fi
  docker rm -f crm-app crm-mariadb crm-redis crm-nginx 2>/dev/null || true
  if [ "${KEEP_DB_VOLUME}" != "true" ]; then
    docker volume rm crm-mariadb-data crm-sites 2>/dev/null || true
  else
    log "保留数据卷 crm-mariadb-data / crm-sites"
  fi
  rm -rf "${PROD_DIR}"
  log "已重置 ${PROD_DIR}"
}

main() {
  local cmd="${1:-}"
  case "${cmd}" in
    init) shift; cmd_init "$@" ;;
    app) shift; cmd_app "$@" ;;
    nginx-host) cmd_nginx_host ;;
    nginx) cmd_nginx ;;
    reset) cmd_reset ;;
    -h|--help|help) usage ;;
    "") die "请指定: init | app | nginx | nginx-host | reset" ;;
    *) die "未知子命令: ${cmd}" ;;
  esac
}

main "$@"
