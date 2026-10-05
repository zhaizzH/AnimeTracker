# 交接状态 (2026-10-04 第二会话结束)

分支: `feat/db-schema-slim`（基线 main）

## 总览

| 需求 | 状态 |
|---|---|
| R1 credit 合并 | ✅ 完成 |
| R2 三 job 表 → 单 job 表 | ✅ 完成 |
| R3 operation_log 收窄 | ✅ 完成 |
| R4 导入锁迁 Redis | ✅ 完成 |
| R5 进度计数迁 Redis | ✅ 完成 |
| R6 撤销（spec 冲突） | — 不迁移 |
| R7 生产重建 | ⏸ **未执行**，runbook 已就绪 |

- 已提交：`4afa38be`（schema 23→20 表 + spec + 任务文档）
- 未提交：R1–R6 全部代码改动 + 文档同步

## 本会话完成的工作（第二轮）

### R2 收尾
- `backfill/repository.py`：`json.dumps` → 统一走 `jobs/job_payload.py` 的 `encode`；删未用 `JobType` import
- `indexer/search_repository.py`：同上清理；还原被上一轮半成品剥掉的两空行分隔
- 删 Java `pojo/entity/EntityDetailJob.java`、`SearchIndexJob.java`（`@TableName` 指向已 DROP 的表，全仓无引用）
- 确认 `jobs/indexer --queue legacy|search|both` 三种模式语义不变：`rag_index_job` 并入 `job` 表后 `type='RAG_INDEX'` 路径仍完整可用，非废弃代码

### R3 收尾
- `OperationLogConstants` 删除 `ACTION_SUBJECT_CREATE` / `ACTION_SUBJECT_UPDATE`
- **未改** `operation_log` 表结构与 `db-schema.sql` 中该列的注释：R3 明确"表结构不动"，且该表不在重建范围内，改注释会让 `db-schema.sql` 与生产库 drift。历史行仍含这两个 action，前端 action 筛选是自由文本输入，不受影响

### 文档同步
- `backend/agent/README.md`、`jobs/importer/README.md`、`backend/business/README.md`、`backend/README.md`、`docs/README.md`、`docs/api/README.md`、根 `README.md`：表清单、实体计数、迁移说明、`--queue` 语义全部对齐新 schema
- 顺带修掉一轮遗留的 R4/R5 过期文档：importer README 仍在说"后台线程每 3 秒刷 subject_count""MySQL GET_LOCK 加锁"
- 各 py docstring（`ports.py` / `entity_loader.py` / `backfill/worker.py` / `indexer/main.py`）表名同步

### 测试
- **修掉一个与本任务无关的日期炸弹**：`tests/agent/test_collection_progress.py` fixture 硬编码 `expires_at="2026-09-30"`，今天（10-04）之后 7 个用例全部误判为「已过期」。改为相对时间 `_FUTURE_EXPIRES_AT`，保留一个显式过去时间用例覆盖过期分支。HEAD 上同样失败，非本分支引入

## 验证结果

```
cd backend/agent && .venv/Scripts/python -m pytest tests -q
→ 594 passed, 6 xfailed, 0 failed

cd backend/business && mvn -q -o test-compile
→ EXIT=0
```

残留扫描：全仓无 `subject_credit` / `entity_detail_job` / `search_index_job` / `rag_index_job` / `migration-00x` 的失效引用（方法名 `_upsert_search_index_job` 属有意保留）。

## 未做的验证

- Redis 锁并发手测（两个终端同跑 importer，后者应立即失败）——需可达 MySQL + Redis
- `SHOW TABLES` = 20 的实库确认——handoff 第一轮已在临时库验过
- R7 全部步骤

## R7 执行状态（2026-10-04 本地库）

已执行到索引重建，**因网络受阻未完成**。详见 [`implement.md`](implement.md) 第 7 节与 [`runbook-r7.md`](runbook-r7.md)。

- ✅ 备份 + 实测可还原；schema 重建（20 表）；恢复用户三表；导入 `season 2026-autumn` 136 条 COMPLETED
- ✅ AC1 / AC2 / AC6 / AC7 全部通过（AC2：98 个重叠 bangumi_id 中 97 个逐字符一致，唯一差异为上游超集）
- ✅ **索引重建（2026-10-05 完成）**：5368 SEARCH_INDEX + 136 RAG_INDEX 全部 COMPLETED，`search_document` 5504 行，0 FAILED。此前 42 个 `EMBEDDING_UNAVAILABLE` FAILED 任务网络恢复后自动重领成功
- ✅ **backfill（2026-10-05 完成）**：ENTITY_DETAIL 4080/4080 全 COMPLETED；person 3086 / character 994 全 COMPLETE；credit 未解析 0。R7 全部步骤已完成，终态对账全绿（见 implement.md）

