# 数据与存储规范

## 事实来源

- MySQL 8 表结构唯一事实来源是 `docs/database/db-schema.sql`；当前终态 **20 张表**（任务 10-04-db-schema-slim，23→20，2026-10-04 收尾）。
- Spring 配置为 `spring.sql.init.mode: never`，当前不使用 Flyway/Liquibase。
- 表结构变更必须同步 Schema、Java Entity/Mapper、Python importer/indexer、OpenAPI 与前端共享类型。
- Redis 与 MinIO 是辅助存储，不能替代 MySQL 中的用户、番剧和收藏权威数据。
- RAG 发布例外：Redis Vector Set 只承担语义索引数据平面；MySQL `search_index_release` 是唯一 active release 事实。索引发布、24 小时灰度和回滚的完整代码契约见 [RAG 检索与版本发布契约](./rag-retrieval-contract.md)。

## DDL 与存量库安全门禁

### 1. Scope / Trigger

- 触发条件：初始化数据库、修改 `docs/database/db-schema.sql`，或需要在已有环境变更表结构。
- 当前仓库没有 Flyway/Liquibase；`spring.sql.init.mode: never`，因此 Schema 文件不是自动迁移器。

### 2. Signatures

- 全新空库初始化入口：`mysql ... < docs/database/db-schema.sql`。
- 存量库变更入口：必须由评审确认的前向 `ALTER`/回填步骤；不得把完整 Schema 文件当作升级脚本。
- 仓库当前不提供前向迁移脚本：`docs/database/` 下只有 `db-schema.sql`。历史上的 `migration-002-rag-entities.sql`、`migration-003-search-projection.sql` 已随提交 `f9b8fd39` 删除，不得再引用或执行。
- 历史迁移脚本曾用 `INFORMATION_SCHEMA.COLUMNS` + `PREPARE` 条件执行旧表兼容列变更，因为 MySQL 8.4 不支持 `ALTER TABLE ... ADD COLUMN IF NOT EXISTS`；该手法仍是新增前向迁移时的既有参考实现。

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
- MySQL 版本门禁：至少在项目声明的 MySQL 8.0+ 实际小版本（当前验证为 8.4.9）执行空库初始化并断言不出现 1064。历史门禁还包含“旧表前向迁移、二次迁移、`source_active` 三列与 9 张新增表”，但那些断言依赖已删除的 `migration-002`，当前无法复现，不得沿用其结果；`source_active` 如今在 `db-schema.sql` 中出现 17 处，不再只有三列。

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

## Scenario: 主创关系单表（subject_person_credit）

### 1. Scope / Trigger

- 触发：新增或维护 `person`/`subject_person_credit` 主创关系。
- 历史：旧兼容表 `subject_credit` 已于任务 10-04-db-schema-slim 合并删除，不得再引用。

### 2. Signatures

- 单表：`subject_person_credit(subject_id, person_id NULL, name NULL, credit_type, role, relation, sort_order, source_active)`。
- `person_id` 已解析时填 FK 且 `name` 为 NULL；未解析时 `person_id` 为 NULL 且 `name` 存占位名。

### 3. Contracts

- 所有主创关系只写 `subject_person_credit`；importer 是**唯一写入方**（`jobs/importer/repository.py:_upsert_subject_person_credits`）。
- 未解析到 `person` 表的 credit 写 `name` 占位行（`person_id=NULL`），**当前没有任何代码会把占位行提升为 FK 行**。占位行靠下一次 full import 自愈：那时 `person_ids` 已有映射，写入的 FK 行 `dedup_key` 不同，与占位行并存；而函数开头的 `UPDATE ... SET source_active=0` 会把旧占位行标为失效。因此同一 credit 可能短暂存在一条 inactive 占位行 + 一条 active FK 行，摘要在 `source_active=1` 过滤下只读后者。**不要再假设存在 backfill 回填路径。**
- 去重依赖 `dedup_key char(64)` 生成列（`sha2(concat_ws('#', subject_id, role, ifnull(person_id,0), ifnull(name,'')), 256)`，VIRTUAL）+ 唯一索引 `uk_subject_person_credit`。用 sha2 定长哈希而非明文拼接，是为避免生成列长度受拼接字段隐式约束（提交 `6297ce21`）；改拼接字段时必须同步改生成列表达式。
- `credit_type` 只能使用 `PERSON` 或 `ORGANIZATION`；Python 侧由 `CreditType` 枚举（`app/entities/enums.py`）约束取值，但**没有运行时校验拒绝非法写入**——`SubjectPersonCredit` 是无 `__post_init__` 的 frozen dataclass。
- Profile/索引摘要读取走单表 `LEFT JOIN person`：`IFNULL(person.name, spc.name)` 取展示名。注意 `tests/evals/generate_golden_cases.py` 生成 person 关系用例时用的是 `JOIN person`（INNER），会自然排除占位行——这是有意的（用例需要 person 名）。

