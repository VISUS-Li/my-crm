#!/bin/bash
# deploy-prod.sh 共用函数

resolve_prod_config() {
  local script_dir="$1"
  local config_file="${CONFIG_FILE:-${script_dir}/release.prod.env}"
  if [ -f "${config_file}" ]; then
    echo "${config_file}"
    return 0
  fi
  if [ -f "${script_dir}/release.prod.env.example" ]; then
    echo "警告：${config_file} 不存在，使用 release.prod.env.example" >&2
    echo "${script_dir}/release.prod.env.example"
    return 0
  fi
  echo "错误：未找到 ${config_file}" >&2
  return 1
}

gen_db_password() {
  if command -v openssl >/dev/null 2>&1; then
    openssl rand -base64 24 | tr -d "/+=" | head -c 24
  else
    head -c 24 /dev/urandom | base64 | tr -d "/+=" | head -c 24
  fi
}

gen_admin_password() {
  gen_db_password
}

read_env_value() {
  local file="$1"
  local key="$2"
  grep -E "^${key}=" "${file}" 2>/dev/null | head -n1 | cut -d= -f2- || true
}

write_env_value() {
  local file="$1"
  local key="$2"
  local value="$3"
  if grep -qE "^${key}=" "${file}" 2>/dev/null; then
    sed -i.bak "s|^${key}=.*|${key}=${value}|" "${file}" && rm -f "${file}.bak"
  else
    echo "${key}=${value}" >> "${file}"
  fi
}

ensure_prod_secrets() {
  local config_file="$1"
  if [ -z "${DB_ROOT_PASSWORD:-}" ]; then
    DB_ROOT_PASSWORD="$(read_env_value "${config_file}" "DB_ROOT_PASSWORD")"
  fi
  if [ -z "${DB_ROOT_PASSWORD:-}" ]; then
    DB_ROOT_PASSWORD="$(gen_db_password)"
    write_env_value "${config_file}" "DB_ROOT_PASSWORD" "${DB_ROOT_PASSWORD}"
    echo "已生成 DB_ROOT_PASSWORD 并写入 ${config_file}"
  fi
  if [ -z "${ADMIN_PASSWORD:-}" ]; then
    ADMIN_PASSWORD="$(read_env_value "${config_file}" "ADMIN_PASSWORD")"
  fi
  if [ -z "${ADMIN_PASSWORD:-}" ]; then
    ADMIN_PASSWORD="$(gen_admin_password)"
    write_env_value "${config_file}" "ADMIN_PASSWORD" "${ADMIN_PASSWORD}"
    echo "已生成 ADMIN_PASSWORD 并写入 ${config_file}"
  fi
}

maybe_enable_swap() {
  if [ "${ENABLE_SWAP:-false}" != "true" ] || [ -f /swapfile ]; then
    return 0
  fi
  local size="${SWAP_SIZE_GB:-2}"
  echo "创建 ${size}G swap..."
  fallocate -l "${size}G" /swapfile 2>/dev/null \
    || dd if=/dev/zero of=/swapfile bs=1M count=$((size * 1024)) status=none
  chmod 600 /swapfile
  mkswap /swapfile >/dev/null
  grep -q swapfile /etc/fstab 2>/dev/null || echo "/swapfile none swap sw 0 0" >> /etc/fstab
  swapon /swapfile 2>/dev/null || true
}

ensure_docker() {
  command -v docker >/dev/null 2>&1 || {
    echo "安装 Docker..."
    curl -fsSL https://get.docker.com | sh
    systemctl enable docker
    systemctl start docker
  }
  docker compose version >/dev/null 2>&1 || {
    echo "错误：需要 docker compose 插件" >&2
    return 1
  }
}

ensure_nginx() {
  command -v nginx >/dev/null 2>&1 || {
    apt-get update -qq
    DEBIAN_FRONTEND=noninteractive apt-get install -y nginx
  }
  mkdir -p /var/www/certbot
}

install_mariadb_compose() {
  local repo_root="$1"
  local prod_dir="$2"
  local compose_src="${repo_root}/deploy/docker-compose.prod.yml"
  mkdir -p "${prod_dir}"
  cp "${compose_src}" "${prod_dir}/docker-compose.yml"
  cat > "${prod_dir}/.env" <<EOF
DB_ROOT_PASSWORD=${DB_ROOT_PASSWORD}
DB_PORT=${DB_PORT:-3307}
EOF
  chmod 600 "${prod_dir}/.env"
  (cd "${prod_dir}" && docker compose up -d)
}

wait_mariadb() {
  local password="$1"
  echo "等待 MariaDB 就绪..."
  for _ in $(seq 1 40); do
    if docker exec crm-mariadb mariadb-admin ping -h127.0.0.1 -uroot -p"${password}" --silent 2>/dev/null; then
      echo "MariaDB 已就绪"
      return 0
    fi
    sleep 2
  done
  echo "错误：MariaDB 启动超时" >&2
  return 1
}

render_nginx_config() {
  local repo_root="$1"
  local mode="$2"
  local out_dir="$3"
  NGINX_MODE="${mode}" \
    DOMAIN="${DOMAIN}" \
    SITE_NAME="${SITE_NAME}" \
    WEB_PORT="${WEB_PORT}" \
    SOCKETIO_PORT="${SOCKETIO_PORT}" \
    bash "${repo_root}/deploy/nginx/render-nginx-crm.sh" "${out_dir}"
}

