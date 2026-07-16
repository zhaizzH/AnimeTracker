# AnimeTracker 数据导入器

从 Bangumi API v0 导入动漫数据到 MySQL 数据库。

## 快速开始

```bash
cd backend/data/importer

# 1. 安装依赖
pip install -r requirements.txt

# 2. 配置数据库连接
cp .env.example .env
# 编辑 .env 填入你的 MySQL 连接信息

# 3. 初始化数据库（如尚未初始化）
mysql -u root -p < ../schema/init.sql

# 4. 运行导入
python main.py --recent                 # 最近2年数据
python main.py --season 2024-spring     # 指定季度
python main.py --since 2024-01-01       # 增量导入
python main.py --full                   # 全量导入（谨慎使用）
```

## 导入模式

| 模式 | 命令 | 说明 |
|------|------|------|
| 全量 | `--full` | 遍历 2000 年至今所有动画条目，**可能耗时数小时** |
| 近期 | `--recent` | 默认导入最近 2 年数据，`--years-back N` 控制回溯年数 |
| 季度 | `--season YYYY-season` | 导入指定季度，如 `2024-spring`, `2024-winter` |
| 增量 | `--since YYYY-MM-DD` | 导入指定日期之后播出的条目（使用 search API） |

## 架构

```
main.py → import_runner.py (CLI/流程)
              ├── bangumi_client.py (httpx, Bangumi API v0)
              ├── db_writer.py (SQLAlchemy UPSERT)
              │   ├── models.py (ORM 模型)
              │   └── database.py (引擎/会话)
              └── config.py (Pydantic 配置)
```

## Bangumi API 端点

- `GET /v0/subjects/{subject_id}` — 条目详情（cache 300s）
- `GET /v0/subjects?type=2&year=&month=` — 浏览条目（分页）
- `POST /v0/search/subjects` — 搜索/筛选（支持 air_date 过滤）
- `GET /v0/episodes?subject_id=` — 剧集列表（分页）

## 测试

```bash
cd backend/data/importer
python -m pytest tests/ -v
```
