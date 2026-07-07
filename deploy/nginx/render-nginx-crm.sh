#!/bin/bash
# 生成 Frappe CRM 的 Nginx 配置（Web + Socket.IO，Docker 或宿主机 upstream）
# 用法: NGINX_MODE=http|full DOMAIN=... bash render-nginx-crm.sh [输出目录]

set -euo pipefail

DOMAIN="${DOMAIN:-crm.zccmz.cn}"
SITE_NAME="${SITE_NAME:-${DOMAIN}}"
APP_UPSTREAM_HOST="${APP_UPSTREAM_HOST:-crm-app}"
WEB_PORT="${WEB_PORT:-8000}"
SOCKETIO_PORT="${SOCKETIO_PORT:-9000}"
NGINX_MODE="${NGINX_MODE:-full}"
TARGET="${1:-}"

write_file() {
  local path="$1"
  local content="$2"
  mkdir -p "$(dirname "${path}")"
  printf '%s\n' "${content}" > "${path}"
}

ssl_block() {
  cat <<EOF
    ssl_certificate /etc/letsencrypt/live/${DOMAIN}/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/${DOMAIN}/privkey.pem;
    ssl_session_timeout 1d;
    ssl_session_cache shared:CRMSSL:10m;
    ssl_session_tickets off;
    ssl_protocols TLSv1.2 TLSv1.3;
    ssl_prefer_server_ciphers off;
EOF
}

proxy_common() {
  cat <<EOF
        proxy_http_version 1.1;
        proxy_set_header Host \$host;
        proxy_set_header X-Real-IP \$remote_addr;
        proxy_set_header X-Forwarded-For \$proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto \$scheme;
        proxy_set_header X-Forwarded-Host \$host;
        proxy_set_header X-Frappe-Site-Name ${SITE_NAME};
        proxy_read_timeout 120;
        proxy_send_timeout 120;
EOF
}

socketio_location() {
  cat <<EOF
    location /socket.io {
        proxy_http_version 1.1;
        proxy_set_header Upgrade \$http_upgrade;
        proxy_set_header Connection "upgrade";
        proxy_set_header Origin \$scheme://\$http_host;
        proxy_set_header Host \$host;
        proxy_set_header X-Frappe-Site-Name ${SITE_NAME};
        proxy_pass http://${APP_UPSTREAM_HOST}:${SOCKETIO_PORT};
    }
EOF
}

app_location() {
  cat <<EOF
    location / {
        proxy_set_header X-Use-X-Accel-Redirect True;
        proxy_redirect off;
        proxy_pass http://${APP_UPSTREAM_HOST}:${WEB_PORT};
$(proxy_common)
    }
EOF
}

acme_location() {
  cat <<'EOF'
    location /.well-known/acme-challenge/ {
        root /var/www/certbot;
    }
EOF
}

if [ "${NGINX_MODE}" = "http" ]; then
  config="$(cat <<EOF
server {
    listen 80;
    listen [::]:80;
    server_name ${DOMAIN};

$(acme_location)

$(socketio_location)

$(app_location)
}
EOF
)"
else
  config="$(cat <<EOF
server {
    listen 80;
    listen [::]:80;
    server_name ${DOMAIN};

$(acme_location)

    location / {
        return 301 https://${DOMAIN}\$request_uri;
    }
}

server {
    listen 443 ssl http2;
    listen [::]:443 ssl http2;
    server_name ${DOMAIN};

$(ssl_block)

    client_max_body_size 100m;

$(socketio_location)

$(app_location)
}
EOF
)"
fi

if [ -n "${TARGET}" ]; then
  local_dir="${TARGET%/}"
  mkdir -p "${local_dir}"
  write_file "${local_dir}/00-crm.conf" "${config}"
  echo "已生成 Nginx 配置: ${local_dir}/00-crm.conf"
else
  printf '%s\n' "${config}"
fi
