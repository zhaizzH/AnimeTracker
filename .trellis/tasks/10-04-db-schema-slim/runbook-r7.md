# R7 迁移 Runbook：23 表 → 20 表重建

> **用户已决定：本会话只产出 runbook，不执行。** 执行前必须有人工确认停机窗口。

## 0. 前置检查

| 项 | 检查方式 | 本机现状 |
|---|---|---|
| `mysqldump` / `mysql` 客户端 | `which mysqldump mysql` | ❌ **不在 PATH**。需装 MySQL 客户端工具，或在 DB 主机上执行备份/恢复 |
| 目标库可达 | `mysql -h $DB_HOST -u $DB_USER -p -e "SELECT 1" $DB_NAME` | 未验证 |
| Bangumi API 配额 | full import 全量拉取需要较长窗口 | 未验证 |
| Redis 可达 | `redis-cli ping`（R4/R5 依赖） | 未验证 |
| 停机窗口 | 重建期间 business 写 `subject` 会与重灌冲突 | 待安排 |

工作目录约定：所有 `python -m jobs.*` 命令必须在 `backend/agent` 下执行（模块依赖 `app.*` 包）。

## 1. 备份（**唯一回滚依赖，未完成不得进入第 2 步**）

```bash
STAMP=$(date +%Y%m%d-%H%M%S)
mkdir -p backup/$STAMP

# 1a. 三张用户表（必须原样恢复）
mysqldump -h "$DB_HOST" -u "$DB_USER" -p"$DB_PASSWORD" \
  --single-transaction --set-gtid-purged=OFF \
  "$DB_NAME" user user_collection operation_log \
  > backup/$STAMP/user-tables.sql

# 1b. 整库逻辑备份（含派生表，用于兜底回滚）
mysqldump -h "$DB_HOST" -u "$DB_USER" -p"$DB_PASSWORD" \
  --single-transaction --set-gtid-purged=OFF --routines --triggers \
  "$DB_NAME" > backup/$STAMP/full-db.sql

# 1c. 迁移前基线计数（对账用，见第 5 节）
```

备份后校验：`grep -c "INSERT INTO\|CREATE TABLE" backup/$STAMP/user-tables.sql` 应为非零，且三张表各有 `CREATE TABLE`。

## 2. 重建 schema

⚠️ **`docs/database/db-schema.sql` 是全量脚本，含 `DROP TABLE IF EXISTS user / user_collection / operation_log`。**
直接整份执行会清空用户数据 —— 必须先备份，并在第 3 步立即恢复。

```bash
mysql -h "$DB_HOST" -u "$DB_USER" -p"$DB_PASSWORD" "$DB_NAME" < docs/database/db-schema.sql

# 验收 AC1：应为 20 张
mysql -h "$DB_HOST" -u "$DB_USER" -p"$DB_PASSWORD" -N -e "SHOW TABLES" "$DB_NAME" | wc -l
```

期望的 20 张：
`episode, import_record, subject, subject_alias, subject_meta_tag, job, subject_tag, user, user_collection, search_document, search_index_release, subject_relation, operation_log, person, character, person_alias, character_alias, subject_person_credit, subject_character, character_actor`

确认已消失的 4 张：`subject_credit, entity_detail_job, search_index_job, rag_index_job`。

## 3. 恢复用户三表

```bash
mysql -h "$DB_HOST" -u "$DB_USER" -p"$DB_PASSWORD" "$DB_NAME" < backup/$STAMP/user-tables.sql
```

## 4. 部署新代码

切换 business 与 agent 到本分支产物，**先不要启动 indexer/backfill/scheduler**（第 6 步才启动）。

## 5. full import 重灌派生数据

```bash
cd backend/agent
uv run python -m jobs.importer.main --mode full
```

- 这是长任务，`--resume` 可断点续跑
- 导入期 Redis 锁 `animetracker:import:lock` 生效（R4）；并发启动第二个 importer 应立即失败退出（AC4）
- 进度计数走 Redis `animetracker:import:{record_id}:done`（R5），`import_record` 仅在终态落库

## 6. 启动派生任务

```bash
uv run python -m jobs.indexer.main --index-version <新版本号>
uv run python -m jobs.backfill.main --batch-size 5
```

`job` 表三种 type 分别由 importer（`ENTITY_DETAIL`/`SEARCH_INDEX`/`RAG_INDEX` 入队）、backfill（消费 `ENTITY_DETAIL`）、indexer（消费 `SEARCH_INDEX` 与 `RAG_INDEX`）驱动。

## 7. 对账

