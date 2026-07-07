#!/bin/bash
# 部署脚本共用函数（由 deploy.sh / build.sh source）

resolve_release_config() {
  local script_dir="$1"
  local config_file="${CONFIG_FILE:-${script_dir}/release.env}"
  if [ -f "${config_file}" ]; then
    echo "${config_file}"
    return 0
  fi
  if [ -f "${script_dir}/release.env.example" ]; then
    echo "警告：${config_file} 不存在，使用 release.env.example（请 cp 为 release.env 并填写密钥）" >&2
    echo "${script_dir}/release.env.example"
    return 0
  fi
  echo "错误：未找到 ${config_file} 或 release.env.example" >&2
  return 1
}

gen_hex_secret() {
  if command -v openssl >/dev/null 2>&1; then
    openssl rand -hex 32
  else
    head -c 32 /dev/urandom | od -An -tx1 | tr -d " \n"
  fi
}

gen_db_password() {
  if command -v openssl >/dev/null 2>&1; then
    openssl rand -base64 24 | tr -d "/+=" | head -c 24
  else
    head -c 24 /dev/urandom | base64 | tr -d "/+=" | head -c 24
  fi
}

docker_compose_bin() {
  if docker compose version >/dev/null 2>&1; then
    echo "docker compose"
    return 0
  fi
  if command -v docker-compose >/dev/null 2>&1; then
    echo "docker-compose"
    return 0
  fi
  echo "错误：未安装 docker compose 插件（docker compose version）" >&2
  return 1
}

registry_login() {
  local domain="$1"
  local user="$2"
  local password="$3"
  local skip_login="${4:-false}"
  if [ "${skip_login}" = "true" ]; then
    echo "已跳过镜像仓库登录"
    return 0
  fi
  if [ -z "${user}" ] || [ -z "${password}" ]; then
    echo "错误：请在 scripts/release.env 中设置 REGISTRY_USER 与 REGISTRY_PASSWORD（或 SKIP_LOGIN=true）" >&2
    return 1
  fi
  echo "登录镜像仓库: ${domain}"
  docker login --username="${user}" "${domain}" --password "${password}"
}

wait_app_ready() {
  local port="$1"
  local ready_url="http://127.0.0.1:${port}/api/method/ping"
  echo "等待 CRM 应用就绪: ${ready_url}"
  for _ in $(seq 1 90); do
    if curl -fsS "${ready_url}" >/dev/null 2>&1; then
      echo "CRM 应用已就绪"
      return 0
    fi
    sleep 3
  done
  echo "错误：CRM 应用未在预期时间内启动: ${ready_url}" >&2
  return 1
}

verify_crm_container() {
  local container_name="${1:-crm-app}"
  echo "检查 CRM 容器日志..."
  local logs
  logs="$(docker logs "${container_name}" 2>&1 || true)"
  if echo "${logs}" | grep -qiE "traceback|error.*migrate|failed to start"; then
    echo "警告：容器日志中可能存在错误，请执行: docker logs ${container_name}"
    echo "${logs}" | tail -30
  else
    echo "CRM 容器启动正常（详见: docker logs ${container_name}）"
  fi
  return 0
}

resolve_enable_nginx() {
  local flag="${ENABLE_NGINX:-auto}"
  case "${flag}" in
    true|1|yes) echo "true"; return 0 ;;
    false|0|no) echo "false"; return 0 ;;
  esac
  if [ -n "${DOMAIN:-}" ]; then
    echo "true"
    return 0
  fi
  case "${SERVER_URL:-}" in
    https://*) echo "true" ;;
    *) echo "false" ;;
  esac
}

ensure_nginx_dirs() {
  local prod_dir="$1"
  mkdir -p \
    "${prod_dir}/nginx/conf.d" \
    "${prod_dir}/certbot/conf" \
    "${prod_dir}/certbot/www" \
    "${prod_dir}/scripts"
}

