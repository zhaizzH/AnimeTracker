# Phase 5–7 MySQL + Vector Set 实现报告

日期：2026-09-05

## 已实现

- `search_document` 与 `search_index_release` 已加入初始化 Schema 和 `migration-003-search-projection.sql`。
- Business 新增 `POST /api/client/subjects/lexical-search`，返回 `indexVersion`、`profileVersion`、候选和词法分数；无 active release 时返回 503。
- Agent indexer 在同一任务中写 MySQL lexical shadow 与 Redis Vector Set；任一侧失败不会确认任务完成。
- Vector Set 使用 `rag:vectors:{entity_kind}:{indexVersion}`，通过 `VADD/VSIM/VREM` 写入、查询和 tombstone；发布/回滚只通过 MySQL release store。
- Agent RRF 使用 Business 返回的 `indexVersion` 查询同版本 Vector Set，并将 `candidates` 归一化为检索候选。
- Shadow/gate 已改为只接受 MySQL release store；生产 CLI 会在 gate 通过后通过事务切换 release，当前不会误切 Redis alias。

## 本地验证

```text
backend/agent: .venv\Scripts\python.exe -m pytest -q
233 passed

backend/business: mvn -B clean test
BUILD SUCCESS
36 tests in client/app modules passed
```

## 尚未完成

- 已在本地运行库 `localhost:3306/anime_tracker` 执行 `migration-003-search-projection.sql`；`search_document` 与 `search_index_release` 已创建，但尚未进行全量投影回填。
- 尚未生成 120 条真实 golden case、完成 Recall/MRR/nDCG/延迟门禁和 20 条人工证据检查。
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
- 当前 `search_index_release` 的 `ACTIVE` 行数为 0；词法 API 返回 HTTP 503 `词法索引尚未发布`，符合发布指针 fail-closed 约束。

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
