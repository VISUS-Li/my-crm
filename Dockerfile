# Frappe CRM 生产镜像：预装 frappe + crm（含已构建前端）
# 构建: ./scripts/build.sh [version]
# 运行: ./scripts/deploy.sh init [version]

# 国内构建机请用 DaoCloud 直连，避免 docker.io 经 Clash TUN 拉取大 layer 卡死
FROM docker.m.daocloud.io/frappe/bench:latest AS builder

USER frappe
WORKDIR /home/frappe

RUN bench init frappe-bench \
    --frappe-branch version-15 \
    --skip-redis-config-generation \
    --python python3

WORKDIR /home/frappe/frappe-bench

COPY --chown=frappe:frappe . /tmp/crm-src
RUN rm -rf apps/crm \
    && cp -a /tmp/crm-src apps/crm \
    && rm -rf /tmp/crm-src

RUN cd apps/crm \
    && python3 scripts/generate_zh_fallback.py

RUN cd apps/crm/frontend \
    && export NODE_OPTIONS=--max-old-space-size=4096 \
    && yarn install --frozen-lockfile 2>/dev/null || yarn install \
    && yarn build

# CRM frontend is built above; compile zh.po -> sites/assets/locale/zh/LC_MESSAGES/crm.mo only.
# Full `bench build --app crm` fails here (esbuild paths undefined without an installed site).
RUN pip install -e apps/crm -q \
    && bench compile-po-to-mo --app crm --locale zh --force

FROM docker.m.daocloud.io/frappe/bench:latest AS runner

USER root
RUN apt-get update \
    && DEBIAN_FRONTEND=noninteractive apt-get install -y --no-install-recommends \
        mariadb-client curl \
    && rm -rf /var/lib/apt/lists/*

USER frappe
COPY --from=builder --chown=frappe:frappe /home/frappe/frappe-bench /home/frappe/frappe-bench
COPY --chown=frappe:frappe deploy/docker-entrypoint.sh /home/frappe/docker-entrypoint.sh
RUN chmod +x /home/frappe/docker-entrypoint.sh

WORKDIR /home/frappe/frappe-bench

EXPOSE 8000 9000

HEALTHCHECK --interval=30s --timeout=10s --start-period=180s --retries=5 \
  CMD curl -fsS http://127.0.0.1:8000/api/method/ping || exit 1

ENTRYPOINT ["/home/frappe/docker-entrypoint.sh"]
