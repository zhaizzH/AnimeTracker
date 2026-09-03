# 全量 Bangumi 数据与 RAG 检索闭环研究

核对日期：2026-09-03

## 结论

首版不新增 Neo4j、Elasticsearch、Milvus、RabbitMQ 或 MongoDB。MySQL 继续作为唯一权威事实库，Redis/RediSearch 作为可重建的全文与向量索引，MinIO 保存原始响应与图片。先补齐数据模型、同步语义、索引自动化、证据返回和评测，再用指标决定是否引入新组件。

## API 能力与导入差距

Bangumi v0 OpenAPI 位于 `docs/api/open-api/v0.yaml`：

- Subject 详情与搜索：`:257`、`:331`、`:3572`。
- Subject persons：`:400`；Person 详情及反向关系：`:769`、`:3181`、`:3273`。
- Subject characters：`:431`；Character 详情及反向关系：`:578`、`:2179`、`:3391`。
- Subject relations：`:462`。
- Episode 列表与详情：`:493`、`:2596`、`:2667`。
- 用户收藏含私有数据，不进入共享索引：`:361`、`:2747`。

当前 importer 的实际行为：

- `jobs/importer/client.py:68-136` 只覆盖 subject、persons、episodes、related subjects、calendar、browse；search 方法不是导入主路径。
- `jobs/importer/normalize.py:42-90` 保存作品核心字段，但新主路径遗漏 `eps`/`volumes`。
- `jobs/importer/normalize.py:94-105` 只从 infobox 抽取别名、中文名和英文名。
- `jobs/importer/normalize.py:133-142` 只保留六类主创职责。
- `jobs/importer/repository.py:167-208` 与 `jobs/importer/db.py:109-198` 只做 upsert，不失效上游已删除的标签、主创和剧集。
- `jobs/importer/main.py:411-428` 为相关作品逐项请求详情，只保留动画且非 NSFW 的目标。
- `jobs/importer/main.py:388-397` 与 `jobs/importer/storage.py:68-70` 已保存 gzip 原始详情和封面，可用于重放与字段回填。
- 当前未调用 characters、person detail、character detail，因此角色、声优关系和完整人物/角色资料缺失。

## Schema 与迁移约束

- `docs/database/db-schema.sql` 是带 `DROP TABLE IF EXISTS` 的初始化快照，不能用于非空库升级。
- `backend/business/app/src/main/resources/application.yml:28-31` 设置 `spring.sql.init.mode: never`；项目没有 Flyway/Liquibase。
- `db-schema.sql:120-193` 已包含 alias、meta tag、credit、RAG job，但 Java entity 未完整覆盖这些表。
- `subject_credit.credit_type` schema 契约为 `PERSON|ORGANIZATION`，`jobs/importer/repository.py:190-198` 却固定写入 `MAIN`，存在契约漂移。

存量库必须提供独立的前向迁移脚本或运维步骤：备份 → 新表/兼容列 → 应用双读或兼容写 → 回填 → 校验 → 切换 → 保留回滚窗口。不得执行初始化 schema。

## 当前 RAG 能力与缺口

已经实现：

- LangGraph 路由：`app/agent/graph.py:13-58`。
- 三个领域节点均挂载 RAG 工具：`app/agent/client/search.py:10-20`、`discover.py:10-20`、`recommend.py:9-18`。
- BM25 + KNN + RRF：`app/rag/retrieval.py:45-63,94-124`。
- 结构化过滤、Business 权威回查和轻量重排：`app/rag/retrieval.py:134-225,252-340`。
- 版本化 Redis 索引与 1024 维 Float32：`app/adapters/redis/subject_index.py:79-168,193-245`。

阻断上线的问题：

