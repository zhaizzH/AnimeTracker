# Phase 2 Java/Python 映射契约报告

日期：2026-09-05

## 结果

- Java POJO 已覆盖 `person`、`character`、两类 alias、三类关系、`entity_detail_job` 和 `search_index_job`。
- 新增旧版 `subject_credit` 的 Java `SubjectCredit` 映射，保留存量数据窗口内的 ORM 兼容契约。
- Python `app.entities` 已覆盖同一组新表；新增 `CreditType` 与 `SubjectCredit`，严格保留 `PERSON|ORGANIZATION` 数据库字面值。
- 现有 importer/indexer 继续通过参数化 raw SQL 读取 `subject_credit`，未切断旧表兼容路径；新关系继续使用 `subject_person_credit`。

## 验证

```text
cd backend/agent
\.venv\Scripts\python.exe -m pytest -q
227 passed

cd backend/business
mvn -B clean test
BUILD SUCCESS；Client 20、App 12，共 32 项
```

未修改真实数据库；未启用 RAG 或 Redis alias。
