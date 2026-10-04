# PRD: 缩减数据库表数量 + Redis 适配迁移

## Goal

db-schema.sql 23 表 → 19 表，消除逻辑重复（双写 credit 表、三份雷同 job 队列表），收窄 operation_log 噪音；把天然适合 Redis 的功能（导入锁、导入进度计数）迁出 MySQL。

## 已确认事实

- 生产库实测：`subject_credit` 14,685 行（14,684 active），`subject_person_credit` 14,687 行，两表**并行双写**（importer/repository.py:670-698 同时 INSERT 两表；indexer/repository.py:124 摘要只读 `subject_credit`）
- 核心数据量小：subject 220 行，person 9,393 行 → 派生数据可 full 重导重建
- 三 job 表（`entity_detail_job`/`search_index_job`/`rag_index_job`）schema ~90% 雷同（status/attempts/max_attempts/next_retry_at/last_error_*/content_hash），差异仅 entity_kind 枚举 + embedding 元组 + source_id/checkpoint_json
- 现有索引查询只按 `(status, next_retry_at)`，embedding 元数据不作为查询条件
- Redis 已在用：chat_store/entity_name_lookup/model_config/prompt/subject_index/user_preference/vector_set（backend/agent/app/adapters/redis/）
- 导入锁现为 MySQL `GET_LOCK('animetracker:import')`（importer/db.py:292-299），main.py:651 注释说明需保持主连接检出防锁漂移
- 导入进度计数：`_start_count_flusher` 后台线程每 3s UPDATE `import_record.subject_count`（importer/main.py）
- Java 遗留实体 `SubjectCredit.java` 标注"旧版兼容表"，Python 侧仅 legacy 映射 + 测试引用

## Requirements

### R1 合并 subject_credit → subject_person_credit
- `subject_person_credit` 加列：`person_id` 改 NULL、`name varchar(255) NULL`、`credit_type varchar(16) NOT NULL DEFAULT 'PERSON'`
- 未解析行 person_id=NULL + name 占位；已解析行 person_id 填 FK
- 数据迁移：`subject_credit` 14,685 行按 (subject_id, role, name→person) JOIN 入新表，无 person 匹配的行保留 name 占位
- 唯一键改 `(subject_id, COALESCE(person_id,0), name, role)`
- indexer credits 摘要改单表查询（JOIN person 取 name，NULL 时用占位 name）
- 删表 `subject_credit`，删 `SubjectCredit.java` + Python legacy 映射（entities/enums.py:53, entities/models.py:116）+ 相关测试

### R2 三 job 表 → 单 job 表
- 表名 `job`，列：`id, type('ENTITY_DETAIL'/'SEARCH_INDEX'/'RAG_INDEX'), entity_kind, entity_id, status, attempts, max_attempts, next_retry_at, last_error_code, last_error_message, payload_json, claimed_at, completed_at/indexed_at, created_at, updated_at`
- embedding 元组 + source_id + checkpoint_json 塞 `payload_json`
- 唯一键 `(type, entity_kind, entity_id, index_version)`，index_version 从 payload 提升为列（ SEARCH/RAG 需要版本唯一）
- worker claim/retry 逻辑统一一份
- 删 `entity_detail_job`/`search_index_job`/`rag_index_job`

### R3 operation_log 收窄 action
- 保留：LOGIN/LOGOUT/REGISTER/ROLE_CHANGE/SUBJECT_DELETE/IMPORT_RUN
- 移除：SUBJECT_CREATE/SUBJECT_UPDATE（走 access log）
- 表结构不动

### R4 导入锁迁 Redis
- 删 `GET_LOCK`/`RELEASE_LOCK`（importer/db.py:292-299）
- 改 `SET animetracker:import:lock <pid> NX EX 3600`，持有者周期续期；释放用 Lua 校验值后 DEL
- 删掉 main.py 为 GET_LOCK 保持主连接检出的 workaround（main.py:651 注释场景）

### R5 导入进度计数迁 Redis
- `_done_count` 周期刷 MySQL → Redis INCR，flusher 线程改为完成时一次性回写 `import_record`
- 运行中进度查询读 Redis；`import_record` 行只在终态落库

### R6 撤销（spec 冲突）
- `database-guidelines.md` 规定 MySQL `search_index_release` 是唯一 active release 事实，Redis 不得充当事实
- 不迁移，表与读写路径全部不动

### R7 迁移策略：重建
- 改 db-schema.sql → DROP 派生表重建 → full import 重导
- **保留不动**：user / user_collection / operation_log（用户数据）
- 迁移前 mysqldump 备份三张用户表 + 整库逻辑备份

## Acceptance Criteria

1. `SHOW TABLES` 19 张：`subject, episode, subject_alias, subject_tag, subject_meta_tag, subject_relation, subject_person_credit, subject_character, character_actor, person, character, person_alias, character_alias, user, user_collection, import_record, job, operation_log, search_document`（search_index_release 若 R6 全迁可删表 → 18 张，由实现期决定）
2. full import 跑通，credit 摘要（indexer 输出）与迁移前抽样比对一致
3. job worker（backfill/indexer）claim/retry/完成全链路通过现有测试
4. 并发启动两个 importer，后者立刻失败退出（Redis 锁生效）
5. importer 运行中 MySQL 无 `UPDATE import_record` 周期写；完成后终态行正确
6. operation_log 不再出现 SUBJECT_CREATE/SUBJECT_UPDATE 行
7. user/user_collection/operation_log 数据迁移前后行数一致

## Out of Scope

- search_document / search_index_release 挪搜索引擎（Meilisearch/ES）— 另开任务做存储选型
- job 队列整体挪 Redis stream — 数据量小，MySQL SKIP LOCKED 足够
- operation_log 写路径经 Redis 缓冲 — 收窄 action 后写量已低
- 核心域 15 表结构变更

## Risks

- R1 数据迁移 JOIN 失败行 → 保留 name 占位兜底，迁移后校验行数对账
- R4 Redis 锁误释放 → Lua compare-and-del；TTL 续期线程崩溃时 1h 后自然过期可接受
- R7 重建依赖 full import 源数据可用（Bangumi API），迁移窗口预留重试时间
