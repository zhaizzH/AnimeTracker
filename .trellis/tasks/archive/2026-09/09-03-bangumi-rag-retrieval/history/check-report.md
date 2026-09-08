# bangumi-rag-retrieval 最终审查报告

> 历史报告：这是 2026-09-04 的初始审查快照，后续多个 findings 已修复。当前状态以 [任务文档索引](../README.md) 为准。

审查日期：2026-09-04  
审查范围：`c6045be` 之后的全部已提交与未提交改动（当前 `HEAD` 与 `c6045be` 相同，任务实现均为未提交改动）  
结论：**不通过，任务尚不能标记完成或进入灰度发布。** 编译和现有单元测试通过，但 AC2–AC7 的关键运行链路未实现或未验证。

## Findings (fixed)

1. File: `docs/database/db-schema.sql:126,143,163`
   - Issue: importer 和 Evidence Mapper 已读写 `subject_alias`、`subject_meta_tag`、`subject_credit` 的 `source_active`，但空库初始化 schema 没有这些列；新环境会在首次导入/回查时失败。
   - Fix: 在三张初始化表中补齐 `source_active`，与前向迁移和 Java Entity 对齐。

2. File: `backend/agent/jobs/backfill/main.py:35-52`, `backend/agent/jobs/backfill/repository.py:138-166`, `backend/agent/jobs/backfill/worker.py:63-77`
   - Issue: CLI 导入不存在的 `create_engine_and_session`；详情 UPDATE 触发 SQLAlchemy autobegin 后，`mark_completed()` 再次 `begin()` 会在真实 Session 中失败；成功/失败写入没有明确 commit/rollback；空别名响应不会失效旧别名。
   - Fix: 复用现有 `get_engine` + `Session`，补齐关闭 engine；让完成标记加入 worker 当前事务；worker 显式 commit/rollback；空集合也执行 alias replace-set；增加事务断言测试。

3. File: `backend/agent/jobs/indexer/entity_loader.py:161-179`
   - Issue: loader 查询不存在的 `episode.desc`，实际 schema 列为 `description`，单元测试 mock 同样使用了错误列名。
   - Fix: SQL 和映射统一改为 `description`，同步测试 fixture。

4. File: `backend/agent/jobs/indexer/shadow.py:68-74`
   - Issue: `FT._LIST` 实际返回扁平索引名列表，原代码先解构为两个元素，多于两个索引时直接抛错。
   - Fix: 按扁平 list/tuple 解码和过滤；新增三索引响应回归测试。

5. File: `backend/agent/main.py:114-120`, `backend/business/client/src/main/resources/mapper/EvidenceMapper.xml:11-30`
   - Issue: 生产组合根没有注入 `business.batch_evidence`，所以新增 Evidence API 永远不会被 RAG 调用；Evidence 基础查询也没有执行宣称的 type、NSFW、active 校验。
   - Fix: 在组合根注入 evidence lookup；SQL 限制 `type=2`、`nsfw=0`、`import_status=1`。

## Findings (not fixed)

1. **[阻断 / AC2、AC9] 新实体和关系没有接入 importer。** `backend/agent/jobs/importer/main.py:399-435` 只获取 persons、episodes、relations，未调用已经新增的 `get_subject_characters()`，`ImportBundle` 也没有 person/character/actor 字段；`backend/agent/jobs/importer/normalize.py:7,150` 仍只保留六类主创，不是“全部 credits”；没有任何生产代码写入 `person`、`character`、三张新关系表或创建 `entity_detail_job`。此外，`backend/agent/jobs/importer/db.py:109-218` 对 episode/tag 仍仅 upsert、不失效旧集合；`main.py:412-435` 在 relations 请求部分失败时把不完整集合当完整集合提交，而 `db.py:227` 会先删除旧边。修复需要重新设计并实现 subject 级完整响应边界、实体 upsert、关系 replace-set、backfill enqueue 与失败语义，超出机械修复范围。

2. **[阻断 / AC3、AC4] 通用索引与查询规划是孤立代码。** importer 仍只写 `rag_index_job`（`backend/agent/jobs/importer/repository.py:292-316`），indexer 主入口仍只消费旧 `IndexJobRepository`（`backend/agent/jobs/indexer/main.py:191-203`）；新增 `SearchIndexJobRepositoryImpl`、`MultiEntityLoader` 和多实体 profile 没有生产调用方，也没有多实体 Redis schema/消费者/tombstone 执行链。`RetrievalQuery`（`backend/agent/app/rag/schemas.py:42-73`）没有人物、角色或作品关系字段，Business 也没有实现规划所述的精确实体解析和关系过滤 API。因此人物/角色扩展、rewrite、关系召回和 AC4 的组合过滤均不可用。修复涉及模块边界和公开查询契约，未擅自补写。