### 4. Validation & Error Matrix

| 条件 | 处理 |
|---|---|
| `credit_type` 非 `PERSON\|ORGANIZATION` | 无运行时拦截；靠 `CreditType` 枚举与 code review 保证 |
| `person_id` 与 `name` 同时非 NULL 或同时 NULL | 无运行时拦截；importer 赋值处（`local_id is None` 分支）保证恰好其一非 NULL |
| 引用已删除的 `subject_credit` | 阻止发布，改为单表查询 |

### 5. Good/Base/Bad Cases

- Good：已解析 credit 写 `person_id` FK，摘要经 `LEFT JOIN person` 读名。
- Base：未解析 credit 写 `name` 占位行，摘要读 `IFNULL(person.name, spc.name)`。
- Bad：新建第二张 credit 表，或把 `credit_type=ORGANIZATION` 写成 `relation=MAIN`。

### 6. Tests Required

- `tests/entities/test_credit_mapping.py`：断言占位行（`person_id=None` + `name`）与 FK 行（`person_id` + `name=None`）两种构造形态。
- 待补：目前**没有**覆盖摘要 SQL（`IFNULL(person.name, spc.name)` 两种行产出一致 `role：name`）的测试，也**没有**覆盖"二次导入把占位行标 inactive + 写入 FK 行"的测试。改动 credit 写路径时应补上。

### 7. Wrong vs Correct

#### Wrong

```text
为兼容旧查询新建 subject_credit 影子表，或双写两张 credit 表。
```

#### Correct

```text
单表写入；占位行与 FK 行由 credit_type/person_id/name 三列表达，摘要单查询兼容两种行。
```

## Python 离线任务

- importer 将标准化和持久化分开，参考 `jobs/importer/normalize.py` 与 `repository.py`。
- 导入用 Redis 锁保证单实例（键 `animetracker:import:lock`，`SET NX EX` 获取 + 周期续期，释放走 WATCH+MULTI 的 compare-and-del）。**释放与续期不要改用 Lua**：WATCH+MULTI 语义等价，且免去 `lupa` 依赖、fakeredis 无 Lua 时也能测（见 `app/adapters/redis/import_lock.py` 模块 docstring）。导入同时维护 import record、进度和 PID 文件；运行中进度计数在 Redis（`animetracker:import:{record_id}:done`），终态一次性回写 import_record。
- 任务队列统一在 `job` 表，靠 `type` 区分三类：`ENTITY_DETAIL`（backfill 消费）、`SEARCH_INDEX`（indexer 通用双投影）、`RAG_INDEX`（indexer 旧 Subject 兼容队列）。禁止再引入独立的 job 队列表。三表合并理由（任务 10-04）：旧 `entity_detail_job`/`search_index_job`/`rag_index_job` schema 约 90% 雷同（status/attempts/next_retry_at/last_error），差异列（embedding 元组、source_id、checkpoint_json）均非查询条件，折叠进 `payload_json` 后单表可承载。
- **针对 `job` 表的每条 SQL 必须带 `type=` 或 `id=` 作用域**。只按 `status` / `next_retry_at` 过滤会跨队列误伤其他 type 的任务，这是本表最易犯的错误。
- **claim 谓词里的 `next_retry_at IS NULL` 按 type 而异，不要互相「统一」**。合并前 `RAG_INDEX` 靠 `status='RETRY'` vs `'FAILED'` 区分可重试/终态；折叠成单 `FAILED` 后，这个区分必须由 `next_retry_at` 承担：

  | type | claim 谓词的 FAILED 分支 | 终态表示 |
  |---|---|---|
  | `RAG_INDEX` | `next_retry_at <= :now`（**不含** `IS NULL`） | `FAILED` + `next_retry_at NULL` |
  | `SEARCH_INDEX` | `next_retry_at <= :now`（**不含** `IS NULL`） | `ABANDONED` |
  | `ENTITY_DETAIL` | `(next_retry_at IS NULL OR next_retry_at <= :now)`（**必须保留 `IS NULL`**） | `ABANDONED` |

  `RAG_INDEX` / `SEARCH_INDEX` 若把 `IS NULL` 也算作可领，`mark_failed` 与退避耗尽的 `mark_retry` 会被当成「立即可领」，非可重试错误将无退避地重试到 `max_attempts`（白烧 embedding 配额）。回归护栏：`tests/jobs/indexer/test_rag_job_failure_semantics.py`。

  反过来，`ENTITY_DETAIL` **必须**放行 `IS NULL`：`backfill/repository.py:resume()` 用 `next_retry_at=NULL` 表示「解除暂停、立即可领」（`pause()` 写的是远期时间）。若照 RAG 的写法去掉 `IS NULL`，被 `resume()` 清成 NULL 的行将永远无法再被认领。
