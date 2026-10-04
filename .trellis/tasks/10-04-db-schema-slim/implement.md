# Implement: db-schema-slim

## 顺序（依赖驱动）

### 1. Schema 重写 `docs/database/db-schema.sql`
- [ ] 删 4 表：subject_credit, entity_detail_job, search_index_job, rag_index_job
- [ ] 改 `subject_person_credit`（+name/+credit_type/person_id NULL/dedup 生成列唯一键）
- [ ] 新 `job` 表
- [ ] 其余不动；search_index_release 保留

### 2. Python 侧 credit 合并（R1）
- [ ] `backend/agent/jobs/importer/repository.py`：删 subject_credit 双写；未解析 credit 写 name 占位
- [ ] `backend/agent/jobs/indexer/repository.py:124`：摘要 SQL 改单表 LEFT JOIN person
- [ ] 删 `entities/enums.py:53` 旧枚举、`entities/models.py:116` 旧映射
- [ ] 改测试：`test_legacy_credit_mapping.py`、`test_contract_drift.py`
- [ ] 删 Java `SubjectCredit.java`（pojo 模块），检查引用编译通过

### 3. Python 侧 job 合并（R2）
- [ ] 新 `JobRepository`（type 参数化），claim 用 SKIP LOCKED
- [ ] 迁移调用方：`jobs/backfill/repository.py`、`jobs/indexer/repository.py`、`jobs/indexer/search_repository.py`、`jobs/indexer/main.py`、`jobs/importer/quality.py`
- [ ] embedding 元组/source_id/checkpoint 序列化进 payload_json
- [ ] 测试：backfill/indexer/search_outbox/quality 相关

### 4. Redis 导入锁（R4）
- [ ] 新 `app/adapters/redis/import_lock.py`（acquire/renew/release，Lua compare-del）
- [ ] `jobs/importer/db.py` 删 GET_LOCK 两函数；`main.py` 换用新锁 + 删主连接保活 workaround
- [ ] 测试：双进程并发 acquire 其一失败

### 5. Redis 进度计数（R5）
- [ ] `_run_batch` 成功 INCR；删 `_start_count_flusher`；终态回写 import_record
- [ ] 检查 `ImportController.java` 是否读运行中进度 → 若是改读 Redis

### 6. Java operation_log 收窄（R3）
- [ ] 找切面/拦截器（AdminSubjectController 等）移除 SUBJECT_CREATE/SUBJECT_UPDATE 记录点
- [ ] action 白名单常量更新

### 7. 重建执行（R7）
- [ ] mysqldump 备份 user/user_collection/operation_log + 整库
- [ ] 新 schema 建库 → 恢复三表 → 部署 → full import
- [ ] 对账：person/character/credit/search_document 计数、credit 摘要抽样 diff

## 验证命令

- `cd backend/agent && .venv/Scripts/python -m pytest tests/jobs/importer tests/jobs/indexer tests/jobs/backfill -x -q`
- `cd backend/business && mvn -q compile`
- 并发锁手测：两个终端同跑 importer，后者立即失败
- `mysql -e "SHOW TABLES" anime_tracker | wc -l` → 19

## 风险文件（改前必看）

- `backend/agent/jobs/importer/repository.py`（credit 双写 + 原子 bundle，死锁重试逻辑别动）
- `backend/agent/jobs/importer/main.py`（finally 清理顺序：flusher→PID→锁→连接）
- `backend/agent/jobs/indexer/search_repository.py`（16 处 search_index_job 引用）

## 回滚点

- 步骤 1-7 全为代码 + schema，未动生产数据前随时可弃
- 步骤 8 备份 SQL 是唯一回滚依赖；备份未完成不执行重建
