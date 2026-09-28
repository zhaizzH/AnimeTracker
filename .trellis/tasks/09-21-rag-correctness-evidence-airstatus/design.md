# 技术设计：RAG 正确性 — Evidence 重复 ID 与播出状态

对应 `prd.md` 的 R1–R4。本文只记技术决策；需求与验收标准在 PRD。

## 1. 影响面

| 文件 | 改动 |
|---|---|
| `backend/agent/app/rag/retrieval.py` | `_enrich_evidence` 增重复 ID fail-closed；`_infer_air_status_name` 改为复用共享函数 |
| `backend/agent/app/rag/air_status.py` | **新增**：唯一播出状态推断函数 |
| `backend/agent/app/rag/use_case.py` | `_infer_air_status` 改为复用共享函数（删除本地实现） |
| `backend/agent/tests/rag/test_evidence_contract.py` | **修改既有测试**（见 §5）；新增重复 ID 用例 |
| `backend/agent/tests/rag/test_air_status.py` | **新增**：统一推断的保守语义 + 两调用点一致性 |
| `.trellis/spec/backend/rag-retrieval-contract.md` | 更新 `:22` / `:85` 缺口行（Phase 3） |

**不动**：Business `/evidence/batch` 与 `EvidenceMapper`（权威 airStatus 计算）；检索/重排算法；`query_planner` 的 `air_status` 取值来源。

## 2. R1 / R2：Evidence 重复合法 ID → fail-closed

### 2.1 缺陷机制（已核实）

`retrieval.py:667-688`：

```python
rows = response if isinstance(response, list) else []
by_id: dict[int, Mapping[str, Any]] = {}
for row in rows:
    ...
    by_id[subject_id] = row          # :678 —— 重复时后者静默覆盖
expected_ids = {candidate.subject_id for candidate in candidates}
if by_id.keys() != expected_ids:     # :680 —— 重复已在赋值时坍缩，此处无法发现
```

`by_id` 是 dict，重复 `subjectId` 在进入 `:680` 的集合比对前就已坍缩：两行同 ID、事实不同时，后一行成为「权威证据」送入模型上下文，而完整性门禁（比对 key 集合）看到的集合与合法情形完全一致。这是**绕过 fail-closed 边界的静默数据污染**，与既有「缺项/多项/非法 ID 即拒绝」的严格性不一致（spec `rag-retrieval-contract.md:85` 已把「重复合法 ID 的拒绝尚待实现」记为缺口）。

### 2.2 修复：循环内检测，就地拒绝

在赋值前检测已见 ID，命中即整批拒绝：

```python
for row in rows:
    if not isinstance(row, Mapping) or row.get("subjectId") is None or isinstance(row.get("subjectId"), bool):
        return [], False
    try:
        subject_id = int(row["subjectId"])
    except (TypeError, ValueError, OverflowError):
        return [], False
    if subject_id <= 0:
        return [], False
    if subject_id in by_id:                       # 新增：重复合法 ID → fail-closed
        log_event("rag.evidence.enriched", success=False,
                  errorType="duplicate_subject_id", duplicateSubjectId=subject_id)
        return [], False
    by_id[subject_id] = row
```

设计取舍：

- **在循环内检测而非事后比对 `len(rows) != len(by_id)`**。两者都能发现重复，但循环内检测能拿到**具体重复的 ID** 并写入日志，便于定位 Business 侧数据问题；事后 len 比对只能得出「有重复」。循环内检测在语义上已蕴含 len 相等（所有行都合法且唯一时必然相等），故不重复加 len 断言。
- **日志用独立的 `errorType="duplicate_subject_id"`**，不与既有 `partial_response` / `unsafe_response` 混同——这三者的运维处置方式不同（部分响应是 Business 未返回全量，重复 ID 是 Business 返回了自相矛盾的数据）。
- **不尝试「选取其一」**。任何「按某规则挑一行」的启发式都可能挑错，且违反 PRD「绝不静默后者胜」。整批拒绝是唯一与既有 fail-closed 边界自洽的行为。
- 返回 `[], False` 与既有各拒绝分支一致，上游 `_authoritative_result` 会据此产出 `available=False, reason=evidence_unavailable, items=[]`，不把任何行送入模型上下文（满足 AC1）。

## 3. R2 / R3：播出状态推断统一（保守版）

### 3.1 缺陷机制（已核实）

同一规则存在两份互相矛盾的实现：

| 位置 | 过去日期、无权威状态时 |
|---|---|
| `retrieval.py:989-994` `_infer_air_status_name` | `"FINISHED"`（无条件） |
| `use_case.py:81-92` `_infer_air_status` | `"UNKNOWN"` |

