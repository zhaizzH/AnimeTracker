# RAG 检索与版本发布契约

## 历史发布记录与代码默认值

历史记录日期：2026-09-09（UTC+8）；源码复核日期：2026-09-10。本节发布事实来自 `.trellis/workspace/zhaizzH/journal-1.md` 的会话 5/6，本次文档审计未重新连接运行数据库。

- 历史记录中 v1 `subject-profile-v1` 已通过五份同版本 gate 报告并激活 MySQL `search_index_release`；当前环境是否仍 ACTIVE 必须重新查询，不能仅由仓库推断。
- 24 小时小流量灰度观察以及 release/功能开关回滚确认已完成；旧索引、旧 Vector Set 和旧表仍需独立确认后才能清理。
- `RAG_ENABLED` 默认仍为 `false`。**索引发布完成不等于 Agent RAG 默认启用**；启用功能开关必须单独验证并保留关闭路径。

## 在线装配与当前缺口

源码：`backend/agent/main.py`、`backend/agent/app/rag/retrieval.py`、`backend/agent/app/rag/use_case.py`、`backend/agent/app/agent/client/rag_tools.py`。

| 边界 | 当前实现 | 必须保留的说明 |
|---|---|---|
| 普通用户 / 管理员 | 客户端三个节点注册各自 rag_*；admin 只注册目录/导入/时间工具 | 不得笼统宣称所有 Agent 都有 RAG 工具 |
| 实体名称 | `entity_name_lookup=None`，有名称即 `entity_resolution_unavailable` | 名称参数和 Prompt 已存在不等于在线名称解析可用；显式 ID 的 Business `/resolve` 已接线 |
| 查询版本 | lexical 响应 indexVersion 决定 Subject VSIM key | Python 未独立校验响应 profileVersion；MySQL JOIN 和发布 gate 承担对应版本约束 |
| 收藏画像向量 | `_subject_vector_lookup` 使用配置 `rag_index_version` | 仍可能与 active release 不同，不能把主检索的同版本保证扩大到画像链 |
| 工具错误 | use case 返回 available/reason/personalizationNotice；工具 `_items` 只返回列表 | 不可用与无结果都可能成为 []，模型目前不能可靠报告降级原因 |
| Evidence 重复 ID | 字典按 subjectId 覆盖，随后比较 ID 集合与安全字段 | 尚未拒绝重复合法 ID，应补唯一性校验 |

RRF 按两路排名计算 `Σ 1/(60+rank)`，每路上限 50，权威回查后最终至多 15 条；当前重排为 `retrieval.py::_rerank` 中的规则分数，没有独立 reranker 模型。查询 Embedding 失败时可继续词法召回，版本获取/索引异常进入 Business fallback；正常空召回不一定触发 fallback。

### 日期与状态的已知偏差

- Business `backend/business/client/src/main/java/top/zhaizz/client/util/SeasonUtil.java` 使用冬季=1–3 月、春季=4–6 月、夏季=7–9 月、秋季=10–12 月。
- Python `app/rag/query_planner.py`、`app/rag/retrieval.py`、`app/adapters/redis/subject_index.py` 当前把 spring/summer/autumn/winter 映射为 1/2/3/4。跨层季度条件存在偏差，修复时需一起检查 indexer 数字季度与历史索引，不能单改 Prompt。
- `use_case.py::_infer_air_status` 仅以首播日期推断：未来 UPCOMING、其余 FINISHED、无法解析 UNKNOWN，不产生 AIRING。不得依据该输出声称作品已完结或仍在播；需要权威播出状态或更完整证据。

### 配置和 CLI

- `app/config.py::Settings` 使用 `extra='forbid'`。`.env.example` 仍含已移除的 `RAG_INDEX_ALIAS` 和旧 RediSearch 说明；完整复制旧模板可能触发配置校验错误，应按实际 Settings 核对，不能把 FT.* 作为当前 Vector Set 能力检查。
- `jobs/indexer/gate.py` 的激活分支读取进程环境 `DB_*`，该 CLI 本身不调用 `load_dotenv()`。执行 `--activate` 前须确认目标进程的数据库配置；不能假设和 `jobs/indexer/main.py` 的 `.env` 自动加载相同。

