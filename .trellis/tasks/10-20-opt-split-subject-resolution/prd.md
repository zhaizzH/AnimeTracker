# 优化项 1: 拆 subject_resolution.py 为 4 个单一职责模块

> 父任务：[`10-20-agent-module-optimization`](../10-20-agent-module-optimization/prd.md)
> 本任务：父任务的「核心动机」优化项，对应简历一句话的「把 564 行历史包袱拆成 4 个单一职责模块」

## Goal

把 `backend/agent/app/agent/client/actions/subject_resolution.py`（564 行）拆成 4 个职责单一、契约清晰的模块，让文件名即契约。

**本任务不改任何业务逻辑、不改任何测试、不改任何对外行为**。这是纯文件级拆分，目标是「作者本人能三句话讲清每个文件干什么」。

## Background · 为什么是这个文件

来自拷问会话 Q3=C：

- 564 行，agent 模块最大单文件
- 作者本人「说不清契约」
- 文件名 `subject_resolution` 暗示「解析」，但实际职责远超解析
- 是「加入想看」和「设置收藏类型」两条写链路的**必经入口**

通读全部代码后，确认它实际承担 **5 个职责**：

| 职责 | 行数估算 | 当前位置 |
|---|---|---|
| 1. 标题归一化（NFKC + 标点 + 大小写折叠） | ~30 | `normalize_title` + `_PUNCTUATION_RE`/`_WHITESPACE_RE`/`_ORDINAL_RE` |
| 2. 候选匹配（精确命中识别） | ~50 | `unique_exact_match_ids` / `_candidate_titles` / `dedup_ids` / `_safe_subject_id` |
| 3. 候选选择（用户从多候选中挑一个） | ~40 | `select_candidate` / `_as_index` / `_selection_message` |
| 4. Business /batch 权威校验 | ~60 | `filter_authoritative` / `_is_safe_batch_item` / `_batch_items` / `_display_name` |
| 5. 解析主流程 + 工具入口（LangGraph 编排） | ~380 | `resolve_candidates` / `finalize_resolution` / `_business_lookup` / `_rag_lookup` / `build_resolution_action` / `build_subject_resolution_tools` |

**问题**：5 个职责堆在一个文件里，导致：
- 新加写链路（如「评分」）要复用「标题解析」能力时，**被迫 import 一个 564 行的巨文件**
- 修改归一化规则要在 564 行里找，**容易误改业务流程**
- 测试只能黑盒测整个工具，**无法单测归一化函数**

**现实期望**：拆分后主文件仍会有 ~330 行（主流程 + 工具入口是真正业务逻辑所在）。拆分的**真实收益**不在行数，而在职责独立可测、复用方可以只 import 需要的职责、每个文件能用三句话讲清契约。

## Scope

### In Scope

- 拆出 3 个新文件 + 保留 1 个主文件：
  - `title_normalizer.py`（约 50 行）
  - `candidate_matcher.py`（约 90 行，含 `_safe_subject_id`）
  - `subject_authority.py`（约 100 行，含 `_display_name`）
  - `subject_resolution.py`（保留工具入口与主流程，目标 < 100 行）
- 给每个新文件写**三句话以内**的模块 docstring
- 保留现有公开 API：`build_subject_resolution_tools(business, retrieval)` 签名不变

### Out of Scope

- **不改任何函数的实现**（只移动 + re-export）
- **不改任何测试**（现有 29 个 `test_subject_resolution.py` 测试必须全绿，零修改）
- **不删除任何「过时但无害」的代码**（如 `_selection_message` 的死分支）
- **不抽象、不优化、不改名函数**（保持最小 diff，方便 review）
- **不动 PendingAction 生命周期**（那是优化项 2）

## Acceptance Criteria

- [ ] `subject_resolution.py` 行数从 564 降到 **< 350 行**（搬走的 ~230 行 = 归一化 / 匹配 / 校验三个职责）
- [ ] 4 个文件每个 **< 200 行**
- [ ] `title_normalizer.py` / `candidate_matcher.py` / `subject_authority.py` 各自有 ≤ 3 句话的模块 docstring
- [ ] `subject_resolution.py` 顶部模块 docstring ≤ 3 句话讲清对外契约：
  - 输入：标题字符串或显式 subject_id + 用户上下文
  - 输出三种之一：错误 / 无匹配 / 唯一精确预览或 SUBJECT_RESOLUTION 待选择
  - 副作用：通过 `emit_pending_action_set/clear` 触发状态变更，自身不持久化
- [ ] **跨职责复用能力解锁**：未来的写链路（如「评分」）能只 import `title_normalizer` 而不是 564 行整包
- [ ] `uv run pytest tests/agent/test_subject_resolution.py` 全绿（29 passed, 2 xfailed 与现网一致）
- [ ] `uv run pytest` 全绿（585 passed, 6 xfailed 与现网一致）
- [ ] `uv run ruff check app/` 无新增 warning
- [ ] 所有跨文件 import 走绝对路径，**无循环 import**（`python -c "from app.agent.client.actions.subject_resolution import build_subject_resolution_tools"` 不报错）
- [ ] `git diff --stat` 显示：4 个文件改动（3 新增 + 1 重写），其他文件零改动

## Constraints

1. **零行为变更**：本任务不允许引入任何行为差异，包括错误消息文本、SSE 帧序、Redis 键
2. **零测试改动**：测试是给「对外契约」写的，对外契约不变 → 测试不变
3. **最小 diff**：能用 `from X import Y` re-export 保持兼容的，就不要改调用方
4. **先列调用方再动手**：在 `design.md` 列出 `subject_resolution.py` 的所有 import 方和被 import 方，确认零遗漏

## Open Questions

（在 `design.md` 中回答）

- 现有调用方有哪些？（grep `from app.agent.client.actions.subject_resolution` / `import subject_resolution`）
- `_display_name` 该去哪个文件？它只对 authority 校验的返回结果用，但本身只是 dict 工具——倾向 `subject_authority.py`
- `_safe_subject_id` 该去哪个文件？被 `unique_exact_match_ids` / `dedup_ids` / `resolve_candidates` 三处用——倾向 `candidate_matcher.py`
- `build_resolution_action` 算「主流程」还是「构造器」？它构造 `SubjectResolutionPendingAction`——倾向留在主文件
- `_selection_message` 是死代码吗？只在 `select_resolved_subject` 一处用——倾向留在主文件

## Related

- 父任务 PRD：`../10-20-agent-module-optimization/prd.md`
- 现有测试：`backend/agent/tests/agent/test_subject_resolution.py`（29 passed, 2 xfailed）
- 现有 spec：`.trellis/spec/backend/agent-guidelines.md`（完成后需同步）
- 源码：`backend/agent/app/agent/client/actions/subject_resolution.py`
