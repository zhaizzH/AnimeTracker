# Phase 8 本机真实访问审计

日期：2026-09-06

## 访问边界

- 观察时间：`2026-09-06T18:28:01+08:00` 至 `2026-09-06T18:30:45+08:00`。
- 目标：本机 Business `127.0.0.1:8080`、Agent `127.0.0.1:8090`、MySQL `localhost:3306/anime_tracker`、Redis `localhost:6379/1`。
- HTTP、MySQL 和 Redis 操作均为只读；没有写数据库、激活 release、删除索引或调用外部 Embedding。
- `quality-v1.json` 由只读质量任务重新生成；它是质量证据文件写入，不是运行库写入。

## HTTP 实测

执行命令：

```powershell
curl.exe --noproxy "*" -i http://127.0.0.1:8080/actuator/health
curl.exe --noproxy "*" -i http://127.0.0.1:8080/actuator/health/liveness
curl.exe --noproxy "*" -i http://127.0.0.1:8080/actuator/health/readiness
curl.exe --noproxy "*" -i http://127.0.0.1:8090/api/client/agent/health
curl.exe --noproxy "*" -i -X POST http://127.0.0.1:8080/api/client/subjects/lexical-search -H "Content-Type: application/json" --data-raw '{"q":"动画","limit":5}'
curl.exe --noproxy "*" -i -X POST http://127.0.0.1:8080/api/client/subjects/batch -H "Content-Type: application/json" --data-raw '{"subjectIds":[63],"excludeCollected":false}'
curl.exe --noproxy "*" -i -X POST http://127.0.0.1:8080/api/client/evidence/batch -H "Content-Type: application/json" --data-raw '{"subjectIds":[63]}'
curl.exe --noproxy "*" -i -X POST http://127.0.0.1:8080/api/client/evidence/resolve -H "Content-Type: application/json" --data-raw '{"entityType":"SUBJECT","ids":[63]}'
```

结果：

| 请求 | HTTP | 关键结果 |
|---|---:|---|
| Business health | 200 | `status=UP` |
| Business liveness | 200 | `status=UP`；复核时间 `2026-09-06T18:35:35+08:00` |
| Business readiness | 200 | `status=UP` |
| Agent health | 200 | `status=ok`, `llm_configured=true` |
| lexical search | 503 | `词法索引尚未发布`；符合无 ACTIVE release 时的 fail-closed 契约 |
| subjects batch `[63]` | 200 | 返回 Subject 63，`type=2`, `nsfw=false`, `active=true` |
| Evidence batch `[63]` | 200 | 返回完整 EvidenceCandidate，`active=true`，含标签、主创和角色证据 |
| Evidence resolve Subject `[63]` | 200 | 返回 Subject 63 的权威证据 |

## MySQL 实测

通过 `backend/agent/.env` 建立 SQLAlchemy 只读连接，执行：

```sql
SELECT VERSION(), DATABASE();
SELECT COUNT(*) FROM INFORMATION_SCHEMA.TABLES WHERE TABLE_SCHEMA=DATABASE();
SELECT index_version, profile_version, status FROM search_index_release ORDER BY id;
SELECT index_version, status, COUNT(*) FROM search_index_job GROUP BY index_version, status;
SELECT index_version, status, COUNT(*) FROM rag_index_job GROUP BY index_version, status;
SELECT index_version, profile_version, entity_kind, source_active, COUNT(*)
FROM search_document
GROUP BY index_version, profile_version, entity_kind, source_active;
```

`2026-09-06T18:28:59+08:00` 的结果：

- MySQL `8.4.9`，数据库 `anime_tracker`，当前共 `23` 张表。
- `search_index_release` 为 `[]`，ACTIVE 数为 `0`。
- `search_index_job`: `v1/COMPLETED=13,173`，无其他状态。
- `rag_index_job`: `v1/INDEXED=220`。
- `search_document` 的活跃 v1 数量：SUBJECT=`220`、EPISODE=`1,658`、PERSON=`9,275`、CHARACTER=`2,129`。
- 事实表精确计数：Subject=`220`、Episode=`4,728`、Person=`9,275`、Character=`2,129`；人物 credit=`14,434`、Subject-Character=`2,160`、Character-Actor=`2,293`、Subject relation=`6`。

迁移报告中的“21 张表”只对应 migration-002 完成时的历史快照；后来 migration-003 增加 `search_document` 与 `search_index_release`，所以当前真实库为 23 张表。

## Redis 实测

通过 `backend/agent/.env` 的 `RAG_REDIS_URL/REDIS_URL` 连接，并执行 `PING`、`INFO`、`COMMAND INFO`、`SCAN rag:vectors:*:v1` 和逐 key `VCARD`。未读取或记录密码。

`2026-09-06T18:29:32+08:00` 的结果：

