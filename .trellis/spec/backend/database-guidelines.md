# 数据与存储规范

## 事实来源

- MySQL 8 表结构唯一事实来源是 `docs/database/db-schema.sql`。
- Spring 配置为 `spring.sql.init.mode: never`，当前不使用 Flyway/Liquibase。
- 表结构变更必须同步 Schema、Java Entity/Mapper、Python importer/indexer、OpenAPI 与前端共享类型。
- Redis 与 MinIO 是辅助存储，不能替代 MySQL 中的用户、番剧和收藏权威数据。

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
- Java `Long` ID 在前端改为 `number`，破坏大整数安全；现有跨层类型使用 `string`。
- 索引发布时删除旧版本，导致无法回滚。
