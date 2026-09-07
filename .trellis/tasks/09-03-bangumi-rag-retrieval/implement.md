# 全量 Bangumi 数据与 RAG 检索闭环实施计划

## 执行原则

- 当前文件只定义实施顺序；用户批准最终规划后才能运行 `task.py start`。
- 每阶段先补失败测试，再实现，再运行受影响范围门禁。
- 产品开关默认关闭；每阶段可独立回滚，不能依赖一次性总切换。
- 非空数据库只使用经评审的前向 DDL，不执行 `docs/database/db-schema.sql`。

## 执行状态快照（2026-09-06，技术路线调整）

- Phase 1：golden/eval/契约测试已建立；真实 MySQL 快照定义集、只读质量报告、shadow 指标和正式 release-candidate 指标报告均已生成。
- Phase 2：schema、Java/Python 映射、前向迁移和 MySQL 8.4.9 临时库验证已完成；真实 `anime_tracker` 已按用户授权完成前向迁移并通过二次幂等验证；存量备份恢复演练仍未完成。
- Phase 3–4：导入关系、详情任务和多实体 outbox 已接通，可直接复用。
- Phase 5–7：MySQL FULLTEXT + Redis Vector Set 双投影、Business lexical API、同版本 RRF、Evidence 与 MySQL release store 已完成接线并通过代码门禁；旧 RediSearch `FT.*` 路线只保留历史报告。
- Phase 8：2026-09-07 真实回放确认 v1 120/120 通过；五份 v1 gate 报告（含 20 条人工证据检查）均已通过，v1 ACTIVE release 已激活。真实库在 migration-003 后为 23 张表，Redis 8.8.0 实际使用 DB 1；当前仅未开始 24 小时灰度。
- 当前文档入口：`README.md`。有效运行证据包括 `phase2-mapping-report.md`、`phase4-backfill-report.md`、`phase6-business-report.md`、`phase8-mysql-migration-report.md`、`phase8-springboot-startup-report.md` 和 `phase8-offline-evidence-report.md`；被替代的 RediSearch/阶段审查报告保存在 `history/`。

## Phase 1：建立评测基线与契约测试

- [x] 建立至少 50 条检索 golden cases，覆盖标题/别名、过滤、主观语义、人物/角色/声优、系列关系、否定和降级。
- [x] 实现确定性 eval schema/runner/metrics，先记录当前 Business fallback 与现有 RAG 基线。
- [x] 为当前 schema↔normalize↔repository 漂移增加失败测试：`eps/volumes`、`credit_type`、AIRING、stale replace-set、profile hash。
- [x] 固化 EvidenceCandidate 契约测试和”未经 Business 回查不得进入模型”的失败测试。

验证：

```powershell
cd backend/agent
uv run pytest tests/evals tests/jobs/importer tests/rag -v
```

回滚点：只新增测试与评测资产，不改变运行时行为。

## Phase 2：数据库与存量迁移

- [x] 更新 `docs/database/db-schema.sql`，新增 person、character、alias、三类关系、detail job 和通用 search index job。
- [x] 编写存量库前向迁移 SQL/运行手册：备份、只新增 DDL、兼容窗口、回填校验、停止/恢复步骤。
- [x] 补齐 Java/Python 映射需要的实体、枚举、repository contract；保留旧 `subject_credit` 读取兼容。
- [x] 在临时空库与旧 schema 模拟库分别验证初始化与前向迁移；检查唯一约束、反向索引和外键。

验证：

```powershell
cd backend/business
mvn -B clean test
cd ..\agent
uv run pytest tests/jobs/importer -v
```

回滚点：应用仍读取旧表；新表不删除旧数据。若迁移校验失败，停止部署并从备份恢复测试库。

## Phase 3：导入修复与关系摘要

- [x] 修复 subject `eps/volumes/platform/total_episodes`、credit type 与当前 normalize/repository 漂移。
- [x] 扩展 Bangumi client：分页完整读取 characters，并统一 persons/characters/episodes/relations 的错误和限速策略。
- [x] 保存 Subject 响应附带的 Person/Character 摘要、全部 credits、角色关系与 subject-scoped actors。
- [x] 对 tags、meta tags、credits、characters、actors、episodes、relations 实现完整响应后的事务性 replace-set；不完整响应不得清空旧集合。
- [x] 同事务写入索引 outbox；修复 content hash 与 profile 文本的一致性。

