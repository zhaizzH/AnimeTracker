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

- 尚未在真实存量库执行 `migration-003-search-projection.sql` 和全量投影回填。
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