- 实际连接目标为 `localhost:6379/1`；`PING=true`，Redis `8.8.0`。
- `VADD`、`VSIM`、`VREM`、`VSETATTR`、`VGETATTR` 均存在。
- Vector Set 数量：SUBJECT=`220`、EPISODE=`1,658`、PERSON=`9,275`、CHARACTER=`2,129`，与 MySQL `search_document` 完全一致。
- 观察时 `used_memory=29,321,352` bytes；这是瞬时运行值，不替代正式容量/P95 报告。

## 质量与发布结论

执行命令：

```powershell
cd backend/agent
& '.venv\Scripts\python.exe' -m jobs.importer.quality `
  --output '../../.trellis/tasks/09-03-bangumi-rag-retrieval/research/quality-v1.json' `
  --index-version v1
```

结果：`coverage=1.0`、`vectorCardinality=220`、content-hash 抽样一致；仍有 `EPISODE_SHORTAGE=1` 和 `EPISODE_STATUS_DRIFT=38`。

（历史快照）当时任务仍不能完成：`gate.py` 要求五份同版本报告，且 eval 报告必须先为 `status=RELEASE_CANDIDATE`、120/120 通过；随后才可执行 `--activate`。当时 shadow 仅 115/120，模型校验会拒绝 candidate 状态；其余报告也未齐备。2026-09-07 的修复与回放结果见下方“回放复核”。

candidate 入口验证命令：

```powershell
cd backend/agent
& '.venv\Scripts\python.exe' -m jobs.indexer.shadow_eval `
  --index-version v1 `
  --release-profile-version subject-profile-v1 `
  --dataset tests/evals/golden_cases.json `
  --output '../../.trellis/tasks/09-03-bangumi-rag-retrieval/research/eval-v1.json' `
  --status RELEASE_CANDIDATE
```

（历史快照）当时 5 个失败 case 会使该命令 fail closed，不会写入 `search_index_release`。

## 文档一致性复核（2026-09-06 18:41–19:34，UTC+8）

- 再次真实访问确认 Business health/liveness/readiness 均为 HTTP 200；Agent 有效健康路径 `/api/client/agent/health` 为 HTTP 200，根路径 `/health` 为 HTTP 404（预期，不是健康路径）。
- Subject batch、Evidence batch 和 Evidence resolve 对 Subject 63 均为 HTTP 200、`active=true`；lexical search 仍为 HTTP 503“词法索引尚未发布”。
- 再次只读查询确认 MySQL `8.4.9`、`anime_tracker` 共 23 张表、`search_index_release=[]`、`search_index_job v1/COMPLETED=13,173`；四类 `search_document` 数量未变化。
- 再次只读确认 Redis 目标 `localhost:6379/1`、版本 `8.8.0`，四类 VCARD 仍为 SUBJECT=220、EPISODE=1,658、PERSON=9,275、CHARACTER=2,129。

## 2026-09-07 回放复核

- 清理旧 Maven target 后以 `backend/business/app/target/app.jar` 启动 Business 8080，并启动 Agent 8090；health/readiness 均返回 200。
- Evidence batch Subject 63 真实返回 `airStatus=AIRING`；该字段由 `subject.air_date` 与 `episode.status/airdate` 推导。
- v1 shadow 回放重新执行后为 `120/120`，指标为 Recall@20=`1.0`、MRR@10=`0.9708`、nDCG@10=`0.9635`、hard-filter=`1.0`、Evidence completeness=`1.0`。
- 通过受保护入口生成 `research/eval-v1.json`，报告状态为 `RELEASE_CANDIDATE`，未激活 `search_index_release`。
- 额外修复 FULLTEXT 误命中：Business 与 shadow SQL 均改用 `BOOLEAN MODE`，不存在标题的 `__no_such_anime_2026__` 现在返回空结果。
- 同一 v1 还生成了 `research/capacity-v1.json`（预计占用 41,480,000 bytes、利用率 1.72%）和 `research/latency-v1.json`（Redis P95 15.363 ms、Evidence hydrated P95 18.679 ms）。
- `research/human-v1.json` 已记录 20 条 candidate 结果与 Evidence 来源复核，`severeErrors=0`；随后运行 gate 得到 `gate=PASS`。
- 2026-09-07 21:16（UTC+8）创建 `v1/subject-profile-v1/BUILDING` 发布记录后，通过 gate 激活事务切换为 `ACTIVE`；查询确认 `active_slot=1`、SUBJECT 投影 220 条匹配。
- 激活后重新访问 `POST /api/client/subjects/lexical-search`，HTTP `200` 返回 `indexVersion=v1`、`profileVersion=subject-profile-v1` 和候选列表；8080 health、8090 Agent health 均为 `200`。

## 2026-09-09 灰度与回滚确认

- 用户确认 v1 小流量灰度已完成 24 小时观察，结果通过。
- 用户确认 release 与功能开关回滚路径验证通过；当前 ACTIVE release 保持 v1。
- 未执行旧索引、旧 Vector Set 或旧表清理；清理仍需独立确认。
