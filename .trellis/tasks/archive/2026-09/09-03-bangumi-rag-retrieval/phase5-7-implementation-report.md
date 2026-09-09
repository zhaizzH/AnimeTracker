# Phase 5–7 MySQL + Vector Set 实现报告

日期：2026-09-05

> 本文按时间保留 2026-09-05 至 2026-09-06 的实施流水。早期的 PENDING/RETRY、Embedding 不可用和“尚未回填”均为历史状态；当前结论以本节和 [真实索引运行报告](./phase8-index-runtime-report.md) 为准。

## 当前结论（2026-09-06 18:29，UTC+8）

- `search_index_job v1/COMPLETED=13,173`；`rag_index_job v1/INDEXED=220`。
- MySQL `search_document` 与 Redis DB 1 的 Vector Set 数量一致：SUBJECT=220、EPISODE=1,658、PERSON=9,275、CHARACTER=2,129。
- MySQL/Redis 双投影和 Evidence 实时接口可用；全量回填与 Embedding 网络阻断已解除。
- 上述 5 个 shadow 失败与 candidate 尚未生成属于本报告所记录的历史快照；2026-09-07 已修复并完成 120/120 的 `RELEASE_CANDIDATE` 回放，capacity/latency/human 报告也已生成并通过 gate，v1 ACTIVE release 已激活；2026-09-09 用户确认 24 小时灰度与 release/功能开关回滚通过。`shadow_eval.py --status RELEASE_CANDIDATE` 仍会在失败 case 存在时 fail closed。

## 已实现

- `search_document` 与 `search_index_release` 已加入初始化 Schema 和 `migration-003-search-projection.sql`。
- Business 新增 `POST /api/client/subjects/lexical-search`，返回 `indexVersion`、`profileVersion`、候选和词法分数；无 active release 时返回 503。
- Agent indexer 在同一任务中写 MySQL lexical shadow 与 Redis Vector Set；任一侧失败不会确认任务完成。
- Vector Set 使用 `rag:vectors:{entity_kind}:{indexVersion}`，通过 `VADD/VSIM/VREM` 写入、查询和 tombstone；发布/回滚只通过 MySQL release store。
- Agent RRF 使用 Business 返回的 `indexVersion` 查询同版本 Vector Set，并将 `candidates` 归一化为检索候选。
- Shadow/gate 已改为只接受 MySQL release store；生产 CLI 会在 gate 通过后通过事务切换 release，当前不会误切 Redis alias。

## 实现当时的本地验证（历史快照）

```text
backend/agent: .venv\Scripts\python.exe -m pytest -q
233 passed

backend/business: mvn -B clean test
BUILD SUCCESS
36 tests in client/app modules passed
```

当前全量测试结果已提升为 Agent `268 passed, 1 deselected`、Business `37` tests passed；以 [真实索引运行报告](./phase8-index-runtime-report.md) 为准。

## 初始未完成项（历史快照）

- 已在本地运行库 `localhost:3306/anime_tracker` 执行 `migration-003-search-projection.sql`；`search_document` 与 `search_index_release` 已创建，但尚未进行全量投影回填。
- 120 条真实 golden case、Recall/MRR/nDCG/延迟门禁和 20 条人工证据检查已在 Phase 8 报告中完成；本报告此处保留的是实现阶段的历史状态。
- 尚未进行 24 小时灰度；因此任务保持 `in_progress`，RAG 不应宣称已发布。

## 运行约束

1. 先迁移投影表，再运行 indexer；`search_index_release` 没有 active 行时词法 API 按设计返回 503。
2. Redis 必须支持 `VADD`、`VSIM`、`VREM`；普通 Redis 不满足条件时保持 RAG 关闭。
3. 真实 gate 通过后才允许激活 MySQL release，旧版本在回滚窗口内保留。

## 2026-09-05 运行态检查

- 8080 Business、8090 Agent、6379 Redis 端口均可连接。
- Agent `/api/client/agent/health` 返回 HTTP 200，`llm_configured=true`。
- Redis `COMMAND INFO` 确认 `VADD`、`VSIM`、`VREM` 可用。
- Business `/api/client/subjects/lexical-search` 返回 HTTP 503 `词法索引尚未迁移`；服务已加载新代码，但真实库尚未执行 `migration-003-search-projection.sql`，符合 fail-closed 约束。

## 2026-09-05 质量检查补充