- 新增终态时优先用独立状态（`ABANDONED` / `TOMBSTONE`）而不是复用 `FAILED`+`NULL`，避免与 `next_retry_at` 语义纠缠。
- 每条 `SEARCH_INDEX` 任务必须成组绑定 `index_version`、`profile_version` 与 `content_hash`；`profile_version` 与 embedding 元组存 `payload_json`，`content_hash` 提升为列用于幂等比对。MySQL lexical shadow 和 Redis Vector Set 任一写入失败都不得确认任务完成，tombstone 使用 `VREM`。`jobs/indexer/gate.py` 缺报告时必须 fail closed。
- 清理先生成计划并校验确认摘要，参考 `jobs/importer/cleanup.py`。
- RAG 旧投影清理必须等待回滚窗口结束并取得独立确认；不能以 release 激活或灰度通过替代删除确认。
- CLI 失败路径必须释放锁、关闭会话并返回非零退出码。

## Redis 与 MinIO

- Business Redis 键按职责归属：认证键在 `auth/constant/AuthRedisKeys.java`，限流键在 `infrastructure/ratelimit/RateLimitKeys.java`，账户业务键在 `client/constant/ClientRedisKeys.java`，收藏进度键在 `client/constant/CollectionRedisKeys.java`。
- Agent Redis 适配器位于 `app/adapters/redis`，承载聊天、待确认动作、托管配置与可选 RAG。
- 待确认动作当前 TTL 为 600 秒，修改时同步提示、存储和执行语义。
- Business 对象存储走 `ImageStorageGateway`；实现位于 `infrastructure/storage/minio`。
- importer 的公开封面桶与私有原始桶必须使用不同名称。

## Scenario: MinIO 图片公开 URL 与反代前缀

### 1. Scope / Trigger

- 触发：修改 `jobs/importer/storage.py::ObjectStorage._public_url`、`jobs/importer/quality.py::canonical_cover_object_path`、`infrastructure/storage/minio/MinioImageStorageGateway.publicUrl`，或新增 `MINIO_PUBLIC_BASE_URL` / `minio.public-base-url`（env `AT_MINIO_PUBLIC_BASE_URL`）。
- 目的：SDK 端点（如 `127.0.0.1:9000`）只 bind 环回，把 endpoint 直接拼进 `subject.image`/头像 URL 会让浏览器请求用户本机 9000 → 图片全部 404。封面/头像必须走浏览器可达的反向代理前缀。

### 2. Signatures