## 1. Scope / Trigger

- 触发：修改 `app/rag` 检索、`jobs/indexer`、MySQL `search_index_release`、Redis Vector Set、Evidence 回查、RAG 配置开关或灰度/回滚流程。
- 目标：保证 MySQL 词法投影、Redis 语义投影、Agent RRF、Evidence 权威回查和发布状态使用同一 `indexVersion/profileVersion`，避免跨版本静默混用。
- 不适用：普通 Subject 搜索、无 RAG 开关的 Business CRUD，以及归档任务中的历史审计记录。

## 2. Signatures

### 配置

- `RAG_ENABLED: bool = false`：Agent RAG 总开关；关闭时使用既有 Business 搜索路径。
- `RAG_REDIS_URL: str | empty`：索引专用 Redis；为空时复用 `REDIS_URL`。
- `RAG_INDEX_VERSION: str = v1`：索引构建默认版本；在线查询版本以 Business 返回的 active release 为准。
- `RAG_EMBEDDING_MODEL: text-embedding-v4`、`RAG_EMBEDDING_DIM: 1024`：当前 v1 embedding 契约。

### API / 存储

- `POST /api/client/subjects/lexical-search`：请求包含 `q` 及可选结构化过滤；成功响应至少包含 `{indexVersion, profileVersion, candidates[]}`。
- `search_document(entity_kind, entity_id, index_version, profile_version, ...)`：MySQL 可重建 lexical shadow 投影。
- `search_index_release(index_version, profile_version, status, activated_at, retired_at, active_slot)`：MySQL 唯一发布指针；最多一个 `ACTIVE`。
- Redis Vector Set key：`rag:vectors:{entity_kind}:{indexVersion}`；Redis 只保存数据平面，不保存发布决定权。
- `MySqlReleaseStore.active_version() -> str | None`、`activate(index_version) -> None`；只有该适配器可以切换发布状态。

### 发布命令

```powershell
cd backend/agent
python -m jobs.indexer.gate `
  --index-version v1 `
  --report-dir <REPORT_DIR>

# 只有 gate=PASS 且人工确认后才能执行
python -m jobs.indexer.gate `
  --index-version v1 `
  --report-dir <REPORT_DIR> `
  --activate