- Redis Vector Set 过滤器已统一使用数值布尔值（`1/0`），并将 `air_status` 规范化为小写；`COMMAND INFO` 的映射响应不会再被误判为“不支持”。
- Evidence authority 响应必须显式 `active=true` 才能进入 RAG 上下文；缺失或失效响应按 `evidence_unavailable` fail-closed。
- Python 全量测试结果：236 passed；仅 `tests/evals/test_runner.py::TestLoadGoldenCases::test_loads_from_custom_path` 受当前 Windows 临时目录权限（`C:\Users\zzz\AppData\Local\Temp\pytest-of-zzz`）阻塞，非业务断言失败。
- Maven 全量测试：36 passed；前端 `npm run typecheck` 与受控权限下 `npm run build` 均通过。

## 2026-09-05 真实迁移结果

- 幂等迁移首次执行 2 条 `CREATE TABLE IF NOT EXISTS` 语句成功；第二次重复执行也成功。
- 校验通过：`search_document`、`search_index_release` 存在；`ft_search_document_text` 覆盖 `title`、`aliases`、`lexical_text`。
- 当时 `search_index_release` 的 `ACTIVE` 行数为 0；词法 API 返回 HTTP 503 `词法索引尚未发布`，符合发布指针 fail-closed 约束。

## 2026-09-05 回填 smoke 结果

- 读取到 `rag_index_job` 共 220 条 `v1` 任务：218 条仍为 `PENDING`，2 条 smoke 任务进入 `RETRY`。
- 两条任务均因 `EmbeddingUnavailable` 未写入 `search_document`；Redis 与 MySQL 连接正常。
- DashScope `text-embedding-v4` 连通性在清空本地代理后仍返回 TLS/网络错误（`SSLEOFError`），因此暂停全量回填，未激活任何 release。
- 待外部 embedding 网络恢复后，可直接重试 `RETRY` 任务，再以小批量验证后继续全量回填。

## 2026-09-05 代理关闭后重试结果

- 关闭代理后重试成功：`rag_index_job` 为 `INDEXED=4`、`PENDING=216`，无 `RETRY/FAILED`。
- MySQL `search_document` 已写入 `v1` 版本 4 条；Redis `rag:vectors:SUBJECT:v1` 已有 4 个成员。
- 词法 API 仍返回 HTTP 503 `词法索引尚未发布`，因为尚未创建并激活 `search_index_release` 的 ACTIVE 记录。

## 2026-09-05 全量回填尝试结果

- 全量进程在代理环境下启动后已主动停止，避免继续触发外部 embedding 重试。
- 当前 `rag_index_job`：`INDEXED=4`、`PENDING=66`、`RETRY=150`；被中断的 10 条 `RUNNING` 已恢复为 `PENDING`。
- 150 条 RETRY 均为 `EmbeddingUnavailable`，未写入错误的投影数据；ACTIVE release 仍为 0。
- 后续必须在确认 `DASHSCOPE_API_KEY` 的无代理 HTTPS 出网后，再重试 RETRY/PENDING，成功后才进入评测和 release 激活。

## 2026-09-06 服务重启复核

- 8080 Business、8090 Agent、6379 Redis、3306 MySQL 均可连接；Agent health 返回 HTTP 200 且 `llm_configured=true`。
- DashScope embedding smoke 仍返回 `EmbeddingUnavailable`；数据库队列保持 `INDEXED=4`、`PENDING=66`、`RETRY=150`，未产生新的投影或 release。

## 2026-09-06 Trellis 继续复核

- 当前 Codex 进程仍带有 `HTTP_PROXY/HTTPS_PROXY/ALL_PROXY=http://127.0.0.1:9`；embedding smoke 继续失败。
- 未启动新的回填批次，队列与 release 状态保持不变，等待在清除代理变量的同一进程中验证网络后再继续。

## 2026-09-06 无代理终端 smoke 进展

- 用户在无代理终端成功完成 1 条 smoke：队列更新为 `INDEXED=5`、`PENDING=66`、`RETRY=149`。
- 当前 Codex 进程仍检测到代理变量，因此不从本会话启动全量任务；应在同一无代理终端继续消费剩余任务。

## 2026-09-06 双投影一致性复核

- 全量任务表显示 `INDEXED=220`，MySQL `search_document` 为 220 条，但 Redis `rag:vectors:SUBJECT:v1` 只有 216 个成员。
- 缺失成员为 Subject 1–4；为避免错误发布，已将这 4 条任务恢复为 `PENDING`（其余 216 条保持 `INDEXED`），等待无代理终端补写向量。
- 在 Redis 成员数达到 220 且与 MySQL entity ID 集合一致前，不创建或激活 `search_index_release`。