- Python：`ObjectStorage._public_url(object_name: str) -> str`（`jobs/importer/storage.py`）。
- Java：`MinioImageStorageGateway.publicUrl(String objectName) -> String`（私有方法，返回给客户端）。
- 反解（质量检查必须能还原对象名）：`canonical_cover_object_path(image: object, minio) -> str | None`（`jobs/importer/quality.py`）。
- 配置属性：`ObjectStorage.public_base_url`（property，来自 `MINIO_PUBLIC_BASE_URL`，`.rstrip("/")`）；`MinioProperties.publicBaseUrl`（getter/setter，来自 `minio.public-base-url`）。

### 3. Contracts

- `MINIO_PUBLIC_BASE_URL`（Python，`.env`）/ `minio.public-base-url`（Java，`application.yml`，env `AT_MINIO_PUBLIC_BASE_URL`）是**浏览器访问前缀**，推荐根相对路径 `/media`，也可写绝对 URL。
- 前缀**已映射到桶根**（nginx `location /media/ { proxy_pass http://127.0.0.1:9000/<bucket>/; }`），故拼接公开 URL 时**不再重复拼接桶名**：`{prefix}/{object_name}` → `/media/covers/244.jpg`。
- 前缀留空时退回 endpoint 拼接 `http://{endpoint}/{bucket}/{object_name}`，保持旧部署行为；此形态仅供 SDK 与浏览器同机的本地开发。
- 用相对路径使主机/IP/域名变更无需改存量数据；`:80` 与 `:8081` 两 nginx server 块同源可用，需各配一条 `location /media/`。
- `subject.image` / `user.avatar` 存的就是公开 URL 字符串，前端直接 `<img src={s.image}>`，不拼接。

### 4. Validation & Error Matrix

| 条件 | 必须行为 |
|---|---|
| 前缀已配置 | 公开 URL = `{prefix}/{object_name}`，**不含桶名** |
| 前缀未配置 | 退回 `{scheme}://{endpoint}/{bucket}/{object_name}`（旧行为） |
| 前缀含末尾 `/` | 入库前 `.rstrip("/")`，避免双斜杠 |
| 公开 URL 经质量检查反解 | 前缀形态按前缀匹配；endpoint 形态按 netloc+bucket 匹配；两者并存期都必须还原出 `covers/<id>.jpg` |
| 反解结果非 `covers/` 目录、含 `..`、含 `://`、或前缀不匹配 | 返回 `None`，不得当作 MinIO 对象名，防止误删 |

### 5. Good/Base/Bad Cases

- Good：`MINIO_PUBLIC_BASE_URL=/media`，封面入库 `/media/covers/244.jpg`，浏览器经 nginx 反代命中 MinIO，质量检查还原 `covers/244.jpg`。
- Base：本地开发不配前缀，URL 用 `http://localhost:9000/anime-tracker/covers/x.jpg`，SDK 与浏览器同机可用。
- Bad：前缀拼进桶名生成 `/media/anime-tracker/covers/...`（nginx 已映射桶根 → 404），或 endpoint 直连 `http://127.0.0.1:9000/...`（浏览器不可达）。

### 6. Tests Required

- `tests/jobs/importer/test_storage_public_url.py`：生成 `_public_url` 与反解 `canonical_cover_object_path` 必须同一契约（前缀形态 + 根相对路径形态 round-trip）；留空时退回 endpoint；绝对/相对前缀并存时都能识别。
- `MinioGatewayTest`（business）：`uploadUsesPublicBaseUrlWhenConfigured` 断言反代前缀形态、无桶名重复、无双斜杠。
- 前端：无需单测；仅需确认 `<img src>` 对相对路径可用。

### 7. Wrong vs Correct

#### Wrong

```python
# 把 SDK 内网端点直接拼进公开 URL；或公开 URL 重复拼桶名
return f"{scheme}://{self._endpoint}/{self._bucket}/{object_name}"
# 前缀形态却拼了桶名：/media/anime-tracker/covers/244.jpg → nginx 已映射桶根 → 404
```

#### Correct

```python
# 前缀已指向桶根，只拼 object_name；留空退回 endpoint 保持旧行为
if self._public_base_url:
    return f"{self._public_base_url}/{object_name}"
return f"{scheme}://{endpoint}/{self._bucket}/{object_name}"
```

