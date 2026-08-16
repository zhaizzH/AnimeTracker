# AnimeTracker · 番组手账

> 个人动漫追番管理平台 —— 管理你看过的、在追的、想看的番剧，并用 AI 对话帮你搜索、发现与推荐。

AnimeTracker 是一个面向个人的动漫追番管理工具。它提供番剧条目浏览 / 搜索、剧集进度追踪、评分、标签、收藏等核心能力，并内置一个基于大模型的 **AI 对话 Agent**（搜索 / 发现 / 推荐），可经工具调用实时读取番剧数据；同时提供运营后台用于条目、用户、导入与配置管理。

---

## 功能特性

- **番剧库管理**：番剧条目浏览、按季度 / 标签筛选、关键词搜索、详情查看（含剧集列表、标签）。
- **追番进度**：记录番剧观看状态与剧集进度，管理「在看 / 想看 / 看过」。
- **标签体系**：自定义标签并聚合番剧，按兴趣快速归类。
- **用户系统**：注册 / 登录 / 登出、邮箱验证、找回与重置密码、个人信息管理（JWT 认证）。
- **放送时间表**：按时间线查看番剧更新安排。
- **AI 对话 Agent**：自然语言搜索番剧、发现新番、获取推荐，支持流式输出（思考过程 + 回答 + 工具调用状态）。
- **数据导入**：从 Bangumi（bgm.tv）拉取番剧元数据并清洗入库。
- **运营后台（预览版）**：仪表盘、番剧管理、用户管理、导入任务、操作日志、Agent 配置等管理端界面（前端预览版已就绪，登录与仪表盘已接入真实 API，其余页面陆续接入中）。

---

## 技术全景

| 层 | 技术 | 说明 |
|----|------|------|
| 前端（用户端） | React 18 + TypeScript + Vite 6 + Ant Design 5 + Zustand + React Query + React Router 7 | `frontend/client`（端口 `5173`） |
| 前端（管理端） | React 18 + TypeScript + Vite 6 + Ant Design 5 + Zustand + React Query + React Router 7 | `frontend/admin`（端口 `5174`，预览版） |
| 业务后端 | Spring Boot 3.2 + MyBatis-Plus 3.5.5 + Java 21 | `backend/business`（Maven 多模块） |
| AI Agent | FastAPI + LangGraph + 通义千问（DashScope / Qwen） | `backend/agent`（Python，端口 `8090`） |
| Agent 代理层 | Spring Boot Web（轻量转发） | `backend/business/agent` 模块 |
| 数据层 | MySQL 8 + Redis + MinIO | 业务数据 / 缓存与会话 / 对象存储 |
| 数据导入 | Python 3.10+ + SQLAlchemy + Requests（与 Agent 共用 venv） | `backend/agent/importer`（数据源：Bangumi） |

> ⚠️ 说明：前端技术栈为 **React 生态**（非 Vue）。两个前端（`client` / `admin`）开发态均通过 Vite 代理将 `/api` 转发至 `http://localhost:8080`。业务后端的 `agent` 模块是一个 Java 转发层，真正的大模型推理由独立的 Python FastAPI 服务（`backend/agent`，端口 `8090`）完成。

---

## 系统架构

```
┌─────────────────────┐         ┌─────────────────────┐
│  Browser (5173)     │         │  Browser (5174)     │
│  frontend/client    │         │  frontend/admin     │
│  (用户端 React)      │         │  (管理端 React)      │
└──────────┬──────────┘         └──────────┬──────────┘
           │  /api/*                         │  /api/*
           │  (Vite dev proxy → 8080)        │  (Vite dev proxy → 8080)
           ▼                                 ▼
┌──────────────────────────────────────────────┐
│       业务后端 business (Spring Boot :8080)   │
│  common / pojo / admin / client / agent / app │
│                                               │
│  ├─ /api/client/*      直接处理业务请求       │
│  ├─ /api/admin/*      管理端 API               │
│  └─ /api/client/agent/* ──► 转发到 Python Agent │
└───────────────────────┬──────────────────────┘
                         │  HTTP 转发
                         ▼
              ┌────────────────────────┐
              │  AI Agent (FastAPI :8090)│
              │  LangGraph + Qwen        │
              │  ├─ 调用 business API    │
              │  └─ Redis 会话 / 提示词  │
              └────────────────────────┘

  数据导入 importer (Python) ──► MySQL（anime_tracker）
```

