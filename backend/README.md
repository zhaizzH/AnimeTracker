# AnimeTracker Backend

后端服务包含三个独立模块：

## 目录结构

```
backend/
├── business/     # Spring Boot 多模块工程 (Java 21, 端口 8080)
├── agent/        # AI Agent (FastAPI + LangChain, 端口 8090)
└── data/         # 数据层
```

## 快速开始

### 1. 数据库

创建 MySQL 数据库：

```bash
bash scripts/seed-db.sh
```

### 2. Java API

```bash
cd backend/business
mvn clean package -DskipTests
java -jar app/target/animetracker-app-*.jar
```

API 文档: http://localhost:8080/doc.html

### 3. AI Agent

```bash
cd backend/agent
cp .env.example .env  # 编辑填入 DASHSCOPE_API_KEY
pip install -r requirements.txt
uvicorn main:app --reload --port 8090
```

### 4. 数据导入器

```bash
cd backend/data/importer
pip install -r requirements.txt
python main.py
```

## 技术栈

| 模块 | 技术 | 版本 |
|------|------|------|
| business | Spring Boot | 3.2.0 |
| business | Java | 21 LTS |
| business | MyBatis-Plus | 3.5.5 |
| agent | FastAPI | 0.110+ |
| agent | LangChain | 1.0+ |
| agent | DashScope (qwen3.7-max) | — |
| 数据导入 | Python 3.10+ / SQLAlchemy | 2.x |
