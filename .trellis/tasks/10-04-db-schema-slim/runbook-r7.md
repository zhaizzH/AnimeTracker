# R7 迁移 Runbook：23 表 → 20 表重建

> **用户已决定：本会话只产出 runbook，不执行。** 执行前必须有人工确认停机窗口。

## 0. 前置检查

| 项 | 检查方式 | 2026-10-04 实测 |
|---|---|---|
| `mysqldump` / `mysql` 客户端 | `which mysqldump mysql` | ❌ **不在 PATH**；实际位于 `C:\software\env\MySQL\MySQL Server 8.4\bin\` |
| 目标库可达 | `mysql ... -e "SELECT 1"` | ✅ MySQL 8.4.9 |
| Redis + Vector Set | `COMMAND INFO VADD/VSIM/VREM`（见下） | ✅ Redis 8.8.3，三个命令均可用 |
| Bangumi API | `GET https://api.bgm.tv/v0/subjects/8` | ✅ HTTP 200 |
| **DashScope（embedding）** | 见下 | ❌ **不可用**：`dashscope.aliyuncs.com` 被本机 VPN/代理的 fake-IP DNS 解析到 `198.18.0.19`（保留网段），TLS 握手 `UNEXPECTED_EOF`。索引器因此全部 `EMBEDDING_UNAVAILABLE` |
| 停机窗口 | 重建期间 business 写 `subject` 会与重灌冲突 | 待安排 |

**DashScope 连通性必须在 DROP 之前确认**——否则派生数据清空后重建不出检索投影：

```bash
python -c "import os,dashscope;from dotenv import load_dotenv;load_dotenv();\
print(dashscope.TextEmbedding.call(api_key=os.getenv('DASHSCOPE_API_KEY'),\
model='text-embedding-v4', input=['probe'], dimension=1024).status_code)"
# 期望 200。出现 SSLError/UNEXPECTED_EOF 时先修网络（proxy 放行 *.aliyuncs.com、
# 关闭该域的 fake-IP，或设置 HTTPS_PROXY），不要继续后面的步骤。
# 注意 dashscope SDK 把底层异常吞成 EmbeddingUnavailable，DB 里只会看到这个笼统错误码。
```

**Redis Vector Set 检查**（`FT._LIST` 是 RediSearch，不是 Vector Set，别用它判断）：

```bash
python -c "import os,redis;from dotenv import load_dotenv;load_dotenv();\
c=redis.Redis.from_url(os.getenv('RAG_REDIS_URL') or os.getenv('REDIS_URL'),decode_responses=True);\
print({k: bool(c.execute_command('COMMAND','INFO',k)) for k in ('VADD','VSIM','VREM')})"
```

工作目录约定：所有 `python -m jobs.*` 命令必须在 `backend/agent` 下执行（模块依赖 `app.*` 包）。

## 1. 备份（**唯一回滚依赖，未完成不得进入第 2 步**）

> ⚠️ **两端都必须显式指定字符集。** 本库的 `search_document.lexical_text` 等列含中日韩文本，
> 还原时若 mysql **客户端**未指定字符集，客户端会按本机默认字符集（Windows 上是 GBK/cp936）
> 解析输入流；UTF-8 多字节序列在 GBK 下错位，某个字节被当成 `\`，客户端随即把它解释为
> 自己的反斜杠命令，报出极具误导性的错误：
> - `ERROR 2005 (HY000) at line N: Unknown MySQL server host '<乱码>'`（`\r` = connect 命令）
> - `ERROR at line N: Unknown command '\''` / `Unknown command '\n'`
>
> 这类错误**看上去像备份损坏，实际备份完好**，只是还原命令少了一个参数。
> 2026-10-04 已在 MySQL 8.4.9 上实测确认：加 `--default-character-set=utf8mb4` 后
> 全库 23 表还原、逐表行数完全一致。

```bash
STAMP=$(date +%Y%m%d-%H%M%S)
mkdir -p backup/$STAMP

# 1a. 三张用户表（必须原样恢复）
mysqldump -h "$DB_HOST" -u "$DB_USER" -p"$DB_PASSWORD" \
  --single-transaction --set-gtid-purged=OFF --default-character-set=utf8mb4 \
  "$DB_NAME" user user_collection operation_log \
  > backup/$STAMP/user-tables.sql

# 1b. 整库逻辑备份（含派生表，用于兜底回滚）
mysqldump -h "$DB_HOST" -u "$DB_USER" -p"$DB_PASSWORD" \
  --single-transaction --set-gtid-purged=OFF --default-character-set=utf8mb4 --routines --triggers \
  "$DB_NAME" > backup/$STAMP/full-db.sql

# 1c. 迁移前基线计数（对账用，见第 7 节）
```

**备份后必须实测可还原**（只用文件大小/`grep` 校验是不够的——字符集问题正是这样漏掉的）：

```bash
CHK=anime_tracker_restore_check
mysql -h "$DB_HOST" -u "$DB_USER" -p"$DB_PASSWORD" \
  -e "DROP DATABASE IF EXISTS $CHK; CREATE DATABASE $CHK DEFAULT CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci"
