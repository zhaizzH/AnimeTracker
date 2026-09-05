# MySQL FULLTEXT + Redis Vector Set 技术路线决策

日期：2026-09-05
状态：用户已同意技术方向；最终规划待复核，未授权实现代码

## 已确认事实

- MySQL 8.4.9 是结构化事实源，实际 `anime_tracker` 已完成前向迁移。
- Redis 8.8.0 可连接，`VADD`、`VSIM`、`VREM`、`VSETATTR`、`VGETATTR` 均可用；`FT.CREATE`、`FT.SEARCH`、`FT.ALIASUPDATE` 不可用。
- Business `8080`、Agent `8090`、MinIO `9000` 健康检查均返回 HTTP 200。
- 当前代码中的 profile、outbox、RRF、Evidence 回查和 fail-closed 逻辑可以复用，RediSearch 适配器与 alias 发布机制需要替换。

## 最终选择

1. MySQL 新增可重建的 `search_document` 版本投影，使用 InnoDB FULLTEXT `ngram` 完成标题、别名和简介的中文/日文词法召回。
2. Redis 使用版本化 Vector Set key，通过 `VADD/VSIM/VREM` 完成语义向量写入、查询和删除。
3. Python 保留现有 RRF，融合精确关系候选、MySQL lexical 候选和 Redis vector 候选。
4. MySQL `search_index_release` 是唯一发布指针；Business lexical 响应携带 `indexVersion`，Agent 只查询同版本 Vector Set。
5. 五份 gate 报告通过前不激活 release；异常时只切回上一条已验证 release，不提前删除旧投影。

## 未选择方案

- Redis Stack/RediSearch：当前 Vector Set 已覆盖向量能力，MySQL 可承担词法与结构化过滤，不为尚未发生的指标失败新增运行时。
- OpenSearch/Elasticsearch：只有 MySQL `ngram` 的中文/拼音召回或词法 P95 未达标时再评估。
- Qdrant：只有 Redis Vector Set 的容量、召回或 P95 未达标时再评估。
- Neo4j：仅解决稳定多跳关系/图算法需求，不能替代当前词法和向量召回。

## 实施顺序

1. 先补 schema、迁移和跨层契约测试，不启用 RAG。
2. 实现 MySQL lexical shadow 写入与 Business 查询，再实现 Redis Vector Set shadow 写入与查询。
3. 接入同版本 RRF 与 Evidence 回查，补齐版本错配和依赖故障矩阵。
4. 构建固定真实快照，生成同版本 quality/capacity/eval/latency/human 报告。
5. 人工确认后激活 release，灰度观察 24 小时；稳定后才更新默认开关和清理计划。

## 发布门槛

- 索引覆盖率 ≥99.5%，NSFW/非动画误入均为 0。
- 120/120 必选评测通过；Recall@20 ≥0.85、MRR@10 ≥0.90、nDCG@10 ≥0.75。
- Redis VSIM P95 <250ms，Business 权威回查后 P95 <500ms，预计 Redis 内存占用 ≤60%。
- 至少 20 条人工证据检查且严重错误为 0。
- MySQL lexical、Redis vector、content hash、embedding contract 和五份报告版本完全一致。

## 回滚边界

- 关闭 `RAG_ENABLED` 后继续使用现有 Business 精确搜索。
- active release 只允许切回已通过 gate 的旧版本。
- 旧 `search_document` 版本和 Vector Set key 在回滚窗口结束前保留；删除另行确认。
