# Bangumi 数据导入器设计

> **日期:** 2026-07-16
> **状态:** 设计完成，待实现
> **项目:** AnimeTracker

## 1. 概述

在 `backend/data/importer/` 下开发一个扁平结构的 Python 模块，读取 Bangumi Open API（位于 `C:\Users\zzz\Desktop\api\`）将动画条目数据导入 MySQL 数据库 `anime_tracker`，数据库结构由 `docs/db-schema.sql` 定义。

### 目标

- 支持 4 种导入模式：full / season / recent / since
- 数据写入 subject、episode、subject_tag 三张表
- 每次运行记录到 import_record 表
- 使用 UPSERT 语义保证幂等性
- 保守速率控制，避免触发 Bangumi API 限流

## 2. 架构

```
main.py  (CLI 入口，argparse)
  │
  ├─ client.py  (Bangumi HTTP API 封装，自动限流)
  │    └─ GET /v0/subjects/{id}
  │    └─ GET /v0/episodes?subject_id={id}
  │    └─ GET /v0/subjects?type=2&year=&month=
  │    └─ POST /v0/search/subjects
  │    └─ GET /calendar
  │
  ├─ db.py  (SQLAlchemy ORM + upsert 操作)
  │    └─ subject / episode / subject_tag
  │    └─ import_record
  │
  └─ .env  (数据库连接串 + Access Token，不提交仓库)
```

### 依赖

- `requests` — HTTP 客户端
- `sqlalchemy` + `pymysql` — ORM + MySQL 驱动
- `python-dotenv` — 配置加载

## 3. 文件结构与职责

### `main.py`

CLI 入口，支持参数：

```
python main.py --mode full
python main.py --mode season --key 2026-summer
python main.py --mode recent
python main.py --mode since --since "2026-01-01"
python main.py --mode season --key 2026-summer --resume   # 跳过已导入
```

- 解析参数 → 确定 subject 列表来源 → 遍历调用详情导入 → 记录 import_record
- 通过 *dotenv* 加载 `.env` 配置
- 写入 `import_record` 记录开始/完成/失败状态

### `client.py`

Bangumi HTTP API 封装，单文件 80-120 行：

```python
class BangumiClient:
    def __init__(self, access_token: str, user_agent: str)
    def get_subject(self, subject_id: int) -> dict       # GET /v0/subjects/{id}
    def get_episodes(self, subject_id: int) -> list[dict] # GET /v0/episodes
    def browse_subjects(self, type=2, year=None, month=None, offset=0) -> dict
    def search_subjects(self, keyword, filter=None) -> dict
    def get_calendar(self) -> list[dict]                  # GET /calendar
```

- 自动设置 `User-Agent` 和 `Authorization: Bearer` header
- 每次请求后 `time.sleep(random.uniform(1.0, 2.0))`
- 遇到 429 自动读取 `Retry-After` 等待
- 30s 超时，网络错误重试 3 次

### `db.py`

SQLAlchemy 模型 + upsert 方法，单文件 100-150 行：

**ORM 模型映射：**

| 表 | 模型 | Upsert 匹配键 |
|---|---|---|
| `subject` | `Subject` | `bangumi_id` (UNIQUE) |
| `episode` | `Episode` | `(subject_id, bangumi_ep_id)` |
| `subject_tag` | `SubjectTag` | `(subject_id, name)` (UNIQUE) |

**核心方法：**

```python
upsert_subject(data: dict) -> int           # 返回 subject.id
upsert_episodes(subject_id: int, episodes: list[dict])
upsert_tags(subject_id: int, tags: list[dict])
create_import_record(mode, season_key) -> int
complete_import_record(record_id, subject_count, status, error_message)
```

- 全部使用 `INSERT ... ON DUPLICATE KEY UPDATE` 原生 upsert
- 每 50 个 subject 提交一次事务

## 4. 导入模式详解

### `full` — 全量导入

遍历 Bangumi 所有动画条目（type=2），按年份/月份分批：

1. 从最早有数据的年份到当前年份
2. 对每年 1-12 月调用 `GET /v0/subjects?type=2&year=Y&month=M`
3. 每页 25 条，逐页获取
4. 对每个 subject_id 获取详情 + 剧集 + 标签 → upsert

**预期数据量：** ~10,000-15,000 条目（Bangumi 全部动画）

### `season` — 季度导入

将季度 key 映射为年月范围：

| Key | 月份 |
|-----|------|
| `2026-spring` | 2026-01 ~ 2026-03 |
| `2026-summer` | 2026-04 ~ 2026-06 |
| `2026-autumn` | 2026-07 ~ 2026-09 |
| `2026-winter` | 2026-10 ~ 2026-12 |

遍历该季度各月调用 `GET /v0/subjects?type=2&year=&month=`。

### `recent` — 近期更新

调用 `GET /calendar` 获取本周放送表，包含当前正在播出的所有条目。

**预期数据量：** ~50-100 条目

### `since` — 自某时间起

使用 `air_date >= since` 条件，遍历年份月份过滤：

1. 从 `since` 所在年份开始
2. 逐月遍历直到当前月份
3. 只导入 `air_date` 在范围内的条目

## 5. 数据映射

### Subject

| Bangumi API 字段 | DB 字段 | 说明 |
|---|---|---|
| `id` | `bangumi_id` | Bangumi 条目 ID |
| `name` | `name` | 日文/英文名 |
| `name_cn` | `name_cn` | 中文名 |
| `summary` | `summary` | 简介 |
| `type` | `type` | 固定写入 2（动画） |
| `eps` / `total_episodes` | `eps` | 总集数（取 max） |
| `date` | `air_date` | 播出日期 |
| `images.large` | `image` | 封面 URL |
| `rating.score` | `score` | 评分 |
| `rating.rank` | `rank` | 排名 |
| `collection.collect` | `collection_total` | 收藏数 |
| `nsfw` | `nsfw` | 是否 NSFW |

### Episode

| Bangumi API 字段 | DB 字段 | 说明 |
|---|---|---|
| `id` | `bangumi_ep_id` | Bangumi 剧集 ID |
| `type` | `type` | 0=本篇 1=SP 2=OP 3=ED 4=预告 |
| `sort` | `sort` | 集数序号 |
| `name` | `name` | 标题 |
| `name_cn` | `name_cn` | 中文标题 |
| `duration` | `duration` | 时长 |
| `airdate` | `airdate` | 播出日期 |
| `desc` | `description` | 简介 |
| `status` | `status` | Air/Today/NA |

### SubjectTag

| Bangumi API 字段 | DB 字段 |
|---|---|
| `name` | `name` |
| `count` | `count` |

## 6. 错误处理

| 场景 | 策略 |
|---|---|
| API 429 / 5xx | 自动重试 3 次（指数退避 1s→2s→4s），超过则跳过 |
| 网络超时 (30s) | 重试 2 次 |
| 数据解析异常 | 记录 subject_id + 异常到日志，跳过 |
| 数据库连接失败 | 立即终止，import_record 标记 FAILED |
| API 404 (NSFW) | 跳过，不影响流程 |

## 7. 配置

`.env` 文件（不提交仓库）：

```env
DB_HOST=47.96.127.231
DB_PORT=3306
DB_USER=root
DB_PASSWORD=
DB_NAME=anime_tracker
BANGUMI_ACCESS_TOKEN=
BANGUMI_USER_AGENT=zhaizzH/AnimeTracker
```

## 8. 非功能要求

- Python 3.10+
- 请求间隔 1-2 秒，保守限流
- 所有写操作幂等，可安全重复执行
- 日志输出到 stdout，格式 `[timestamp] [LEVEL] message`