mysql -h "$DB_HOST" -u "$DB_USER" -p"$DB_PASSWORD" --default-character-set=utf8mb4 \
  "$CHK" < backup/$STAMP/full-db.sql          # 必须 rc=0 且无 stderr
# 逐表比对源库与 $CHK 的 COUNT(*)；全部一致才算备份有效
mysql -h "$DB_HOST" -u "$DB_USER" -p"$DB_PASSWORD" -e "DROP DATABASE $CHK"
```

本机 `mysqldump` / `mysql` 不在 PATH，实际位于
`C:\software\env\MySQL\MySQL Server 8.4\bin\`。

## 2. 重建 schema

⚠️ 两个坑，都已在 2026-10-04 于 MySQL 8.4.9 实测踩到：

**坑 A：脚本要求空库，不能在存量库上直接跑。**
`db-schema.sql` 按字母序 `DROP TABLE`，`person`（第 335 行）排在 `person_alias`（第 394 行）之前。
在存量库上执行时，旧的 `person_alias` 仍以 FK 引用 `person`，`DROP TABLE person` 会报：
```
ERROR 3730 (HY000) at line 335: Cannot drop table 'person' referenced by a foreign key
constraint 'fk_person_alias_person' on table 'person_alias'.
```
`SET FOREIGN_KEY_CHECKS = 0`（脚本第一行就有）**不能**绕过这个限制。脚本中断后库处于半迁移状态
（20 张新表 + 未删干净的旧表），必须整库重建重来。

**坑 B：脚本含 `DROP TABLE IF EXISTS user / user_collection / operation_log`**，
整份执行会清空用户数据 —— 必须先完成第 1 节备份，并在第 3 步立即恢复。

```bash
# 正确做法：整库 DROP + CREATE（而不是在存量库上跑脚本）
mysql -h "$DB_HOST" -u "$DB_USER" -p"$DB_PASSWORD" \
  -e "DROP DATABASE IF EXISTS \`$DB_NAME\`; CREATE DATABASE \`$DB_NAME\` DEFAULT CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci"

mysql -h "$DB_HOST" -u "$DB_USER" -p"$DB_PASSWORD" --default-character-set=utf8mb4 \
  "$DB_NAME" < docs/database/db-schema.sql      # 必须 rc=0 且无 stderr

# 验收 AC1：应为 20 张
mysql -h "$DB_HOST" -u "$DB_USER" -p"$DB_PASSWORD" -N -e "SHOW TABLES" "$DB_NAME" | wc -l
```

期望的 20 张：
`character, character_actor, character_alias, episode, import_record, job, operation_log, person, person_alias, search_document, search_index_release, subject, subject_alias, subject_character, subject_meta_tag, subject_person_credit, subject_relation, subject_tag, user, user_collection`

确认已消失的 4 张：`subject_credit, entity_detail_job, search_index_job, rag_index_job`。

> 同时删除 `jobs/importer/importer.pid` 残留（进程已不存在时）；否则 Agent 侧 launcher 可能
> 仍认为有导入在跑，触发「永久 409」。

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
cd backend/agent
# 先用小 limit 验证链路（含真实 embedding 调用，先花几次再放量）
.venv/Scripts/python -m jobs.indexer.main --index-version v1 --limit 20
# 确认 search_document 有小量行、job 状态变为 COMPLETED 后，再去掉 --limit 放量

.venv/Scripts/python -m jobs.backfill.main --batch-size 5
```

`job` 表三种 type 分别由 importer（`ENTITY_DETAIL`/`SEARCH_INDEX`/`RAG_INDEX` 入队）、backfill（消费 `ENTITY_DETAIL`）、indexer（消费 `SEARCH_INDEX` 与 `RAG_INDEX`）驱动。
`--index-version` 沿用迁移前的版本号即可（实测迁移前为 `v1` / `subject-profile-v1`）。

**注意**：indexer 退出码 `1` 表示有终态失败，**不是**崩溃；但 shell 里若接了管道（如 `| tail`），`$?` 取的是管道的状态，别据此判断成败。用 `job` 表的分布判断：

```sql
SELECT type, status, COUNT(*) FROM job GROUP BY type, status;
SELECT last_error_code, COUNT(*) FROM job WHERE status='FAILED' GROUP BY last_error_code;
```

**Embedding 不可用时任务是可重试的**：`EMBEDDING_UNAVAILABLE` 会写 `attempts=1`（< `max_attempts=5`）并设置
`next_retry_at`，网络恢复后直接重跑 indexer 即可接上，**无需重新入队或重灌导入**。
2026-10-04 实测：网络不通时 18 个 `SEARCH_INDEX` + 20 个 `RAG_INDEX` 变为 `FAILED/attempts=1`，
`search_document` 保持 0 行，其余 5350 + 116 个任务仍为 `PENDING`。

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

