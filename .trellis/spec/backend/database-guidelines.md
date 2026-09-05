# 数据与存储规范

## 事实来源

- MySQL 8 表结构唯一事实来源是 `docs/database/db-schema.sql`。
- Spring 配置为 `spring.sql.init.mode: never`，当前不使用 Flyway/Liquibase。
- 表结构变更必须同步 Schema、Java Entity/Mapper、Python importer/indexer、OpenAPI 与前端共享类型。
- Redis 与 MinIO 是辅助存储，不能替代 MySQL 中的用户、番剧和收藏权威数据。

## DDL 与存量库安全门禁

### 1. Scope / Trigger

- 触发条件：初始化数据库、修改 `docs/database/db-schema.sql`，或需要在已有环境变更表结构。
- 当前仓库没有 Flyway/Liquibase；`spring.sql.init.mode: never`，因此 Schema 文件不是自动迁移器。

### 2. Signatures

- 全新空库初始化入口：`mysql ... < docs/database/db-schema.sql`。
- 存量库变更入口：必须由评审确认的前向 `ALTER`/回填步骤；不得把完整 Schema 文件当作升级脚本。
- `docs/database/migration-002-rag-entities.sql` 的旧表兼容列变更使用 `INFORMATION_SCHEMA.COLUMNS` + `PREPARE` 条件执行；MySQL 8.4 不支持 `ALTER TABLE ... ADD COLUMN IF NOT EXISTS`。

### 3. Contracts

- `db-schema.sql` 含 `DROP TABLE IF EXISTS`，只允许用于明确确认的全新空库。
- 任何非空库执行前必须完成可恢复备份，并记录备份位置、影响表和回滚方式。
- 字段或索引变更必须定义：前向 DDL、数据回填、旧新版本兼容窗口、应用切换顺序和回滚路径。
- 当前不支持在线升级时，必须把它写成显式产品/运维限制，不得暗示可安全复用初始化脚本。
- 前向迁移必须在 MySQL 8.4 上支持重复执行：已存在的列走空操作，不得依赖客户端忽略 1064 语法错误。

### 4. Validation & Error Matrix

| 条件 | 处理 |
|---|---|
| 新环境且确认无业务表/数据 | 可执行初始化 Schema；执行后核对表数量、关键索引和外键 |
| 检测到任意业务表或无法确认环境为空 | 禁止执行初始化 Schema；转为存量库迁移评审 |
| 需要删除/重命名字段 | 先备份，采用兼容字段/回填/切换顺序；没有回滚计划则拒绝 |
| Schema 与 Entity/Mapper/importer/OpenAPI 不一致 | 先修复事实来源和映射，禁止只执行其中一层 |
| MySQL 报 `1064` 指向 `ADD COLUMN IF NOT EXISTS` | 改用 `INFORMATION_SCHEMA.COLUMNS` 条件构造动态 `ALTER`，再在临时库重跑 |

### 5. Good / Base / Bad Cases

- Good：空库初始化后运行映射检查，并保留备份/日志记录。
- Base：存量库使用经过评审的 `ALTER` 和回填步骤，应用先兼容旧字段再切换。
- Bad：为“重置开发环境”直接对未知数据库执行带 `DROP TABLE` 的完整 Schema。
- Good：空库初始化后，模拟删除新表和旧兼容列，再执行前向迁移两次；两次都成功且关键表/列存在。

### 6. Tests Required

- 初始化检查：在临时空库执行 Schema，断言关键表、索引和外键存在。
- 迁移检查：在包含旧数据的临时库执行前向 DDL 与回填，断言旧数据可读、新旧应用兼容。
- 回滚演练：验证备份可恢复，且失败步骤不会留下不可解释的半迁移状态。
- MySQL 版本门禁：至少在项目声明的 MySQL 8.0+ 实际小版本（当前验证为 8.4.9）执行空库初始化、旧表前向迁移和二次迁移；断言不出现 1064，且检查 `source_active` 三列与 9 张新增表。

### 7. Wrong vs Correct

#### Wrong

```bash
# 未确认目标库是否为空
mysql -h "$DB_HOST" "$DB_NAME" < docs/database/db-schema.sql
```

#### Correct

