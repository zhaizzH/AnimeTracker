# 完善全量 Bangumi 数据与 RAG 检索闭环

## Goal

让用户可以用自然语言按客观条件与主观语义找番，并获得只基于可追溯数据生成的推荐理由；同时建立可扩展到完整 Bangumi 公共实体与关系的数据模型、导入同步和检索闭环。

## Background

- 产品主目标已经确定为“自然语言找番与可解释推荐”，不是首版动漫百科问答或个人追番助手。
- Bangumi v0 API 可提供作品、剧集、人物/组织、角色、声优、标签、评分、收藏聚合、图片与作品关系；完整响应可以保留为原始快照。
- 当前 MySQL 已迁移到 21 张表并具备人物、角色、声优与关系结构，但真实数据仍以作品、剧集、标签和作品关系为主；人物/角色详情与新的搜索投影尚未完成回填。
- 当前 Agent 已有基于 RediSearch `FT.*` 的 BM25 + KNN + RRF、结构化过滤和轻量重排代码，但本机 Redis 8.8 只提供 Vector Set，无法运行 `FT.CREATE`、`FT.SEARCH` 或 `FT.ALIASUPDATE`；该实现需要改为 MySQL 词法召回 + Redis Vector Set 语义召回。
- 参考项目 `C:\workspace\project\medicine-ai-system` 中 MySQL、MongoDB、Redis、Elasticsearch、RabbitMQ、MinIO、Milvus、Neo4j 分别解决不同问题，不构成必须整体采用的 RAG 套件。

## Requirements

- R1：MySQL 是 Bangumi 结构化事实和索引发布版本的唯一权威数据源；MySQL FULLTEXT、Redis Vector Set 和未来可选图投影均可从事实表重建，不允许跨库双写成为事实来源。
- R2：数据模型应能表达 Subject、Episode、Person、Character、别名、标签以及 Subject↔Subject、Subject↔Person、Subject↔Character、Character↔Person 关系，并区分现实制作组织与作品内组织。
- R3：导入必须保存来源抓取时间、内容哈希、同步状态和删除/失效语义；上游删除的标签、主创、剧集和关系不能永久残留。
- R4：原始 API JSON 与图片继续由 MinIO 保存，用于审计、重放和未来字段回填；结构化字段不能只存在原始快照中。
- R5：查询链必须将 MySQL 精确/全文召回、Redis Vector Set 向量召回和确定性融合分离；评分、排名、热度、日期和 NSFW 作为过滤或重排特征，不进入 embedding 正文。
- R6：为 Subject、Episode、Person、Character 生成不同的实体级检索文档，保留实体 ID、来源、抓取时间和关系元数据；不得把完整 JSON 粗暴拼成一个向量文档。
- R7：Agent 返回的每项推荐必须来自 Business 权威回查，并携带足以解释结果的标题、简介摘录、匹配标签/主创、评分/热度、播出状态和数据时间；证据不足时不得用模型常识补全事实。
- R8：导入完成后必须自动产生可消费的索引任务；MySQL 词法投影、Redis 向量、content hash、profile version 和激活版本必须一致。发布版本以 MySQL release 记录为准，失败可重试且不会静默启用不完整索引。
- R9：建立覆盖标题/别名、结构化过滤、主观语义、人物关系、系列关系、否定条件与降级路径的确定性评测集，以指标而不是主观体验决定是否新增检索中间件。
- R10：首版沿用 MySQL 8.4 FULLTEXT（`ngram`）+ Redis 8 Vector Set + MinIO + FastAPI/LangGraph，不引入 Redis Stack/RediSearch。Neo4j、OpenSearch/Elasticsearch、Qdrant、Milvus、RabbitMQ、MongoDB 均不得在没有对应指标失败证据时引入。
- R11：人物与角色采用分阶段回填：首轮先保存作品端点附带的实体摘要与关系，使检索可用；后台任务通过 checkpoint、限速、幂等写入和失败重试逐步补齐人物/角色完整详情，不以全历史详情回填完成作为首版上线前置条件。

## Acceptance Criteria

- [ ] AC1：数据库 schema 能无歧义保存 R2 的全部实体和关系，并具有唯一约束、反向查询索引、来源时间与失效状态。
- [ ] AC2：导入器可幂等新增、更新和失效 API 数据；`subject.eps` 等现有映射遗漏被修复，重复运行不产生重复边或陈旧关联。
- [ ] AC3：一次成功导入会产生对应索引工作；索引消费者可重试并重建同版本的 MySQL FULLTEXT shadow 投影与 Redis Vector Set，五类门禁报告通过后才能原子切换 MySQL active release。
- [ ] AC4：自然语言查询可同时应用年份、季度、状态、评分、热度、标签、人物、角色和作品关系过滤，并融合精确名称、MySQL `MATCH ... AGAINST` 与 Redis `VSIM` 召回。
- [ ] AC5：每项 Agent 推荐都包含可验证证据；Business 回查失败或候选失效时，该候选不会进入模型上下文。
- [ ] AC6：恰好 120 条必选检索评测覆盖 R9 场景，并锁定 Recall@20、MRR@10、nDCG@10、过滤正确率、证据完整率和 P95 延迟门槛。
- [ ] AC7：RAG 默认开启前，MySQL lexical/Redis vector 版本一致性、索引自动化、数据质量报告、评测报告、故障降级和 release 回滚路径均通过验证。
- [ ] AC8：只有评测证明 MySQL FULLTEXT + Redis Vector Set 失败时，才形成引入 OpenSearch/Elasticsearch、Qdrant、Neo4j、Milvus 或 RabbitMQ 的独立决策记录。
- [ ] AC9：人物/角色详情回填可暂停、恢复和重复执行；未回填实体有明确状态，且不会阻塞已经具备摘要与关系数据的搜索结果。

## Out of Scope

- 用户私有收藏、评论和个人画像进入共享索引。
- 自动抓取 Bangumi 之外的网站、社区评论或未授权语料。
- 首版引入 Neo4j、OpenSearch/Elasticsearch、Qdrant、Milvus、RabbitMQ、MongoDB 或照搬参考项目的微服务拆分。
- 为满足当前检索目标安装 Redis Stack/RediSearch；现有 Redis Vector Set 已覆盖语义向量能力。
- 图片 OCR、caption 或视觉向量检索。
- 用 RAG 代替数据库中已有的结构化事实查询。