**AC2 credit 摘要比对**

> ⚠️ **必须按 `bangumi_id` 关联，不能用 `subject.id`。** `subject.id` 是 AUTO_INCREMENT，重灌后按插入顺序重新分配：同一个 local id 在新旧库指向完全不同的番剧（实测中 `subject.id=1` 旧库是国产动画、新库是法国动画）。按 local id 比对会得到"131/136 全不一致"的假结果。
>
> 正确做法：把迁移前备份还原到一个临时库（如 `anime_tracker_before`），用 `bangumi_id` 做 join 键比对，比对完 DROP 掉。

基线（临时还原库，迁移前 indexer `load_subject` 的 credits 子查询）：

```sql
SELECT s.bangumi_id,
  (SELECT GROUP_CONCAT(CONCAT(sc.role, '：', sc.name)
          ORDER BY sc.sort_order, sc.name SEPARATOR '\n')
     FROM subject_credit sc
    WHERE sc.subject_id = s.id AND sc.source_active = 1) AS credits
FROM subject s WHERE s.type = 2 AND s.nsfw = 0;
```

对照（新库）：

```sql
SELECT s.bangumi_id,
  (SELECT GROUP_CONCAT(CONCAT(spc.role, '：', IFNULL(p.name, spc.name))
          ORDER BY spc.sort_order, IFNULL(p.name, spc.name) SEPARATOR '\n')
     FROM subject_person_credit spc LEFT JOIN person p ON p.id = spc.person_id
    WHERE spc.subject_id = s.id AND spc.source_active = 1) AS credits
FROM subject s WHERE s.type = 2 AND s.nsfw = 0;
```

**判读标准**：差异应只来自上游数据变化，即「新库是旧库的超集」。逐 ID 做集合差：
`仅旧有` 必须为 0（否则是迁移丢数）；`仅新有` 是上游新增职责，可接受。
2026-10-04 实测：98 个重叠 bangumi_id 中 97 个摘要逐字符一致，唯一差异的 `622288` 旧 146 条 / 新 150 条、`仅旧有=0`、`仅新有=4`（上游新增 `主题歌作曲/作词/编曲：polysha`、`背景美术：桒嶋壮志`）——即无丢失。

## 8. 回滚

```bash
# 必须带 --default-character-set=utf8mb4，否则会误报备份损坏（见第 1 节）
mysql -h "$DB_HOST" -u "$DB_USER" -p"$DB_PASSWORD" \
  --default-character-set=utf8mb4 "$DB_NAME" < backup/$STAMP/full-db.sql
```

1. 整库还原（命令见上；还原后同样逐表比对行数）
2. business / agent 镜像回退到迁移前版本
3. Redis 侧无需清理：新键均为 `animetracker:` 前缀（`animetracker:import:lock`、`animetracker:import:{record_id}:done`），旧代码不读这些键，无冲突

> 若只回滚用户数据：`mysql ... --default-character-set=utf8mb4 "$DB_NAME" < backup/$STAMP/user-tables.sql`。

## 9. 遗留项（不阻塞迁移，但需知悉）

1. **progress key 无 TTL**：`animetracker:import:{record_id}:done` 仅在正常终态被 DEL。importer 被 SIGKILL 时残留；`--resume` 复用同一 `record_id`，故 `main()` 在拿到导入锁后会先 `_clear_done(record_id)` 清零残留，避免终态 `subject_count` 虚高。
2. **`subject_count` 语义未变**：终态值与迁移前等价——旧代码写 `run_full()` 返回值（= 主批次 + 追赶批次成功数，`base_done` 已被减去），新代码写 Redis 累计成功数，两者同一口径。Redis 不可用时回退到本次运行的内存计数，不会退化成 0。
3. **`operation_log` 列注释**：`db-schema.sql` 与 `OperationLog.java` 的 javadoc 已从 action 列表移除 `SUBJECT_CREATE/SUBJECT_UPDATE`（新库与新代码取当前口径）。**存量库的列注释仍是旧的**——注释是纯元数据，不影响读写行为；若要对齐可手工执行（可选，不重建表）：
   ```sql
   ALTER TABLE operation_log MODIFY COLUMN action varchar(32) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci NOT NULL COMMENT '动作: LOGIN/LOGOUT/REGISTER/SUBJECT_DELETE/ROLE_CHANGE/IMPORT_RUN';
   ```
   历史行仍含这两个 action，前端 `action` 筛选是自由文本输入，不受影响。
4. **`--queue legacy` 仍保留**：`rag_index_job` 表已并入 `job`（`type='RAG_INDEX'`），但 `jobs/indexer --queue legacy|search|both` 三种消费模式语义不变，默认 `both`。旧链路何时收窄为 `search` 仍未定。
