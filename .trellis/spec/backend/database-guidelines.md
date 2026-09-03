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

### 3. Contracts

- `db-schema.sql` 含 `DROP TABLE IF EXISTS`，只允许用于明确确认的全新空库。
- 任何非空库执行前必须完成可恢复备份，并记录备份位置、影响表和回滚方式。
- 字段或索引变更必须定义：前向 DDL、数据回填、旧新版本兼容窗口、应用切换顺序和回滚路径。
- 当前不支持在线升级时，必须把它写成显式产品/运维限制，不得暗示可安全复用初始化脚本。

### 4. Validation & Error Matrix

| 条件 | 处理 |
|---|---|
| 新环境且确认无业务表/数据 | 可执行初始化 Schema；执行后核对表数量、关键索引和外键 |
| 检测到任意业务表或无法确认环境为空 | 禁止执行初始化 Schema；转为存量库迁移评审 |
| 需要删除/重命名字段 | 先备份，采用兼容字段/回填/切换顺序；没有回滚计划则拒绝 |
| Schema 与 Entity/Mapper/importer/OpenAPI 不一致 | 先修复事实来源和映射，禁止只执行其中一层 |

### 5. Good / Base / Bad Cases

- Good：空库初始化后运行映射检查，并保留备份/日志记录。
- Base：存量库使用经过评审的 `ALTER` 和回填步骤，应用先兼容旧字段再切换。
- Bad：为“重置开发环境”直接对未知数据库执行带 `DROP TABLE` 的完整 Schema。

### 6. Tests Required

- 初始化检查：在临时空库执行 Schema，断言关键表、索引和外键存在。
- 迁移检查：在包含旧数据的临时库执行前向 DDL 与回填，断言旧数据可读、新旧应用兼容。
- 回滚演练：验证备份可恢复，且失败步骤不会留下不可解释的半迁移状态。

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

## Spring / MyBatis

- 单表 CRUD 优先使用 MyBatis-Plus `BaseMapper`；复杂联表和动态条件写在 `resources/mapper/*.xml`。
- Mapper 参数使用 `@Param` 命名，XML 使用 `#{...}` 绑定。参考 `CollectionMapper.java` 与 `CollectionMapper.xml`。
- 分页统一返回 `PageResult<T>{content,total,page,size}`，不要把 MyBatis `Page` 暴露给 Controller。
- 多步写入在 Service 声明事务；每项独立提交可参考 `CollectionProgressItemExecutor` 的 `REQUIRES_NEW`。
- 并发幂等写入依赖唯一约束并处理冲突，参考 `CollectionServiceImpl.addToWishlistIfAbsent`。

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

## 常见错误

- 只改 ORM 或只改 Schema，造成运行时字段漂移。
- XML 拼接未校验字符串而不是使用参数绑定。
- 不要笼统假设所有 Java `Long` 都映射为前端 `string`；必须按领域核对 DTO/VO、OpenAPI 与 shared 类型的实际契约。
- 索引发布时删除旧版本，导致无法回滚。
