# AnimeTracker Backend

AnimeTracker 后端由三个独立子模块组成，分别负责业务 API、AI 对话与数据导入。

## 目录结构

```
backend/
├── business/     # Spring Boot 多模块工程 (Java 21, 端口 8080)
├── agent/        # AI Agent (FastAPI + LangGraph, 端口 8090)
├── data/         # 数据层 / 导入器
│   └── importer/ # 番剧数据导入脚本 (Python)
└── docs/         # 后端 SQL 与文档 (docs/sql)
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

创建 MySQL 数据库并导入表结构：

```bash
mysql -u root -p
CREATE DATABASE animetracker CHARACTER SET utf8mb4;
# 在新会话中执行：
mysql -u root -p animetracker < ../docs/db-schema.sql
```

> `../docs/db-schema.sql` 为项目根目录 `docs/` 下的建表脚本；`backend/docs/sql` 下另有分模块 SQL。

### 2. Java 业务后端（business）

```bash
cd backend/business
mvn clean package -DskipTests
java -jar app/target/animetracker-app-*.jar
```

API 文档（Knife4j）：http://localhost:8080/doc.html

### 3. AI Agent

```bash
cd backend/agent
cp .env.example .env          # 填入 DASHSCOPE_API_KEY 等配置
pip install -r requirements.txt
uvicorn main:app --reload --port 8090
```

API 文档（Swagger）：http://localhost:8090/docs

> Agent 通过 `backend_base_url` 调用 business 后端（默认 `http://localhost:8080`），
> 使用 SQLite（`agent.db`）存储会话与聊天记录。

### 4. 数据导入器

```bash
cd backend/data/importer
pip install -r requirements.txt
python main.py
```

## 模块说明

- **business**：核心业务 API，详见 [business/README.md](business/README.md)。
- **agent**：基于 LangGraph 的多轮对话 Agent，详见 [agent/README.md](agent/README.md)。
- **data/importer**：从外部数据源抓取/清洗番剧信息并写入业务库。
