# 优化项 1 · Design：拆 subject_resolution.py

> PRD：[`prd.md`](./prd.md)

## 调用方盘点（先列清楚再动手）

### `subject_resolution.py` 被谁 import

| 调用方 | 引用的符号 | 是否公开 API |
|---|---|---|
| `app/agent/client/actions/collection_type.py` | `finalize_resolution`, `resolve_candidates` | 否（内部复用） |
| `app/agent/client/recommend.py` | `build_subject_resolution_tools` | 是（唯一对外入口） |
| `tests/agent/test_collection_type.py` | `build_subject_resolution_tools` | 是 |
| `tests/agent/test_subject_resolution.py` | `build_subject_resolution_tools`, `dedup_ids`, `filter_authoritative`, `normalize_title`, `select_candidate`, `unique_exact_match_ids` | 是（测试视为公开契约） |

**关键约束**：测试 import 了 5 个内部函数 + 1 个入口。拆分后这些符号**必须能从 `subject_resolution` 直接 import**，否则就是改测试（违反约束）。

**结论**：`subject_resolution.py` 必须用 `from X import Y` re-export 以下符号：
- `dedup_ids`, `filter_authoritative`, `normalize_title`, `select_candidate`, `unique_exact_match_ids`

### `subject_resolution.py` import 了谁（仅 app 内）

| 依赖 | 用途 |
|---|---|
| `wishlist.build_wishlist_preview` | 唯一精确命中后进入想看预览 |
| `collection_state.require_user` | 用户上下文守卫 |
| `write_guard.is_expired` | 选择过期判断 |
| `middleware.tool_call_status` | 工具装饰器 |
| `ports.BusinessGateway` | Business 接口 |
| `chat.pending_action.SubjectResolutionPendingAction/Candidate` | PendingAction 类型 |
| `chat.pending_events.emit_pending_action_clear/set` | 状态触发 |
| `chat.user.UserInfo` | 用户类型 |
| `rag.schemas.RetrievalQuery` / `rag.use_case.RetrieveSubjectsUseCase` | RAG 回退 |

**无环检查**：`subject_resolution` 不被 `wishlist` / `collection_state` / `write_guard` / `pending_action` / `pending_events` / `user` / `rag.*` 反向 import。拆分后 4 个新文件之间的依赖必须是**单向**的。

## 拆分方案

### 文件 1 · `title_normalizer.py`（新，约 30 行）

**职责**：把用户输入的标题字符串归一化成可比较的规范形式。

**导出**：
- `normalize_title(value: Any) -> str`

**私有**：
- `_PUNCTUATION_RE`、` _WHITESPACE_RE`（标点 / 空白正则）

**docstring**（三句话）：
> 安全标题归一化：NFKC + 大小写折叠 + 标点分隔 + 空白折叠。
> 对查询和候选标题使用同一函数；不包含任何语义转换（如「第二季」→「第2季」）。
> 纯函数，无副作用。

**依赖**：仅标准库 `re` / `unicodedata`。

---

### 文件 2 · `candidate_matcher.py`（新，约 100 行）

**职责**：从候选条目中识别「唯一精确命中」和「去重后的 subject_id 列表」，并支持用户从多候选中按序号或名称选择。

**导出**：
- `unique_exact_match_ids(query, items, id_key) -> tuple[list[int], bool]`
- `dedup_ids(ids: list[Any]) -> list[int]`
- `select_candidate(choice, candidates) -> tuple[SubjectResolutionCandidate | None, str | None]`

**私有**：
- `_safe_subject_id(value) -> int | None`
- `_candidate_titles(item) -> list[str]`
- `_as_index(choice, count) -> int | None`
- `_ORDINAL_RE`

**docstring**：
> 候选匹配与选择：识别「唯一精确命中」、去重 ID 列表、按序号或名称从多候选中选择。
> 不接受子串命中、不接受自造 subject_id。
> 纯函数集合，无副作用。

**依赖**：`title_normalizer.normalize_title`、`chat.pending_action.SubjectResolutionCandidate`。

---

### 文件 3 · `subject_authority.py`（新，约 80 行）

**职责**：调用 Business `/batch` 接口对候选做权威校验，过滤掉非动画 / 已下架 / NSFW 条目。

**导出**：
- `filter_authoritative(subject_ids, business, token) -> tuple[dict[int, dict] | None, dict | None]`

**私有**：
- `_batch_items(response) -> list[Any]`
- `_is_safe_batch_item(item) -> bool`
- `_display_name(detail, fallback) -> str`

**docstring**：
> 权威安全校验：调用 Business `/batch` 过滤候选，只保留 `active=true` / `type=2` / `nsfw=false` 的动画条目。
> 基础设施错误（超时、5xx）返回 `(None, error)`，绝不伪装成「无候选」。
> 副作用：发起一次 Business HTTP 调用。

**依赖**：`agent.ports.BusinessGateway`、`candidate_matcher.dedup_ids` 和 `_safe_subject_id`。

**注意**：`_safe_subject_id` 在 `candidate_matcher` 是私有，但这里要用——把它从 `_safe_subject_id` 改为 `safe_subject_id`（去掉下划线前缀）放进 `candidate_matcher.py` 的公开导出？**不，这会扩大 API 面**。选择：`subject_authority.py` 内部用一个本地副本，或让它 import 私有名（Python 允许，只是惯例不佳）。

**决定**：让 `_safe_subject_id` 在 `candidate_matcher.py` 保持私有，`subject_authority.py` 通过 `from app.agent.client.actions.candidate_matcher import _safe_subject_id` 显式 import 私有名（**罕见但合法**，加注释说明）。

---

### 文件 4 · `subject_resolution.py`（保留，目标 < 100 行）