**R7 已完成（2026-10-05）。** 同日补跑 `--mode recent` 101 条 COMPLETED + backfill 增量清零；索引增量（SEARCH 8937 PENDING + 203 FAILED 可重试 / RAG 80 PENDING）**用户决定跳过**——Clash fake-IP 轮流劫持 dashscope/bgm.tv，网络稳定后 `jobs.indexer.main --index-version v1` 可接上。验证：pytest 629 passed / mvn EXIT=0。
网络教训：Clash fake-IP 轮流劫持 dashscope/bgm.tv，Python 显式 `HTTPS_PROXY=http://127.0.0.1:7897` 绕过。多进程 backfill 死锁：claim_batch 的 lease 回收 UPDATE 与 SKIP LOCKED 冲突，临时并行 worker（已删）跳过 lease UPDATE 后 8 进程无冲突。

**恢复方式**：修好 `*.aliyuncs.com` 的网络/代理规则后，按 runbook 第 6 节重跑
`.venv/Scripts/python -m jobs.indexer.main --index-version v1`（去掉 `--limit`）。

## 下一步

1. 修 DashScope 网络后完成索引重建 + backfill
2. 按需补 full import（本次按用户决定只跑了 `season 2026-autumn` 验证链路）
3. `trellis-check` 复核本批改动 → 提交

## 遗留项

1. **progress key 无 TTL**：`animetracker:import:{record_id}:done` 仅在正常终态被 DEL，SIGKILL 会残留。`--resume` 复用同一 `record_id`，故 `main()` 拿到导入锁后会先 `_clear_done(record_id)` 清零，避免终态 `subject_count` 虚高（已修 + 测试 + 写入 importer README Q&A）。
2. **`subject_count` 语义未变**：终态值与迁移前同口径（`主批次 + 追赶批次`成功数）。Redis 不可用时回退到本次运行的内存计数，不会退化成 0。
3. **`operation_log` 列注释**：`db-schema.sql` 与 `OperationLog.java` 已移除 `SUBJECT_CREATE/SUBJECT_UPDATE`；存量库的列注释仍是旧的（纯元数据，可选 `ALTER ... COMMENT`，见 runbook）。
4. **`job` 表 business 侧无对应 pojo**：Java 不直接读写任务表，`pojo/entity/` 现有 17 个实体。
5. **credit 占位行无提升路径**：`person_id IS NULL` 的行不会被 backfill 回填，靠下次 full import 写 FK 行 + stale-mark 自愈（spec 已按实际行为改写）。
6. **`SEARCH_INDEX` 的 lease 回收写入 `FAILED`+`NULL` 表示耗尽**，与 `mark_failed` 的 `ABANDONED` 终态不一致（功能上由 `attempts < max_attempts` 兜住，属一致性问题）。

## 待开任务：`jobs/backfill --pause` 对 PENDING 任务无效（既有缺陷，非本分支引入）

**用户已决定：本次只记录，另开任务处理。**

- 位置：`backend/agent/jobs/backfill/repository.py:231-251` `pause()` 与 `:127-137` claim 谓词
- 现象：`pause()` 把 PENDING/FAILED 行的 `next_retry_at` 设为一年后（docstring 明写「暂停所有 PENDING 任务（…next_retry_at 远未来）」），但 claim 的 **PENDING 分支完全不看 `next_retry_at`**，所以被暂停的 PENDING 详情任务照常被领取。`--resume`（`:253-272`）对 PENDING 同为空操作。
- 影响：`--pause`（CLI 帮助文字「暂停所有待处理任务」，`jobs/backfill/main.py:35`）只拦得住 FAILED 行，运维用它停 backfill 不生效。
- 测试为何没暴露：`tests/jobs/backfill/test_backfill.py:153-163` 只断言「发出了 UPDATE」，未验证 claim 行为。
- 修复方向：claim 的 PENDING 分支加 `AND (next_retry_at IS NULL OR next_retry_at <= :now)`。安全——正常 PENDING 行的 `next_retry_at` 本就是 NULL（`enqueue` 不写该列），只有被 `pause()` 设过远期时间的行会被挡住。补一条「pause 后 claim 返回空」的用例。
- 注意：**不要**顺手把 FAILED 分支的 `IS NULL` 也去掉——`resume()` 依赖它（见 spec「claim 谓词里的 `next_retry_at IS NULL` 按 type 而异」）。
- 历史：旧 `entity_detail_job` 的谓词形状相同，属历史遗留。

## 复核（trellis-check）修复摘要

复核发现 3 个「应修」，均已修复并补护栏测试（详见 [`implement.md`](implement.md) 的「复核发现与修复」段）：

1. RAG/SEARCH 的 `FAILED` 终态被 claim 当作「立即可领」→ 去掉谓词里的 `IS NULL OR`（backfill 反向保留，因 `resume()` 依赖它）
2. 已解析 credit 的 `credit_type` 硬编码 PERSON，丢掉 ORGANIZATION → 两分支统一用上游 `credit.person_type`
3. Redis 读失败静默写 `subject_count=0` → 返回 `None`，回退到本次运行计数
