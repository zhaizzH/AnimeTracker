# AnimeTracker 部署与运维手册

本文档面向**家庭服务器运维人员**，覆盖首次安装、启动、升级、回滚、备份恢复与故障排查。
所有命令默认在仓库根目录执行；生产部署使用 Docker Compose，仅 `nginx` 暴露宿主机 `80/443`。

- Compose 基础编排：`compose.yml`
- 生产覆盖（TLS、端口映射、certbot）：`compose.prod.yml`
- 环境模板：[`.env.example`](../.env.example)
- 一键部署：[`deploy/scripts/deploy.sh`](scripts/deploy.sh)
- 备份 / 恢复：[`deploy/scripts/backup.sh`](scripts/backup.sh) / [`deploy/scripts/restore.sh`](scripts/restore.sh)

---

## 1. 首次安装

自建的 Business、Agent 运行镜像使用非 root 用户。MySQL、Redis、MinIO、Nginx 和 Certbot 保留官方镜像支持的初始化用户模型；它们不发布内部端口，Certbot 不挂载 Docker Socket。

新主机只需 **Docker（含 Compose v2）、域名与 `.env`** 即可启动。

```bash
# 1) 准备 .env（复制模板并填写）
cp .env.example .env
vim .env
```

`.env` 中**必须**填写（缺失会导致启动失败）：

| 变量 | 说明 |
|------|------|
| `MYSQL_PASSWORD` / `MYSQL_ROOT_PASSWORD` | MySQL 应用用户与 root 密码 |
| `REDIS_PASSWORD` | Redis 密码（同时用于 agent 的 `REDIS_URL` 认证） |
| `JWT_SECRET` | 至少 256-bit 随机串，Business 与 Agent 共享签名密钥 |
| `MINIO_ACCESS_KEY` / `MINIO_SECRET_KEY` | MinIO 管理员凭证 |
| `AT_ADMIN_SUPERADMIN_ID` | 管理端超级管理员用户主键（业务库中已存在的用户 ID） |
| `DOMAIN` / `CERT_EMAIL` | 证书域名与 Let's Encrypt 联系邮箱 |
| `BACKUP_PATH` | 备份目录**绝对路径**，必须位于仓库之外（如 `/srv/backups/animetracker`） |

**LLM 密钥（至少一个）**：`DEEPSEEK_API_KEY` 或 `DASHSCOPE_API_KEY`，二者都为空时 Agent 启动失败。

其余变量（`MYSQL_DATABASE`、`MINIO_BUCKET`、`AT_CORS_ALLOWED_ORIGINS`、`RESEND_*`、模型名等）均有默认值，可按需调整。

```bash
# 2) 一键部署（校验通过后才 pull/up）
deploy/scripts/deploy.sh
```

`deploy.sh` 会依次校验 Docker、Compose、`.env`、备份路径、必需密钥与至少一个 LLM Key，
全部通过后执行 `git pull --ff-only && docker compose pull && docker compose up -d`，最后打印容器健康状态。

### 依赖启动顺序

Compose 已通过 `depends_on.condition: service_healthy` 保证依赖健康后才启动业务：
`mysql` / `redis` / `minio` 健康 → `business` → `nginx` → `certbot`。Agent 仅依赖 Redis。

---

## 2. LLM 供应商优先级

Agent 按**固定优先级**选择 LLM 供应商，且启动时即校验：

1. `DEEPSEEK_API_KEY` 非空 → 使用 **DeepSeek 官方直连**（`DEEPSEEK_BASE_URL`，默认 `https://api.deepseek.com`）。
2. 否则 `DASHSCOPE_API_KEY` 非空 → 使用 **阿里云百炼 DashScope**。
3. 两者皆空 → **Agent 启动失败**，日志只记录供应商与模型名，**绝不记录密钥**。

> 只填 DeepSeek Key 用 DeepSeek；只填百炼 Key 用百炼；两者都填用 DeepSeek。

---

## 3. 启动 / 停止