**职责**：解析主流程编排 + 工具入口（`build_subject_resolution_tools`）+ SUBJECT_RESOLUTION 状态触发。

**导出**：
- `build_subject_resolution_tools(business, retrieval)`（唯一对外入口）
- `resolve_candidates(...)`、`finalize_resolution(...)`（被 `collection_type` 复用）
- re-export 兼容符号：`dedup_ids`, `filter_authoritative`, `normalize_title`, `select_candidate`, `unique_exact_match_ids`

**保留**：
- `resolve_candidates`（主流程）
- `finalize_resolution`（结果落地）
- `build_resolution_action`（构造 PendingAction）
- `_business_lookup` / `_rag_lookup`（解析的两个阶段）
- `build_subject_resolution_tools` + 两个工具函数
- `_selection_message`、所有常量（`_RESOLUTION_TTL_SECONDS` 等）

**docstring**：
> 单标题「加入想看 / 设类型」的确定性解析入口。
> 输入标题或显式 ID，输出三种之一：错误 / 无匹配 / 唯一精确预览或 SUBJECT_RESOLUTION 待选择。
> 副作用：通过 `emit_pending_action_set/clear` 触发状态变更；自身不持久化。

**顶部 re-export**：
```python
# 兼容旧 import 路径（tests 与其他 actions 在用），重构后建议从新模块直接 import
from app.agent.client.actions.title_normalizer import normalize_title  # noqa: F401
from app.agent.client.actions.candidate_matcher import (  # noqa: F401
    dedup_ids,
    select_candidate,
    unique_exact_match_ids,
)
from app.agent.client.actions.subject_authority import filter_authoritative  # noqa: F401
```

## 依赖方向（单向）

```
title_normalizer.py   ←  无依赖
        ↑
candidate_matcher.py  ←  依赖 title_normalizer + pending_action.SubjectResolutionCandidate
        ↑
subject_authority.py  ←  依赖 candidate_matcher._safe_subject_id / dedup_ids + ports.BusinessGateway
        ↑
subject_resolution.py ←  依赖以上三者 + wishlist / collection_state / write_guard / middleware / pending_action / pending_events / rag.*
```

**无环证明**：每一层只依赖下层，且最上层 `subject_resolution` 不被任何下层 import。

## 行数估算

| 文件 | 估算行数 | 当前行数 | 备注 |
|---|---|---|---|
| `title_normalizer.py` | ~35 | — | normalize_title + 2 个正则 + docstring |
| `candidate_matcher.py` | ~110 | — | 4 个公开函数 + 3 个私有 + docstring |
| `subject_authority.py` | ~85 | — | 1 个公开 + 3 个私有 + docstring |
| `subject_resolution.py` | ~330 | 564 | 减去上面 3 个文件搬走的 ~230 行 |

**等等，主文件还有 ~330 行，远超 PRD 说的 < 100 行。**

重新审视：剩下 330 行主要是 `resolve_candidates` (~70) + `finalize_resolution` (~50) + `_business_lookup` (~50) + `_rag_lookup` (~50) + `build_resolution_action` (~25) + `build_subject_resolution_tools` (~90) + re-export / docstring。

**调整 PRD 验收信号**：把「主文件 < 100 行」改为「主文件 < 350 行」+「4 个文件每个 < 200 行」+「总行数从 564 → 560 左右（重导出 + docstring 略增）」。

**真正的收益**不在行数，而在：
- 归一化 / 匹配 / 校验三个职责可以**独立单测**（未来加测试不必绕过工具入口）
- 复用方（未来的「评分」写链路）可以只 import `title_normalizer`，而不是 564 行整包
- 每个文件**三句话讲清契约**

PRD 需要修正这一点。

## 迁移步骤（高层）

1. 读 `prd.md`，确认范围与约束
2. 创建 `title_normalizer.py`，把 `normalize_title` + `_PUNCTUATION_RE` + `_WHITESPACE_RE` 搬过去
3. 创建 `candidate_matcher.py`，把 `unique_exact_match_ids` / `dedup_ids` / `select_candidate` + 私有辅助搬过去
4. 创建 `subject_authority.py`，把 `filter_authoritative` + `_batch_items` / `_is_safe_batch_item` / `_display_name` 搬过去
5. 改 `subject_resolution.py`：删除已搬走的代码 + 加 re-export + 改 import + 更新 docstring
6. 跑 `pytest tests/agent/test_subject_resolution.py`，必须 29 passed 2 xfailed
7. 跑 `pytest`，必须 585 passed 6 xfailed
8. 跑 `ruff check app/`，无新增 warning
9. 跑 `python -c "from app.agent.client.actions.subject_resolution import build_subject_resolution_tools, dedup_ids, filter_authoritative, normalize_title, select_candidate, unique_exact_match_ids"`，确认 re-export 完整

## Rollback

每个迁移步骤独立 commit。任意一步失败：
```bash
git reset --hard HEAD~1   # 撤到上一步
```

完全撤清：
```bash
git reset --hard <任务开始前 commit>
```

## Risks

| 风险 | 概率 | 缓解 |
|---|---|---|
| 漏 import 某个私有名导致 import error | 中 | 每步跑 pytest + ruff |
| re-export 顺序导致 import 循环 | 低 | 按依赖方向单向 import；出现环立刻回滚 |
| `collection_type.py` 引用了未 re-export 的内部函数 | 低 | 已盘点：只用了 `finalize_resolution` / `resolve_candidates`，保留在主文件 |
| `_safe_subject_id` 跨文件私有 import 触发 ruff SLF001 | 中 | ruff 配置允许；若不允许，把 `_safe_subject_id` 改公开（去下划线）并加 docstring |