render_nginx_configs() {
  local repo_root="$1"
  local prod_dir="$2"
  local mode="$3"
  local render_script="${prod_dir}/scripts/render-nginx-crm.sh"
  if [ ! -f "${render_script}" ]; then
    render_script="${repo_root}/deploy/nginx/render-nginx-crm.sh"
  fi

  NGINX_MODE="${mode}" \
    DOMAIN="${DOMAIN}" \
    SITE_NAME="${SITE_NAME:-${DOMAIN}}" \
    APP_UPSTREAM_HOST="${APP_UPSTREAM_HOST:-crm-app}" \
    WEB_PORT="${APP_PORT:-8000}" \
    SOCKETIO_PORT="${SOCKETIO_PORT:-9000}" \
    bash "${render_script}" "${prod_dir}/nginx/conf.d"
}

letsencrypt_cert_exists() {
  local prod_dir="$1"
  local domain="$2"
  [ -f "${prod_dir}/certbot/conf/live/${domain}/fullchain.pem" ]
}

compose_in_dir() {
  local prod_dir="$1"
  shift
  if docker compose version >/dev/null 2>&1; then
    (cd "${prod_dir}" && docker compose "$@")
    return
  fi
  (cd "${prod_dir}" && docker-compose "$@")
}

reload_nginx_container() {
  local container_name="${1:-crm-nginx}"
  docker exec "${container_name}" nginx -t
  docker exec "${container_name}" nginx -s reload
}

cert_provider_normalized() {
  case "${CERT_PROVIDER:-acme-dns-ali}" in
    certbot | letsencrypt) echo "certbot" ;;
    acme-dns-ali | acme-dns-aliyun | aliyun-dns) echo "acme-dns-ali" ;;
    acme-webroot | acme-zerossl | acme-zerossl-webroot) echo "acme-webroot" ;;
    manual | aliyun | aliyun-manual) echo "manual" ;;
    *) echo "${CERT_PROVIDER:-acme-dns-ali}" ;;
  esac
}

cert_uses_dns_challenge() {
  [ "$(cert_provider_normalized)" = "acme-dns-ali" ]
}

aliyun_dns_credentials_ready() {
  local key="${ALIYUN_ACCESS_KEY_ID:-}"
  local secret="${ALIYUN_ACCESS_KEY_SECRET:-}"
  [ -n "${key}" ] && [ -n "${secret}" ]
}

ensure_acme_data_dir() {
  local prod_dir="$1"
  mkdir -p "${prod_dir}/acme-data"
}

acme_sh_image() {
  echo "${ACME_SH_IMAGE:-neilpang/acme.sh:3.0.7}"
}

acme_server_list() {
  local list="${ACME_SERVERS:-zerossl,letsencrypt}"
  list="${list//,/ }"
  echo "${list}"
}

_acme_sh_issue_once() {
  local prod_dir="$1"
  local email="$2"
  local method="$3"
  local server="$4"
  shift 4
  local domain_flags=("$@")
  local run_env=(-e "ACME_DEFAULT_EMAIL=${email}")
  local issue_cmd=(--issue --server "${server}" --email "${email}" --force)

  issue_cmd+=("${domain_flags[@]}")
  if [ "${method}" = "dns_ali" ]; then
    issue_cmd+=(--dns dns_ali)
    run_env+=(
      -e "Ali_Key=${ALIYUN_ACCESS_KEY_ID:-}"
      -e "Ali_Secret=${ALIYUN_ACCESS_KEY_SECRET:-}"
    )
  else
    issue_cmd+=(-w /var/www/certbot --webroot)
  fi

  docker pull "$(acme_sh_image)" >/dev/null 2>&1 || true
  docker run --rm \
    -v "${prod_dir}/acme-data:/acme.sh" \
    -v "${prod_dir}/certbot/www:/var/www/certbot" \
    "${run_env[@]}" \
    "$(acme_sh_image)" \
    "${issue_cmd[@]}"
}

_acme_sh_install_to_nginx_layout() {
  local prod_dir="$1"
  local domain="$2"
  mkdir -p "${prod_dir}/certbot/conf/live/${domain}"
  docker run --rm \
    -v "${prod_dir}/acme-data:/acme.sh" \
    -v "${prod_dir}/certbot/conf:/cert-deploy" \
    "$(acme_sh_image)" \
    --install-cert \
    -d "${domain}" \
    --key-file "/cert-deploy/live/${domain}/privkey.pem" \
    --fullchain-file "/cert-deploy/live/${domain}/fullchain.pem" \
    --cert-file "/cert-deploy/live/${domain}/cert.pem" \
    --reloadcmd "docker exec crm-nginx nginx -s reload 2>/dev/null || true"
}