```bash
# 启动
docker compose -f compose.yml -f compose.prod.yml up -d

# 查看状态
docker compose -f compose.yml -f compose.prod.yml ps

# 停止
docker compose -f compose.yml -f compose.prod.yml down
```

首次启动会创建 MySQL / Redis / MinIO 数据卷，并由 Flyway 在空库上自动建表。

---

## 4. 演示数据（可选）

空库上可显式导入演示数据（`demo-seeder` 位于 `tools` profile，默认不启动）：

```bash
# 空库写入
docker compose -f compose.yml -f compose.prod.yml --profile tools run --rm demo-seeder

# 非空库显式覆盖（仅当你确认要重置业务数据）
ALLOW_DEMO_SEED=true docker compose -f compose.yml -f compose.prod.yml --profile tools run --rm demo-seeder
```

`DEMO_USER_PASSWORD`（见 `.env`）为演示用户密码，运行时生成 bcrypt 哈希写入。**默认拒绝写入非空库**。

---

## 5. 升级

```bash
deploy/scripts/deploy.sh
```

脚本执行 `git pull --ff-only`（快进合并，本地改动不会被覆盖）、拉取新镜像、`up -d` 应用新版本。
升级后观察 `docker compose ps` 健康列与日志。

---

## 6. 回滚

```bash
# 回退到上一个发布标签（或具体提交）
git checkout <上一版本标签>
deploy/scripts/deploy.sh
```

若新版本镜像已推送到镜像仓库，也可直接回退镜像 tag 后 `up -d`。
回滚前建议先执行一次备份（见第 8 节）。

---

## 7. 证书续期（Let's Encrypt）

`certbot` 容器每 12 小时自动执行一次续期检查（webroot 方式）。`nginx` 容器每小时对共享证书卷执行一次平滑 reload，因此无需向 certbot 暴露 Docker Socket；新证书最多延迟一小时生效。

```bash
# 查看续期日志
docker compose -f compose.yml -f compose.prod.yml logs -f certbot
```

手工续期：

```bash
docker compose -f compose.yml -f compose.prod.yml exec certbot /opt/init-cert.sh
```

> 家庭网络若无法对外开放 80/443，证书将无法申请；可在内网先以自签占位证书运行（`deploy/nginx/bootstrap.sh` 自动生成）。

---

## 8. 日志与可观测性

所有服务单行 JSON 结构化日志输出到容器 stdout/stderr，字段含 `ts`、`level`、`service`、`traceId`、`logger`、`message`。

```bash
# 跟踪业务日志
docker compose -f compose.yml -f compose.prod.yml logs -f --tail=200 business

# 跟踪 Agent 日志（排查 503 时重点看这里）
docker compose -f compose.yml -f compose.prod.yml logs -f --tail=200 agent
```

同一请求的 `X-Request-ID` 会在 **Nginx → Business → Agent** 各层日志中保持一致（traceId）。
日志轮转由 Docker daemon 统一控制（`json-file` 的 `max-size` / `max-file`），无需 ELK。

---

## 9. 健康检查

| 探针 | 地址 | 语义 |
|------|------|------|
| Business liveness | `/actuator/health/liveness` | Java 进程可响应，不依赖外部组件 |
| Business readiness | `/actuator/health/readiness` | MySQL / Redis 可用 |
| Agent | `/api/client/agent/health` | Agent 进程健康 |

Compose 的 `service_healthy` 依赖已自动使用这些探针；排障时也可手动访问：

```bash
curl -s http://localhost/actuator/health/liveness
curl -s http://localhost/api/client/agent/health
```

> Agent 或 MinIO 故障**不会**令 Business readiness 整体失败，只影响对应能力。

---

## 10. 备份

依赖：compose 栈已启动（至少 `mysql` 与 `minio` 服务）。

```bash
deploy/scripts/backup.sh          # 每日备份
deploy/scripts/backup.sh --weekly # 归档为每周一份
```

