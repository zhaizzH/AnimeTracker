# Phase 8 Spring Boot 启动验证报告

日期：2026-09-05

## 故障

启动日志在创建 MyBatis `SqlSessionFactory` 时失败：

```text
The alias 'Character' is already mapped to the value 'java.lang.Character'.
```

`mybatis-plus.type-aliases-package=top.zhaizz.pojo.entity` 会扫描业务实体。新增的 `top.zhaizz.pojo.entity.Character` 使用默认简单类名别名 `Character`，与 MyBatis 内置 `java.lang.Character` 别名冲突，随后连锁导致 `operationLogMapper` 和 `operationLogAspect` 创建失败。

## 修复

- 为 `top.zhaizz.pojo.entity.Character` 增加 `@Alias("BangumiCharacter")`。
- 保留 Java 类名和数据库表名 `character`，不改变 Mapper/XML 的全限定类名和业务 API。
- 增加 `MyBatisEntityAliasTest`，断言 `BangumiCharacter` 指向业务实体，内置 `Character` 仍指向 `java.lang.Character`。

## 验证

- `mvn -B clean test`：BUILD SUCCESS；Business 全部 **32 tests passed**（Client 20、App 12）。新增 SQL 兼容性回归测试覆盖三个实体扩展查询。
- Agent RAG/适配器测试：**82 passed**；质量复核全量 Agent：**226 passed**。
- Agent 健康路由：`GET /api/client/agent/health` 返回 HTTP 200；根路径 `/health` 不是有效路由。

## 仍未通过的 Phase 8 门禁

- Business `127.0.0.1:8080` 已使用 reactor 依赖重启并监听；`/actuator/health`、`/liveness`、`/readiness` 均返回 HTTP 200。真实库迁移完成后，Evidence 的 PERSON、CHARACTER、ACTOR 查询均返回 HTTP 200；MySQL 8.4 的 3065 排序错误已由分组查询修复。
- Redis 仅加载 `vectorset`，缺少现有 indexer 所需的 RediSearch `FT.*` 命令；RAG 仍保持关闭。
