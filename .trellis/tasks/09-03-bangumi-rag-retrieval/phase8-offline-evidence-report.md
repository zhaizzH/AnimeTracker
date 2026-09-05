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
