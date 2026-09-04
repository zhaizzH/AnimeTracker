# 番剧数据导入器（Bangumi Importer）

> **一句话定位**：从 [Bangumi（bgm.tv）](https://bgm.tv) 拉取番剧元数据、封面与剧集，清洗后写入业务数据库 `anime_tracker` 的命令行工具。

> 上级文档：[AI Agent 总览](../../README.md) · [后端总览](../../../README.md) · [项目总览](../../../../README.md)

## 适用场景

- **首次建库**：用 `full` 或按季度 `season` 批量导入历史番剧条目。
- **日常增量**：用 `recent` 抓取当前在播条目，或用 `since` 补齐指定日期之后开播的条目。
- **抽样验证**：用 `sample` 按年代分层抽样，快速验证导入链路与数据质量。
- **数据体检**：用 `quality.py` 生成只读质量报告，必要时用 `cleanup.py` 按报告执行修复。

- **语言**：Python 3.10 及以上
- **依赖**：`requests`、`sqlalchemy>=2.0`、`pymysql`、`python-dotenv`、`minio`（已并入 Agent 的 `pyproject.toml`）
- **数据源**：Bangumi v0 API（客户端见 `client.py`，自带 429 退避与重试）

## 前置依赖

| 组件 | 说明 |
|------|------|
| Python 3.10+ 与 uv | 与 Agent 共用同一虚拟环境，依赖由 `backend/agent/uv.lock` 锁定 |
| MySQL 8 | 目标库 `anime_tracker`，表结构由 [`docs/database/db-schema.sql`](../../../../docs/database/db-schema.sql) 创建 |
| MinIO | 封面与原始快照存储；**未配置时封面回退为 Bangumi 原始 URL** |
| Redis（可选） | 写入时会登记 RAG 索引任务，供 `jobs/indexer` 消费；Redis 不可用时索引登记失败 |
| 网络 | 需可访问 `https://api.bgm.tv`；如有代理请配置 `HTTPS_PROXY` |

## 架构定位

本工具位于 `backend/agent/jobs/` 下，与 Agent **共用同一 Python 环境与 `.env`**，是数据写入侧的独立 CLI。可由管理后台触发（business 转发到 Agent 的 `POST /api/admin/agent/import/run`，Agent 再以子进程启动本工具），也可命令行手动执行。

## 工作原理

1. 按模式拉取一批 Bangumi `subject_id`（`type=2`，即动画）。
2. 对每个条目：获取详情、制作人员、角色（含声优）与剧集，过滤 NSFW 与非动画条目，下载封面转存 MinIO（替换 URL）、保存原始 JSON 快照到私有桶，解析别名、标签、元标签与全部制作人员职责，最后在一个事务中 upsert 实体和关系。
3. 解析关联条目：只保留 `type=2` 且非 NSFW 的动画关系，由仓储层按本地自然键写入已存在的关联目标。
4. 并发模型：**网络请求并行、数据库写入串行**（`_db_lock` 全局锁），并对任务按线程数交错重排（`_stagger`）降低同区段锁竞争；遇到死锁自动重试最多 4 次并指数退避。
5. 每次运行写入一条 `import_record` 记录，标注模式、数量与状态；后台线程每 3 秒把已处理数刷到 `subject_count`。
6. 单实例保护：通过 MySQL `GET_LOCK` 加锁，并在 `jobs/importer/importer.pid` 写入 PID 文件，供 Agent 跨 worker 重启识别仍存活的导入子进程。

## 快速开始

```bash
cd backend/agent                 # 必须在 agent 根目录执行（依赖 app.* 包路径）
cp .env.example .env             # 与 Agent 共用，填写 DB_* / MINIO_* / BANGUMI_*
uv sync --dev

# 导入 2026 年夏季番，5 并发
uv run python -m jobs.importer.main --mode season --key 2026-summer --workers 5
```

> 请使用 `python -m jobs.importer.main`，不要用 `cd jobs/importer && python main.py`：模块内部依赖 `app.*` 包，需以 `backend/agent` 为工作目录。

## 导入模式

| 模式 | 参数 | 说明 |
|------|------|------|
| `full` | — | 扫描 Bangumi 全目录（去重、保持首次出现顺序），导入所有动画条目；完成后自动追加 `recent` 追赶批次 |
| `season` | `--key 2026-summer` | 按季度导入，key 形如 `{year}-{spring\|summer\|autumn\|winter}` |
| `recent` | — | 仅导入 Bangumi 日历中当前在播条目 |
| `since` | `--since 2026-01-01` | 导入指定日期之后开播的条目（按年月逐月扫描） |
| `sample` | 可选 `--limit` | 按年代分层抽样（`before_1990` / `1990_2009` / `2010_2019` / `2020_plus`），默认配额 `(50, 100, 150, 200)`，默认 `--limit 500` |

季度与月份的映射为：`spring` → 1–3 月，`summer` → 4–6 月，`autumn` → 7–9 月，`winter` → 10–12 月。

通用参数：

| 参数 | 说明 |
|------|------|
| `--mode` | **必填**，取值 `full` / `season` / `recent` / `since` / `sample` |
| `--key` | `season` 模式必填，如 `2026-summer` |
| `--since` | `since` 模式必填，格式 `YYYY-MM-DD` |
| `--resume` | 断点续传：跳过已导入条目，并从 `import_record` 加载上次 checkpoint 继续 |
| `--workers N` | 并发线程数，默认 `10`，上限 `10` |
| `--limit N` | `full` / `sample` 模式的最大条目数；`full` 默认不限，`sample` 默认 `500` |
| `--dry-run` | 仅扫描不写库，**当前只支持 `full` 模式**；不创建 `import_record`，不写 MySQL / MinIO / Redis |

### 核心用法示例

```bash
# 全量导入（不限条数）
uv run python -m jobs.importer.main --mode full

# 全量导入，最多 2000 条，并跳过已导入条目
uv run python -m jobs.importer.main --mode full --limit 2000 --resume

# 试跑：只扫描目录，确认规模后再真正导入
uv run python -m jobs.importer.main --mode full --dry-run --limit 200

# 按季度导入，5 并发
uv run python -m jobs.importer.main --mode season --key 2026-summer --workers 5

# 导入 2025-10-01 之后开播的条目，支持断点续传
uv run python -m jobs.importer.main --mode since --since 2025-10-01 --resume

# 抽样 100 条验证链路
uv run python -m jobs.importer.main --mode sample --limit 100
```

## 配置（`.env`）

配置文件为 `backend/agent/.env`（与 Agent 共用，模板见 `backend/agent/.env.example`）。本工具通过 `load_dotenv() + os.getenv` 读取以下变量：

| 变量 | 默认值 | 说明 |
|------|--------|------|
| `DB_HOST` | `127.0.0.1` | MySQL 主机 |
| `DB_PORT` | `3306` | MySQL 端口 |
| `DB_USER` | `root` | MySQL 用户 |
| `DB_PASSWORD` | 空 | MySQL 密码 |
| `DB_NAME` | `anime_tracker` | 目标数据库名 |
| `BANGUMI_BASE_URL` | `https://api.bgm.tv` | Bangumi API 基址（直连；如走本地代理请配 `HTTPS_PROXY`） |
| `BANGUMI_IMAGE_PROXY_URL` | 空 | 封面图代理前缀（转存 MinIO 前下载用；空则直接下载原图） |
| `BANGUMI_ACCESS_TOKEN` | 空 | Bangumi 访问令牌（可选，提升限流额度） |
| `BANGUMI_USER_AGENT` | `zhaizzH/AnimeTracker` | 请求 UA |
| `MINIO_ENDPOINT` | `localhost:9000` | MinIO 地址 |
| `MINIO_SECURE` | `false` | 是否走 https，同时决定 SDK `secure` 与公开 URL scheme |
| `MINIO_ACCESS_KEY` / `MINIO_SECRET_KEY` | `minioadmin` | MinIO 凭据 |
| `MINIO_BUCKET` | `anime-tracker` | 公开封面桶 |
| `MINIO_RAW_BUCKET` | `anime-tracker-private` | 原始 Bangumi 快照私有桶，**必须与 `MINIO_BUCKET` 不同**（Agent 启动时校验） |
| `RAG_INDEX_VERSION` | `v1` | 写入时登记 RAG 索引任务的版本标识 |

> 若未配置 MinIO，封面将回退为 Bangumi 原始 URL，原始快照不落盘。

## 写入的表

`subject`、`episode`、`subject_tag`、`subject_relation`、`subject_alias`、`subject_meta_tag`、`subject_credit`、`person`、`character`、`subject_person_credit`、`subject_character`、`character_actor`、`entity_detail_job`、`import_record` 由 `repository.py` 的 `write_bundle` 在同一事务内提交；`rag_index_job` 用于登记待索引条目（由 `jobs/indexer` 消费）。

表结构定义见 [`docs/database/db-schema.sql`](../../../../docs/database/db-schema.sql)。

## 目录

```
jobs/importer/
├── main.py        # CLI 入口：参数解析、模式分发、并发编排、进度与 import_record
├── client.py      # Bangumi API 客户端（429 退避 + 指数重试 + 可选请求间隔）
├── db.py          # SQLAlchemy 引擎、upsert 逻辑、导入锁与 import_record 读写
├── normalize.py   # 原始 JSON → 规范化结构（别名、标签、元标签、制作人员、放送星期）
├── repository.py  # 仓储层：单条目事务提交、checkpoint 读写、RAG 索引任务登记
├── storage.py     # MinIO 边界：封面转存与原始快照写入
├── quality.py     # 只读数据质量报告生成器（独立 CLI）
├── cleanup.py     # 按已确认报告执行的最小修复器（独立 CLI）
├── importer.pid   # 运行时 PID 文件（自动生成，便于跨进程识别存活实例）
└── import.log     # 运行日志（视本地配置生成）
```

> 依赖并入 `../../pyproject.toml`（与 Agent 共用环境），不在本目录单独维护 `requirements.txt`。

## 数据质量与修复

`quality.py` 与 `cleanup.py` 是独立于导入主流程的体检工具：

```bash
# 生成只读质量报告（不修改数据库或对象存储）
uv run python -m jobs.importer.quality --output ./quality-report.json --index-version v1

# 按报告执行修复：必须显式传入报告的 sha256 作为确认
uv run python -m jobs.importer.cleanup --plan ./quality-report.json --confirm-sha256 <sha256>
```

`--index-version` 传入时会额外校验 Redis 向量索引的一致性。`cleanup` 未传 `--confirm-sha256` 时直接以退出码 `2` 拒绝执行；报告与计划不匹配时同样拒绝，避免误删。

## 常见问题

**Q：提示 `ModuleNotFoundError: No module named 'app'`？**
A：工作目录不对。必须在 `backend/agent` 下用 `python -m jobs.importer.main` 执行。

**Q：`season mode needs --key` / `since mode needs --since`？**
A：这两个参数在对应模式下必填，缺一即报错终止。

**Q：`dry-run currently supports full mode only`？**
A：`--dry-run` 目前只对 `full` 模式实现，其他模式需改用 `sample --limit` 做小规模验证。

**Q：导入中途失败，能续跑吗？**
A：可以。加 `--resume` 会加载上次的 `import_record` checkpoint。注意 checkpoint 会校验扫描结果的 SHA-256 与最后一条目的 ID，**扫描范围变化（如换季度）会拒绝复用旧断点**，需不带 `--resume` 重跑。

**Q：日志里出现「死锁，重试」？**
A：正常保护机制。写入串行化后仍可能与外部事务冲突，导入器最多重试 4 次并指数退避，超过后该条目标记为失败并继续。

**Q：导入突然被拒绝，提示已有导入在跑？**
A：MySQL `GET_LOCK` 单实例保护生效。确认无其他导入进程后，检查 `jobs/importer/importer.pid` 是否残留（异常退出时应自动清理），或通过 Agent 的僵尸记录清理逻辑处理。

**Q：封面没有转存到 MinIO？**
A：检查 `MINIO_*` 配置与桶是否存在。未配置时是预期行为——封面会保留 Bangumi 原始 URL。

**Q：`subject_count` 显示的数字和最终条目数不一致？**
A：`subject_count` 由后台线程每 3 秒刷新，是过程值；导入结束会写入最终值。以结束日志的「共 N 个条目」为准。

## 与相邻模块的关联

- **Agent**（[`../../README.md`](../../README.md)）：管理端触发的导入由 Agent 的 `POST /api/admin/agent/import/run` 以子进程方式启动本工具（见 `app/adapters/subprocess/import_job.py`），共用环境与 `.env`。
- **索引器**（[`../indexer/`](../indexer/)）：本工具在 `rag_index_job` 登记待索引条目，索引器消费该表构建向量索引。
- **调度器**（[`../scheduler/`](../scheduler/)）：按 Asia/Shanghai 时间定时以 `recent` / `since` / `full` 模式启动本工具。
- **business**：导入结果经 `subject` 等表对外提供查询；管理端「导入记录」页读取 `import_record`。
- **后端总览**：[`../../../README.md`](../../../README.md) · **项目总览**：[`../../../../README.md`](../../../../README.md)

## 待补充

1. **本地运行产物未纳入版本控制**：`import.log` 与 `importer.pid` 是运行期产物，当前存在于工作区。建议确认是否应加入 `.gitignore`（仓库根 `.gitignore` 已忽略 `*.log`，但 `importer.pid` 未见对应规则）。
2. **质量报告与容量门禁的判读阈值**：`quality.py` 生成的报告可被 `jobs/indexer/gate.py` 消费，但各项指标（覆盖率、NSFW 计数、内容哈希一致性）的合格线随数据规模变化，尚无文档化建议值。
3. **Bangumi 限流的具体额度**：代码中按 429 响应动态退避，`BANGUMI_ACCESS_TOKEN` 能提升额度但具体配额取决于 Bangumi 平台策略，无法从代码推断。