issue_cert_acme_sh() {
  local prod_dir="$1"
  local email="$2"
  local method="$3"
  local primary="$4"
  shift 4
  local extras=("$@")
  local server

  if letsencrypt_cert_exists "${prod_dir}" "${primary}"; then
    echo "证书已存在，跳过: ${primary}"
    return 0
  fi

  if [ "${method}" = "dns_ali" ] && ! aliyun_dns_credentials_ready; then
    echo "错误：acme-dns-ali 需要 ALIYUN_ACCESS_KEY_ID 与 ALIYUN_ACCESS_KEY_SECRET" >&2
    return 1
  fi

  ensure_acme_data_dir "${prod_dir}"
  mkdir -p "${prod_dir}/certbot/conf/live/${primary}"

  local domain_flags=(-d "${primary}")
  local d
  for d in "${extras[@]}"; do
    [ -n "${d}" ] && domain_flags+=(-d "${d}")
  done

  for server in $(acme_server_list); do
    echo "acme.sh 申请 (${method} / ${server}): ${primary} ${extras[*]-}"
    if _acme_sh_issue_once "${prod_dir}" "${email}" "${method}" "${server}" \
      "${domain_flags[@]}"; then
      _acme_sh_install_to_nginx_layout "${prod_dir}" "${primary}"
      echo "证书申请成功: ${primary}（CA: ${server}）"
      return 0
    fi
    echo "acme.sh (${server}) 失败，尝试下一个 CA..."
  done
  return 1
}

issue_cert_for_domain() {
  local prod_dir="$1"
  local email="$2"
  local primary="$3"
  shift 3
  local extras=("$@")
  local provider
  provider="$(cert_provider_normalized)"

  case "${provider}" in
    certbot) issue_letsencrypt_cert "${prod_dir}" "${email}" "${primary}" "${extras[@]}" ;;
    acme-dns-ali) issue_cert_acme_sh "${prod_dir}" "${email}" "dns_ali" "${primary}" "${extras[@]}" ;;
    acme-webroot) issue_cert_acme_sh "${prod_dir}" "${email}" "webroot" "${primary}" "${extras[@]}" ;;
    manual)
      if letsencrypt_cert_exists "${prod_dir}" "${primary}"; then
        return 0
      fi
      echo "错误：未找到 ${prod_dir}/certbot/conf/live/${primary}/fullchain.pem" >&2
      return 1
      ;;
    *) echo "错误：未知 CERT_PROVIDER=${CERT_PROVIDER}" >&2; return 1 ;;
  esac
}

issue_letsencrypt_cert() {
  local prod_dir="$1"
  local email="$2"
  local primary_domain="$3"
  shift 3
  local extra_domains=("$@")
  local cert_args=(-d "${primary_domain}")

  if letsencrypt_cert_exists "${prod_dir}" "${primary_domain}"; then
    echo "证书已存在，跳过: ${primary_domain}"
    return 0
  fi

  local domain
  for domain in "${extra_domains[@]}"; do
    [ -n "${domain}" ] && cert_args+=(-d "${domain}")
  done

  compose_in_dir "${prod_dir}" --profile tools run --rm certbot certonly \
    --webroot -w /var/www/certbot \
    --email "${email}" --agree-tos --no-eff-email --non-interactive \
    "${cert_args[@]}"
}