验证：

```powershell
cd backend/agent
uv run pytest tests/jobs/importer tests/rag/test_profile.py -v
```

回滚点：关闭新关系导入开关，继续旧 Subject 导入；新关系表保留但不被在线查询使用。

## Phase 4：人物/角色详情渐进回填

- [x] 实现 `entity_detail_job` repository、claim/lease、重试、退避、checkpoint、暂停/恢复和失败报告。
- [x] 实现 Person/Character 详情 normalize 与幂等写入；详情失败保留已有摘要和关系。
- [x] 增加 CLI 与 scheduler 低速批次入口；避免与 Subject importer 争用同一锁或超过上游限速预算。
- [x] 生成回填覆盖率、失败原因和 stale 数据报告。

验证：

```powershell
cd backend/agent
uv run pytest tests/jobs/backfill -v
```

回滚点：停止 backfill worker；已完成的详情是向前兼容增强，无需删除。

## Phase 5：多实体 profile 与索引自动化

- [x] 为 SUBJECT/EPISODE/PERSON/CHARACTER 建立确定性 profile 与 profile_version；只向量化语义正文。
- [x] 演进 indexer repository，安全消费通用任务、处理 tombstone、hash 漂移、失败重试和幂等完成。
- [x] scheduler 增加受控 indexer/backfill 调度，提供重叠任务和进程重启测试；是否常驻部署仍由运行手册明确。
- [x] 新增版本化 MySQL `search_document` FULLTEXT（`ngram`）投影与 `search_index_release`，同步空库 schema 和只新增前向迁移。
- [x] 将 indexer 改为同一 job 同时写 MySQL lexical shadow 与 Redis `rag:vectors:{entity_kind}:{indexVersion}`；任一侧失败不得确认 job 完成。
- [x] 使用 `VADD/VSIM/VREM` 实现四类实体的向量写入、查询和 tombstone；属性只包含允许过滤的非私有元数据。
- [x] 将 gate/容量/质量报告和 rollback 接入真实 MySQL release store；真实 gate 报告和灰度仍需运行环境证据。

验证：

```powershell
cd backend/agent
uv run pytest tests/jobs/indexer tests/jobs/scheduler tests/rag -v
python -m jobs.indexer.vector_probe
```

回滚点：停止消费者并保持 MySQL active release 指向旧版本；新 `search_document` 行和 Vector Set key 保留排查。

## Phase 6：Business 精确查询与证据接口

- [x] 增加标题/别名/人物/角色解析与关系过滤 Mapper/Service；复杂联表使用参数绑定的 XML。
- [x] 增加受控 lexical search API：在 active release 上执行 `MATCH(title, aliases, lexical_text) AGAINST (?)` 与结构化过滤，返回候选、词法排名和 `indexVersion`。
- [x] 增加面向 Agent 的批量 EvidenceCandidate 回查接口，验证 type、NSFW、active 状态并返回来源时间。
- [x] 同步 Java DTO/VO、OpenAPI；若前端直接消费新字段，再同步 shared types。
- [x] 添加成功、空结果、无效 ID、越权/错误和批量上限测试。

验证：

```powershell
cd backend/business
mvn -B clean test
cd ..\..\frontend
npm run typecheck
```

回滚点：Agent 保持调用旧 batch/detail API，新接口可不暴露给现有前端。

## Phase 7：混合检索与 Agent 证据回答

- [x] 将自然语言解析成受限 RetrievalQuery；结构化过滤、原 query 与可选 rewrite 分离，rewrite 失败回退原 query。
- [x] 将召回链改为精确实体解析 → 关系扩展 → Business MySQL FULLTEXT → 同版本 Redis `VSIM` → RRF → Business 回查 → 可选 rerank → evidence format。
- [x] 版本不一致、Vector Set/Embedding 故障时 fail-closed 到 Business 精确/词法搜索，并发出不含查询原文的结构化 fallback 事件。
- [x] search/discover/recommend 共用 retrieval use case，更新提示词以禁止无证据事实；保持当前 SSE wire 类型兼容。
- [x] 返回简介摘录、匹配标签/主创/角色/关系、评分热度、状态、来源时间和 retrieval reason。

验证：

```powershell
cd backend/agent
uv run pytest tests/rag tests/agent tests/api -v
```

回滚点：关闭 evidence retrieval/RAG 开关，回退现有 Business 工具；MySQL active release 不变。

