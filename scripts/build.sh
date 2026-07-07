#!/bin/bash
# 构建机：docker build 并 push 到阿里云镜像仓库
# 配置：scripts/release.env（cp release.env.example）
# 用法: ./scripts/build.sh [version]   默认 latest

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "${SCRIPT_DIR}/.." && pwd)"
# shellcheck source=deploy-lib.sh
source "${SCRIPT_DIR}/deploy-lib.sh"
CONFIG_FILE="$(resolve_release_config "${SCRIPT_DIR}")"
# shellcheck disable=SC1090
source "${CONFIG_FILE}"

REGISTRY_DOMAIN="${REGISTRY_DOMAIN:-crpi-dwpdx29dne1d4tyy.cn-chengdu.personal.cr.aliyuncs.com}"
REGISTRY_USER="${REGISTRY_USER:-}"
REGISTRY_PASSWORD="${REGISTRY_PASSWORD:-}"
NAMESPACE="${NAMESPACE:-visus}"
IMAGE_NAME="${IMAGE_NAME:-my-crm}"
VERSION="${1:-latest}"
SKIP_LOGIN="${SKIP_LOGIN:-false}"
SKIP_PUSH="${SKIP_PUSH:-false}"

FULL_IMAGE="${REGISTRY_DOMAIN}/${NAMESPACE}/${IMAGE_NAME}:${VERSION}"

echo "准备构建 CRM 镜像"
echo "配置文件: ${CONFIG_FILE}"
echo "镜像地址: ${FULL_IMAGE}"

cd "${REPO_ROOT}"

registry_login "${REGISTRY_DOMAIN}" "${REGISTRY_USER}" "${REGISTRY_PASSWORD}" "${SKIP_LOGIN}"

echo "开始构建镜像（含 frontend yarn build + bench build --app crm）..."
docker build -t "${FULL_IMAGE}" .

if [ "${SKIP_PUSH}" != "true" ]; then
  echo "开始推送镜像..."
  docker push "${FULL_IMAGE}"
else
  echo "已跳过镜像推送"
fi

echo "构建流程完成"
echo "镜像: ${FULL_IMAGE}"
echo "生产机部署: ./scripts/deploy.sh init ${VERSION}"
