# 优化项 1 · Implement：拆 subject_resolution.py

> PRD：[`prd.md`](./prd.md) · Design：[`design.md`](./design.md)

## 前置检查

- [ ] 在 `backend/agent/` 下，确认基线测试全绿：`uv run pytest tests/agent/test_subject_resolution.py -v` 输出 `29 passed, 2 xfailed`
- [ ] 确认基线：`uv run pytest` 输出 `585 passed, 6 xfailed`
- [ ] 确认基线：`uv run ruff check app/` 无 warning
- [ ] `git status` 干净（除了 `.trellis/tasks/` 下的本任务文件）

## 执行步骤

每一步独立 commit，每步后跑「快速验证」。

### Step 1 · 创建 `title_normalizer.py`

**操作**：
- 新建 `app/agent/client/actions/title_normalizer.py`
- 从 `subject_resolution.py` 剪贴：`normalize_title`、`_PUNCTUATION_RE`、`_WHITESPACE_RE`
- 加上 design.md 文件 1 的 docstring
- `subject_resolution.py` 删除已剪切的代码，改为 `from app.agent.client.actions.title_normalizer import normalize_title` + re-export

**快速验证**：
```bash
cd backend/agent
uv run pytest tests/agent/test_subject_resolution.py -x
```

**commit**：
```
refactor(agent): extract title_normalizer from subject_resolution
```

---

### Step 2 · 创建 `candidate_matcher.py`

**操作**：
- 新建 `app/agent/client/actions/candidate_matcher.py`
- 从 `subject_resolution.py` 剪贴：
  - 公开：`unique_exact_match_ids`、`dedup_ids`、`select_candidate`
  - 私有：`_safe_subject_id`、`_candidate_titles`、`_as_index`、`_ORDINAL_RE`
- import：`from app.agent.client.actions.title_normalizer import normalize_title`、`from app.chat.pending_action import SubjectResolutionCandidate`
- 加上 design.md 文件 2 的 docstring
- `subject_resolution.py` 删除已剪切的代码，加 re-export

**快速验证**：
```bash
uv run pytest tests/agent/test_subject_resolution.py -x
uv run ruff check app/agent/client/actions/
```

**commit**：
```
refactor(agent): extract candidate_matcher from subject_resolution
```

---

### Step 3 · 创建 `subject_authority.py`

**操作**：
- 新建 `app/agent/client/actions/subject_authority.py`
- 从 `subject_resolution.py` 剪贴：
  - 公开：`filter_authoritative`
  - 私有：`_batch_items`、`_is_safe_batch_item`、`_display_name`
- import：
  ```python
  from app.agent.client.actions.candidate_matcher import dedup_ids, _safe_subject_id  # noqa: SLF001
  from app.agent.ports import BusinessGateway
  ```
  （如果 ruff SLF001 报错且配置不允许 noqa，把 `_safe_subject_id` 在 `candidate_matcher.py` 改公开并加 docstring）
- 加上 design.md 文件 3 的 docstring
- `subject_resolution.py` 删除已剪切的代码，加 re-export

**快速验证**：
```bash
uv run pytest tests/agent/test_subject_resolution.py -x
uv run ruff check app/agent/client/actions/
```

**commit**：
```
refactor(agent): extract subject_authority from subject_resolution
```

---

### Step 4 · 更新 `subject_resolution.py` 模块 docstring + re-export 头

**操作**：
- 把 `subject_resolution.py` 顶部 docstring 改为 design.md 文件 4 的三句话
- 确保顶部 re-export 完整：
  ```python
  # 兼容旧 import 路径（tests / collection_type / recommend 在用），新代码建议直接从源模块 import
  from app.agent.client.actions.title_normalizer import normalize_title  # noqa: F401
  from app.agent.client.actions.candidate_matcher import (  # noqa: F401
      dedup_ids,
      select_candidate,
      unique_exact_match_ids,
  )
  from app.agent.client.actions.subject_authority import filter_authoritative  # noqa: F401
  ```
- 确认保留：`resolve_candidates`、`finalize_resolution`、`build_resolution_action`、`_business_lookup`、`_rag_lookup`、`build_subject_resolution_tools`、`select_resolved_subject`、`resolve_subject_by_title`、`_selection_message`、所有常量

**快速验证**：
```bash
uv run pytest tests/agent/test_subject_resolution.py -v
uv run pytest tests/agent/test_collection_type.py -v
uv run python -c "from app.agent.client.actions.subject_resolution import build_subject_resolution_tools, dedup_ids, filter_authoritative, normalize_title, select_candidate, unique_exact_match_ids; print('re-export OK')"
```

**commit**：
```
refactor(agent): update subject_resolution docstring and re-exports
```

---

### Step 5 · 全量回归

**操作**：
```bash
cd backend/agent
uv run pytest                                    # 585 passed, 6 xfailed
uv run ruff check app/                           # 无 warning
wc -l app/agent/client/actions/subject_resolution.py  # < 350
wc -l app/agent/client/actions/title_normalizer.py    # < 60
wc -l app/agent/client/actions/candidate_matcher.py   # < 200
wc -l app/agent/client/actions/subject_authority.py   # < 200
```

**如果 585 passed 退到 < 585**：逐步回滚到上一个绿点，定位问题。

**commit**（如有 lint/格式微调）：
```
chore(agent): lint/format after subject_resolution split
```

---

### Step 6 · 验收对照

逐项检查 `prd.md` 的 Acceptance Criteria：

- [ ] `subject_resolution.py` < 350 行
- [ ] 4 个文件每个 < 200 行
- [ ] 3 个新文件 docstring ≤ 3 句话
- [ ] `subject_resolution.py` docstring ≤ 3 句话
- [ ] `test_subject_resolution.py` 29 passed, 2 xfailed（与基线一致）
- [ ] 全套 585 passed, 6 xfailed（与基线一致）
- [ ] ruff 无新增 warning
- [ ] `git diff --stat $(git merge-base HEAD main)..HEAD -- backend/agent/` 只动 4 个文件

---

## Review Gates（每个 Step 结束问自己）

| Gate | 检查 |
|---|---|
| G1 | 这一步删掉的代码，是否全部在新文件里？没有「顺手优化」 |
| G2 | re-export 是否完整？测试 import 的 6 个符号都能从 `subject_resolution` 拿到 |
| G3 | import 是否单向？没有形成环 |
| G4 | docstring 是否 ≤ 3 句话讲清契约？没有抄袭原文件的冗长注释 |

## Rollback Plan

任意 Step 失败：
```bash
git reset --hard HEAD~1    # 撤到上一个绿点
```

完全放弃本任务：
```bash
git reset --hard $(git merge-base HEAD main)
```

## Completion Signal

所有 Step commit 完成 + 验收对照全过 + 父任务 PRD 的「辅信号」前两条勾选。