```

`<REPORT_DIR>` 必须指向当前版本的五份 gate 报告目录，不得复用未核对版本的历史报告。

## 3. Contracts

- **版本一致性**：词法响应的 `indexVersion` 是 Agent 查询 Vector Set 的唯一版本来源；禁止使用 `RAG_INDEX_VERSION` 猜测在线版本，禁止跨版本 RRF。
- **Embedding 一致性**：quality、capacity、eval、latency、human 五份报告必须绑定同一 `indexVersion/profileVersion` 和 provider/model/dimensions/profile 契约。
- **Gate 门禁**：`jobs.indexer.gate` 缺报告、版本不一致、契约不一致或任一指标失败时 fail-closed；未通过不得激活 release。
- **Gate 阈值**：coverage ≥ 99.5%、Recall@20 ≥ 0.85、MRR@10 ≥ 0.90、nDCG@10 ≥ 0.75、Evidence completeness = 100%、Redis P95 < 250 ms、hydrated P95 < 500 ms、容量利用率 ≤ 60%、人工检查 ≥ 20 且严重错误为 0、正式 eval 必须为 `RELEASE_CANDIDATE` 且 120/120 通过。
- **激活边界**：先完成 MySQL/Redis 双 shadow，再生成五份报告，gate 通过后在 MySQL 事务中激活；Redis alias 不得参与发布。
- **功能开关边界**：release `ACTIVE` 只表示索引可供查询；`RAG_ENABLED=false` 时不得把索引发布描述为 Agent RAG 已默认启用。
- **Evidence 权威性**：候选必须先经过 Business 权威回查，再经过 Evidence API；Evidence 超时、错误、缺项、非法 ID、inactive 或 NSFW 时返回 `available=false` 和空候选。重复合法 ID 的拒绝尚待实现，见本页缺口表。
- **灰度确认**：启用 RAG 后至少观察 24 小时，记录观察起止时间、版本、成功率/错误率、延迟、Evidence 完整率和告警结果；没有原始指标时只能记录“人工确认通过”，不得补写数值。
- **回滚**：异常时先关闭 RAG 功能开关，再通过 MySQL release store 切回已通过 gate 的旧版本；保留新旧投影，禁止 Redis-only 回滚。
- **清理**：回滚窗口结束前不得删除旧 `search_document` 版本或 Vector Set；删除索引、Vector Set 或表必须另起确认与迁移记录。

## 4. Validation & Error Matrix

| 条件 | 必须行为 |
|---|---|
| `RAG_ENABLED=false` | 使用既有 Business 搜索；不得调用向量检索并声称 RAG 已启用 |
| 无 `ACTIVE` release | Business lexical 返回 503；Agent 保持既定 fallback/fail-closed，不猜测版本 |
| lexical 响应缺少 `indexVersion` | 拒绝跨版本查询，记录失败原因 |
| 五份报告缺失或版本/embedding 契约不一致 | gate fail-closed，拒绝激活 |
| coverage、Recall、MRR、nDCG、P95、容量或人工检查未达阈值 | gate fail-closed，保留旧 release |
| Redis `VADD/VSIM/VREM` 不可用 | 不确认 index job，不激活 release，按既定降级/重试处理 |
| Business 权威回查失败 | `available=false`、空候选 |
| Evidence 失败或部分结果 | `available=false`、`reason=evidence_unavailable`、空候选 |
| 灰度出现异常 | 关闭功能开关并切回已验证旧 release；不得先删新索引 |
| 回滚窗口未结束却请求清理 | 拒绝清理，要求独立人工确认 |

## 5. Good / Base / Bad Cases

- **Good**：构建 `v1` 双 shadow → 生成同版本五份报告 → `gate=PASS` → MySQL 事务激活 → 单独打开 RAG 开关 → 观察 24 小时 → 稳定后保留回滚窗口。
- **Base**：release 已为 `ACTIVE` 但 `RAG_ENABLED=false`，在线 Agent 仍走 Business fallback；后续开启时重新检查健康、版本和 Evidence 指标。
- **Bad**：直接把 Redis key 当 active alias、让 Agent 猜版本、只写一侧投影、gate 未通过就 `--activate`、或先删除旧版本再做回滚。

## 6. Tests Required

- `backend/agent/tests/jobs/indexer/test_gate.py`：断言五份报告完整、版本/embedding 契约一致、阈值和 `RELEASE_CANDIDATE` 门禁；缺失或失败时不得激活。
- `backend/agent/tests/jobs/indexer/test_entity_loader_and_shadow.py`：断言 gate 失败拒绝切换、MySQL release 激活、rollback 只切回已验证版本且不删投影。
- `backend/agent/tests/jobs/indexer/test_shadow_eval.py`：断言 shadow 评测不写 `search_index_release`，报告携带同一 index/profile 版本。
- `backend/agent/tests/rag`：断言 `RAG_ENABLED` 关闭 fallback、缺 `indexVersion` fail-closed、Evidence 缺项/异常为空候选。
- Business `SubjectMapperLexicalSqlCompatibilityTest` 与相关 Controller/Service 测试：断言无 active release 为 503，成功响应含 `indexVersion/profileVersion`。
- 真实交付复核：`mvn -B clean test`、`uv run pytest`、gate CLI、健康检查、词法 API 成功请求，以及灰度观察/回滚记录；命令和结果必须写入运行审计。

## 7. Wrong vs Correct

### Wrong

```python
# 用配置默认值猜在线版本，并把 Redis key 当作 active 发布事实
version = settings.rag_index_version
rows = vector_set.vsim(f"rag:vectors:SUBJECT:{version}", embedding)
```

### Correct

```python
# 先读取 Business active release，再查询同版本 Vector Set
release = business.lexical_search(request, token=token)
version = release["indexVersion"]
rows = vector_set.vsim(f"rag:vectors:SUBJECT:{version}", embedding)
```

```text
Correct rollback: 关闭 RAG_ENABLED → MySqlReleaseStore.activate(previous_version)
→ 保留新旧投影 → 记录回滚原因和观察窗口；禁止 Redis-only rollback。
```
