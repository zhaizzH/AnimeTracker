# Implement: db-schema-slim

> 状态：R1–R6 代码全部完成，验证通过。R7 生产重建**未执行**，runbook 见 [`runbook-r7.md`](runbook-r7.md)。

## 顺序（依赖驱动）

### 1. Schema 重写 `docs/database/db-schema.sql` ✅
- [x] 删 4 表：subject_credit, entity_detail_job, search_index_job, rag_index_job
- [x] 改 `subject_person_credit`（+name/+credit_type/person_id NULL/dedup 生成列唯一键）
- [x] 新 `job` 表
- [x] 其余不动；search_index_release 保留
- 已提交 `4afa38be`；临时库验证 20 表建成、dedup_key 与 job 唯一键生效
- 两个坑：① STORED 生成列引用 FK 列时禁止 ON DELETE CASCADE → 改用 VIRTUAL
  ② dedup_key 曾用定长 varchar(191)（原 384 超 utf8mb4 索引字节上限）；复核后改为
     `char(64) GENERATED ALWAYS AS (sha2(concat_ws('#', subject_id, role, ifnull(person_id,0), ifnull(name,'')), 256))`，
     消除隐式长度约束（明文拼接理论上限约 360 字符，严格模式会报 1406 回滚整个事务）与分隔符歧义

### 2. Python 侧 credit 合并（R1） ✅
- [x] `jobs/importer/repository.py`：删 subject_credit 双写；未解析 credit 写 name 占位
- [x] `jobs/indexer/repository.py:124` 摘要 SQL 改单表 LEFT JOIN person
- [x] 删 `entities/enums.py:53` 旧枚举、`entities/models.py:116` 旧映射
- [x] 测试：`test_legacy_credit_mapping.py` → `test_credit_mapping.py`；`test_contract_drift.py` 同步
- [x] 删 Java `pojo/entity/SubjectCredit.java`

### 3. Python 侧 job 合并（R2） ✅
- [x] 三处 repository（backfill / indexer / search_repository）统一读写 `job` 表，靠 `type` 区分
- [x] claim 用 `FOR UPDATE SKIP LOCKED`
- [x] 差异元数据序列化进 `payload_json`；新增 `jobs/job_payload.py` 统一编解码
- [x] `content_hash` 提升为列（幂等比对）；`finished_at` 替代 indexed_at/completed_at
- [x] 调用方迁移：`indexer/main.py`、`importer/repository.py`（`_upsert_search_index_job` / `_upsert_index_job`）、`importer/quality.py`
- [x] 删 Java `pojo/entity/EntityDetailJob.java`、`SearchIndexJob.java`
- [x] 测试：backfill / indexer / search_outbox / quality 全通过

### 4. Redis 导入锁（R4） ✅
- [x] 新 `app/adapters/redis/import_lock.py`（SET NX EX 获取 / 600s 续期 / compare-and-del 释放）
- [x] `jobs/importer/db.py` 删 GET_LOCK 两函数；`main.py` 换用 Redis 锁
- [x] 新增 `tests/adapters/redis/test_import_lock.py`（8 用例）
- 实现注记：用 WATCH+MULTI 做 compare-and-del，而非 Lua——fakeredis 不支持 EVAL

### 5. Redis 进度计数（R5） ✅
- [x] `_run_batch` 成功 INCR `animetracker:import:{record_id}:done`；删 `_start_count_flusher`
- [x] 终态读回计数 → 一次 `complete_import_record` 写库 → DEL 计数键
- [x] 确认 Java `ImportController` 不读运行中进度（无需改）

### 6. Java operation_log 收窄（R3） ✅
- [x] `AdminSubjectController` 移除 SUBJECT_CREATE / SUBJECT_UPDATE 两个 `@OperationLog` 触发点
- [x] `OperationLogConstants` 删除对应两个常量
- 未改 `operation_log` 表结构（R3 明确不动）；`db-schema.sql` 的 action 列注释同步保留原样以免与生产库 drift

### 7. 重建执行（R7） ⏸ 未执行（用户决定：先出 runbook）
- [ ] mysqldump 备份 user/user_collection/operation_log + 整库
- [ ] 新 schema 建库 → 恢复三表 → 部署 → full import
- [ ] 对账：person/character/credit/search_document 计数、credit 摘要抽样 diff
- runbook： [`runbook-r7.md`](runbook-r7.md)

## 验证结果（2026-10-04）

