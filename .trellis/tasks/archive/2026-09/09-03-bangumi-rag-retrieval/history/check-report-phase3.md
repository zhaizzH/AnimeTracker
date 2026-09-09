# Phase 3 导入与关系摘要专项审查报告

> 历史报告：这是 Phase 3 当时状态的专项快照，后续阶段已继续修复。当前状态以 [任务文档索引](../README.md) 为准。

审查日期：2026-09-04
审查范围：Phase 3 Importer 关系摘要实现，以及对现有 RAG、Indexer、Schema、Java 构建的兼容性。
结论：**Phase 3 局部实现可通过定向测试，但任务整体仍不通过，不能启用 RAG 或进入灰度。**

## Findings (fixed)

### 1. 导入记录没有传入实体 lineage

- File: `backend/agent/jobs/importer/main.py:139-185,378-507`
- Issue: worker 调用 `ImportRepository.write_bundle()` 时没有把当前 `import_record.id` 放进 `ImportBundle`，导致 `person.last_seen_import_id`、`character.last_seen_import_id` 长期为空；`full` 模式的 recent catch-up 也会丢失该关联。
- Fix: `_run_batch` 将记录 ID传入 worker；`import_single_subject` 将其写入 bundle；full catch-up 使用独立的 `entity_import_record_id`，避免覆盖 full checkpoint。

### 2. 不完整的 Subject 集合可能被误认为“空集合”

- File: `backend/agent/jobs/importer/main.py:438-510`
- Issue: `infobox/tags/meta_tags` 只要存在 key 就被视为完整；`eps`/`total_episodes` 为 `null` 也可能触发剧集清理。上游返回 null 或类型错误时，会错误失效已有数据。
- Fix: 只有实际 list 才允许 alias/tag/meta-tag replace-set；只有非负整数 episode count 才允许剧集 replace-set；显式合法的零仍表示权威空集合。

### 3. 关系响应缺少逐项完整性保护

- File: `backend/agent/jobs/importer/main.py:460-490,781-800`
- Issue: 关系列表中缺少 ID、relation 或关联目标缺少有效 `type/nsfw` 时，旧逻辑可能继续提交空的 replace-set 并删除旧关系。
- Fix: 增加 relation item 和目标响应校验；异常、非法或不完整目标会保留旧关系。`db.upsert_relations()` 继续负责解析本地 ID、去重和跳过自环。

### 4. 回填任务可能被 Importer 重置为 PENDING

- File: `backend/agent/jobs/importer/repository.py:227-238`
- Issue: 重复导入遇到回填任务 `CLAIMED/RUNNING` 时，旧 SQL 会改回 `PENDING`，可能造成并发 worker 重复处理或 lease 状态失真。
- Fix: `COMPLETED/ABANDONED/CLAIMED/RUNNING` 状态保持不变；仅待处理/失败任务重新置为 `PENDING`。新增 SQL 回归断言。

### 5. Phase 3 数据落库路径已核对

- File: `backend/agent/jobs/importer/normalize.py:35-67,93-128,175-266`
- Result: `persons`、`characters`、character actors 被规范化；全部非空 credit roles 被保留；person type、character type、角色 relation 和声优摘要被转换为 schema 对应值。
- File: `backend/agent/jobs/importer/repository.py:94-340`
- Result: Subject、Person、Character、Subject↔Person、Subject↔Character、Character↔Person 在同一事务中写入；完整响应才执行关系 replace-set；每个摘要实体幂等入队 `entity_detail_job`。
- File: `backend/agent/jobs/importer/db.py:205-257`
- Result: relation 本地 ID 解析、重复 pair 去重、自环跳过和双向关系写入逻辑保持有效。

## Findings (not fixed)

### 1. [阻断 / AC1、AC9] 存量迁移和真实数据库验证仍缺失

- `docs/database/db-schema.sql` 包含新实体/关系/job 表，但本轮没有在临时 MySQL 空库、带旧数据数据库或备份恢复流程执行初始化/前向迁移。
- 关系表没有统一的来源抓取时间字段；`subject_relation` 仍是物理删除模型，无法提供与新关系表一致的来源审计语义。
- Backfill 的 checkpoint、MinIO 原始 Person/Character 快照和 stale 报告仍未形成完整运行链。
- 这是迁移和运维设计问题，未在 Phase 3 审查中擅自扩大修复。

