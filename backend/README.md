# AnimeTracker 后端总览

> **一句话定位**：后端由两个相互独立的服务组成——**business**（Spring Boot 业务 API）负责数据与鉴权，**agent**（FastAPI AI 对话，内含 `jobs/` 离线任务）负责推理与数据导入。

> 返回项目总览见 [`../README.md`](../README.md)。

## 适用场景

- 需要为 AnimeTracker 前端提供番剧浏览、搜索、收藏、进度、认证等 REST API。
- 需要接入 AI 对话能力，让模型通过受控工具回查业务数据并安全写库。
- 需要从 Bangumi 抓取番剧数据入库，或构建 RAG 向量索引以支持语义检索。

前端所有请求经 Vite 代理统一走 business 的 `8080`，Agent 类请求再由 business 内置代理层转发至 `8090`。

## 架构定位

```
前端 ──/api/*──► business :8080（业务 API + agent 代理层）──HTTP──► agent :8090（AI 对话）
                │                                                   └─jobs/importer─► Bangumi API
                └──MySQL 8 / Redis / MinIO
```

- 前端不直接访问 `8090`；Agent 流量经 business 代理层对外（`/api/client/agent/*`、`/api/admin/agent/*`）。
- agent 通过回查 business API 获取番剧实时数据；数据导入由管理端经 agent 触发（`POST /api/admin/agent/import/run`）。
- agent 与 `jobs/` 下的离线任务共用同一 Python 环境与 `.env`。
- 涉及收藏与进度的 Agent 写操作采用「预览 → 用户确认 → 执行」，待确认动作存储在 Redis，模型不直接构造最终写入参数。

## 服务与端口

| 服务 | 目录 | 端口 | 技术 | 说明 |
|------|------|------|------|------|
| business | `business/` | 8080（Actuator `/actuator/health`） | Spring Boot 3.2.0 / Java 21 / MyBatis-Plus 3.5.5 | 核心业务 API + agent 代理层 |
| agent | `agent/` | 8090（Swagger `/docs`） | FastAPI / LangGraph / Python 3.10+（v3.0.0） | AI 对话，LLM 推理层 |
| importer | `agent/jobs/importer/` | CLI | Python / SQLAlchemy / Bangumi v0 API | 番剧数据导入器 |
| indexer | `agent/jobs/indexer/` | CLI | Python / Redis / DashScope Embeddings | RAG 向量索引构建 |
| scheduler | `agent/jobs/scheduler/` | 常驻进程 | Python | Asia/Shanghai 时区定时导入调度 |

> business 未集成 Knife4j 或 springdoc，接口文档以 [`docs/spec/openapi.yaml`](../docs/spec/openapi.yaml) 为准。

## 前置依赖

| 组件 | 版本要求 | 说明 |
|------|---------|------|
| JDK | 21（含）以上 | 由 maven-enforcer-plugin 强制 |
| Maven | 3.9（含）以上 | 同上 |
| Python | 3.10（含）以上 | `pyproject.toml` 声明 `requires-python = ">=3.10"` |
| uv | 最新版 | Agent 依赖由 `uv.lock` 锁定，CI 使用 `astral-sh/setup-uv@v5` |
| MySQL | 8 | 库名 `anime_tracker` |
| Redis | 5+ 协议兼容；RAG 需 RediSearch/Redis Stack | 会话、消息、提示词、待确认动作；RAG 索引需要 `FT.*` 命令（可选） |
| MinIO | 任意近期版本 | 头像、封面、原始快照存储 |

## 目录结构

```
backend/
├── business/     # Spring Boot 多模块工程（Java 21，端口 8080）
│   ├── common/   # 公共基础：Result/异常/JWT/Redis/安全/MinIO 端口、操作审计、限流
│   ├── pojo/     # 实体 / DTO / VO（dto、vo 按领域子包分包）
│   ├── admin/    # 管理端：条目 CRUD、用户管理、数据导入、仪表盘统计、操作日志
│   ├── client/   # 用户端：浏览/搜索、认证、收藏、标签、剧集进度
│   ├── agent/    # Agent 代理模块（转发至 Python Agent）
│   └── app/      # 启动模块：聚合 admin + client + agent，Spring Boot 入口
└── agent/        # AI Agent（FastAPI + LangGraph，端口 8090，v3.0.0）
    ├── main.py       # FastAPI 入口，注册 client / admin / import 路由
    ├── pyproject.toml
    ├── uv.lock
    ├── .env.example  # 配置模板（Agent 与 jobs 共用）
    ├── resources/    # 本地托管提示词（Redis 不可用时的回退）
    ├── app/          # 端口与适配器：agent / chat / rag / api / adapters / admin / shared
    ├── jobs/         # 离线任务
    │   ├── importer/ # Bangumi 数据导入器
    │   ├── indexer/  # RAG 向量索引构建
    │   └── scheduler/# 定时导入调度（Asia/Shanghai）
    └── tests/        # pytest 测试
```

## 快速开始

按「数据库 → business → agent」顺序启动。

```bash
# 1. 建库（执行一次即可）
mysql -u root -p -e "CREATE DATABASE anime_tracker DEFAULT CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;"
mysql -u root -p anime_tracker < ../docs/database/db-schema.sql

# 2. 启动 business（:8080）
cd business
mvn clean install -DskipTests
mvn -pl app spring-boot:run -Dspring-boot.run.arguments=--spring.profiles.active=local

# 3. 启动 agent（:8090）
cd ../agent
cp .env.example .env        # 填写 LLM_PROVIDER、对应 API Key 与 REDIS_URL
uv sync --dev
uv run uvicorn main:app --reload --port 8090
```

