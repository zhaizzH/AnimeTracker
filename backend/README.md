# AnimeTracker Backend

AnimeTracker 后端由两个独立子模块组成，分别负责业务 API 与 AI 对话（含数据导入）：

- **business**：Spring Boot 多模块工程（Java 21，端口 `8080`），提供番剧、用户、收藏、标签等核心 API，并内置 `agent` 代理层将 AI 对话请求转发至 Python Agent。
- **agent**：基于 FastAPI + LangGraph 的 AI 对话服务（Python，端口 `8090`），调用业务 API 获取实时数据并以 SSE 流式输出；内含 `importer`（Bangumi 数据导入器），导入任务由管理端经 agent 触发。

> 前端由 `frontend/client`（用户端，端口 `5173`）与 `frontend/admin`（运营后台，端口 `5174`，预览版）两个独立 React 工程组成，二者均通过 Vite 代理将 `/api` 转发至本后端的 `8080` 端口。详见 [前端总览](../frontend/README.md) 及各自子目录 README。

> 数据库名统一为 **`anime_tracker`**。建表脚本位于项目根 [`../docs/db-schema.sql`](../docs/db-schema.sql)，文档目录说明见 [`../docs/README.md`](../docs/README.md)。

## 目录结构

```
backend/
├── business/     # Spring Boot 多模块工程 (Java 21, 端口 8080)
│   ├── common/   # 公共基础：Result/异常/JWT/Redis/安全/MinIO 配置
│   ├── pojo/     # 实体 / DTO / VO
│   ├── admin/    # 管理端：条目 CRUD、用户管理、数据导入
│   ├── client/   # 用户端：浏览/搜索、认证、收藏、标签、剧集进度
│   ├── agent/    # Agent 代理模块（转发至 Python Agent）
│   └── app/      # 启动模块：聚合 admin + client，Spring Boot 入口
├── agent/        # AI Agent (FastAPI + LangGraph, 端口 8090)
│   ├── app/      # FastAPI 应用
│   └── importer/ # 番剧数据导入脚本 (Python, 数据源: Bangumi)
```

## 技术栈

| 模块 | 技术 | 版本 |
|------|------|------|
| business | Spring Boot | 3.2.0 |
| business | Java | 21 LTS |
| business | MyBatis-Plus | 3.5.5 |
| business | MySQL / Redis / MinIO | — |
| agent | FastAPI | 0.110+ |
| agent | LangGraph | 1.2+ |
| agent | DashScope (Qwen) | — |
| 数据导入 | Python 3.10+ / SQLAlchemy | 2.x |

## 快速开始

### 1. 数据库

```bash
mysql -u root -p
CREATE DATABASE anime_tracker DEFAULT CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;

# 另开会话导入表结构
mysql -u root -p anime_tracker < ../docs/db-schema.sql
```

> 建表脚本为项目根 `docs/db-schema.sql`（非 `backend/docs/sql`）。

### 2. Java 业务后端（business）

```bash
cd backend/business
mvn clean install -DskipTests
mvn -pl app spring-boot:run -Dspring-boot.run.profiles.active=local
```

API 文档（Knife4j）：http://localhost:8080/doc.html

> 该模块内置 `agent` 代理层，对外暴露 `/api/client/agent/*`（用户端）与 `/api/admin/agent/*`（管理端）。Agent 类请求经此后被转发至 Python Agent（默认 `http://localhost:8090`），由 `at.agent.host` / `at.agent.port` 配置。

### 3. AI Agent（Python）

```bash
cd backend/agent
cp .env.example .env          # 填入 DASHSCOPE_API_KEY 与 REDIS_URL
pip install -r requirements.txt
uvicorn main:app --reload --port 8090
```

API 文档（Swagger）：http://localhost:8090/docs

> Agent 通过 `BACKEND_BASE_URL`（默认 `http://localhost:8080`）调用 business 后端；会话与托管提示词存储于 **Redis**（非 SQLite）。Redis 不可用时仅告警并继续启动，但会话功能不可用。

### 4. 数据导入器

```bash
cd backend/agent              # 与 Agent 共用 venv 与 .env
python importer/main.py --mode season --key 2026-summer
```

- 与 Agent 共用 `backend/agent` 的 venv 与 `.env`，无需单独安装环境。

详见 [agent/importer/README.md](agent/importer/README.md)。

## 模块说明

- **business**：核心业务 API，详见 [business/README.md](business/README.md)。
- **agent**：基于 LangGraph 的多轮对话 Agent，详见 [agent/README.md](agent/README.md)。
- **agent/importer**：从 Bangumi 抓取 / 清洗番剧信息并写入业务库，详见 [agent/importer/README.md](agent/importer/README.md)。
