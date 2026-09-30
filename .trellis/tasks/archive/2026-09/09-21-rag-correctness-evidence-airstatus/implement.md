# 执行计划：RAG 正确性 — Evidence 重复 ID 与播出状态

对应 `prd.md`（R1–R4 / AC1–AC4）与 `design.md`（§1–§7）。命令在 `backend/agent` 下执行。

## 前置

- 基线：`uv run pytest` 应为 413 passed（`.trellis/spec/backend/index.md:50`）。
- 确认工作区干净：`git status --short` 只含 `.trellis/tasks/**` 未跟踪项。

## 验证命令

```bash
cd backend/agent
uv run pytest tests/rag/ -v          # 本任务主战场（含被修改的既有测试）
uv run pytest                        # 全量（交付前，AC3）
```

## 执行清单

### 阶段 1：Evidence 重复 ID fail-closed（R1/R2，AC1）

- [ ] **1.1** `app/rag/retrieval.py::_enrich_evidence`：在 `by_id[subject_id] = row`（`:678`）前插入重复检测，命中即 `log_event(errorType="duplicate_subject_id", duplicateSubjectId=...)` + `return [], False`。按 `design.md` §2.2 的代码形状实现；不额外加 `len(rows) != len(by_id)` 断言（循环内检测已蕴含）。
- [ ] **1.2** `tests/rag/test_evidence_contract.py`：在既有 fail-closed 用例组（`:232-350` 一带）追加「重复合法 ID → fail-closed」，`evidence_lookup` 返回同 ID 两行且事实不同，断言 `available=False` / `reason=evidence_unavailable` / `items=[]`，并断言两行均未进入任何候选上下文。
- [ ] **1.3** `uv run pytest tests/rag/test_evidence_contract.py -v` 通过；确认既有 `test_enrich_attaches_evidence`（ID 唯一）仍绿——证明新检查不误伤正常路径。

**回滚点 A**：阶段 1 独立成组；回滚即回到静默覆盖行为。

### 阶段 2：播出状态推断统一（R2/R3，AC2）

- [ ] **2.1** 新建 `app/rag/air_status.py`：以 `use_case.py:81-92` 现有实现为正本搬迁为 `infer_air_status(air_date, explicit_status=None)`，语义不变（权威三值透传；未来→UPCOMING；过去/不可解析→UNKNOWN；绝不返回 FINISHED）。模块 docstring 写明「两处调用点必须复用本函数」。
- [ ] **2.2** `app/rag/use_case.py`：删除本地 `_infer_air_status`，改为从 `app.rag.air_status` 导入调用。**对外输出行为不得改变**（AC1 的既有输出不回归由此保证）。
- [ ] **2.3** `app/rag/retrieval.py`：`_infer_air_status_name` 改为复用共享函数（或删除并改调用点）；过滤分支条件由 `if not status` 改为 `status not in {"UPCOMING","AIRING","FINISHED"}`（`design.md` §3.3）。
- [ ] **2.4** `tests/rag/test_evidence_contract.py:170-230` `test_structured_filters_run_after_evidence_enrichment`：给两 subject 夹具补 `airStatus: "FINISHED"`，**不改测试目的**（该测试验证结构化过滤发生在 Evidence 富化之后）。保留 `:230` 的 `evidence_calls == [[1, 2]]` 断言。
- [ ] **2.5** 新建 `tests/rag/test_air_status.py`：共享函数参数化用例（权威三值/未来/过去/不可解析/None/组合）；两调用点行为一致性；「`air_status=FINISHED` + 过去 airDate + 无权威 → 排除」与「补权威 FINISHED → 纳入」两条过滤用例。
- [ ] **2.6** `uv run pytest tests/rag/ -v` 通过，确认既有 RAG 过滤、故障矩阵、Evidence 完整性测试不回归（AC3）。

**回滚点 B**：阶段 2 的代码与测试修改（2.4/2.5）绑定，须同组回滚。

### 阶段 3：spec 登记（AC4）

- [ ] **3.1** `.trellis/spec/backend/rag-retrieval-contract.md`：`:85` 与 `:22` 的「重复合法 ID 尚未拒绝」缺口行改为已实现（写明 fail-closed 行为与日志 errorType）。
- [ ] **3.2** 同文件缺口表登记 12e（适配器出参纵深校验）与 12f（静默 except 错误分类细化）为 backlog（`design.md` §4 已给出理由），避免只留在任务记录里。
- [ ] **3.3** 若实现中确认了共享函数位置与 spec 描述不一致，同步更新相关表述。

### 阶段 4：交付验证

- [ ] **4.1** `uv run pytest` 全量通过（AC3），对照基线 413 passed 记录实际数字。
- [ ] **4.2** 逐条核对 AC1–AC4，把实际证据（命令 + 结果）写入完成说明；不得只标「已完成」。
- [ ] **4.3** `git diff` 自查：确认未改 Business `/evidence/batch`、未改 `EvidenceMapper`、未改检索/重排算法、未改 `query_planner` 的 air_status 取值来源。

## 审查门禁

- 阶段 1 完成后：核对 AC1，重点确认「正常唯一 ID 路径不被误伤」与「重复时两行都不进上下文」。
- 阶段 2 完成后：核对 AC2，重点确认 §3.4 的测试修改确实未削弱其原目的，以及过滤排除行为符合保守原则。
- 全部完成后：`trellis-check` 子代理复核，再按 Phase 3.4 提交。

## 已知不做（防范围蔓延）

- 12e 适配器出参 ID/类型纵深校验 → backlog（`design.md` §4）。
- 12f 静默 `except Exception` 错误分类细化 → backlog。
- 不改 Business `/evidence/batch` 与 `EvidenceMapper` 的 airStatus 计算（其为权威）。
- 不重写检索/重排算法。
- 不追求 100% 覆盖率；只补本任务两项缺陷及受影响测试。

## 与 T4（测试补齐）的边界

本任务补：Evidence 重复 ID 用例、播出状态统一用例、受影响的既有测试修改。
归 T4：`collection_progress`、SSE 序列化、health 端点、streaming pending 持久化失败、gateway LLM 路由。若 T4 先行且已覆盖重复 ID，本任务对应用例跳过，避免重复。