```text
确认是全新空库 → 备份/记录环境 → 执行初始化 Schema → 核对表与索引
已有数据 → 先设计 ALTER/回填/兼容/回滚 → 评审通过后再执行
```

#### 迁移列的正确写法

```sql
-- Wrong: MySQL 8.4 会报 1064
ALTER TABLE subject_alias ADD COLUMN IF NOT EXISTS source_active tinyint NOT NULL;

-- Correct: 先检查，再动态执行；重复迁移时执行 SELECT 1 空操作
SET @sql = IF(
  (SELECT COUNT(*) FROM INFORMATION_SCHEMA.COLUMNS
   WHERE TABLE_SCHEMA = DATABASE()
     AND TABLE_NAME = 'subject_alias'
     AND COLUMN_NAME = 'source_active') = 0,
  'ALTER TABLE subject_alias ADD COLUMN source_active tinyint NOT NULL',
  'SELECT 1'
);
PREPARE stmt FROM @sql;
EXECUTE stmt;
DEALLOCATE PREPARE stmt;
```

## Spring / MyBatis

- 单表 CRUD 优先使用 MyBatis-Plus `BaseMapper`；复杂联表和动态条件写在 `resources/mapper/*.xml`。
- Mapper 参数使用 `@Param` 命名，XML 使用 `#{...}` 绑定。参考 `CollectionMapper.java` 与 `CollectionMapper.xml`。
- MySQL 8.4 默认 `ONLY_FULL_GROUP_BY` 下，禁止在 `SELECT DISTINCT` 查询中按未出现在投影中的字段排序；需要去重并按评分排序时使用 `SELECT` + `GROUP BY`（将排序字段一并分组），例如 `GROUP BY s.id, s.score ORDER BY s.score DESC, s.id ASC`。涉及实体扩展查询的 SQL 必须有 MySQL 8.4 回归断言，避免本地宽松模式掩盖 3065 错误。
- 分页统一返回 `PageResult<T>{content,total,page,size}`，不要把 MyBatis `Page` 暴露给 Controller。
- 多步写入在 Service 声明事务；每项独立提交可参考 `CollectionProgressItemExecutor` 的 `REQUIRES_NEW`。
- 并发幂等写入依赖唯一约束并处理冲突，参考 `CollectionServiceImpl.addToWishlistIfAbsent`。

## Scenario: 新旧主创关系映射兼容

### 1. Scope / Trigger

- 触发：新增 `person`/`subject_person_credit` 关系，或维护已有 `subject_credit` 存量数据。

### 2. Signatures

- 新关系表：`subject_person_credit(subject_id, person_id, role, relation, source_active)`。
- 旧兼容表：`subject_credit(subject_id, bangumi_person_id, name, role, credit_type, source_active)`。

### 3. Contracts

- 新导入关系写入 `subject_person_credit`；旧表只保留兼容读取窗口。
- `credit_type` 只能使用 `PERSON` 或 `ORGANIZATION`；Java `SubjectCredit` 与 Python `CreditType` 必须保持相同字面值。
- 旧表读取继续使用参数化 SQL，不得因为新增关系表而删除或改写旧查询语义。

### 4. Validation & Error Matrix

| 条件 | 处理 |
|---|---|
| 新实体/关系查询 | 使用新关系表和本地外键 ID |
| 存量旧主创读取 | 保留 `subject_credit` 兼容路径 |
| `credit_type` 非 `PERSON|ORGANIZATION` | 拒绝写入并记录契约错误 |
| 新旧字段混写 | 阻止发布，先补齐 Entity/枚举/测试 |

### 5. Good/Base/Bad Cases

- Good：新关系使用 `subject_person_credit`，旧报表仍可读取 `subject_credit`。
- Base：仅需要旧数据展示时，通过参数化 SQL 读取旧表。
- Bad：把 `subject_credit.credit_type` 的 `ORGANIZATION` 写成新关系的 `relation=MAIN`。

### 6. Tests Required

- Java 编译/映射检查：`SubjectCredit` 的表名和字段映射存在。
- Python 单测：`CreditType` 仅接受两个数据库字面值，`SubjectCredit` 可实例化。
- 导入器 SQL 契约测试：旧 `subject_credit` 读取路径仍存在，新关系写入不替换旧表查询。

### 7. Wrong vs Correct

#### Wrong