3. **[阻断 / AC5、跨层契约] Evidence 链仍违反验收契约。** `backend/agent/app/rag/retrieval.py:236-263` 在 Evidence 异常、错误响应或缺少某个 ID 时保留无证据候选，直接违反 PRD“回查失败或候选失效不得进入模型上下文”；本次修改的 `.trellis/spec/backend/agent-guidelines.md` 反而把这一 fail-open 行为写成规范，与 PRD AC5 冲突。`backend/agent/app/rag/use_case.py:70` 又用 MySQL 本地 `subject_id` 拼 Bangumi URL，链接通常错误，因为响应没有 `bangumi_id`。新增 `POST /api/client/evidence/batch` 及 DTO/VO 也完全未写入 `docs/spec/openapi.yaml`，且没有前端/shared 契约（若明确仅内部 Agent 使用，应在 OpenAPI 和安全边界中明示）。这些属于产品失败语义和跨层接口决策，未擅自变更。

4. **[阻断 / AC1、AC7、AC9] 数据库与回填只经过 mock，未达到存量迁移门禁。** `migration-002-rag-entities.sql` 没有在临时 MySQL 空库、带旧数据数据库或备份恢复中执行；仓库也没有对应自动化验证，无法证明 DDL、索引、外键和回滚有效。关系表没有独立来源抓取时间；backfill 未保存 Person/Character 原始 JSON 或图片到 MinIO，`checkpoint_json` 只提供存取方法但 worker 不消费，报告也没有设计要求的 stale 数据；且由于 importer 不创建任务，worker 现实中无数据可处理。通用 index job 的 `mark_completed(..., claimed_at=...)` 参数未参与 WHERE 条件（`backend/agent/jobs/indexer/search_repository.py:197-210`），过期 worker 可完成已被重新认领的任务。需要真实 MySQL/MinIO 集成和 lease 所有权设计，未作为局部修复处理。

5. **[阻断 / AC6、AC7、阶段 8] 评测与发布证据不存在，任务状态记录失真。** `golden_cases.json` 虽有 53 条，但期望值是未绑定固定数据快照的占位本地 ID（例如 1、2、3）；runner 只接受注入函数，没有真实 Business/RAG CLI、基线输出、index/profile version 绑定、证据完整率、无依据陈述率或 P95 计算。任务目录与仓库中没有本次运行生成的数据质量、容量、评测、延迟、人工证据、故障演练、alias 灰度、24 小时观测或回滚报告，RAG 仍默认关闭（`backend/agent/app/config.py:48`）。但 `implement.md` 已把 Phase 1–8 全部勾选完成。现有故障矩阵大量使用 mock，且没有 schema/migration、真实 Redis/MySQL、生产组合根或 SSE 端到端测试；因此测试全绿不能证明发布门禁。应将未完成项恢复为未勾选，并按 Phase 2→8 顺序继续实现与留存证据。

## Acceptance Criteria

| AC | 结果 | 证据摘要 |
|---|---|---|
| AC1 | 部分 | schema/Entity 已新增；初始化列漂移已修；真实 DDL/迁移、全部来源时间未验证 |
| AC2 | 失败 | importer 未写新实体/关系，episode/tag stale，relations 部分失败会清旧边 |
| AC3 | 失败 | 生产仍使用旧 `rag_index_job`，通用任务和多实体消费者未接通 |
| AC4 | 失败 | 无 person/character/relation 查询字段、解析 API 和关系扩展链 |
| AC5 | 失败 | Evidence 缺失 fail-open，来源 URL 使用错误 ID，OpenAPI 未同步 |
| AC6 | 失败 | 有 53 条占位 case，但无真实基线、发布指标和延迟/证据指标 |
| AC7 | 失败 | 无发布报告、真实故障演练、alias 灰度与 24 小时观测证据 |
| AC8 | 通过 | 未引入 Neo4j/Elasticsearch/Milvus/RabbitMQ/MongoDB |
| AC9 | 失败 | backfill 骨架可测试，但 importer 不入队、checkpoint/stale/MinIO 链不完整 |

## Verification

- Lint: **部分通过**。`git diff --check` 与 Python `compileall` 通过；项目未配置/安装 Ruff、Mypy 或 Pyright，无法声明 Python lint/type-check 全绿。
- TypeCheck: **Java 通过**（Maven clean compile/test）；Python 无配置的静态类型门禁。前端没有改动，因此未运行前端 typecheck/build；这不消除 OpenAPI 缺失。
- Tests: **通过但覆盖不足**。
  - `backend/business`: `mvn -B clean test` → BUILD SUCCESS，22 tests passed（client 11 + app 11）。
  - `backend/agent`: `.venv\\Scripts\\python.exe -m pytest` → 171 passed。
  - `backend/agent`: `.venv\\Scripts\\python.exe -m compileall -q app jobs` → passed。
  - `backend/agent`: `.venv\\Scripts\\python.exe -m jobs.backfill.main --help` → exit 0。
  - 未执行真实 MySQL/Redis/MinIO/外部 Bangumi API、alias 切换或 24 小时灰度；这些仍是发布阻断项。

## Recommended next action

将 `implement.md` 中 Phase 2–8 的未实现项恢复为未勾选，先完成 Phase 3 的 importer 新实体/关系写入与完整响应保护；在这条数据链有真实 MySQL 集成测试之前，不开始多实体索引或灰度发布。