write_cert_renew_script() {
  local prod_dir="$1"
  local script_path="${prod_dir}/scripts/renew-certs.sh"
  local provider
  provider="$(cert_provider_normalized)"

  if [ "${provider}" = "manual" ]; then
    cat > "${script_path}" <<'EOF'
#!/bin/bash
set -euo pipefail
docker exec crm-nginx nginx -s reload
echo "[renew-certs] manual 证书已 reload"
EOF
  elif [ "${provider}" = "certbot" ]; then
    cat > "${script_path}" <<'EOF'
#!/bin/bash
set -euo pipefail
PROD_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "${PROD_DIR}"
docker compose --profile tools run --rm certbot renew --quiet
docker exec crm-nginx nginx -s reload
EOF
  else
    cat > "${script_path}" <<EOF
#!/bin/bash
set -euo pipefail
PROD_DIR="\$(cd "\$(dirname "\${BASH_SOURCE[0]}")/.." && pwd)"
docker run --rm -v "\${PROD_DIR}/acme-data:/acme.sh" $(acme_sh_image) --renew-all \\
  --reloadcmd "docker exec crm-nginx nginx -s reload"
EOF
  fi
  chmod +x "${script_path}"
}

install_cert_renew_cron() {
  local prod_dir="$1"
  local cron_file="/etc/cron.d/crm-cert-renew"
  local renew_script="${prod_dir}/scripts/renew-certs.sh"
  write_cert_renew_script "${prod_dir}"
  if [ "$(id -u)" -ne 0 ]; then
    echo "警告：非 root，请手动 cron: 0 3 * * * root ${renew_script}" >&2
    return 0
  fi
  cat > "${cron_file}" <<EOF
SHELL=/bin/bash
PATH=/usr/local/sbin:/usr/local/bin:/sbin:/bin:/usr/sbin:/usr/bin
0 3 * * * root ${renew_script} >> /var/log/crm-cert-renew.log 2>&1
EOF
  chmod 644 "${cron_file}"
}

setup_nginx_tls() {
  local repo_root="$1"
  local prod_dir="$2"
  local certbot_email="$3"
  local skip_nginx_up="${4:-false}"
  local provider
  provider="$(cert_provider_normalized)"

  echo "证书方案: ${provider}"
  ensure_nginx_dirs "${prod_dir}"

  if [ "${provider}" = "manual" ]; then
    letsencrypt_cert_exists "${prod_dir}" "${DOMAIN}" || {
      echo "错误：manual 模式请先 import-aliyun-cert.sh" >&2
      return 1
    }
    render_nginx_configs "${repo_root}" "${prod_dir}" "full"
    compose_in_dir "${prod_dir}" up -d nginx
    reload_nginx_container crm-nginx
    install_cert_renew_cron "${prod_dir}"
    return 0
  fi

  if cert_uses_dns_challenge; then
    issue_cert_for_domain "${prod_dir}" "${certbot_email}" "${DOMAIN}" "${WWW_DOMAIN:-}" \
      || return 1
    render_nginx_configs "${repo_root}" "${prod_dir}" "full"
    compose_in_dir "${prod_dir}" up -d nginx
    reload_nginx_container crm-nginx
    install_cert_renew_cron "${prod_dir}"
    return 0
  fi

  render_nginx_configs "${repo_root}" "${prod_dir}" "http"
  if [ "${skip_nginx_up}" != "true" ]; then
    compose_in_dir "${prod_dir}" up -d nginx
    sleep 2
  fi

  issue_cert_for_domain "${prod_dir}" "${certbot_email}" "${DOMAIN}" "${WWW_DOMAIN:-}" \
    || return 1

  render_nginx_configs "${repo_root}" "${prod_dir}" "full"
  reload_nginx_container crm-nginx
  install_cert_renew_cron "${prod_dir}"
}

maybe_enable_swap() {
  if [ "${ENABLE_SWAP:-false}" != "true" ] || [ -f /swapfile ]; then
    return 0
  fi
  local size="${SWAP_SIZE_GB:-2}"
  fallocate -l "${size}G" /swapfile 2>/dev/null \
    || dd if=/dev/zero of=/swapfile bs=1M count=$((size * 1024)) status=none
  chmod 600 /swapfile
  mkswap /swapfile >/dev/null
  swapon /swapfile 2>/dev/null || true
}

ensure_docker() {
  command -v docker >/dev/null 2>&1 || {
    curl -fsSL https://get.docker.com | sh
    systemctl enable docker
    systemctl start docker
  }
  docker_compose_bin >/dev/null
}
