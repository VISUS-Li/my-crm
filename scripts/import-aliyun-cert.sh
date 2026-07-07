#!/bin/bash
# 将阿里云 SSL 控制台下载的 Nginx 证书导入 CRM 部署目录
# 用法:
#   ./scripts/import-aliyun-cert.sh crm.zccmz.cn /path/to/key.pem /path/to/cert.pem
#
# 阿里云：SSL 证书服务 -> 免费证书 -> 下载 -> Nginx

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
# shellcheck source=deploy-lib.sh
source "${SCRIPT_DIR}/deploy-lib.sh"
CONFIG_FILE="$(resolve_release_config "${SCRIPT_DIR}")"
# shellcheck disable=SC1090
source "${CONFIG_FILE}"

DOMAIN="${1:-}"
KEY_SRC="${2:-}"
CERT_SRC="${3:-}"
PROD_DIR="${PROD_DIR:-/opt/crm}"

if [ -z "${DOMAIN}" ] || [ -z "${KEY_SRC}" ] || [ -z "${CERT_SRC}" ]; then
  echo "用法: $0 <域名> <私钥文件> <证书链pem文件>" >&2
  exit 1
fi
if [ ! -f "${KEY_SRC}" ] || [ ! -f "${CERT_SRC}" ]; then
  echo "错误：找不到密钥或证书文件" >&2
  exit 1
fi

TARGET_DIR="${PROD_DIR}/certbot/conf/live/${DOMAIN}"
mkdir -p "${TARGET_DIR}"
cp "${KEY_SRC}" "${TARGET_DIR}/privkey.pem"
cp "${CERT_SRC}" "${TARGET_DIR}/fullchain.pem"
cp "${CERT_SRC}" "${TARGET_DIR}/cert.pem"
chmod 600 "${TARGET_DIR}/privkey.pem"
chmod 644 "${TARGET_DIR}/fullchain.pem" "${TARGET_DIR}/cert.pem"

echo "已导入证书: ${TARGET_DIR}"
echo "下一步: CERT_PROVIDER=manual ./scripts/deploy.sh nginx"