前者被 `:803` 的 `air_status` 过滤使用：无权威状态的过期番被判为 `FINISHED`，于是 `air_status=FINISHED` 查询会把它纳入——**违反「单个首播日期不臆断完结」**（`cross-layer-thinking-guide.md:99`、`use_case.py:82` 注释均已明示该原则）。后者用于对外输出，行为正确。

### 3.2 修复：提取共享函数

**放置点：新建 `app/rag/air_status.py`。**

理由（对照既有先例）：`app/rag/seasons.py` 就是同类模式——两端必须一致的共享规则词表，独立成小模块，并由 `tests/rag/test_season_alignment.py` 校验对齐（`cross-layer-thinking-guide.md:99` 记录其为「Python 唯一词表」）。其模块 docstring 已把纪律写死：

> 「任何标签→数字/月份段的换算都必须经过本模块，**禁止在消费方内联第二份映射**。」

本次 air-status 分叉（`retrieval.py:989` 与 `use_case.py:81` 各存一份矛盾实现）正是这条纪律被违反的结果。播出状态推断是同一类「两端必须一致的小规则」，故沿用 `seasons.py` 的形态与措辞。

影响面已核实为最小：`_infer_air_status` 仅 1 处调用（`use_case.py:50`），`_infer_air_status_name` 仅 1 处调用（`retrieval.py:803`），两者均无测试直接导入，搬迁不牵动其他模块。

备选：放进 `app/rag/retrieval.py`（`use_case.py:7` 已 `from app.rag.retrieval import ...`，无新增依赖、无循环）。**未采用**：把纯规则挂在 `RagRetrievalService` 所在的重量级模块上，会让 `use_case` 为了一个无状态helper 依赖整个检索实现，且不符合 `seasons.py` 已确立的「小规则独立模块」习惯。

```python
# app/rag/air_status.py
"""播出状态推断的唯一实现；两处调用点必须复用本函数。"""

def infer_air_status(air_date: Any, explicit_status: Any = None) -> str:
    """优先权威 airStatus；无权威状态时按日期保守推断。

    单个首播日期不能证明已完结：无权威状态时，未来日期 → UPCOMING，
    过去或无法解析的日期 → UNKNOWN。绝不返回 FINISHED。
    """
    normalized = str(explicit_status or "").upper()
    if normalized in {"UPCOMING", "AIRING", "FINISHED"}:
        return normalized
    parsed = _parse_date(air_date)
    if parsed is None:
        return "UNKNOWN"
    return "UPCOMING" if parsed > datetime.today().date() else "UNKNOWN"
```

`use_case.py:81-92` 的函数体本就是上述语义，故该函数以 `use_case` 现有实现为正本搬迁，**不改变对外输出行为**（AC1 的「既有输出不回归」由此保证）。

### 3.3 过滤路径的行为变更

`retrieval.py:800-805` 改为：

```python
if query.air_status is not None:
    status = str(item.get("airStatus") or item.get("air_status") or "").upper()
    if status not in {"UPCOMING", "AIRING", "FINISHED"}:
        status = infer_air_status(item.get("airDate") or item.get("air_date"))
    if status != query.air_status:
        return False
```

- **R3 由构造满足**：权威 `airStatus` 存在时仍以权威值判定，仅兜底路径受影响。
- 判定条件由 `if not status` 改为 `status not in {三值}`：原写法在 `airStatus` 为 `"UNKNOWN"` 时不会回落兜底；改为集合判定后，`"UNKNOWN"` 会走兜底再得 `UNKNOWN`——结果同为 `UNKNOWN`，不改变过滤结果，但消除了「非空即权威」的隐含假设。
- `RetrievalQuery.air_status` 的 `Literal` 仅含 `UPCOMING/AIRING/FINISHED`（`schemas.py:62`），故 `UNKNOWN` 必然不等于查询值 → 被排除，正是 PRD 要的行为。
- 原实现对**无法解析**的日期返回 `""`，新实现返回 `"UNKNOWN"`；两者对过滤结果等价（均 ≠ 三个合法值），但新值语义明确。

### 3.4 一处必须确认的既有测试

`tests/rag/test_evidence_contract.py:170-230` `test_structured_filters_run_after_evidence_enrichment` 的夹具给两个 subject 均设 `airDate: 2024-01-01` 且**无** `airStatus`，断言 subject 1 通过 `air_status="FINISHED"` 过滤。保守化后该断言必然失败（过去日期 + 无权威 → UNKNOWN → 排除）。