请求链路：**前端 → 业务后端(:8080) →（Agent 类请求）Python Agent(:8090) →（工具调用）回查业务后端 API**。

---

## 目录结构

```
AnimeTracker/
├── frontend/
│   ├── client/            # 用户端前端（React + Vite，生产代码；构建产物 dist/）
│   └── admin/             # 管理端前端（React + Vite，预览版；构建产物 dist/）
├── backend/
│   ├── business/          # Spring Boot 多模块后端（核心 API）
│   │   ├── common/        # 公共基础：Result、异常、JWT、Redis、安全、MinIO 配置
│   │   ├── pojo/          # 实体 / DTO / VO
│   │   ├── admin/         # 管理端：条目 CRUD、用户管理、导入、日志、Agent 配置
│   │   ├── client/        # 用户端：浏览/搜索、认证、收藏、标签、剧集进度
│   │   ├── agent/         # Agent 代理模块（转发至 Python Agent）
│   │   └── app/           # 启动模块：聚合 admin + client + agent，Spring Boot 入口
│   ├── agent/             # AI Agent（FastAPI + LangGraph，端口 8090）
│   │   ├── app/           # FastAPI 应用
│   │   ├── importer/      # 番剧数据导入器（Bangumi 数据源）
│   │   └── main.py        # FastAPI 入口
└── docs/                  # 项目级文档与数据库脚本
    ├── database/
    │   └── db-schema.sql  # 建表脚本（含 operation_log 等操作审计表）
    └── spec/
        └── openapi.yaml   # OpenAPI 规范
```

> 注：`docs/api/` 为第三方 API 文档工具（独立仓库，已被 `.gitignore` 忽略），不属于本项目源码。

---

## 环境要求

| 组件 | 版本 |
|------|------|
| JDK | 21 LTS |
| Maven | 3.9+ |
| Node.js | 18+（建议 20+） |
| Python | 3.10+ |
| MySQL | 8.0+ |
| Redis | 6+ |
| MinIO | 任意近期版本（可选，对象存储） |

---

## 快速开始

各子模块需**分别启动**。推荐启动顺序：基础设施 → 业务后端 → AI Agent → 前端。

### 1. 基础设施（MySQL / Redis / MinIO）

```bash
# 以 Docker 为例（可按本地环境自行调整）
docker run -d --name mysql -p 3306:3306 -e MYSQL_ROOT_PASSWORD=your-password mysql:8
docker run -d --name redis -p 6379:6379 redis:7
# MinIO 可选：docker run -d --name minio -p 9000:9000 -p 9001:9001 minio/minio server /data
```

### 2. 数据库初始化

```bash
mysql -u root -p
CREATE DATABASE anime_tracker DEFAULT CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;

# 另开会话导入表结构
mysql -u root -p anime_tracker < docs/database/db-schema.sql
```

> 数据库名统一为 `anime_tracker`。建表脚本位于 `docs/database/db-schema.sql`（含 `operation_log` 等操作审计表）。

### 3. 业务后端（business，端口 8080）

```bash
cd backend/business

# 复制并填写本地配置
cp app/src/main/resources/application-local.yml \
   app/src/main/resources/application-local.yml   # 已提供模板，填入实际值

# 构建并运行
mvn clean install -DskipTests
mvn -pl app spring-boot:run -Dspring-boot.run.profiles.active=local
```

- 配置项：`zzz.datasource`（MySQL）、`zzz.data.redis`、`jwt.secret` / `jwt.expiration`、`minio.*`、`resend.api-key`、`at.agent.host` / `at.agent.port`。
- API 文档（Knife4j）：http://localhost:8080/doc.html
- 该模块内置 `agent` 转发层，对外暴露 `/api/client/agent/*`（用户端）与 `/api/admin/agent/*`（管理端），将请求转发至 Python Agent。

