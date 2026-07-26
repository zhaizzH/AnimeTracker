# AnimeTracker

> 个人动漫追番管理平台 —— 管理你看过的、在追的、想看的番剧。

AnimeTracker 是一个面向个人的动漫追番管理工具，提供番剧条目浏览/搜索、剧集进度追踪、评分、标签、收藏，以及 AI 智能对话（搜索 / 发现 / 推荐）能力。

## 技术全景

| 层 | 技术 | 说明 |
|----|------|------|
| 前端 | Vue 3 + TypeScript + Vite + Tailwind CSS + Pinia | `frontend/client` |
| 业务后端 | Spring Boot 3.2 + MyBatis-Plus + Java 21 | `backend/business`（Maven 多模块） |
| AI Agent | FastAPI + LangGraph + DashScope (Qwen) | `backend/agent` |
| 数据层 | MySQL + Redis + MinIO | 业务数据 / 缓存 / 对象存储 |
| 数据导入 | Python + SQLAlchemy | `backend/data/importer` |

## 目录结构

```
AnimeTracker/
├── frontend/
│   └── client/            # Vue 3 前端应用
├── backend/
│   ├── business/          # Spring Boot 多模块后端（核心 API）
│   ├── agent/             # AI Agent（FastAPI + LangGraph）
│   ├── data/
│   │   └── importer/      # 番剧数据导入器
│   └── docs/              # 后端 SQL / 文档
└── docs/                  # 项目级文档（后端文档、OpenAPI、数据库 schema）
```

## 快速开始

各子模块独立运行，请参考对应目录的 README：

- [backend/README.md](backend/README.md) — 后端整体启动（business + agent + 数据导入）
- [backend/business/README.md](backend/business/README.md) — Spring Boot 业务后端详解
- [backend/agent/README.md](backend/agent/README.md) — AI Agent 详解
- 前端：`cd frontend/client && npm install && npm run dev`

## 文档

- 后端 API 文档：`docs/backend.md`、`docs/openapi.yaml`
- 数据库 schema：`docs/db-schema.sql`

## 约定

- 中文提交信息，前缀 `feat/fix/style/refactor/docs/chore`。
- 业务后端端口 `8080`，AI Agent 端口 `8090`，前端开发端口 `5173`。