- `cd backend/agent && .venv/Scripts/python -m pytest tests -q` → **610 passed, 6 xfailed, 0 failed**
- `cd backend/business && mvn -q -o test-compile` → **EXIT=0**
- 全仓残留扫描：无 `subject_credit` / `entity_detail_job` / `search_index_job` / `rag_index_job` / `migration-00x` 的失效引用
- 顺手修掉一个**与本任务无关的日期炸弹**：`tests/agent/test_collection_progress.py` fixture 硬编码 `expires_at="2026-09-30"`，到期后 7 个用例全部误走「已过期」分支。改为相对时间（HEAD 上同样失败，非本分支引入）

## 复核发现与修复（trellis-check）

### 阻断
无。

### 已修 / 应修

**1. RAG/SEARCH 的 `FAILED` 终态被当作「立即可领」（回归）**
合并前靠 `status='RETRY'` vs `'FAILED'` 区分可重试/终态；折叠成单 `FAILED` 后该区分必须由 `next_retry_at` 承担，但 claim 谓词写成了 `(next_retry_at IS NULL OR next_retry_at <= :now)` —— `mark_failed` 与退避耗尽的 `mark_retry` 都写 `FAILED` + `NULL`，于是被当成立即可领，**非可重试错误会无退避地重试到 `max_attempts`**（白烧 embedding 配额）。
- 修复：`indexer/repository.py` 与 `indexer/search_repository.py` 的 claim 谓词去掉 `IS NULL OR`。
- **`backfill/repository.py` 必须保留 `IS NULL OR`**：`resume()` 用 `next_retry_at=NULL` 表示「解除暂停、立即可领」，去掉后 resume 的行永远无法再被认领。三种 type 的差异已写入 spec 并各加护栏测试。
- 护栏：`tests/jobs/indexer/test_rag_job_failure_semantics.py`（7 例）、`tests/jobs/backfill/test_backfill.py::test_claim_predicate_keeps_null_next_retry_at_claimable`。

**2. 已解析 credit 的 `credit_type` 被硬编码成 PERSON（语义丢失）**
`local_id is None` 分支保留 `credit.person_type`，已解析分支硬编码 `CreditType.PERSON`。而 `person_ids` 几乎必然命中，占位分支基本不可达 → `credit_type` 实际恒为 `PERSON`，公司/组合条目全部被标成个人，**旧表携带的 PERSON/ORGANIZATION 区分在重建后丢失**，违背 PRD R1「删表但不丢语义」。
- 修复：两分支统一用 `credit.person_type`（HEAD 原 `_upsert_credits` 两个分支都写它）。
- 护栏：`tests/jobs/importer/test_contract_drift.py::test_resolved_organization_credit_keeps_organization_type`（原测试只传 `person_ids={}`，覆盖的是几乎不可达的占位分支）。

**3. Redis 读失败时静默写 `subject_count=0` 的 COMPLETED**
`_read_and_clear_done` 捕获所有异常后 `count = 0`，随后写 COMPLETED —— 一次成功的 full import 会因终态前 Redis 抖动被记成 0 条，无告警。
- 修复：失败时返回 `None`；`main()` 回退到本次运行的内存计数。该回退与旧语义**完全等价**：HEAD 的终态值也是 `run_full()` 的返回值（= `主批次 + 追赶批次` 成功数）。
- 护栏：`tests/jobs/importer/test_progress_counter.py`（7 例）。

### 建议（已处理）
- `test_contract_drift.py` 模块 docstring 写「这些测试应当失败」但当时 10 例全通过 → 改写为回归护栏说明。
- runbook「Redis 计数与旧 `subject_count` 语义略有差异」不准确 → 改为两者同一口径。
- `OperationLog.java` javadoc 与 `db-schema.sql` 的 action 列表仍含 `SUBJECT_CREATE/SUBJECT_UPDATE` → 已同步移除；存量库的列注释为纯元数据，可选 `ALTER ... COMMENT` 对齐（已写入 runbook）。

## 验证命令

- `cd backend/agent && .venv/Scripts/python -m pytest tests -q`
- `cd backend/business && mvn -q -o test-compile`
- 并发锁手测（未做）：两个终端同跑 importer，后者立即失败
- `mysql -e "SHOW TABLES" anime_tracker | wc -l` → 20

## 风险文件（改前必看）

- `backend/agent/jobs/importer/repository.py`（credit 双写 + 原子 bundle，死锁重试逻辑别动）
- `backend/agent/jobs/importer/main.py`（finally 清理顺序：renewer→PID→锁→连接）
- `backend/agent/jobs/indexer/search_repository.py`

## 回滚点

- 步骤 1-6 全为代码 + schema，未动生产数据前随时可弃
- 步骤 7 的备份 SQL 是唯一回滚依赖；备份未完成不执行重建