### 4. AI Agent（Python，端口 8090）

```bash
cd backend/agent
cp .env.example .env          # 填入 DASHSCOPE_API_KEY 与 REDIS_URL

python -m venv .venv && source .venv/bin/activate   # 或已存在的 .venv
pip install -r requirements.txt
uvicorn main:app --reload --port 8090
```

- 通过 `BACKEND_BASE_URL`（默认 `http://localhost:8080`）回查业务 API。
- 会话与提示词存储于 Redis；Redis 不可用时仅告警，会话功能不可用。
- 交互接口：`POST /api/client/agent/stream`（SSE 流式）、`GET /api/client/agent/sessions`、`GET /docs`（Swagger）。

### 5. 数据导入（Bangumi）

```bash
cd backend/agent/importer   # 依赖与环境变量与 Agent 共用（backend/agent/.env）
python main.py --mode season --key 2026-summer
```

- 与 Agent 共用 `backend/agent` 的 venv 与 `.env`，无需单独安装环境。
- 数据源为 Bangumi（`api.bgm.tv`），客户端自动限流与重试。支持 `full` / `season` / `recent` / `since` 多种模式。

### 6. 用户端前端（端口 5173）

```bash
cd frontend/client
npm install
npm run dev                   # 开发服务器 http://localhost:5173
# 生产构建：npm run build → dist/
```

- 开发态 Vite 代理将 `/api` 转发至 `http://localhost:8080`，因此无需额外配置跨域即可联调。

### 7. 管理端前端（端口 5174，预览版）

```bash
cd frontend/admin
npm install
npm run dev                   # 开发服务器 http://localhost:5174
# 生产构建：npm run build → dist/
```

- 与用户端共用同一套 `/api` 代理（指向 `http://localhost:8080`）。
- 当前为**预览版**：登录页与仪表盘已接入真实 API，其余页面（番剧 / 用户 / 导入 / 日志 / Agent 配置）陆续接入中；登录调用真实 `/api/client/auth/login` 并校验 `ADMIN` 角色。

---

## 配置说明

### 业务后端 `application-local.yml`

| 配置项 | 说明 |
|--------|------|
| `zzz.datasource.*` | MySQL 连接（host / port / database=`anime_tracker` / username / password） |
| `zzz.data.redis.*` | Redis 连接（host / port / database） |
| `jwt.secret` | JWT 签名密钥（推荐 256-bit） |
| `jwt.expiration` | Token 有效期（毫秒，默认 86400000 = 24h） |
| `minio.*` | 对象存储 endpoint / access-key / secret-key / bucket |
| `resend.api-key` | 邮件验证服务密钥 |
| `at.agent.host` / `at.agent.port` | Python Agent 地址（默认 `localhost:8090`） |

### AI Agent `backend/agent/.env`

| 变量 | 默认值 | 说明 |
|------|--------|------|
| `DASHSCOPE_API_KEY` | 空 | 通义千问 API Key（必填） |
| `LLM_MODEL` | `qwen-plus` | 模型名 |
| `LLM_MODEL_ROUTE` | `qwen-plus` | gateway 路由专用模型（快速模型，降低首段等待） |
| `LLM_TEMPERATURE` | `0.3` | 温度 |
| `LLM_MAX_TOKENS` | `4096` | 最大 token |
| `LLM_THINKING_BUDGET` | `2048` | 思考预算 |
| `AGENT_HOST` / `AGENT_PORT` | `0.0.0.0` / `8090` | 服务监听 |
| `BACKEND_BASE_URL` | `http://localhost:8080` | 业务后端地址 |
| `JWT_SECRET` | 开发占位密钥 | 与 business 共享的 JWT 签名密钥（agent 本地验签，不回调业务后端） |
| `REDIS_URL` | `redis://localhost:6379/0` | Redis 地址 |
| `CORS_ORIGINS` | `["http://localhost:5173"]` | 前端跨域来源 |

### 数据导入（`backend/agent/importer`，环境变量并入 `backend/agent/.env`）