## Phase 8：端到端门禁与灰度启用

- [x] 从真实 MySQL 快照生成恰好 120 条带 snapshot/evidence/index/profile 追溯字段的 golden case 定义集；定义集状态为 `DEFINITION_ONLY`。
- [x] 在未发布的 v1 候选上完成只读 120-case shadow 回放并记录失败项；报告明确为 `SHADOW_ONLY`，不能替代 active release gate。
- [x] 在同一 release candidate 上运行数据质量、双投影容量、120-case 正式 eval、延迟与至少 20 条人工证据检查，所有报告绑定同一 index/profile version；eval 明确为 `RELEASE_CANDIDATE`，五份报告已通过 gate，等待激活确认。
- [ ] 覆盖 MySQL FULLTEXT、Redis Vector Set、版本错配、Embedding、Business、MinIO 故障矩阵，证明 fail-closed 或既定降级行为。
- [ ] 小流量激活新 MySQL release 与 RAG，观测 24 小时；异常时回切 release 和功能开关。
- [ ] 指标稳定后更新 README、运行手册与 `.trellis/spec/`；旧索引/旧表删除另行确认和规划。

全量验证：

```powershell
cd backend/business
mvn -B clean test
cd ..\agent
uv run pytest
cd ..\..\frontend
npm run typecheck
npm run build
```

## 启动实施前检查

- [ ] PRD、design、implement 已由用户批准。
- [ ] `implement.jsonl` 与 `check.jsonl` 含真实 spec/research 条目。
- [ ] 先实现 Phase 1，不直接修改生产数据库或启用 RAG。
- [ ] 所有真实数据库迁移、release 激活和旧数据删除均需要独立人工确认。

## 最新运行态（2026-09-06）

- recent 导入已完成当前日历 113 条扫描，实体摘要/关系已写入真实库；人物、角色和声优关系数据不再是 0，但系列关系仍只有 6 条边。
- `search_index_job` 的 13,173 条任务均为 `COMPLETED`；`search_document` v1 与 Redis Vector Set 的实体数量分别为 SUBJECT=220、EPISODE=1,658、PERSON=9,275、CHARACTER=2,129，数量一致。此前由 MySQL `character` 保留字导致的失败已通过引用修复并重试完成。
- DashScope `text-embedding-v4` 在清空代理环境后返回 HTTP 200；索引报告为 `failed=0`。v1 `search_index_release` 已为 ACTIVE，词法 API 实测返回 HTTP 200。
- 质量报告覆盖率为 1.0（catalog=220、vectorCardinality=220），content hash 抽样一致；报告发现 1 条 `EPISODE_SHORTAGE`、38 条 `EPISODE_STATUS_DRIFT`，需要在真实 gate 前处理或明确豁免。
- 120-case 端到端评测、五份 gate 报告和 24 小时灰度仍未勾选完成。`phase8-index-runtime-report.md` 与 `research/phase8-case-audit.md` 记录了当前证据和阻断条件。
- 已完成同版本 v1 shadow 回放：`requiredPassed=120`、`requiredFailed=0`、`recall20=1.0`、`mrr10=0.9708`、`ndcg10=0.9635`、`hardFilterAccuracy=1.0`、`evidenceCompleteness=1.0`；另已生成 `research/eval-v1.json`，其 `status=RELEASE_CANDIDATE`。
- 已从真实 MySQL 快照生成恰好 120 条带 snapshot/evidence/index 追溯信息的定义集；数据集状态明确为 `DEFINITION_ONLY`，不能替代 ACTIVE release 后的真实回放门禁。详见 `phase8-golden-case-definition-report.md`。
- 已修复 Business 批量权威回查缺少 `active` 字段的问题；8080 服务已重启并重新生成 `eval-shadow-v1.json`，当前指标以修复后的运行态为准。
- 18:28（UTC+8）重新实测：8080 health/readiness=200，8090 Agent health=200，Subject batch 63 与 Evidence batch/resolve=200；lexical-search=503“词法索引尚未发布”。MySQL 为 23 张表、release 0 行；Redis 为 `localhost:6379/1`，四类 VCARD 与 MySQL 投影一致。完整命令见 `phase8-live-runtime-audit.md`。
- 正式发布链当前状态为：五份报告已 gate PASS → v1 已人工确认并激活 → 等待 24 小时灰度。不能在缺少独立确认时自动切换后续版本 ACTIVE。