- `app/config.py:41-49` 默认 `rag_enabled=false`。
- `app/rag/use_case.py:39-47` 只向 Agent 返回 subjectId、title、score、reason，缺少简介、标签、主创、关系、来源与时间，无法形成 grounded explanation。
- `jobs/scheduler/main.py:25-34,103-108` 只调度 importer；`jobs/indexer/main.py:178-236` 仍需人工执行。
- `jobs/indexer/gate.py:22-29,80-127` 要求五份报告和 120 条评测，但仓库不存在对应 eval 数据集和 runner。
- `jobs/indexer/repository.py:127-129` 不会生成 AIRING 状态，但查询模型允许 AIRING。
- importer 写 job 时使用旧 content hash，indexer 又以实时 profile 生成文本，存在文本/hash 不一致风险。
- 当前 Python 测试只有 `tests/jobs/importer/test_subject_metrics.py`，无法证明 retrieval、indexer、gate、graph、fallback 或 SSE。

## 参考项目技术栈映射

本地参考仓库：`C:/workspace/project/medicine-ai-system`。

- `README.md:103-112` 列出 Spring Boot、FastAPI/LangGraph、MySQL、MongoDB、Redis、Elasticsearch、Milvus、Neo4j、RabbitMQ 和 MinIO；这些组件职责彼此独立。
- MySQL 保存业务与知识库控制面元数据：`database/MySQL/medicine.sql:360-469`。
- Elasticsearch 只用于商品中文/拼音搜索，不是 RAG。
- RabbitMQ 只编排异步导入、切片重建和配置刷新，不参与在线召回。
- Milvus 是文档 chunk 的纯向量召回：`medicine-ai-agent/app/rag/query/retriever.py:191-243`。
- Neo4j 是固定医疗实体 Cypher 工具，不是 GraphRAG，也没有与 Milvus 融合：`medicine-ai-agent/app/agent/client/domain/diagnosis/tools/graph_tool.py:323-542`。
- 可借鉴的 RAG 链路是 rewrite → retrieve → optional rerank → budgeted format；参考 `medicine-ai-agent/app/rag/query/`。
- 可借鉴 Trace 的 span/middleware/异步写入思路，但 AnimeTracker 可先使用现有日志与存储，不为 Trace 单独引入 MongoDB。

## 推荐分阶段依赖

1. 数据契约与安全迁移：修复现有映射漂移，建立 Person/Character 及关系表、同步状态和失效语义。
2. 导入与渐进回填：先保存 subject 端点附带的实体摘要和边；后台任务再 checkpoint 化回填完整详情。
3. 实体档案与索引自动化：为四类实体生成确定性 profile，导入事务产生版本化索引工作，消费者建立 shadow index。
4. 检索与证据：结构化过滤、全文、向量、RRF、可选 rerank，随后 Business 批量回查并输出证据块。
5. 评测与发布：至少 50 条首版 golden cases，生成质量/召回/延迟/人工报告，gate fail-closed 后才允许启用 alias 与 RAG。

阶段 2 依赖阶段 1；阶段 3 依赖阶段 1 的 schema 和阶段 2 的稳定规范化；阶段 4 可先针对 Subject 实施，再扩展其他实体；阶段 5 贯穿每阶段并最终负责启用。

## 验证与回滚建议

- Schema：在临时空库验证完整 schema；在带旧数据的临时库验证前向迁移、回填和兼容读取。
- Python：`cd backend/agent && uv run pytest`，新增 importer、backfill、profile、indexer、retrieval、gate、graph/SSE 定向测试。
- Java：`cd backend/business && mvn -B clean test`，新增批量证据接口与 mapper 集成测试。
- 前端/API 有契约变化时：`cd frontend && npm run typecheck`，同步 `docs/spec/openapi.yaml` 与 shared types。
- Redis 发布：新版本只建 shadow index；alias 切换失败或线上指标异常时切回旧 alias，不先删除旧索引。
- MySQL 回滚：保留旧字段与旧表读取窗口；破坏性删除放到后续独立任务，且必须有备份恢复验证。

## 新技术引入门槛

- Neo4j：核心用例稳定出现三跳以上路径解释或图算法需求，并且 MySQL 基准证明不可接受。
- Elasticsearch：中文分词、拼音、错别字或 completion 的 golden cases 在 Redis 上不达标。
- Milvus：Redis 向量容量或 P95 延迟压测不达标。
- RabbitMQ：单机任务表无法满足跨机器 worker、背压与交付语义。
- MongoDB：现有存储无法满足对话/Trace 的容量与查询要求；不得仅因参考项目使用而引入。