| 变量 | 说明 |
|------|------|
| `DB_HOST` / `DB_PORT` / `DB_USER` / `DB_PASSWORD` / `DB_NAME` | 目标 MySQL（库名 `anime_tracker`） |
| `BANGUMI_ACCESS_TOKEN` | Bangumi 访问令牌（可选，提高限流额度） |
| `BANGUMI_USER_AGENT` | 请求 UA，如 `zhaizzH/AnimeTracker` |
| `MINIO_*` | 封面转存相关（可选，未配置则回退原始 URL） |

---

## API 概览

完整定义见 `docs/spec/openapi.yaml`。主要分组：

| 分组 | 路径前缀 | 说明 |
|------|----------|------|
| 认证 | `/api/client/auth` | 注册 / 登录 / 登出 / 邮箱验证 / 找回密码 |
| 用户 | `/api/client` | 个人信息获取与修改 |
| 番剧 | `/api/client/subjects` | 列表 / 搜索 / 季度筛选 / 详情 / 剧集 |
| 标签 | `/api/client/tags` | 标签列表与标签下番剧 |
| 收藏 | `/api/client/collections` | 收藏与观看进度 |
| 管理 | `/api/admin/*` | 条目 CRUD、用户管理、导入任务、操作日志、Agent 配置 |
| Agent | `/api/client/agent/*` | 会话管理与 SSE 流式对话（转发至 Python Agent） |

---

## 数据库 Schema

建表脚本：`docs/database/db-schema.sql`。核心表：

| 表 | 说明 |
|----|------|
| `user` | 用户信息、认证、角色与邮箱状态 |
| `subject` | 番剧条目（Bangumi ID、标题、封面、季度、评分、NSFW、导入状态等） |
| `episode` | 番剧剧集（集数、类型、播出状态、时长等） |
| `subject_tag` | 番剧—标签关联 |
| `user_collection` | 用户收藏与观看进度 |
| `subject_relation` | 番剧间关联关系 |
| `import_record` | 数据导入批次记录 |
| `operation_log` | 操作审计日志（登录、番剧增删改、角色变更、导入等） |

---

## 提交规范

本仓库采用约定式提交，提交信息以类型前缀开头，正文使用中文：

```
<type>(<scope>): <subject>

# 类型：feat | fix | docs | style | refactor | perf | test | chore | ci
# 示例：
# feat(data): 添加 Bangumi 数据导入器
# fix(auth): 修复登录页面未捕获空值异常
# docs: 更新 API 使用说明
```

详见仓库根目录 `.gitmessage`。

---

## 文档与子模块 README

- 前端总览：[`frontend/README.md`](frontend/README.md)
- 用户端前端：[`frontend/client/README.md`](frontend/client/README.md)
- 管理端前端：[`frontend/admin/README.md`](frontend/admin/README.md)
- 后端整体：[`backend/README.md`](backend/README.md)
- 业务后端详解：[`backend/business/README.md`](backend/business/README.md)
- AI Agent 详解：[`backend/agent/README.md`](backend/agent/README.md)
- 数据导入器：[`backend/agent/importer/README.md`](backend/agent/importer/README.md)
- 文档目录：[`docs/README.md`](docs/README.md)
- 数据库脚本：[`docs/database/db-schema.sql`](docs/database/db-schema.sql)
- OpenAPI 规范：[`docs/spec/openapi.yaml`](docs/spec/openapi.yaml)

---

## 端口速查

| 服务 | 端口 | 说明 |
|------|------|------|
| 业务后端 business | `8080` | 核心 API + Agent 代理层 |
| AI Agent（Python） | `8090` | 内部服务，经 business 转发对外 |
| 用户端前端 | `5173` | Vite dev server（client） |
| 管理端前端 | `5174` | Vite dev server（admin，预览版） |
| MySQL | `3306` | — |
| Redis | `6379` | 缓存 / 会话 / 提示词 |

---

## 生产部署与运维

生产环境通过 **Docker Compose** 部署，仅 `nginx` 映射宿主机 `80/443`，其余服务走内部网络。
部署与运维细节见 [`deploy/README.md`](deploy/README.md)，本节约略概述。

### 部署文件

