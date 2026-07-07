# Windows → Ubuntu 部署脚本

在 **Windows** 上改代码，同步到 **Ubuntu 服务器** 编译前端并重启 Frappe bench。

## Agent 快速指令

开发完成、需要用户在服务器上看效果时，在**仓库根目录**执行：

```bash
python scripts/sync_to_server.py --deploy
```

仅同步文件、不编译不重启：

```bash
python scripts/sync_to_server.py
```

PowerShell 等价命令：

```powershell
.\scripts\sync-and-deploy.ps1 -Deploy
```

**前提**：`scripts/deploy.config.json` 已存在且 SSH 可连服务器（见下方「首次配置」）。

---

## 架构

```
Windows (本仓库)                    Ubuntu 服务器
─────────────────                ─────────────────────────────
d:\code\GitHub\my-crm   ──SFTP──►  ~/crm-src          (源码)
                                   ~/frappe-bench/apps/crm → ~/crm-src  (symlink)
                                   ~/frappe-bench       (Frappe bench)
                                   docker: crm-mariadb   (3307)
```

| 脚本 | 运行位置 | 作用 |
|------|----------|------|
| `sync_to_server.py` | Windows | SFTP 增量同步 + 可选触发远程部署 |
| `sync-and-deploy.ps1` | Windows | PowerShell 封装 |
| `watch_and_sync.py` | Windows | 监听文件变化，空闲后自动 `--deploy` |
| `deploy-remote.sh` | Ubuntu | `yarn build`、`bench build --app crm`（编译 zh.po）、清缓存、重启 bench |
| `setup-ubuntu-crm.sh` | Ubuntu | **一次性**安装 bench + site + CRM |
| `finish-setup.sh` | Ubuntu | 修复/补全安装（注册 app、建 site、启动） |
| `docker-compose.crm.yml` | Ubuntu | 独立 MariaDB（3307，避免与现有 MySQL 冲突） |

---

## 配置文件

1. 复制示例配置：

   ```bash
   cp scripts/deploy.config.example.json scripts/deploy.config.json
   ```

2. 编辑 `scripts/deploy.config.json`：
   - `host` / `user` / `password`（或使用 SSH 密钥后可留空 password）
   - `remote_crm_src`、`remote_bench` 与服务器路径一致

3. **首次**配置 SSH 免密（可选）：

   ```bash
   python scripts/sync_to_server.py --setup-key
   ```

`deploy.config.json` 已在 `.gitignore` 中，勿提交。

---

## 常用命令

### 同步 + 编译 + 重启（日常开发后）

```bash
python scripts/sync_to_server.py --deploy
```

远程会执行 `deploy-remote.sh`：`yarn build` → `bench migrate` → **`bench build --app crm`**（将 `crm/locale/zh.po` 编译为 `.mo`，注入 `translated_messages`）→ `bench clear-cache` → `bench restart`（若未运行则 `nohup bench start`）。

部署后请在浏览器 **硬刷新**（Ctrl+Shift+R），确保加载新的前端与翻译词典。

### 自动监听（长时间开发）

```bash
python scripts/watch_and_sync.py
# 可选：python scripts/watch_and_sync.py --interval 5
```

保存文件后，空闲若干秒自动 sync + deploy。

### 服务器首次安装（仅需一次）

在 Ubuntu 上（或从 Windows 用 SSH 执行）：

```bash
bash ~/crm-src/scripts/setup-ubuntu-crm.sh
```

若安装中断，可运行：

```bash
bash ~/crm-src/scripts/finish-setup.sh
```

### 服务器手动重启 bench

```bash
ssh visus@10.0.161.126
cd ~/frappe-bench && bench restart
# 若未运行：
cd ~/frappe-bench && nohup bench start > ~/crm-bench.log 2>&1 &
```

---

## 访问信息（当前环境）

| 项 | 值 |
|----|-----|
| 登录 | http://crm.localhost:8010/login（推荐；见下方 hosts） |
| CRM | http://crm.localhost:8010/crm |
| 备用（IP，实时通知/WebSocket 不可用） | http://10.0.161.126:8010/crm |
| 账号 | `Administrator` / `admin` |
| Web 端口 | **8010**（8000 被 casdoor 占用） |
| Socket.IO | **9010** |

---

## 注意事项

- Shell 脚本必须使用 **LF** 换行（`scripts/.gitattributes` 已配置 `*.sh text eol=lf`）。
- 前端构建需 **Node 20+**；服务器上通过 nvm 安装。
- 构建内存不足时，`deploy-remote.sh` 已设置 `NODE_OPTIONS=--max-old-space-size=4096`。
- Procfile 中已去掉 `watch`，并将 web 端口改为 **8010**（避免与 8000 冲突）。
- 同步会排除 `node_modules`、`.git`、`crm/public/frontend` 等（见 `deploy.config.json` 的 `exclude`）。

---

## 故障排查

| 现象 | 处理 |
|------|------|
| SSH 连接失败 | 检查 `deploy.config.json`，或运行 `--setup-key` |
| `bench: 未找到命令` | 服务器上 `export PATH=$HOME/.local/bin:$PATH` |
| 前端 OOM | 增大 `NODE_OPTIONS` 或在服务器上单独 `cd ~/crm-src/frontend && yarn build` |
| 8010 无响应 | `pgrep -af honcho`；若无进程则 `cd ~/frappe-bench && bench start` |
| `/crm` 白屏、JS/CSS 404 | 运行 `ln -sfn ~/frappe-bench/apps/crm/crm/public ~/frappe-bench/sites/assets/crm`；`deploy-remote.sh` 已自动处理 |
| `/crm` 返回 Not Permitted | 先访问 `/login` 登录 |
| 选中文仍大量英文（Leads、Calls 等） | 确认已 `--deploy`（含 `bench build --app crm`）；检查用户 Language=中文；硬刷新浏览器 |
| Socket.IO CORS / 连到 9000 / WebSocket 失败 | 见下方「Socket.IO」；用 `crm.localhost` 访问，勿用裸 IP |

### Socket.IO（实时通知、活动流）

Frappe 要求 **浏览器地址栏主机名 = 站点名**（本环境为 `crm.localhost`），否则 Socket.IO 命名空间校验失败。Web 在 **8010**，Socket.IO 在 **9010**（9000 被 ClickHouse 占用）。

**Windows 开发机** 在 `C:\Windows\System32\drivers\etc\hosts` 增加：

```
10.0.161.126 crm.localhost
```

然后用 **http://crm.localhost:8010/crm** 打开（不要用 `http://10.0.161.126:8010`）。

若仍报错：硬刷新（Ctrl+Shift+R）；确认 `~/frappe-bench/sites/common_site_config.json` 中 `socketio_port` 为 `9010`；`pgrep -af socketio` 应有 node 进程监听 9010。

日志：`~/crm-bench.log`（Ubuntu）。