**处理方式（见 §5）**：给该测试夹具补 `airStatus: "FINISHED"`。该测试的**目的是验证结构化过滤发生在 Evidence 富化之后**（其 docstring 与 `:230` 的 `evidence_calls == [[1, 2]]` 断言均为该目的），air-status 语义只是顺带经过的过滤条件之一。补权威值后测试目的不变且更强（现在同时证明了权威值被采用）；播出状态语义另由新测试专门覆盖。**这不是弱化测试**，需在实现与 review 中显式说明，避免被误读为「改断言以迁就新行为」。

## 4. R4：12e / 12f 决策（PRD 要求 design 明确）

**结论：两项均转入 backlog，本轮不实现。**

| 项 | 决策 | 理由 |
|---|---|---|
| 12e 适配器出参 ID/类型纵深校验（`business_http.py:70-141`） | **转 backlog** | spec 已记录该层「依赖上游 typed 工具」为既定边界；纵深校验会改动 `batch_subjects` / `batch_evidence` / `resolve_evidence` / `save_collection` 四个方法的出参与错误语义，需重新确认与上游 typed 工具的职责划分。本轮两个真缺陷（重复 ID 静默覆盖、状态自相矛盾）是**已发生的正确性缺陷**，12e 是**纵深防御**；混做会让前者被稀释，且扩大回归面。 |
| 12f 静默 `except Exception` 错误分类细化（`retrieval.py:146-149,225-227`、`main.py:176-177`） | **转 backlog** | 细化错误分类会变更降级语义与 `log_event` 的 errorType 取值，连带影响故障矩阵测试与 `rag-retrieval-contract.md` 的错误矩阵文档。应作为独立任务，先定义好错误分类契约再改。 |

两项均需在实现后的 Phase 3 spec 更新中登记到缺口表，避免只留在任务记录里（PRD AC4 要求 design 明确，本条已满足）。

## 5. 测试设计

| 用例 | 覆盖 | 方式 |
|---|---|---|
| 重复合法 ID → fail-closed | AC1 | `evidence_lookup` 返回同 ID 两行（事实不同），断言 `available=False` / `reason=evidence_unavailable` / `items=[]`，且断言**两行都没有**进入任何候选的上下文 |
| 重复检测不误伤 | AC1 | 既有 `test_enrich_attaches_evidence`（ID 唯一）必须仍绿——确认新检查不把正常路径判失败 |
| 共享函数保守语义 | AC2 | 参数化：权威三值各自透传；未来日期→UPCOMING；过去日期→UNKNOWN；无法解析/None→UNKNOWN；`airDate` 与 `explicit_status` 组合 |
| 两调用点一致性 | AC2 | 断言 `retrieval._infer_air_status_name` 与 `use_case._infer_air_status` **不存在**（改为断言两模块均从 `app.rag.air_status` 导入同一函数）；或对同一输入断言两条路径产出相同结果 |
| 过滤排除过期无状态番 | AC2 | `air_status=FINISHED` 且无权威 `airStatus`、`airDate` 在过去 → 被排除；补 `airStatus="FINISHED"` 后 → 被纳入 |
| 既有测试修改 | AC2 | `test_structured_filters_run_after_evidence_enrichment` 夹具补 `airStatus: "FINISHED"`（§3.4） |

新增测试落 `tests/rag/test_air_status.py`（与 `test_season_alignment.py` 同目录同形态）；重复 ID 用例追加到既有 `tests/rag/test_evidence_contract.py` 的 fail-closed 用例组（`:232-350` 一带），与该组风格一致。

## 6. 回滚

三组可独立回滚：

1. 重复 ID 检查（§2）——回滚后回到静默覆盖。
2. 共享 air-status 函数与两处接线（§3）——回滚后回到两函数矛盾状态；须同时回滚 §5 的测试修改。
3. 测试修改（§5/§3.4）——与 2 绑定，不可单独回滚。

无数据库、无接口契约、无 schema 变更。

## 7. 风险

| 风险 | 缓解 |
|---|---|
| 保守化导致 `air_status` 过滤召回下降 | 已核实 Business `/evidence/batch` 用 SQL 计算权威 `airStatus`（剧集感知、几乎不为 null），Python 推断只是极少走到的兜底，故实际召回损失可忽略；AC 要求「既有 RAG 过滤测试不回归」以实测确认 |
| `test_structured_filters_...` 的修改被误读为迁就实现 | §3.4 已写明该测试目的与为何补权威值；实现说明与 review 中显式声明 |
| 新建 `air_status.py` 被视为「为一个小函数开文件」 | §3.2 已给出 `seasons.py` 先例；若 review 认为过度，备选是放 `retrieval.py`（已注明无循环风险） |
| 重复 ID 检查误伤正常单行响应 | §5 第 2 条用例专门覆盖 |
