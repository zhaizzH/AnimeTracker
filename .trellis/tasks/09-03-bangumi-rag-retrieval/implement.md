# 全量 Bangumi 数据与 RAG 检索闭环实施计划

## 执行原则

- 当前文件只定义实施顺序；用户批准最终规划后才能运行 `task.py start`。
- 每阶段先补失败测试，再实现，再运行受影响范围门禁。
- 产品开关默认关闭；每阶段可独立回滚，不能依赖一次性总切换。
- 非空数据库只使用经评审的前向 DDL，不执行 `docs/database/db-schema.sql`。

## Phase 1：建立评测基线与契约测试

- [ ] 建立至少 50 条检索 golden cases，覆盖标题/别名、过滤、主观语义、人物/角色/声优、系列关系、否定和降级。
- [ ] 实现确定性 eval schema/runner/metrics，先记录当前 Business fallback 与现有 RAG 基线。
- [ ] 为当前 schema↔normalize↔repository 漂移增加失败测试：`eps/volumes`、`credit_type`、AIRING、stale replace-set、profile hash。
- [ ] 固化 EvidenceCandidate 契约测试和“未经 Business 回查不得进入模型”的失败测试。

验证：

```powershell
cd backend/agent
uv run pytest tests/evals tests/jobs/importer tests/rag -v
```

回滚点：只新增测试与评测资产，不改变运行时行为。

## Phase 2：数据库与存量迁移

- [ ] 更新 `docs/database/db-schema.sql`，新增 person、character、alias、三类关系、detail job 和通用 search index job。
- [ ] 编写存量库前向迁移 SQL/运行手册：备份、只新增 DDL、兼容窗口、回填校验、停止/恢复步骤。
- [ ] 补齐 Java/Python 映射需要的实体、枚举、repository contract；保留旧 `subject_credit` 读取兼容。
- [ ] 在临时空库与带旧数据的临时库分别验证初始化与前向迁移；检查唯一约束、反向索引和外键。

验证：

```powershell
cd backend/business
mvn -B clean test
cd ..\agent
uv run pytest tests/jobs/importer -v
```

回滚点：应用仍读取旧表；新表不删除旧数据。若迁移校验失败，停止部署并从备份恢复测试库。

## Phase 3：导入修复与关系摘要

- [ ] 修复 subject `eps/volumes/platform/total_episodes`、credit type 与当前 normalize/repository 漂移。
- [ ] 扩展 Bangumi client：分页完整读取 characters，并统一 persons/characters/episodes/relations 的错误和限速策略。
- [ ] 保存 Subject 响应附带的 Person/Character 摘要、全部 credits、角色关系与 subject-scoped actors。
- [ ] 对 tags、meta tags、credits、characters、actors、episodes、relations 实现完整响应后的事务性 replace-set；不完整响应不得清空旧集合。
- [ ] 同事务写入索引 outbox；修复 content hash 与 profile 文本的一致性。

验证：

```powershell
cd backend/agent
uv run pytest tests/jobs/importer tests/rag/test_profile.py -v
```

回滚点：关闭新关系导入开关，继续旧 Subject 导入；新关系表保留但不被在线查询使用。

## Phase 4：人物/角色详情渐进回填

- [ ] 实现 `entity_detail_job` repository、claim/lease、重试、退避、checkpoint、暂停/恢复和失败报告。
- [ ] 实现 Person/Character 详情 normalize 与幂等写入；详情失败保留已有摘要和关系。
- [ ] 增加 CLI 与 scheduler 低速批次入口；避免与 Subject importer 争用同一锁或超过上游限速预算。
- [ ] 生成回填覆盖率、失败原因和 stale 数据报告。

验证：

```powershell
cd backend/agent
uv run pytest tests/jobs/backfill -v
```

回滚点：停止 backfill worker；已完成的详情是向前兼容增强，无需删除。

## Phase 5：多实体 profile 与索引自动化

- [ ] 为 SUBJECT/EPISODE/PERSON/CHARACTER 建立确定性 profile 与 profile_version；只向量化语义正文。
- [ ] 演进 indexer repository，安全消费通用任务、处理 tombstone、hash 漂移、失败重试和幂等完成。
- [ ] scheduler 增加受控 indexer/backfill 调度，提供重叠任务和进程重启测试；是否常驻部署仍由运行手册明确。
- [ ] 建 shadow index、容量/数据质量报告与 alias 回滚流程；旧 index 不提前删除。

验证：

```powershell
cd backend/agent
uv run pytest tests/jobs/indexer tests/jobs/scheduler tests/rag -v
```

回滚点：停止消费者并保持 alias 指向旧 index。

## Phase 6：Business 精确查询与证据接口

- [ ] 增加标题/别名/人物/角色解析与关系过滤 Mapper/Service；复杂联表使用参数绑定的 XML。
- [ ] 增加面向 Agent 的批量 EvidenceCandidate 回查接口，验证 type、NSFW、active 状态并返回来源时间。
- [ ] 同步 Java DTO/VO、OpenAPI；若前端直接消费新字段，再同步 shared types。
- [ ] 添加成功、空结果、无效 ID、越权/错误和批量上限测试。

验证：

```powershell
cd backend/business
mvn -B clean test
cd ..\..\frontend
npm run typecheck
```

回滚点：Agent 保持调用旧 batch/detail API，新接口可不暴露给现有前端。

## Phase 7：混合检索与 Agent 证据回答

- [ ] 将自然语言解析成受限 RetrievalQuery；结构化过滤、原 query 与可选 rewrite 分离，rewrite 失败回退原 query。
- [ ] 完成精确实体解析 → 关系扩展 → Subject BM25/KNN → RRF → Business 回查 → 可选 rerank → evidence format 链。
- [ ] Reranker 失败回退确定性融合；Redis/Embedding 故障回退 Business 搜索，并发出结构化 fallback 事件。
- [ ] search/discover/recommend 共用 retrieval use case，更新提示词以禁止无证据事实；保持当前 SSE wire 类型兼容。
- [ ] 返回简介摘录、匹配标签/主创/角色/关系、评分热度、状态、来源时间和 retrieval reason。

验证：

```powershell
cd backend/agent
uv run pytest tests/rag tests/agent tests/api -v
```

回滚点：关闭 evidence retrieval/RAG 开关，回退现有 Business 工具；旧 Redis alias 不变。

## Phase 8：端到端门禁与灰度启用

- [ ] 运行数据质量、容量、50-case eval、延迟与人工证据检查，所有报告绑定同一 index/profile version。
- [ ] 覆盖 MySQL、Redis、Embedding、Business、MinIO 故障矩阵，证明 fail-closed 或既定降级行为。
- [ ] 小流量启用新 alias 与 RAG，观测 24 小时；异常时回切 alias 和功能开关。
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
- [ ] 所有真实数据库迁移、alias 激活和旧数据删除均需要独立人工确认。