- **MySQL**：容器内 `mysqldump --single-transaction` 一致性转储并 `gzip`，生成 `sha256`。
- **MinIO**：`mc mirror` 对象镜像到备份目录，按文件生成校验和。
- 布局：`$BACKUP_PATH/daily/<时间戳>/`（`mysql/`、`minio/`、`manifest.json`）。
- 保留：**每日 7 份、每周 4 份**（周日或 `--weekly` 时归档一份，硬链接省磁盘）。
- 安全：写入前校验 `BACKUP_PATH` 为**仓库之外的明确绝对路径**，拒绝 `/`、家目录、根级目录等过宽路径。

建议加入 cron 每日执行：

```bash
0 3 * * * /path/to/AnimeTracker/deploy/scripts/backup.sh >> /var/log/animetracker-backup.log 2>&1
```

---

## 11. 恢复

```bash
# 交互确认（打印环境、备份时间、校验和与被覆盖数据）
deploy/scripts/restore.sh

# 指定备份目录并跳过确认（脚本 / 演练用）
deploy/scripts/restore.sh --backup "$BACKUP_PATH/daily/20260816-030000" --yes
```

恢复流程：

1. 校验备份产物存在且 `sha256` 匹配（**在任何服务停止之前**），拒绝缺失/损坏备份。
2. 打印目标环境、备份时间、将被覆盖的 MySQL 库与 MinIO 桶。
3. 交互确认（或 `--yes`）。
4. 停止 `business` / `agent` 防止恢复期间脏写。
5. 灌入 MySQL 转储（含 `DROP DATABASE` / `CREATE DATABASE`），`mc mirror` 恢复对象。
6. 重启 `business` / `agent`。

> 恢复会**覆盖**当前 MySQL 数据库与 MinIO 桶，请谨慎操作。

---

## 12. 月度恢复演练

恢复是否可用必须定期验证。建议**每月至少一次**：

```bash
# 在一次性/隔离环境执行
bash deploy/tests/test-scripts.sh   # 覆盖：不安全路径拒绝 / 损坏备份拒绝 / 一次性数据还原
```

演练要点：

- 用最新备份在隔离 MySQL / MinIO 上还原，核对业务数据与对象文件可读。
- 记录演练日期、备份时间戳与结果（通过 / 失败原因）。
- 若演练失败，优先检查备份产物校验和与磁盘空间。

---

## 13. Agent 503 故障排查

Business 将 Agent 代理请求失败映射为 `503 Service Unavailable`；**普通业务（浏览 / 收藏 / 搜索）不受影响**。
出现 503 时按顺序排查：

1. **Agent 容器状态**：`docker compose ps` 中 `agent` 是否 healthy；`docker compose logs agent` 有无异常。
2. **Redis**：Agent 依赖 Redis 存会话；Redis 不可用时 Agent 启动仅告警，但聊天功能可能异常。
3. **LLM 配置**：`DEEPSEEK_API_KEY` / `DASHSCOPE_API_KEY` 是否至少配置一个；二者皆空 Agent 启动即失败。
4. **Agent→Business 回查**：Agent 工具调用会回查 Business，`BACKEND_BASE_URL` 在 compose 中固定为 `http://business:8080`，无需修改。
5. **网络**：`docker compose exec agent python -c "import urllib.request; print(urllib.request.urlopen('http://business:8080/actuator/health/liveness', timeout=3).status)"`。
6. **traceId**：从 Business 与 Agent 日志按相同 `traceId` 串联请求，定位是转发失败还是 Agent 内部失败。

---

## 14. 运维速查

| 操作 | 命令 |
|------|------|
| 部署 / 升级 | `deploy/scripts/deploy.sh` |
| 查看状态 | `docker compose -f compose.yml -f compose.prod.yml ps` |
| 跟踪日志 | `docker compose -f compose.yml -f compose.prod.yml logs -f --tail=200 <service>` |
| 备份 | `deploy/scripts/backup.sh` |
| 恢复 | `deploy/scripts/restore.sh [--backup <目录>] [--yes]` |
| 演示数据 | `docker compose -f compose.yml -f compose.prod.yml --profile tools run --rm demo-seeder` |
| 演练测试 | `bash deploy/tests/test-scripts.sh` |
