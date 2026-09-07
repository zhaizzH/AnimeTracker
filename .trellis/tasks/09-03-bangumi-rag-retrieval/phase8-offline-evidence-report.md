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

## 初始未满足项（2026-09-05 历史快照）

- golden cases 当前仍使用本地期望 ID，未绑定真实 MySQL/Redis 快照、`indexVersion` 或 `profileVersion`。
- 未产生真实 Recall@20、MRR@10、nDCG@10、过滤正确率、证据完整率、Redis/Business P95 或人工证据报告。
- 当时 MinIO、Embedding provider 和灰度尚未执行；Redis Stack/RediSearch 与 alias 后来被 MySQL FULLTEXT + Redis Vector Set + MySQL release store 路线取代，不再是当前前置条件。本离线报告仍不能用于激活 RAG。

历史结论（2026-09-05）：离线 fail-closed 行为通过，真实发布 gate 当时保持关闭；当前真实 gate 状态见下方 2026-09-07 回放记录。

## 2026-09-06 真实库追溯性复核

- recent 导入后人物/角色摘要和关系已具备；`golden_cases.json` 已从真实 MySQL 快照生成恰好 120 条，并绑定 snapshot/evidence/index/profile 追溯字段，但它仍是 `DEFINITION_ONLY`，不是通过型评测报告。
- `search_document` 与 Redis `rag:vectors:SUBJECT:v1` 均为 220；发布前已由 release-candidate 评测入口对未激活 v1 执行正式回放并输出 `status=RELEASE_CANDIDATE`，且五份 v1 报告（含 20 条 human 检查）已通过 gate；随后 v1 已激活，Business lexical API 实测返回 HTTP 200。
- DashScope 已在清空代理后返回 HTTP 200，search 队列已完成全量消费；v1 MySQL release 已激活。
- 详细字段、SQL 证据和 120 条配额见 [Phase 8 case 审查](./research/phase8-case-audit.md)。

## 2026-09-06 真实接口补充

- 18:28（UTC+8）实测 Business health/readiness、Agent health、Subject batch、Evidence batch 与 Evidence resolve 均为 HTTP 200。
- Subject 63 的 batch 与 Evidence 响应均明确 `active=true`；这证明实时 Evidence 链可用，但不能替代 120-case 正式 eval、P95 和人工检查报告。
- 完整命令见 [本机真实访问审计](./phase8-live-runtime-audit.md)。
