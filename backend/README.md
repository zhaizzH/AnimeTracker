# AnimeTracker 后端总览

后端由两个相互独立的服务组成：**business**（Spring Boot 业务 API）与 **agent**（FastAPI AI 对话，内含 importer 数据导入）。前端所有请求经 Vite 代理统一走 business 的 `8080`，Agent 类请求再由 business 内置代理层转发至 `8090`。

## 架构定位

```
前端 ──/api/*──► business :8080（业务 API + agent 代理层）──HTTP──► agent :8090（AI 对话）
                │                                                   └─importer─► Bangumi API
                └──MySQL 8 / Redis / MinIO
```

- 前端不直接访问 `8090`；Agent 流量经 business 代理层对外（`/api/client/agent/*`、`/api/admin/agent/*`）。
- agent 通过回查 business API 获取番剧实时数据；数据导入由管理端经 agent 触发（`POST /api/admin/agent/import/run`）。
- agent 与 importer 共用同一 Python venv 与 `.env`。
- 涉及收藏与进度的 Agent 写操作采用“预览 → 用户确认 → 执行”，待确认动作存储在 Redis，模型不直接构造最终写入参数。
- `agent/evals/` 提供零网络、零副作用的确定性评测，覆盖路由、推荐与安全写入边界。

## 服务与端口

| 服务 | 目录 | 端口 | 技术 | 说明 |
|------|------|------|------|------|
| business | `business/` | 8080（Knife4j `/doc.html`） | Spring Boot 3.2 / Java 21 / MyBatis-Plus | 核心业务 API + agent 代理层 |
| agent | `agent/` | 8090（Swagger `/docs`） | FastAPI / LangGraph / Python | AI 对话，LLM 推理层 |
| importer | `agent/importer/` | CLI | Python 3.10+ / SQLAlchemy | Bangumi 数据导入器 |

## 目录结构

```
backend/
├── business/     # Spring Boot 多模块工程（Java 21，端口 8080）
│   ├── common/   # 公共基础：Result/异常/JWT/Redis/安全/MinIO 配置、操作审计、限流
│   ├── pojo/     # 实体 / DTO / VO（dto、vo 按领域子包分包）
│   ├── admin/    # 管理端：条目 CRUD、用户管理、数据导入、仪表盘统计、操作日志
│   ├── client/   # 用户端：浏览/搜索、认证、收藏、标签、剧集进度
│   ├── agent/    # Agent 代理模块（转发至 Python Agent）
│   └── app/      # 启动模块：聚合 admin + client + agent，Spring Boot 入口
└── agent/        # AI Agent（FastAPI + LangGraph，端口 8090）
    ├── app/      # FastAPI 应用
    └── importer/ # 番剧数据导入器（Python，数据源：Bangumi）
```

## 子模块文档

| 文档 | 内容 |
|------|------|
| [`business/README.md`](business/README.md) | 多模块架构、模块职责、分层约定、配置、测试 |
| [`agent/README.md`](agent/README.md) | LangGraph 状态图、SSE 协议、托管提示词、`.env` 配置、接口清单 |
| [`agent/importer/README.md`](agent/importer/README.md) | 导入模式、并发模型、`.env` 配置、写入表 |
| [`agent/evals/README.md`](agent/evals/README.md) | 离线 / Live Agent 评测、数据集与 CI 门禁 |

> 前端联调需先启动 business（:8080）；数据库建表脚本见 [`../docs/database/db-schema.sql`](../docs/database/db-schema.sql)。
## 认证会话部署

business 通过 Redis 保存轮换刷新会话，响应只返回短期 Access Token；刷新凭据写入 `at_refresh` HttpOnly Cookie（路径 `/api/client/auth`，SameSite=Lax）。刷新会话空闲 7 天、绝对最多 30 天；退出、改密、重置密码、禁用账户和角色变更会撤销会话。Cookie 默认启用 Secure；生产环境保持 `AT_AUTH_COOKIE_SECURE=true`，本地 HTTP 开发才显式设置为 false，并确保 `at.cors.allowed-origins` 使用实际前端 Origin；刷新与退出接口会校验 Origin。新增用户启用字段请执行 [`../docs/database/migrations/2026-08-27-user-enabled.sql`](../docs/database/migrations/2026-08-27-user-enabled.sql)。
