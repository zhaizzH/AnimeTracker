# Phase 6 Business 精确查询报告

## 已完成

- 新增 `POST /api/client/evidence/resolve`，使用 `entityType=SUBJECT|PERSON|CHARACTER|ACTOR` 与最多 50 个本地 ID。
- `PERSON` 沿 `subject_person_credit`，`CHARACTER` 沿 `subject_character`，`ACTOR` 沿 `character_actor` 扩展到安全动画条目；所有 SQL 使用 MyBatis `@Param` + `<foreach>` 绑定参数。
- 统一回查只返回 `type=2`、`nsfw=0`、`import_status=1` 且关联实体 `source_active=1` 的候选；补充 `active`、Bangumi `sourceId`、`sourceUrl`、`sourceFetchedAt`，保留旧 `sourceTime` 字段兼容 Agent。
- 旧 `POST /api/client/evidence/batch` 请求与调用方式保持不变；同步了 OpenAPI 与匿名 Agent 路由授权回归测试。

## 验证

```text
mvn -B -pl client -am "-Dtest=EvidenceServiceImplTest,EvidenceControllerTest" "-Dsurefire.failIfNoSpecifiedTests=false" test  # 18 passed
mvn -B test                                                                                       # 29 passed
```

OpenAPI YAML 通过 PyYAML 解析；本任务未修改 Python indexer，也未连接真实数据库或执行迁移。
