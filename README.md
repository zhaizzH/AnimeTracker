# AnimeTracker

个人动漫追踪平台 — 支持浏览、搜索、收藏动漫条目，AI 助手聊天，以及从 Bangumi API 导入数据。

## 项目结构

```
AnimeTracker/
├── frontend/       # Vue 3 + TypeScript SPA (端口 5173)
├── backend/
│   ├── api/        # Spring Boot REST API (端口 8080)
│   ├── ai/         # AI Agent (FastAPI + LangChain, 端口 8090)
│   └── data/       # 数据层（导入器 + DDL)
├── docs/           # 项目文档
└── scripts/        # 部署和构建脚本
```

## 系统要求

- **Java**: OpenJDK 21+
- **Node.js**: 18+
- **Python**: 3.10+
- **MySQL**: 8.0
- **Redis**: 7-alpine（可选，用于缓存）

## 快速启动

### 1. 数据库初始化

```bash
bash scripts/seed-db.sh
```

### 2. 后端 API

```bash
cd backend/business
mvn clean package -DskipTests
java -jar app/target/animetracker-app-*.jar
```

### 3. 前端

```bash
cd frontend
npm install
npm run dev
```

### 4. AI Agent（可选）

```bash
cd backend/ai
cp .env.example .env  # 填入 DASHSCOPE_API_KEY
pip install -r requirements.txt
uvicorn main:app --reload --port 8090
```

### 5. 数据导入（可选）

```bash
cd backend/data/importer
pip install -r requirements.txt
python main.py
```

## 端口分配

| 服务 | 端口 |
|------|------|
| Spring Boot API (business) | 8080 |
| Vue 3 Frontend | 5173 |
| FastAPI Agent | 8090 |
| MySQL | 3306 |
| Redis | 6379 |

## 技术栈

| 层级 | 技术 |
|------|------|
| 前端 | Vue 3 + TypeScript + Vite + Tailwind CSS |
| 后端 | Spring Boot 3.2 + MyBatis-Plus |
| AI Agent | FastAPI + LangChain + DashScope |
| 数据库 | MySQL 8.0 + Redis 7 |
| 构建 | Maven + npm |