install_nginx_site() {
  local src_conf="$1"
  local domain="$2"
  local avail="/etc/nginx/sites-available/${domain}.conf"
  local enabled="/etc/nginx/sites-enabled/${domain}.conf"
  cp "${src_conf}" "${avail}"
  ln -sfn "${avail}" "${enabled}"
  rm -f /etc/nginx/sites-enabled/default 2>/dev/null || true
  nginx -t
  systemctl reload nginx
}

letsencrypt_cert_exists() {
  local domain="$1"
  [ -f "/etc/letsencrypt/live/${domain}/fullchain.pem" ]
}

cert_provider_normalized() {
  case "${CERT_PROVIDER:-acme-dns-ali}" in
    certbot | letsencrypt) echo "certbot" ;;
    acme-dns-ali | acme-dns-aliyun | aliyun-dns) echo "acme-dns-ali" ;;
    acme-webroot | acme-zerossl) echo "acme-webroot" ;;
    manual | aliyun | aliyun-manual) echo "manual" ;;
    *) echo "${CERT_PROVIDER:-acme-dns-ali}" ;;
  esac
}

issue_cert_acme_sh_dns() {
  local email="$1"
  local domain="$2"
  local image="${ACME_SH_IMAGE:-neilpang/acme.sh:3.0.7}"
  local servers="${ACME_SERVERS:-zerossl,letsencrypt}"
  local acme_data="${PROD_DIR:-/opt/crm}/acme-data"
  mkdir -p "${acme_data}"

  if letsencrypt_cert_exists "${domain}"; then
    echo "证书已存在: ${domain}"
    return 0
  fi

  local key="${ALIYUN_ACCESS_KEY_ID:-}"
  local secret="${ALIYUN_ACCESS_KEY_SECRET:-}"
  if [ -z "${key}" ] || [ -z "${secret}" ]; then
    echo "错误：acme-dns-ali 需要 ALIYUN_ACCESS_KEY_ID / ALIYUN_ACCESS_KEY_SECRET" >&2
    return 1
  fi

  local server
  for server in ${servers//,/ }; do
    echo "acme.sh 申请 (${server}): ${domain}"
    if docker run --rm \
      -v "${acme_data}:/acme.sh" \
      -e "Ali_Key=${key}" \
      -e "Ali_Secret=${secret}" \
      "${image}" \
      --issue --dns dns_ali --server "${server}" \
      -d "${domain}" --email "${email}" --force; then
      mkdir -p "/etc/letsencrypt/live/${domain}"
      docker run --rm \
        -v "${acme_data}:/acme.sh" \
        -v "/etc/letsencrypt:/cert-deploy" \
        "${image}" \
        --install-cert -d "${domain}" \
        --key-file "/cert-deploy/live/${domain}/privkey.pem" \
        --fullchain-file "/cert-deploy/live/${domain}/fullchain.pem" \
        --reloadcmd "systemctl reload nginx"
      echo "证书安装成功: ${domain}"
      return 0
    fi
    echo "CA ${server} 失败，尝试下一个..."
  done
  return 1
}

issue_cert_webroot() {
  local email="$1"
  local domain="$2"
  if letsencrypt_cert_exists "${domain}"; then
    return 0
  fi
  apt-get install -y certbot 2>/dev/null || true
  certbot certonly --webroot \
    -w /var/www/certbot \
    -d "${domain}" \
    --email "${email}" \
    --agree-tos --no-eff-email --non-interactive
}

setup_nginx_tls() {
  local repo_root="$1"
  local tmp_dir
  tmp_dir="$(mktemp -d)"
  local provider
  provider="$(cert_provider_normalized)"

  render_nginx_config "${repo_root}" "http" "${tmp_dir}"
  install_nginx_site "${tmp_dir}/crm.conf" "${DOMAIN}"

  case "${provider}" in
    manual)
      letsencrypt_cert_exists "${DOMAIN}" || {
        echo "错误：manual 模式请先 import-aliyun-cert.sh" >&2
        return 1
      }
      ;;
    acme-dns-ali)
      issue_cert_acme_sh_dns "${CERTBOT_EMAIL}" "${DOMAIN}" || return 1
      ;;
    acme-webroot | certbot)
      issue_cert_webroot "${CERTBOT_EMAIL}" "${DOMAIN}" || return 1
      ;;
    *)
      echo "错误：未知 CERT_PROVIDER=${CERT_PROVIDER}" >&2
      return 1
      ;;
  esac

  render_nginx_config "${repo_root}" "full" "${tmp_dir}"
  install_nginx_site "${tmp_dir}/crm.conf" "${DOMAIN}"
  rm -rf "${tmp_dir}"

  cat > "${PROD_DIR}/scripts/renew-certs.sh" <<'RENEW'
#!/bin/bash
set -euo pipefail
certbot renew --quiet 2>/dev/null || true
systemctl reload nginx
echo "[renew-certs] done: $(date -Is)"
RENEW
  chmod +x "${PROD_DIR}/scripts/renew-certs.sh"
}

wait_bench_ready() {
  local port="$1"
  for _ in $(seq 1 60); do
    if curl -fsS -o /dev/null "http://127.0.0.1:${port}/api/method/ping" 2>/dev/null \
      || curl -fsS -o /dev/null "http://127.0.0.1:${port}/" 2>/dev/null; then
      return 0
    fi
    sleep 2
  done
  echo "警告：bench 端口 ${port} 探活未通过" >&2
  return 0
}
