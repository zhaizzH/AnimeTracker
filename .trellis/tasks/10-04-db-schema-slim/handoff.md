# 交接状态 (2026-10-04 会话中断快照)

分支: `feat/db-schema-slim`（基线 main，task.py set-branch 已记录）

## 已完成并提交 (commit 4afa38be)

- `docs/database/db-schema.sql`：23→20 表（job 统一表、subject_person_credit 合并版、删 4 表）
- `.trellis/spec/backend/database-guidelines.md`：credit 单表契约 + Redis 锁描述
- 任务文档 prd.md / design.md / implement.md（R6 已撤销：spec 规定 search_index_release 为 MySQL 唯一事实）
- schema 已在临时库验证：20 表建成、dedup_key 唯一键生效、job 唯一键生效
  - 关键坑：MySQL STORED 生成列引用 FK 列时禁止 ON DELETE CASCADE → dedup_key 用 VIRTUAL
  - dedup_key 定长 varchar(191)（原 384 超 utf8mb4 索引 3072 字节限）

## 已完成未提交（工作区改动，两个 worker 完成）

### R1 credit 合并 — worker creditmerge 完成 ✅
- importer/repository.py：删 `_upsert_credits` 双写；`_upsert_subject_person_credits` 写占位行/FK 行；`_profile_source` 摘要改单表 LEFT JOIN
- indexer/repository.py:124 摘要同步改
- 删 `SubjectCredit.java`（301 行）；entities 层清理 + `SubjectPersonCredit` 加 name/credit_type
- 测试改为 test_credit_mapping.py
- ✅ 30 passed；✅ mvn compile EXIT=0
- 汇报全文: /tmp/db-slim/creditmerge_report.md

### R3+R4+R5 — worker redisops 完成 ✅
- 新增 `app/adapters/redis/import_lock.py`（WATCH+MULTI compare-and-del，非 Lua——fakeredis 不支持 EVAL）
- importer/db.py：删 GET_LOCK 两函数；main.py：Redis 锁 + renew 线程 + finally release
- R5：`_done_count`/flusher 删，改 Redis INCR `animetracker:import:{record_id}:done`，终态 `_read_and_clear_done` 回写
- R3：AdminSubjectController 删 SUBJECT_CREATE/UPDATE 两个 @OperationLog 触发点
- 新增 tests/adapters/redis/test_import_lock.py（8 用例）
- ✅ 47 passed（其范围）；全量 15 failed 均属 jobmerge 未完成的范围
- 遗留: ① progress key 无 TTL，SIGKILL 残留 ② full 模式 count 语义=实际成功数（不含 base_done）
- 汇报全文: /tmp/db-slim/redisops_report.md

### R2 job 合并 — worker jobmerge 未完成 ❌（被 kill）
已动文件（工作区有半成品改动）:
- `backend/agent/jobs/job_payload.py`（新增，untracked）
- backfill/repository.py、indexer/repository.py、indexer/search_repository.py（部分改）、
  importer/quality.py、entities/ports.py、tests/jobs/{backfill,indexer} 等 19 个 modified 文件中属于 R2 的部分
- 失败测试集中在: tests/jobs/backfill/test_backfill.py、tests/jobs/indexer/test_search_repository.py、tests/agent/test_collection_progress.py

## 下一步（新会话）

1. `cd C:/workspace/project/AnimeTracker && git checkout feat/db-schema-slim`
2. `python .trellis/scripts/task.py start 10-04-db-schema-slim`（恢复 active 指针）
3. 评估 R2 半成品：`git diff HEAD -- backend/agent/jobs/backfill backend/agent/jobs/indexer backend/agent/jobs/job_payload.py backend/agent/app/entities/ports.py`
   - 若质量可救 → 接着补完（契约见 implement.md 第 3 节 + design.md R2 节）
   - 若太乱 → `git checkout HEAD -- <R2 文件>`（注意别波及 R1 改的 importer/repository.py、indexer/repository.py 摘要行；这两文件 R1/R2 改动交织，建议只重做而非 checkout）
4. R2 完成后跑全量: `cd backend/agent && .venv/Scripts/python -m pytest tests -q` → 目标 0 failed
5. `cd backend/business && mvn -q compile` → EXIT=0
6. 提交 → R7 重建（implement.md 第 7 节：备份 user/user_collection/operation_log → 新 schema → full import 重灌）
7. trellis-check + finish-work

## R2 新表契约速查（给接续者）

- type: ENTITY_DETAIL / SEARCH_INDEX / RAG_INDEX
- index_version: ENTITY_DETAIL 固定 ''；content_hash 是列（幂等比对）
- embedding_provider/model/dimensions、profile_version、source_id、checkpoint_json、source_hash → payload_json
- finished_at 替代 indexed_at/completed_at
- 唯一键 (type, entity_kind, entity_id, index_version)
- claim: `... FOR UPDATE SKIP LOCKED`
- importer/repository.py 的 `_upsert_search_index_job`/`_upsert_index_job` 两方法属 R2（embedding 元组进 payload）

## 进程清理

3 个 pi worker 已全部结束（creditmerge/redisops 自然完成，jobmerge PID 1213 已 kill）。/tmp/db-slim/ 下有日志与汇报。
