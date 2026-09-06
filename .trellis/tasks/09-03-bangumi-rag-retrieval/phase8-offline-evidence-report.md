# Phase 8 离线评测与故障矩阵报告

日期：2026-09-05

## 已验证

- `tests/evals` 验证 golden case schema、Recall/MRR/nDCG/硬过滤指标计算与 runner 聚合。
- `tests/rag/test_fault_matrix.py` 覆盖 Redis、Embedding、Business、Evidence 故障及组合降级；Redis/Embedding 可降级时继续走既定路径，权威回查或 Evidence 失败时 fail-closed。
- 本轮命令：

```text
cd backend/agent
\.venv\Scripts\python.exe -m pytest tests/evals tests/rag/test_fault_matrix.py -q --basetemp pytest-tmp-phase8-final
52 passed
```

## 未满足的真实门禁

- golden cases 当前仍使用本地期望 ID，未绑定真实 MySQL/Redis 快照、`indexVersion` 或 `profileVersion`。
- 未产生真实 Recall@20、MRR@10、nDCG@10、过滤正确率、证据完整率、Redis/Business P95 或人工证据报告。
- MinIO、Embedding provider、Redis Stack/RediSearch 和 alias 灰度未执行；因此不允许用本报告激活 RAG。

结论：离线 fail-closed 行为通过，真实发布 gate 继续保持关闭。

## 2026-09-06 真实库追溯性复核

- recent 导入后人物/角色摘要和关系已具备；`golden_cases.json` 已从真实 MySQL 快照生成恰好 120 条，并绑定 snapshot/evidence/index/profile 追溯字段，但它仍是 `DEFINITION_ONLY`，不是通过型评测报告。
- `search_document` 与 Redis `rag:vectors:SUBJECT:v1` 均为 220，但 `search_index_release` 没有 ACTIVE 行；Business lexical API 仍按设计返回 503，不能生成可信的端到端 Recall/MRR/nDCG 或 Evidence P95 通过报告。
- DashScope 已在清空代理后返回 HTTP 200，search 队列已完成全量消费；本轮没有激活 MySQL release。
- 详细字段、SQL 证据和 120 条配额见 [Phase 8 case 审查](./research/phase8-case-audit.md)。
