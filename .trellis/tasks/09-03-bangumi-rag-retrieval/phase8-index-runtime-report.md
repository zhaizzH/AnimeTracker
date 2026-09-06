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
- 发现并修复批量权威回查契约缺口：`POST /api/client/subjects/batch` 的 item 现在返回由 `subject.import_status=1` 派生的 `active=true`，并已同步 Java VO、OpenAPI 与回归测试；8080 服务已重启以加载该字段。

## Shadow 评测（只读）

- 使用 `backend/agent/jobs/indexer/shadow_eval.py` 读取同一 `v1` 候选版本，未读取或写入 `search_index_release`，也未改变数据库、Redis 或 ACTIVE 状态。
- 报告：[research/eval-shadow-v1.json](./research/eval-shadow-v1.json)。报告状态为 `SHADOW_ONLY`，`activeReleaseCount=0`、`datasetStatus=DEFINITION_ONLY`。
- 120 条真实定义集回放结果：`115` 通过、`5` 失败；Recall@20=`0.9847`、MRR@10=`0.8803`、nDCG@10=`0.8716`、hard-filter accuracy=`0.9667`、Evidence completeness=`1.0`。
- 失败主要集中在标签/年份/季度/air 状态过滤、语义标签、关系与否定 case；当前结果低于发布门槛，不能转换成 `RELEASE_CANDIDATE`。
- 上述 shadow JSON 已在 Business 服务重启、批量响应包含 `active` 后重新生成；它仍是 `SHADOW_ONLY` 诊断结果，不能替代 ACTIVE release gate，5 个失败 case 仍需处理。

## 当前代码门禁

- Agent 全量测试：`266 passed, 1 deselected`（排除需要自定义路径权限的环境测试）。
- Business：`mvn -B test`，共 `37` 个测试通过。
- Frontend：`npm run typecheck` 通过（shared/client/admin）。

## Gate 结果

运行 `python -m jobs.indexer.gate --index-version v1 --report-dir .../research` 返回 `gate=FAIL`：quality 已加载并通过覆盖率、NSFW、非 Anime 和 content hash 检查；capacity、eval、latency、human 四份报告缺失，因此保持 fail-closed。

## 仍未完成

- `search_index_release` 没有 `ACTIVE` 记录；词法 API 返回 HTTP 503“词法索引尚未发布”，符合 fail-closed 约束。
- shadow 回放已执行并产生诊断指标，但尚未在 ACTIVE release 上完成正式 120-case eval；因此不能把上述 shadow 指标当作发布 gate，也不能填写真实 hydrated P95。
- 五份同版本 gate 报告（quality/capacity/eval/latency/human）尚未齐备，不能激活 release。
- 质量报告还有 1 条 `EPISODE_SHORTAGE` 和 38 条 `EPISODE_STATUS_DRIFT`，需在 gate 前修复或形成明确的人工豁免证据。

结论：实体索引构建和双投影一致性已通过；发布门禁和灰度阶段仍保持关闭，不能把当前状态标记为任务完成。