### 2. [阻断 / AC3] 多实体索引仍未接入生产 indexer

- `backend/agent/jobs/importer/repository.py:529-555` 仍只写旧 `rag_index_job`（Subject）。
- `backend/agent/jobs/indexer/main.py` 生产入口仍消费旧 `IndexJobRepository`；`SearchIndexJobRepositoryImpl`、`MultiEntityLoader` 和多实体 profile 没有生产调用方。
- 因此 Person/Character 摘要虽已入 MySQL，尚未自动生成并消费通用搜索索引，也没有 tombstone/alias 发布闭环。

### 3. [阻断 / AC4] 人物、角色和关系查询规划尚未接通

- `RetrievalQuery` 尚无 person/character/relation 字段，Business 没有对应精确解析和关系过滤接口。
- 当前代码不能把人物/角色命中扩展为 Subject ID，也不能完成“找某声优参与作品”等结构化查询。
- 属于公开查询契约和模块边界设计，未在本轮局部修复。

### 4. [已修复 / AC5] Evidence 当前已改为 fail-closed

- `backend/agent/app/rag/retrieval.py` 现在要求 Evidence 返回所有候选，且逐项验证 `subjectId/type/nsfw`；异常、错误、部分结果或不安全结果统一返回 `available=False, reason=evidence_unavailable`。
- `backend/agent/tests/rag/test_evidence_contract.py` 与 `test_fault_matrix.py` 已覆盖异常、错误、部分和不安全响应。
- Business Evidence DTO 现已暴露 `sourceId/sourceUrl/sourceFetchedAt`，Agent 映射优先使用上游 URL；无证据的旧兼容路径才保留本地 Subject URL。

### 5. [阻断 / AC6、AC7] 评测和发布证据仍不存在

- `tests/evals/golden_cases.json` 的用例仍未绑定固定数据快照；没有真实 Business/RAG 基线、Recall/MRR/nDCG、过滤正确率、证据完整率或 P95 报告。
- 没有真实 MySQL/Redis/Embedding/Business 故障演练、shadow alias 灰度、24 小时观测和回滚记录；RAG 默认开关仍未达到可启用条件。

### 6. [跨层契约] 新关系表尚无 Java Business 查询映射

- Java 构建通过，且本轮没有破坏现有 Evidence/Subject 映射；但 `backend/business` 未找到 Person、Character、SubjectPersonCredit、SubjectCharacter 或 CharacterActor 的 Mapper/Service/DTO。
- 如果 Phase 6 要向 Agent 提供人物/角色精确查询，必须同步 Java Mapper、DTO/VO、OpenAPI 和必要的 shared types。

## Verification

- Lint: **部分通过**。`git diff --check` 通过；项目未安装/配置 Ruff、Mypy 或 Pyright，不能声明 Python 静态 lint/type-check 全绿。
- TypeCheck: **Java 通过**。`mvn -B clean test` → BUILD SUCCESS，Java 现有 22 项测试通过；Python 通过 `compileall`，没有独立静态类型门禁。
- Tests: **通过但覆盖仍有限**。
  - `backend/agent`: `.venv\Scripts\python.exe -m pytest tests/jobs/importer tests/rag -q --basetemp=.pytest-tmp-phase3` → **58 passed**。
  - `backend/agent`: `.venv\Scripts\python.exe -m pytest -q --basetemp=.pytest-tmp-phase3` → **176 passed**。
  - `backend/agent`: `.venv\Scripts\python.exe -m compileall -q app jobs tests` → 通过。
- `git diff --check` → 通过。
- 补充 Evidence fail-closed 定向测试：`tests/rag/test_evidence_contract.py tests/rag/test_fault_matrix.py` → **28 passed**。
  - 未执行真实 MySQL、Redis、MinIO、外部 Bangumi API、alias 发布或灰度；pytest cache 有 Windows 拒绝访问 warning，但通过仓库内 `--basetemp` 完成测试，未修改系统目录。

## Recommendation

Phase 3 导入器在 mock/静态路径上已具备人物、角色、声优、全部职责和完整响应保护；可以作为后续 Phase 4 的输入，但不能据此宣称整个任务完成。下一步应先完成真实 MySQL migration/integration 门禁，再接通通用 indexer 和 Business 人物/角色查询，最后修复 Evidence fail-closed 与评测发布证据。
