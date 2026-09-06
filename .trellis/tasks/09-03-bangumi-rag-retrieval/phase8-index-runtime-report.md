# Phase 8 真实索引运行报告

日期：2026-09-06

## 已完成

- 在清空 `HTTP_PROXY`、`HTTPS_PROXY`、`ALL_PROXY` 后，DashScope `text-embedding-v4` 探针返回 HTTP 200，返回向量输出。
- v1 indexer smoke：10 条任务完成，`failed=0`。
- v1 全量 search 队列最终状态：`search_index_job = COMPLETED 13,173`，无待处理和失败任务。此前 1,760 条 `CHARACTER` 任务因 MySQL 保留字 `character` 失败，修复为反引号引用后已重试完成。
- `search_document` 与 Redis Vector Set 数量一致：

| 实体 | MySQL | Redis |
|---|---:|---:|
| SUBJECT | 220 | 220 |
| EPISODE | 1,658 | 1,658 |
| PERSON | 9,275 | 9,275 |
| CHARACTER | 2,129 | 2,129 |

- 实时质量报告：`coverage=1.0`、`coverageCatalogCount=220`、`vectorCardinality=220`；content hash 抽样一致。原始 JSON 见 [research/quality-v1.json](./research/quality-v1.json)。
- Business health、Agent health 和 Evidence batch API 已返回 200。

## 当前代码门禁

- Agent 受影响测试：`159 passed`（`tests/jobs/indexer`、`tests/jobs/importer`、`tests/rag`）。
- Business：`mvn -B test`，共 `36` 个测试通过。
- Frontend：`npm run typecheck` 通过（shared/client/admin）。

## Gate 结果

运行 `python -m jobs.indexer.gate --index-version v1 --report-dir .../research` 返回 `gate=FAIL`：quality 已加载并通过覆盖率、NSFW、非 Anime 和 content hash 检查；capacity、eval、latency、human 四份报告缺失，因此保持 fail-closed。

## 仍未完成

- `search_index_release` 没有 `ACTIVE` 记录；词法 API 返回 HTTP 503“词法索引尚未发布”，符合 fail-closed 约束。
- 120 条真实回放尚未执行，因此不能填写 Recall@20、MRR@10、nDCG@10、过滤正确率、Evidence 完整率和真实 P95。
- 五份同版本 gate 报告（quality/capacity/eval/latency/human）尚未齐备，不能激活 release。
- 质量报告还有 1 条 `EPISODE_SHORTAGE` 和 38 条 `EPISODE_STATUS_DRIFT`，需在 gate 前修复或形成明确的人工豁免证据。

结论：实体索引构建和双投影一致性已通过；发布门禁和灰度阶段仍保持关闭，不能把当前状态标记为任务完成。