> **Warning**: `canonical_cover_object_path` 只处理 `covers/` 目录的反解。把前缀公开 URL 入库前必须保证它能被该函数还原，否则质量检查会把所有封面判为 `UNREFERENCED_OBJECT`，随后的 cleanup 将删除全部封面对象。

> **Warning**: 代码先改后部署有窗口期。运行中的 importer 进程持有旧内存代码，会继续写入旧 endpoint URL；存量行需用幂等前向 SQL 改写为 `/media/...`（只匹配旧前缀 `http://{endpoint}/{bucket}/%`，替换为 `/media/<object>`），且应在导入结束后**再次**执行以覆盖窗口期新写入的行。该 SQL 属服务器本地部署件（`docs/deploy/` 已不入库），不在仓库中。

## Scenario: RAG 词法投影与发布指针

### 1. Scope / Trigger

- 触发：新增 `search_document`/`search_index_release`、MySQL FULLTEXT 词法召回或索引版本发布。

### 2. Signatures

- `search_document(entity_kind, entity_id, index_version, profile_version, title, aliases, lexical_text, content_hash, source_active, source_fetched_at)`。
- `search_index_release(index_version, profile_version, status, activated_at, retired_at, active_slot)`。
- 空库入口：`docs/database/db-schema.sql`；存量库前向迁移脚本已移除，当前无独立迁移入口，变更需由评审确认后手工执行 `ALTER`/回填。

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
| 初始化 Schema 用于非空库 | 禁止执行（全量 DDL 会 DROP 用户表），改走手工 ALTER 或重建流程评审 |

### 5. Good / Base / Bad Cases

- Good：先迁移投影表，再由 indexer 写入同一版本，gate 通过后在事务中切换 release。
- Base：旧版本保留到回滚窗口结束，清理作为独立运维操作。
- Bad：把 `db-schema.sql` 当升级脚本，或让 Redis key 充当 active release 事实。

### 6. Tests Required

- DDL：MySQL 8.4 空库执行 `db-schema.sql` 成功，断言 FULLTEXT、唯一键和生成列存在。（迁移脚本已移除，其二次执行断言不可复现。）
- Mapper：断言 `MATCH ... AGAINST` 绑定参数和 `indexVersion` 过滤。
- Service：断言无 active release 返回 503，成功响应包含版本和候选排名。

### 7. Wrong vs Correct

#### Wrong

```sql
ALTER TABLE search_document ADD COLUMN IF NOT EXISTS lexical_text TEXT;
```

#### Correct

```text
存量库结构不一致时先检查 INFORMATION_SCHEMA，再由评审决定 ALTER/回填/回滚；仓库当前不提供前向迁移脚本。
```

## 运维注意

- **代理 fake-IP 劫持**：Clash fake-IP 模式会轮流劫持 `dashscope`（embedding）与 `bgm.tv`（数据源）域名，导致 importer/indexer/backfill 随机超时。绕过方式：Python 进程显式设 `HTTPS_PROXY=http://127.0.0.1:7897` 走真实代理。backfill 多进程并发时注意 `claim_batch` 的 lease 回收 UPDATE 与 `SKIP LOCKED` 冲突死锁（任务 10-04 实测）。
- **backlog：索引增量补跑**：2026-10-05 recent 增量导入 101 条 COMPLETED + backfill 增量清零后，索引增量（SEARCH_INDEX 8937 PENDING + 203 FAILED 可重试 / RAG_INDEX 80 PENDING）因 fake-IP 网络受限被决定跳过。网络稳定后执行 `python -m jobs.indexer.main --index-version v1` 接上；执行前先 `--limit 20` 验证链路（FAILED 任务会自动重领）。

## 常见错误

- 只改 ORM 或只改 Schema，造成运行时字段漂移。
- XML 拼接未校验字符串而不是使用参数绑定。
- MySQL 8.4 中 `character` 是保留字；Python/SQLAlchemy、MyBatis XML 和迁移 SQL 引用该表时必须写成 `` `character` ``，并为索引、回填查询增加 SQL 引用回归断言。
- 不要笼统假设所有 Java `Long` 都映射为前端 `string`；必须按领域核对 DTO/VO、OpenAPI 与 shared 类型的实际契约。
- 索引发布时删除旧版本，导致无法回滚。
