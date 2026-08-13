# 番剧数据导入器（Bangumi Importer）

从 [Bangumi（bgm.tv）](https://bgm.tv) 拉取番剧元数据并清洗写入业务数据库（`anime_tracker`）的命令行工具。支持多种导入范围、并发抓取、封面转存 MinIO，以及 NSFW 过滤。

- **语言**：Python 3.10+
- **依赖**：`requests`、`sqlalchemy>=2.0`、`pymysql`、`python-dotenv`、`minio`
- **数据源**：Bangumi v0 API（客户端见 `client.py`，自动限流 + 重试）

## 架构定位

本工具内置于 `backend/agent/` 下，与 Agent **共用同一 Python venv 与 `.env`**，是数据写入侧的独立 CLI。可由管理后台触发（Java 经 agent 转发到 `POST /api/admin/agent/import/run`），也可命令行手动执行。

## 工作原理

1. 按模式拉取一批 Bangumi `subject_id`（type=2，即动画）。
2. 对每个条目：获取详情与剧集、下载封面并转存到 MinIO（替换 URL）、解析标签与番剧关联，最后 upsert 入库。
3. 并发模型：**网络请求并行、数据库写入串行**（全局锁），从结构上消除并发事务的死锁；遇到死锁自动重试。
4. 每次运行写入一条 `import_record` 记录，标注模式 / 数量 / 状态。

## 快速开始

```bash
cd backend/agent/importer    # 依赖与环境变量与 Agent 共用（backend/agent/.env）
python main.py --mode season --key 2026-summer
```

## 导入模式

| 模式 | 参数 | 说明 |
|------|------|------|
| `full` | — | 扫描 2000 年至今全部月份，导入所有动画条目 |
| `season` | `--key 2026-summer` | 按季度导入，key 形如 `{year}-{spring\|summer\|autumn\|winter}` |
| `recent` | — | 仅导入 Bangumi 日历中当前在播条目 |
| `since` | `--since 2026-01-01` | 导入指定日期之后开播的条目 |

通用参数：

- `--resume`：跳过已导入（`import_status = 1`）的条目，适合断点续传。
- `--workers N`：并发线程数（默认 `10`，上限 `10`）。

示例：

```bash
python main.py --mode full --resume
python main.py --mode season --key 2026-summer --workers 5
python main.py --mode since --since 2025-10-01 --resume
```

## 配置（`.env`）

| 变量 | 默认值 | 说明 |
|------|--------|------|
| `DB_HOST` | `127.0.0.1` | MySQL 主机 |
| `DB_PORT` | `3306` | MySQL 端口 |
| `DB_USER` | `root` | MySQL 用户 |
| `DB_PASSWORD` | 空 | MySQL 密码 |
| `DB_NAME` | `anime_tracker` | 目标数据库名 |
| `BANGUMI_ACCESS_TOKEN` | 空 | Bangumi 访问令牌（可选，提升限流额度） |
| `BANGUMI_USER_AGENT` | `zhaizzH/AnimeTracker` | 请求 UA |
| `BANGUMI_BASE_URL` | `https://proxy.8000150.xyz/https%3A%2F%2Fapi.bgm.tv` | Bangumi API 基址（经代理访问） |
| `BANGUMI_IMAGE_PROXY_URL` | `https://proxy.8000150.xyz` | 封面图代理前缀（转存 MinIO 前下载用） |
| `MINIO_ENDPOINT` | `localhost:9000` | MinIO 地址（封面转存；公开 URL 由 `{scheme}://{endpoint}` 推导，可选） |
| `MINIO_SECURE` | `false` | 是否走 https，同时决定 SDK `secure` 与公开 URL scheme |
| `MINIO_ACCESS_KEY` / `MINIO_SECRET_KEY` | `minioadmin` | MinIO 凭据 |
| `MINIO_BUCKET` | `anime-tracker` | 封面存储桶 |

> 若未配置 MinIO，封面将回退为 Bangumi 原始 URL。

## 写入的表

`subject`、`episode`、`subject_tag`、`subject_relation`、`import_record`（由 `db.py` 中的 upsert / record 函数负责）。

## 目录

```
importer/
├── main.py        # CLI 入口：模式分发、并发编排、进度与 import_record
├── client.py      # Bangumi API 客户端（限流 + 重试）
└── db.py          # SQLAlchemy 引擎与 upsert 逻辑
```

> 依赖并入 `../requirements.txt`（与 Agent 共用 venv）。

## 相关文档

- AI Agent 总览：[`../README.md`](../README.md)
- 后端总览：[`../../README.md`](../../README.md)
- 项目总览：[`../../../README.md`](../../../README.md)