```text
把旧 subject_credit 行直接当作 subject_person_credit，或删除旧表读取以“清理重复模型”。
```

#### Correct

```text
新事实写 subject_person_credit；旧 subject_credit 保留只读兼容契约，待独立迁移任务确认后再移除。
```

## Python 离线任务

- importer 将标准化和持久化分开，参考 `jobs/importer/normalize.py` 与 `repository.py`。
- 导入用 MySQL `GET_LOCK` 保证单实例，并维护 import record、进度和 PID 文件。
- indexer 使用 `rag_index_job` 与版本化 Redis 索引；`jobs/indexer/gate.py` 缺报告时必须 fail closed。
- 清理先生成计划并校验确认摘要，参考 `jobs/importer/cleanup.py`。
- CLI 失败路径必须释放锁、关闭会话并返回非零退出码。

## Redis 与 MinIO

- Business Redis 键集中在 `common/constant/RedisKeys.java`。
- Agent Redis 适配器位于 `app/adapters/redis`，承载聊天、待确认动作、托管配置与可选 RAG。
- 待确认动作当前 TTL 为 600 秒，修改时同步提示、存储和执行语义。
- Business 对象存储走 `ImageStorageGateway`；实现位于 `app/infrastructure/storage/minio`。
- importer 的公开封面桶与私有原始桶必须使用不同名称。

## Scenario: RAG 词法投影与发布指针

### 1. Scope / Trigger

- 触发：新增 `search_document`/`search_index_release`、MySQL FULLTEXT 词法召回或索引版本发布。

### 2. Signatures

- `search_document(entity_kind, entity_id, index_version, profile_version, title, aliases, lexical_text, content_hash, source_active, source_fetched_at)`。
- `search_index_release(index_version, profile_version, status, activated_at, retired_at, active_slot)`。
- 存量库入口：`docs/database/migration-003-search-projection.sql`；空库入口：`docs/database/db-schema.sql`。

### 3. Contracts

- `search_document` 是可按 `index_version` 重建的 InnoDB 投影，不是事实来源；全文索引使用 `WITH PARSER ngram`。
- `search_index_release.active_slot` 是由 `status='ACTIVE'` 派生的生成列，唯一索引保证最多一个 active release。
- 前向迁移只使用 `CREATE TABLE IF NOT EXISTS`；同名但结构不一致时必须人工检查，不得假装迁移完成。
- MySQL lexical API 返回 `indexVersion`；Agent 用同版本查询 Redis Vector Set。

### 4. Validation & Error Matrix

| 条件 | 必须行为 |
|---|---|
| 存量库未执行迁移 | Business lexical API 失败或返回 503，不伪造候选 |
| 无 active release | 返回 503，Agent 降级到既有 Business 搜索 |
| 第二条 ACTIVE release | 唯一约束拒绝写入，保留原 active |
| 初始化 Schema 用于非空库 | 禁止执行，改走前向迁移评审 |

### 5. Good / Base / Bad Cases

- Good：先迁移投影表，再由 indexer 写入同一版本，gate 通过后在事务中切换 release。
- Base：旧版本保留到回滚窗口结束，清理作为独立运维操作。
- Bad：把 `db-schema.sql` 当升级脚本，或让 Redis key 充当 active release 事实。

### 6. Tests Required

- DDL：MySQL 8.4 空库初始化和迁移脚本二次执行均成功，断言 FULLTEXT、唯一键和生成列存在。
- Mapper：断言 `MATCH ... AGAINST` 绑定参数和 `indexVersion` 过滤。
- Service：断言无 active release 返回 503，成功响应包含版本和候选排名。

### 7. Wrong vs Correct

#### Wrong

```sql
ALTER TABLE search_document ADD COLUMN IF NOT EXISTS lexical_text TEXT;
```

#### Correct

```text
存量库执行 migration-003；结构不一致先检查 INFORMATION_SCHEMA，再由评审决定 ALTER/回填/回滚。
```

## 常见错误

- 只改 ORM 或只改 Schema，造成运行时字段漂移。
- XML 拼接未校验字符串而不是使用参数绑定。
- 不要笼统假设所有 Java `Long` 都映射为前端 `string`；必须按领域核对 DTO/VO、OpenAPI 与 shared 类型的实际契约。
- 索引发布时删除旧版本，导致无法回滚。
