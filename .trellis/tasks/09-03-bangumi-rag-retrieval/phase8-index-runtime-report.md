# Phase 8 真实索引运行报告

日期：2026-09-06

最新真实访问：`2026-09-06T18:28:01+08:00` 至 `18:30:45+08:00`。完整命令与响应摘要见 [本机真实访问审计](./phase8-live-runtime-audit.md)。

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
- 最新实测确认：Business health/readiness 与 Agent health 均为 HTTP 200；Subject batch 63、Evidence batch 63 和 Evidence resolve Subject 63 均为 HTTP 200，且权威响应为 `active=true`。
- MySQL 8.4.9 当前为 23 张表；`search_index_release` 已有 `v1/subject-profile-v1/ACTIVE`。Redis 8.8.0 实际连接 DB 1，四个 Vector Set 的 VCARD 与上表 MySQL 计数一致。

## Shadow 评测（只读）

- 使用 `backend/agent/jobs/indexer/shadow_eval.py` 读取同一 `v1` 候选版本，未读取或写入 `search_index_release`，也未改变数据库、Redis 或 ACTIVE 状态。
- 报告：[research/eval-shadow-v1.json](./research/eval-shadow-v1.json) 保留 `SHADOW_ONLY` 诊断；正式报告：[research/eval-v1.json](./research/eval-v1.json) 状态为 `RELEASE_CANDIDATE`，`activeReleaseCount=0`、`datasetStatus=DEFINITION_ONLY`。
- 2026-09-07 真实回放结果：`120` 通过、`0` 失败；Recall@20=`1.0`、MRR@10=`0.9708`、nDCG@10=`0.9635`、hard-filter accuracy=`1.0`、Evidence completeness=`1.0`。
- 修复内容：FULLTEXT 改为 BOOLEAN MODE 以避免数字 token 误命中；Evidence 返回 `airStatus`；纯结构化过滤保持 SQL 确定性顺序；语义查询对 Evidence 元标签做精确加权。

## 当前代码门禁

- Agent 全量测试：`268 passed, 1 deselected`（排除需要自定义路径权限的环境测试）。
- Business：`mvn -B test`，共 `37` 个测试通过。
- Frontend：`npm run typecheck` 通过（shared/client/admin）。

## Gate 结果

运行 `python -m jobs.indexer.gate --index-version v1 --report-dir .../research` 已返回 `gate=PASS`：五份 v1 报告均加载成功，activation 仍显式跳过。

## 仍未完成

- v1 `search_index_release` 已激活；词法 API 实测返回 HTTP 200，并返回 `indexVersion=v1`、`profileVersion=subject-profile-v1`。
- 正式 eval、capacity、latency、human 已在激活前输出并绑定 v1；gate 已通过并完成 v1 激活。
- human 报告包含 20 条 candidate 结果检查，`severeErrors=0`；v1 激活事务已写入 `search_index_release`。
- 质量报告还有 1 条 `EPISODE_SHORTAGE` 和 38 条 `EPISODE_STATUS_DRIFT`；它们未触发当前 gate，但应作为 release 灰度期间的后续数据质量修复项。

结论：实体索引构建、双投影一致性、五报告发布门禁和 v1 激活已通过；灰度阶段未开始，任务仍不能标记为完成。