自检：

```bash
curl http://localhost:8080/actuator/health    # business 就绪状态（要求 MySQL + Redis）
curl http://localhost:8090/api/client/agent/health
```

## 核心用法示例

### 通过 business 代理调用 Agent（前端实际路径）

```bash
curl -N -X POST http://localhost:8080/api/client/agent/stream \
  -H "Authorization: Bearer <access-token>" \
  -H "Content-Type: application/json" \
  -d '{"sessionId": null, "message": "推荐几部 2026 年夏季的治愈系番剧"}'
```

响应为 `text/event-stream`，逐行返回 `data: {"type": "...", ...}` 事件。

### 管理端触发数据导入

```bash
curl -X POST "http://localhost:8080/api/admin/agent/import/run?mode=recent" \
  -H "Authorization: Bearer <admin-access-token>"
```

等价于在 Agent 侧直接调用 `POST /api/admin/agent/import/run`，Agent 会以子进程方式启动 `jobs/importer/main.py`，并通过 MySQL 锁与 PID 文件保证单实例。

### 命令行导入一个季度

```bash
cd agent
uv run python -m jobs.importer.main --mode season --key 2026-summer --workers 5
```

## 子模块文档

| 文档 | 内容 |
|------|------|
| [`business/README.md`](business/README.md) | 多模块架构、模块职责、分层约定、配置、测试 |
| [`agent/README.md`](agent/README.md) | LangGraph 状态图、SSE 协议、托管提示词、`.env` 配置、接口清单 |
| [`agent/jobs/importer/README.md`](agent/jobs/importer/README.md) | 导入模式、并发模型、断点续传、`.env` 配置、写入表 |

> 前端联调需先启动 business（:8080）；数据库建表脚本见 [`../docs/database/db-schema.sql`](../docs/database/db-schema.sql)。

## 认证会话部署

business 通过 Redis 保存轮换刷新会话，响应只返回短期 Access Token；刷新凭据写入 `at_refresh` HttpOnly Cookie（路径 `/api/client/auth`，SameSite=Lax）。

- 有效期：Access Token 默认 30 分钟，刷新会话空闲 7 天、绝对上限 30 天（配置项见 `application.yml` 的 `jwt.*`）。
- 撤销场景：退出登录、改密、重置密码、禁用账户和角色变更。
- Cookie 默认启用 Secure（`AT_AUTH_COOKIE_SECURE=true`）；本地 HTTP 开发环境才显式设为 `false`，并确保 `at.cors.allowed-origins` 使用实际前端 Origin。
- 刷新与退出接口会校验 Origin。
- Agent 与 business 必须配置相同的 `JWT_SECRET`，Agent 在本地验签，不回调业务后端。
- `user` 表的 `enabled` 字段已直接包含在 [`../docs/database/db-schema.sql`](../docs/database/db-schema.sql) 中，新环境执行该脚本即可，无需额外的迁移脚本。

## 常见问题

**Q：business 启动后访问 `/doc.html` 404？**
A：项目未集成 Knife4j / springdoc，没有内置 API 文档页面。请查阅 [`../docs/spec/openapi.yaml`](../docs/spec/openapi.yaml) 或直接看各模块 Controller。

**Q：Agent 启动了但对话报 401？**
A：`JWT_SECRET` 与 business 的 `jwt.secret` 不一致。两者默认值都是 `dev-secret-key-not-for-production-use-change-it`，一旦修改 business 配置，Agent 侧必须同步。

**Q：Agent 日志提示 `Redis 连接失败,启动继续`？**
A：这是告警而非致命错误，服务会继续启动，但会话与历史消息功能不可用。修复 Redis 地址后重启即可。

**Q：`mvn test` 没有跑任何用例？**
A：当前 `app/src/test` 与 `client/src/test` 目录存在但为空，business 模块没有落地的 Java 测试用例（父 POM 已声明 `archunit-junit5`、`spring-boot-starter-test`、`spring-security-test`、`h2`，但尚无测试类）。Agent 侧的有效测试位于 `agent/tests/`。

**Q：为什么 Agent 改了提示词没生效？**
A：托管提示词优先读 Redis（键 `agent:prompt:{key}`，启动时加载为进程内快照），未命中才回退 `resources/prompt/` 下的本地 Markdown。在管理端「Agent 配置」页更新后需确认快照已同步。

## 与相邻模块的关联

- **前端**（`../frontend/`）：通过 Vite 代理访问 `/api/**`，只依赖 business；Agent 能力由 business 代理层间接暴露。
- **文档**（`../docs/`）：数据库脚本、OpenAPI 规范、后端编码规范与规划文档的存放地。
- **CI**（`../.github/workflows/ci.yml`）：`backend-java` 作业运行 `mvn -B test`，`backend-python` 作业运行 `uv sync --dev && uv run pytest`。

## 待补充

1. **business 自动化测试**：`app/src/test` 与 `client/src/test` 为空目录，父 POM 已引入 ArchUnit（用于模块边界守卫）但无测试类落地，单元测试与架构约束测试的规划待确认。
2. **生产部署形态**：仓库中不存在 Docker Compose、Nginx 或进程守护配置，business 与 agent 的生产启动方式（JVM 参数、uvicorn worker 数、反向代理）无代码依据，暂无法文档化。
3. **MinIO 桶的初始化**：`MINIO_BUCKET`（公开封面）与 `MINIO_RAW_BUCKET`（原始快照私有桶）需预先创建，仓库中无桶策略或生命周期配置脚本，权限设置方式待确认。
