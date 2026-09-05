# Phase 5 Shadow Index 与发布报告

日期：2026-09-05

## 已实现的本地契约

- `ShadowIndexManager` 通过 `idx:rag:subject:<version>` 建立/读取 shadow index，不删除旧 index。
- `prepare_switch` 只生成计划；`execute_switch` 只有在 gate 通过时才调用 `FT.ALIASUPDATE`。
- `rollback(previous_version)` 原子切回旧 alias，并保留旧索引作为回滚窗口。
- `build_capacity_report` 根据样本文档大小投影总容量，超过 60% 可用物理内存时拒绝发布；空样本 fail-closed。
- `jobs.indexer.gate` 要求 quality/capacity/eval/latency/human 五份同版本报告，缺失或版本不一致时拒绝 alias 激活。

## 验证

```text
cd backend/agent
\.venv\Scripts\python.exe -m pytest tests/jobs/indexer tests/rag -q -p no:cacheprovider -p no:tmpdir
120 passed
python -m compileall -q app jobs
git diff --check
```

新增容量报告 JSON 回归测试，覆盖容量投影、空样本拒绝和机器可读输出；既有 shadow 测试覆盖 gate 未通过拒绝切换及 rollback。

## 未通过的运行时门禁

当前 Redis 仅加载 `vectorset`，缺少 `FT.*`；因此本报告只证明代码契约，不代表真实 shadow index、BM25/KNN、alias 灰度或容量压测已执行。RAG 仍保持关闭。