```sql
-- AC7：用户数据行数迁移前后一致（对照第 1c 步基线）
SELECT 'user' AS t, COUNT(*) FROM user
UNION ALL SELECT 'user_collection', COUNT(*) FROM user_collection
UNION ALL SELECT 'operation_log',  COUNT(*) FROM operation_log;

-- AC6：operation_log 不再产生 SUBJECT_CREATE / SUBJECT_UPDATE
SELECT action, COUNT(*) FROM operation_log
WHERE action IN ('SUBJECT_CREATE','SUBJECT_UPDATE')
GROUP BY action;
-- 迁移后新增行应为 0（历史行仍可能 >0，属预期）

-- 派生数据规模
SELECT 'subject' t, COUNT(*) FROM subject
UNION ALL SELECT 'person', COUNT(*) FROM person
UNION ALL SELECT 'character', COUNT(*) FROM character
UNION ALL SELECT 'subject_person_credit', COUNT(*) FROM subject_person_credit
UNION ALL SELECT 'job', COUNT(*) FROM job
UNION ALL SELECT 'search_document', COUNT(*) FROM search_document;

-- job 表分布
SELECT type, status, COUNT(*) FROM job GROUP BY type, status;

-- credit 未解析残留（应尽量小）
SELECT COUNT(*) FROM subject_person_credit WHERE person_id IS NULL;
```

**AC2 credit 摘要抽样比对** —— 需在第 2 步**之前**先在旧库跑基线查询留档，迁移后再跑对照查询，两条都导出为 `subject_id\tcredits` 后 `diff`。

基线（旧库，对应迁移前 indexer `load_subject` 的 credits 子查询）：

```sql
SELECT s.id,
  (SELECT GROUP_CONCAT(CONCAT(sc.role, '：', sc.name)
          ORDER BY sc.sort_order, sc.name SEPARATOR '\n')
     FROM subject_credit sc
    WHERE sc.subject_id = s.id AND sc.source_active = 1) AS credits
FROM subject s WHERE s.type = 2 AND s.nsfw = 0 ORDER BY s.id;
```

对照（新库，对应迁移后 indexer `load_subject` 的 credits 子查询）：

```sql
SELECT s.id,
  (SELECT GROUP_CONCAT(CONCAT(spc.role, '：', IFNULL(p.name, spc.name))
          ORDER BY spc.sort_order, IFNULL(p.name, spc.name) SEPARATOR '\n')
     FROM subject_person_credit spc LEFT JOIN person p ON p.id = spc.person_id
    WHERE spc.subject_id = s.id AND spc.source_active = 1) AS credits
FROM subject s WHERE s.type = 2 AND s.nsfw = 0 ORDER BY s.id;
```

预期差异：只在 `person_id` 解析成功但 `person.name` 与旧 `subject_credit.name` 不一致的行上出现。逐条 diff 后需人工确认这些差异都是"上游改名"而非迁移丢失。

## 8. 回滚

1. `mysql ... < backup/$STAMP/full-db.sql`（整库还原）
2. business / agent 镜像回退到迁移前版本
3. Redis 侧无需清理：新键均为 `animetracker:` 前缀（`animetracker:import:lock`、`animetracker:import:{record_id}:done`），旧代码不读这些键，无冲突

## 9. 遗留项（不阻塞迁移，但需知悉）

1. **progress key 无 TTL**：`animetracker:import:{record_id}:done` 仅在正常终态被 DEL。importer 被 SIGKILL 时残留；`--resume` 复用同一 `record_id`，故 `main()` 在拿到导入锁后会先 `_clear_done(record_id)` 清零残留，避免终态 `subject_count` 虚高。
2. **`subject_count` 语义未变**：终态值与迁移前等价——旧代码写 `run_full()` 返回值（= 主批次 + 追赶批次成功数，`base_done` 已被减去），新代码写 Redis 累计成功数，两者同一口径。Redis 不可用时回退到本次运行的内存计数，不会退化成 0。
3. **`operation_log` 列注释**：`db-schema.sql` 与 `OperationLog.java` 的 javadoc 已从 action 列表移除 `SUBJECT_CREATE/SUBJECT_UPDATE`（新库与新代码取当前口径）。**存量库的列注释仍是旧的**——注释是纯元数据，不影响读写行为；若要对齐可手工执行（可选，不重建表）：
   ```sql
   ALTER TABLE operation_log MODIFY COLUMN action varchar(32) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci NOT NULL COMMENT '动作: LOGIN/LOGOUT/REGISTER/SUBJECT_DELETE/ROLE_CHANGE/IMPORT_RUN';
   ```
   历史行仍含这两个 action，前端 `action` 筛选是自由文本输入，不受影响。
4. **`--queue legacy` 仍保留**：`rag_index_job` 表已并入 `job`（`type='RAG_INDEX'`），但 `jobs/indexer --queue legacy|search|both` 三种消费模式语义不变，默认 `both`。旧链路何时收窄为 `search` 仍未定。
