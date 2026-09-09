# Phase 8 Spring Boot 启动验证报告

日期：2026-09-05

> 本文前半保留 2026-09-05 的启动故障与修复历史；当前服务状态以文末 2026-09-06 真实访问复核为准。

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
- 当时的 RediSearch `FT.*` 阻断已被后续“MySQL FULLTEXT + Redis Vector Set”实现路线取代，不再是当前阻断。RAG 仍保持未发布，是因为正式 release-candidate gate 和灰度尚未完成。

## 2026-09-06 真实访问复核

- `2026-09-06T18:28:01+08:00`：`GET /actuator/health` 与 `/actuator/health/readiness` 均为 HTTP 200、`status=UP`。
- `GET http://127.0.0.1:8090/api/client/agent/health` 为 HTTP 200，返回 `status=ok`、`llm_configured=true`。
- `POST /api/client/subjects/batch`、`/api/client/evidence/batch`、`/api/client/evidence/resolve` 对 Subject 63 均为 HTTP 200，且返回 `active=true`。
- `POST /api/client/subjects/lexical-search` 为 HTTP 503“词法索引尚未发布”，与 `search_index_release` 0 行一致，不是启动故障。
- 当前完整测试总数以 [真实索引运行报告](./phase8-index-runtime-report.md) 为准：Agent `268 passed, 1 deselected`，Business `37` tests passed。

## 2026-09-07 激活后复核

- v1 release 已切换为 `ACTIVE` 后，`POST /api/client/subjects/lexical-search` 实测返回 HTTP 200，并携带 `indexVersion=v1`、`profileVersion=subject-profile-v1`。
- 8080 Business 与 8090 Agent 健康检查仍为 HTTP 200；RAG 功能开关未在本次激活中修改。
