# Design: 缩减数据库表 + Redis 适配迁移

## 架构边界

- 事实数据（subject/episode/person/character/user/...）：MySQL 不动
- 派生数据（credit 关系、job 队列、search 投影）：MySQL 重建，结构精简
- 瞬态协调（导入锁、进行中进度、ACTIVE release 指针）：Redis

## R1 credit 合并

**新 schema (`subject_person_credit`)**

```sql
person_id   bigint NULL,               -- 解析成功填 FK；未解析 NULL
name        varchar(255) NULL,         -- 未解析时的占位名（来自旧 subject_credit）
credit_type varchar(16) NOT NULL DEFAULT 'PERSON',  -- PERSON / ORGANIZATION
-- 既有: subject_id, role, relation, sort_order, source_active, created_at, updated_at
-- 既有: bangumi_person_id 不需要（person 表有）
UNIQUE KEY uk_spc (subject_id, role, COALESCE(person_id, 0), COALESCE(name, ''))
```

MySQL 唯一键不允许表达式？8.0 支持 functional index；保守做法加生成列 `dedup_key` + 唯一键。

> **实现期修订**：生成列必须是 `VIRTUAL` 而非 `STORED`（STORED 生成列引用 FK 列时 MySQL 禁止 `ON DELETE CASCADE`）。最终形态为
> `dedup_key char(64) GENERATED ALWAYS AS (sha2(concat_ws('#', subject_id, role, ifnull(person_id,0), ifnull(name,'')), 256)) VIRTUAL`——用 sha2 定长哈希而非明文拼接，避免生成列变成隐式长度约束（明文拼接理论上限约 360 字符，严格模式下超长报 1406 并回滚整个 subject 事务），同时消除分隔符歧义。已在 MySQL 8.4.9 实测：重复被唯一键拦截，255 字符占位名可正常插入。

**数据流变更**
- importer `repository.py:670-698`：删 subject_credit 双写，未解析 person 的 credit 写 name 占位行
- indexer 摘要 `repository.py:124`：改单表 `SELECT concat_ws('：', role, ifnull(p.name, spc.name)) ... LEFT JOIN person p ON p.id = spc.person_id`
- 删除：`SubjectCredit.java`、`entities/enums.py:53`、`entities/models.py:116`、`tests/entities/test_legacy_credit_mapping.py` 改为新映射测试

**迁移 SQL**（重建策略下即 seed）：
旧行 → 新表：`INSERT ... SELECT s.id, p.id, sc.name, sc.credit_type, sc.role, 'MAIN', sc.sort_order, sc.source_active ... FROM subject_credit sc JOIN subject s ON ... LEFT JOIN person p ON p.bangumi_person_id = sc.bangumi_person_id`。重建策略下直接 full import 重灌，无需此 SQL 跑生产。

## R2 单 job 表

```sql
CREATE TABLE job (
  id bigint AUTO_INCREMENT PRIMARY KEY,
  type varchar(16) NOT NULL,            -- ENTITY_DETAIL / SEARCH_INDEX / RAG_INDEX
  entity_kind varchar(16) NOT NULL,     -- SUBJECT/EPISODE/PERSON/CHARACTER
  entity_id bigint NOT NULL,
  index_version varchar(32) NOT NULL DEFAULT '',  -- ENTITY_DETAIL 为 ''
  status varchar(16) NOT NULL DEFAULT 'PENDING',
  attempts int NOT NULL DEFAULT 0,
  max_attempts int NOT NULL DEFAULT 5,
  next_retry_at datetime NULL,
  last_error_code varchar(64) NULL,
  last_error_message varchar(512) NULL,
  payload_json json NULL,               -- embedding 元组 / source_id / checkpoint / content_hash
  claimed_at datetime NULL,
  finished_at datetime NULL,
  created_at datetime NOT NULL,
  updated_at datetime NOT NULL,
  UNIQUE KEY uk_job (type, entity_kind, entity_id, index_version),
  KEY idx_job_status_retry (status, next_retry_at)
);
```

- `content_hash` 放 payload_json（仅完成时写、不作查询条件）
- claim：`UPDATE job SET status='CLAIMED', claimed_at=now() WHERE id IN (SELECT id FROM job WHERE status='PENDING' AND next_retry_at<=now() ORDER BY id LIMIT n) ` + `FOR UPDATE SKIP LOCKED`（8.0 支持）
- 三处 repository（backfill/indexer/search_repository）合为一个 `JobRepository(type=...)`

## R4 导入锁

```
acquire: SET animetracker:import:lock {pid}:{ts} NX EX 3600  → 失败即退
renew:   后台线程每 600s PEXPIRE 3600_000（仅当值匹配）
release: Lua: if get==val then del
```

- 新增 `app/adapters/redis/import_lock.py`；importer/db.py 删 `acquire/release_import_lock`
- main.py 不再为锁保持 `main_connection` 检出（简化 finally 块）；连接仍用于 import_record 读写，但允许回池

## R5 进度计数

- `_run_batch` 成功时 `INCR animetracker:import:{record_id}:done`；flusher 线程删除
- main() 终态：读 Redis 计数 → 一次 `complete_import_record` 写库 → DEL key
- 运行中外部查询进度：business 端读 Redis（若当前无人查库，可省，实现期确认 ImportController）

## R6 撤销

spec 规定 `search_index_release` 是唯一 active release 事实。不迁移。

## R7 重建顺序

1. 备份：`mysqldump anime_tracker user user_collection operation_log > backup.sql` + 整库逻辑备份
2. 新 schema 建库（19 表）
3. 恢复三张用户表
4. 部署新代码 → full import 重灌派生数据
5. 抽样对账：credit 摘要、person/character 计数、search_document 计数

## 回滚

- 备份 SQL + 旧 schema + 旧代码镜像即可回退；Redis key 无前缀冲突（全用 `animetracker:` 前缀，旧代码不读这些 key）