## 2026-09-06 缺失向量修复结果

- 无代理终端已补写 Subject 1–4；最终 `rag_index_job=INDEXED 220`、`search_document(v1)=220`、`rag:vectors:SUBJECT:v1=220`，entity ID 集合一致。
- 当前双投影回填通过；Phase 8 五报告 gate 已通过，但 release 仍按人工确认要求保持未发布。

## 2026-09-06 120-case 可行性核验

- 当前真实库计数：`subject=220`、`subject_alias=181`、`subject_tag=3888`、`subject_meta_tag=804`。
- 人物/角色关系数据尚未具备：`person=0`、`character_alias=0`、`subject_person_credit=0`、`subject_character=0`、`character_actor=0`；`subject_relation` 仅 6 行（3 对双向关系）。
- 现有 53 条 golden case 含部分与真实库不匹配的人物、角色、经典番名和系列关系样例，不能在此基础上直接补 67 条并宣称已完成真实 120-case 门禁。
- 结论：先补齐人物/角色/关系真实导入，或将评测目标拆成“当前数据可验证子集 + 明确缺口报告”；在此之前不激活 release。

## 2026-09-06 recent 导入代理复核

- 首次 `recent --resume` 使用环境代理 `127.0.0.1:9` 时，Bangumi 日历请求被拒绝；旧逻辑将“日历未获取到”当作 0 条成功并错误完成 `import_record=9`。
- 已修复 `backend/agent/jobs/importer/main.py`：日历请求失败现在抛出异常，由主流程将记录置为 `FAILED`，保留 checkpoint 和累计计数，不再伪造完成；新增回归测试 `tests/jobs/importer/test_recent_failure.py`。
- 使用可用代理 `http://127.0.0.1:7897` 执行 `--mode recent --resume` 成功：日历去重后 113 条，数据库已有条目 113/113，无缺失；`import_record=9` 最终为 `COMPLETED`、`success_count=111`、`failure_count=0`、`skipped_count=90`、checkpoint `offset=113`。
- 原日志中的“跳过关联条目”仍是关联目标不在当前本地集合的非致命警告，不代表主条目导入失败；当前日历条目集合与数据库集合差集为空。
- 验证：导入器测试 26 passed，Python compileall 通过，`git diff --check` 通过；修复提交为 `7da6006`。

## 2026-09-06 recent 导入后实体索引复核

- recent 导入后真实库实体计数为：`subject=220`、`person=9275`、`character=2129`、`subject_person_credit=14434`、`subject_character=2160`、`character_actor=2293`。
- 导入已产生通用 `search_index_job`：`SUBJECT=111`、`PERSON=9275`、`CHARACTER=2129`、`EPISODE=1658` 条待消费任务；此前已有 Subject 投影仍为 MySQL 220 条、Redis Vector Set 220 个成员。
- 使用代理 `http://127.0.0.1:7897` 消费 search 队列 10 条进行 smoke；DashScope 返回 `EmbeddingUnavailable`，未新增投影，10 条任务进入带 `next_retry_at` 的可重试失败状态。未激活 release。
- 本次 smoke 暴露错误码语义问题：Embedding 故障曾被记录为 `REDIS_UNAVAILABLE`；已修复为 `EMBEDDING_UNAVAILABLE`，并补充限流与 Redis 故障区分测试。修复前产生的历史 10 条失败记录不作为成功证据。
- 当时 `rag_index_job` 为 `INDEXED=118/PENDING=102`，`search_index_release` 为空；该队列数已被文首当前结论覆盖。

## 2026-09-06 全量 search 双投影完成（覆盖前述运行态）

- 用户在清空代理变量的终端中完成 DashScope `text-embedding-v4` HTTP 200 探针，并继续消费剩余 search 队列。
- `search_index_job` 最终为 `COMPLETED=13,173`，`PENDING=0`、`FAILED=0`；`character` 保留字导致的 1,760 条失败已通过 SQL 引用修复后重试完成。
- v1 `search_document` 与 Redis Vector Set 数量一致：SUBJECT=220、EPISODE=1,658、PERSON=9,275、CHARACTER=2,129。
- 质量报告覆盖率为 100%，但仍发现 1 条 `EPISODE_SHORTAGE` 和 38 条 `EPISODE_STATUS_DRIFT`；此处“报告、120-case 真实评测尚未完成”属于 2026-09-06 历史快照，当前五报告 gate、release 激活和 24 小时灰度/回滚确认均已通过。
