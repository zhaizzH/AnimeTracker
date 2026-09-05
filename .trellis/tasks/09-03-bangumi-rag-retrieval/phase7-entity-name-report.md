# Phase 7 实体名称解析切片报告

日期：2026-09-04

## 已完成

- `RetrievalQuery` 新增 `entity_name` 与可选 `entity_kind`（`PERSON|CHARACTER|ACTOR|RELATION_SUBJECT`）；名称沿用可见字符、长度和 `extra="forbid"` 约束，`entity_kind` 不能脱离名称单独使用。
- 新增 `RedisEntityNameLookup`，读取已有 `idx:rag:entity:<version>` shadow index；名称只作为经过转义和引号包裹的 TEXT 查询，索引版本和返回实体 ID 均校验。
- 三个 RAG 工具以可选参数暴露 `entity_name/entity_kind`，旧调用签名保持可用。
- 名称命中后只提取 typed local entity ID，再复用 Business `POST /api/client/evidence/resolve`；最终 Subject 仍通过既有 `type=2`、`nsfw=false`、`active=true` 权威边界。
- 名称索引或 Business resolve 异常返回 `entity_resolution_unavailable`；名称无命中返回空结果，不使用未验证候选。
- `ACTOR` 名称查询复用索引中的 `PERSON` 文档，但保留 `ACTOR` 关系解析类型。
- `RELATION_SUBJECT` 名称查询复用索引中的 `SUBJECT` 文档，但保留 `RELATION_SUBJECT` 双向关系扩展类型。
- 新增受限查询规划器：仅从明确标记提取年份/年份范围、季度、播出状态、最低评分和最低评分人数；显式结构化字段优先，不明确或越界提示保留在原始语义查询。
- 未指定 `entity_kind` 时，PERSON 与 CHARACTER 名称命中在名称约束内取并集；不同查询字段仍取交集，避免同名实体被错误过滤。

## 验证

```text
cd backend/agent
.\.venv\Scripts\python.exe -m pytest tests/adapters/test_business_http.py tests/adapters/test_entity_name_lookup.py tests/rag/test_entity_filters.py tests/rag/test_fault_matrix.py tests/rag/test_evidence_contract.py -q --basetemp .pytest-tmp-phase7-name
# 61 passed

.\.venv\Scripts\python.exe -m pytest tests/rag tests/adapters -q --basetemp .pytest-tmp-phase7-name-all
# 81 passed

# query planner
.\.venv\Scripts\python.exe -m pytest tests/rag/test_query_planner.py -q
# 7 passed

.\.venv\Scripts\python.exe -m compileall -q app jobs
git diff --check
```

测试使用工作区 basetemp；pytest 仍提示 Windows `.pytest_cache` ACL warning，不影响测试结果。未新增 Java API、数据库表或依赖；真实 Redis/Business 运行门禁仍属于 Phase 8。