| 文件 | 说明 |
|------|------|
| `compose.yml` | 基础编排（business / agent / mysql / redis / minio / nginx / certbot / demo-seeder） |
| `compose.prod.yml` | 生产覆盖（80/443 端口、TLS 配置、certbot 平滑 reload） |
| `.env.example` | 环境模板（复制为 `.env` 填写） |
| `deploy/scripts/deploy.sh` | 一键部署（校验后 `git pull --ff-only` + `compose pull` + `up -d`） |
| `deploy/scripts/backup.sh` | 每日/每周备份（MySQL 一致性转储 + MinIO 对象镜像，保留 7+4 份） |
| `deploy/scripts/restore.sh` | 受保护恢复（先校验产物再覆盖，需交互确认或 `--yes`） |
| `deploy/nginx/`、`deploy/certbot/` | 反向代理 / TLS 模板与证书续期 |
| `deploy/demo-seeder/` | 演示数据写入（仅 `tools` profile 下显式运行） |

### 首次部署

```bash
cp .env.example .env        # 填写必需密钥与 DOMAIN / BACKUP_PATH
deploy/scripts/deploy.sh    # 校验通过后自动部署
```

- **必需密钥**：`MYSQL_PASSWORD`、`MYSQL_ROOT_PASSWORD`、`REDIS_PASSWORD`、`JWT_SECRET`、`MINIO_ACCESS_KEY`、`MINIO_SECRET_KEY`、`AT_ADMIN_SUPERADMIN_ID`、`DOMAIN`、`CERT_EMAIL`、`BACKUP_PATH`。
- **LLM 密钥（至少一个）**：`DEEPSEEK_API_KEY` 或 `DASHSCOPE_API_KEY`。**优先级 DeepSeek > DashScope**，二者都为空时 Agent 启动失败。

### 升级 / 回滚 / 备份恢复

- 升级：重新运行 `deploy/scripts/deploy.sh`（快进合并 + 拉取镜像 + `up -d`）。
- 回滚：`git checkout <上一版本标签>` 后再次 `deploy.sh`，或回退镜像 tag。
- 备份：`deploy/scripts/backup.sh`（MySQL 一致性转储 + MinIO 镜像，校验和 + 7 日/4 周保留，目标目录必须位于仓库之外）。
- 恢复：`deploy/scripts/restore.sh [--backup <目录>] [--yes]`，先校验产物、打印将被覆盖的数据，再要求确认。
- 演练：**每月至少一次** `bash deploy/tests/test-scripts.sh` 验证恢复链路。

### 可观测性与排障

- 单行 JSON 结构化日志（`ts` / `level` / `service` / `traceId` / `logger` / `message`），同一请求在 Nginx → Business → Agent 各层共享 `X-Request-ID`。
- 健康检查：Business liveness `/actuator/health/liveness`、readiness `/actuator/health/readiness`；Agent `/api/client/agent/health`。
- **Agent 503**：仅影响 Agent 类请求，普通业务不受影响；按 `deploy/README.md` 第 13 节从 Agent 容器、Redis、LLM 配置、traceId 逐步排查。

### CI / 发布

- `.github/workflows/ci.yml`：PR / push 自动执行 Maven 测试、Agent pytest、两端前端构建、`docker compose config` 校验与全部镜像构建（不推送，无需真实密钥）。
- `.github/workflows/release.yml`：仅版本标签（`v*`）触发，使用 `GITHUB_TOKEN` 构建并推送 GHCR 镜像（tag + commit SHA 双标签），记录镜像摘要；**不向任何主机 SSH**。

---

## 项目状态与待办

- ✅ 用户端前端（`frontend/client`）：功能完整，可生产构建。
- ✅ 业务后端、AI Agent、数据导入：可用。
- 🟡 管理端前端（`frontend/admin`）：预览版已就绪（登录与仪表盘已接入真实 API，番剧 / 用户 / 导入 / 日志 / Agent 配置页面陆续接入中）。
- ✅ 容器化 / CI 流水线：已提供 `compose.yml` / `compose.prod.yml`、`deploy/` 运维脚本与 GitHub Actions（CI + 发布）。详见 [生产部署与运维](#生产部署与运维)。
