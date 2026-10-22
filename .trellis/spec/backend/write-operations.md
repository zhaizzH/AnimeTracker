# Agent 安全写操作契约

> 从 [Agent 编排与流式协议](./agent-guidelines.md) 拆出（2026-10-22），因为主文件已达单文件注入上限的 82%。
> 本章是**预览 → 用户确认 → 执行**协议的单一来源；`agent-guidelines.md` 只保留摘要与指针。

## 安全写操作

1. 预览工具查询权威 Business 数据并生成强类型 `PendingAction`。
2. `ChatService` 按用户与会话把动作写入 Redis；成功写入后才允许把动作视为可确认。
3. 用户明确确认后，执行工具只读取 `InjectedState` 中的 action 或 preview ID。
4. **确认是代码级硬门禁，不只靠提示词**：`AgentState.write_confirmed` 只由 `gateway_router` 依据当前回合 `_is_explicit_confirmation` 确定性设置，模型无法通过工具参数改写；三条写链路的 `execute_*` 都先过共享守卫 `write_guard.require_confirmed_write`（用户 → 动作类型 → 用户绑定 → TTL → `write_confirmed`），非确认回合即使模型调用 `execute_*` 也一律拒写、Business 零调用。选择状态（`SUBJECT_RESOLUTION`）下的"确认"只是选择意图，不产生写入类动作，因此不会触发写入。
5. `WishlistPendingAction` 与 `SetCollectionTypePendingAction` 携带服务端生成的 `action_id`（每次 SET/REPLACE 重新生成），用于持久化层版本失效与 trace 关联；它是服务端持有的版本标识，**不是模型回传令牌**，写入判定不依赖模型提供它。`CollectionProgressPendingAction` 继续用 Business 的 `preview_id`。
6. 基础设施错误导致结果不确定时保留动作；`PREVIEW_CHANGED` 必须重新确认。
7. 取消只清理待确认状态，不修改业务数据。

参考：`app/agent/client/actions/wishlist.py`、`collection_progress.py`、`collection_type.py`、`write_guard.py`、`app/chat/pending_action.py`。

> 持久化层面（键模板、600 秒 TTL、判别联合往返、信封字段蛇形/business 字段驼峰、preview 版本绑定）由 `backend/agent/tests/contracts/test_preview_contract.py` 自动钉住，字段大小写易误，详见 [Agent↔Business 契约测试](./contract-tests.md#pendingaction-字段大小写易误解单列)。

#### 待确认动作持久化失败矩阵

`streaming.py` 会记录并报告 `on_pending_action` 异常，然后继续发送结束事件；调用方必须依据 `status` 错误事件执行重试提示，不能把动作宣告为已持久化。任何新增或修改必须满足以下契约：

| 条件 | 必须行为 |
|---|---|
| 新建/替换动作写 Redis 成功 | 返回可确认状态，并绑定 `user_id`、`session_id`、`preview_id`/nonce 与 TTL |
| 新建/替换动作写 Redis 失败 | 不宣告动作可确认；不得继续执行不可见动作；向调用方返回可重试的失败语义 |
| 已有旧动作且替换失败 | 不能让下一次确认误执行旧动作；清除旧动作或使其版本失效，并记录可关联 trace |
| 用户取消 | 仅删除同一用户/会话的待确认动作，不能修改 Business 数据 |
| 确认时 preview 已变化/过期 | 返回 `PREVIEW_CHANGED`/过期错误，必须重新预览确认 |

最低回归场景：预存旧动作 → `REPLACE` 失败 → 再次确认；断言旧动作不会被执行。

#### Scenario: 单标题「加入想看」确定性解析与 SUBJECT_RESOLUTION 候选状态

##### 1. Scope / Trigger

- 触发：修改 Agent 单标题加入想看链路（`resolve_subject_by_title` / `select_resolved_subject`）、`SUBJECT_RESOLUTION` 待确认状态，或 gateway 对该状态的路由。
- 目的：保证标题→条目走 Business 优先、RAG 仅在“成功空结果”时回退、权威校验后唯一精确候选才进预览；多候选或歧义进入受控选择状态，绝不把接口异常伪装成无结果，也绝不自动选中相似候选。
- 边界：只覆盖“加入想看”（type=1，`/collections/{id}/wishlist`）。“加入追番/在看”（type=3）当前 Agent 无写工具，属另一任务。

##### 2. Signatures

- `resolve_subject_by_title(title="", subject_id=None) -> dict`；`select_resolved_subject(choice: int | str) -> dict`（`user`、`pending` 由 `InjectedState` 注入）。
- `SubjectResolutionPendingAction{type:"SUBJECT_RESOLUTION", user_id, expires_at, query, candidates:[{subjectId,subjectName,matchSource,matchType}]}`，camelCase `by_alias`，复用 Agent Redis 键与 600 秒 TTL。
- 复用 `BusinessGateway.search_subjects(query, *, token, size=15)` → `GET /api/client/subjects/search`（响应 `content[]`，字段 `id/name/nameCn`，无 `active/nsfw`）；`batch_subjects(subject_ids, *, token, exclude_collected)` → `POST /api/client/subjects/batch`（`items[]` 含 `id/type/nsfw/active/name/nameCn`，另有 `missingIds/filteredIds`；`exclude_collected` 为 keyword-only 且无默认值）。
- 复用 `app/agent/client/actions/wishlist.py::build_wishlist_preview(subjects,user,business)` 与 `RetrieveSubjectsUseCase.execute(query, mode="search", user)`。

##### 3. Contracts

- 顺序：显式 `subject_id` → 跳过名称搜索但仍 `/batch`；否则 Business `/search`（原始标题，仅去外围空白）→ 归一化唯一精确命中 → 仅“成功且候选为空”才回退 RAG（`mode="search"`，只传 `semantic_query`）。
- 归一化只做字符层面：NFKC + casefold + 安全标点当分隔符 + 连续空白折叠 + strip。禁止“第二季/第2季/2nd Season/II”等语义转换；只有真实标题或工具证据 `aliases` 可命中，子串命中不算精确。
- `/batch` 只保留 `active is True`、`type==2`、`nsfw is False`；`missingIds/filteredIds` 丢弃；`excludeCollected=false`（收藏与否由预览阶段判断，不覆盖既有收藏）。
- 结果分流：权威校验后 0 → “没有找到匹配项”，不预览不写入；1 且唯一精确 → `build_wishlist_preview`（仍走预览→明确确认→幂等写入）；多个，或“非唯一精确”（含单个歧义/相似候选）→ 保存 `SUBJECT_RESOLUTION`，绝不自动预览。
- 选择：只接受注入的 `SUBJECT_RESOLUTION`，按 1-based 序号或归一化后唯一名称从服务端候选中选择，模型不能提交任意 `subjectId`；选中后重新 `/batch` 再进预览，状态由 `ADD_TO_WISHLIST` 覆盖（SET/REPLACE 都调用 `save_pending_action` 覆盖同一键）。
- gateway：`pending.type==SUBJECT_RESOLUTION` 时任何回合确定性路由 `recommend_agent`；确认词只对 `ADD_TO_WISHLIST/COLLECTION_PROGRESS_UPDATE` 触发写入路由，选择状态下的“确认/好”只是选择意图，不得当写入确认。

##### 4. Validation & Error Matrix

| 条件 | 必须行为 |
|---|---|
| Business `/search` 超时/5xx/401/坏响应 | 返回错误语义；不回退 RAG；不建状态；不预览 |
| Business 成功非空但无唯一精确命中 | 保留安全候选进 `SUBJECT_RESOLUTION`；不得当空结果回退 RAG |
| Business 成功空结果 | 回退 RAG |
| RAG `available=false` 或异常 | 返回“候选解析暂时不可用”；不伪装无结果；不预览；不建状态 |
| RAG 多候选或无唯一精确命中 | 作为候选进 `SUBJECT_RESOLUTION`；相似度最高也不自动预览 |
| `/batch` 过滤后 0 | “没有找到匹配项”，不预览不写入 |
| 选择时 user 不匹配 / 过期 / 候选已失效 | `CLEAR` 并返回错误 |
| 选择名称不唯一 / 序号越界 / 无待选择状态 | 返回错误；名称不唯一或越界时保留状态供重选 |

##### 5. Good/Base/Bad Cases

- Good：标题在 Business 唯一精确命中 → `/batch` 通过 → 预览 → 用户明确确认 → 幂等写入，不覆盖既有收藏。
- Base：多候选 → `SUBJECT_RESOLUTION` → 用户按序号选 → 重新 `/batch` → 预览 → 确认。
- Bad：把 Business 500 当空结果回退 RAG；把“第2季”归一化成“第二季”自动选中；RAG 相似度最高的单候选直接预览；把选择状态下的“确认”当写入确认。

##### 6. Tests Required

- `tests/agent/test_subject_resolution.py`：归一化仅字符层面（`第二季 != 第2季`）、唯一精确/多命中、`dedup_ids` 拒 bool 与非正数、`/batch` 过滤 `active/type/nsfw` 与基础设施错误、Business 命中不回退 RAG、Business 错误不回退不预览、空结果回退 RAG、RAG 不可用不伪装、非空无精确进 resolution、显式 `subject_id` 跳搜索仍 `/batch`、选择按序号/唯一名/歧义/越界/用户不匹配/过期/已收藏/失效重校验、gateway 对 `SUBJECT_RESOLUTION` 路由、判别联合序列化往返。
- 运行 `uv run pytest tests/agent` 与 `uv run pytest`。

##### 7. Wrong vs Correct

##### Wrong

```python
rows = business.search_subjects(title, token=token)
if not rows:                       # 把错误/超时也当成空结果
    rows = rag_fallback(title)
picked = max(rows, key=lambda r: r["score"])   # 相似度最高自动选中
preview_add_to_wishlist([picked])              # 绕过唯一精确与歧义判定
```

##### Correct

```python
stage = _business_lookup(title, user, business)
if stage["error"]:
    return stage["error"]                       # 基础设施错误：不回退、不预览
candidates, exact_unique = stage["candidates"], stage["exact_unique"]
if stage["empty"]:
    stage = _rag_lookup(title, user, retrieval)  # 仅“成功空结果”回退 RAG
valid, err = filter_authoritative(ids, business, token)  # active/type2/nsfw，excludeCollected=false
if len(survivors) == 1 and exact_unique:
    return build_wishlist_preview(...)           # 预览 → 明确确认
emit_pending_action_set(build_resolution_action(...)) # 多个/歧义 → SUBJECT_RESOLUTION，不自动预览
```

#### Scenario: 按标题设置收藏类型（/save）与写入意图路由

##### 1. Scope / Trigger

- 触发：修改 Agent“按标题设置/变更收藏类型”链路（`set_subject_collection` / `execute_set_collection_type`）、`SET_COLLECTION_TYPE` 待确认动作、`BusinessGateway.save_collection`，或 gateway 写入意图路由。
- 边界：写入任意收藏类型 1..5（想看/看过/在看(追番)/搁置/抛弃），经 `POST /api/client/collections/{id}/save`。普通“加入想看”仍走幂等 `/wishlist`（不覆盖）；显式“设为/标记为/改成 <类型>”走 `/save`。

##### 2. Signatures

- `set_subject_collection(collection_type: Literal[1,2,3,4,5], title="", subject_id=None) -> dict`；`execute_set_collection_type() -> dict`（`pending`/`user` 注入）；`cancel_set_collection_type()`。
- `SetCollectionTypePendingAction{type:"SET_COLLECTION_TYPE", user_id, expires_at, subjectId, subjectName, targetType, currentType(int|None), action("ADD"|"CHANGE")}`，camelCase by_alias，600s TTL。
- `BusinessGateway.save_collection(subject_id, *, collection_type, token, rate=None, ep_status=None)` → `POST /api/client/collections/{id}/save`，body `{"type","rate","epStatus"}`（对齐 `CollectionUpdateDTO`）。
- `SubjectResolutionPendingAction.collection_type`（alias `collectionType`，默认 None）：多候选选中后要设置的目标类型；None=回到想看预览（向后兼容）。

##### 3. Contracts

- 解析复用 09-16：`resolve_candidates`（显式 id 跳搜索仍 `/batch`；Business 首查；仅成功空结果回退 RAG；`/batch` 只留 active/type2/nsfw，excludeCollected=false）+ `finalize_resolution`（0 无匹配 / 1 唯一精确预览 / 多或歧义 SUBJECT_RESOLUTION 且携带 collection_type）。
- `save_collection` 语义（源码 `CollectionServiceImpl.saveOrUpdate`）：条目不存在→404；已收藏且同类型、rate/epStatus 无变化→409；已收藏但类型不同或有变化→UPDATE 覆盖；未收藏→INSERT。`/save` **不做** active/nsfw 安全过滤，安全边界仍由 Agent `/batch` 承担。
- 预览三态：未收藏→ADD；已在目标类型→NOOP（不发待确认动作、不写入，避免 409）；他类型→CHANGE（必须在预览中展示“当前→目标”，绝不静默覆盖）。
- 写入只在用户对 ADD/CHANGE 明确确认后由 `execute_set_collection_type` 执行，且只读注入的 `SET_COLLECTION_TYPE`，模型不能自造 subjectId/类型。
- 路由：写入意图 = 写入动词 + 可选填充词 + 类型名的复合正则（覆盖“添加到我的追番”“把这部设为在看”等插词），保留否定前缀守卫；纯查询（追番进度/追番日程/我在看什么/我收藏了哪些）不得误触发。`SET_COLLECTION_TYPE` 加入 `RECOMMEND_PENDING_ACTION_TYPES`，明确确认可确定性路由 recommend_agent 执行。

##### 4. Validation & Error Matrix

| 条件 | 必须行为 |
|---|---|
| `collection_type` 非 1..5 / 非整数 | 工具 schema(Literal) 拒绝；不写入 |
| 解析基础设施错误 / RAG 不可用 | 返回错误语义；不回退、不预览、不建状态 |
| 已在目标类型（NOOP） | 不发待确认动作、不写入；如实告知已在该列表 |
| 他类型（CHANGE） | 预览展示 当前→目标，确认后才 `/save` 覆盖 |
| `/save` 返回成功(None) | `SAVED`，clear，汇报 ADD/CHANGE |
| `/save` 409 | `ALREADY_COLLECTED`，clear，不算失败 |
| `/save` 404 | 报错，clear，不宣称写入 |
| `/save` 基础设施错误(code 为 None) | 保留待确认动作供重试，不宣称成功 |
| 未确认 / 取消 | 不写入；cancel 仅 clear |

##### 5. Good/Base/Bad Cases

- Good：标题唯一精确→预览 ADD→确认→`/save` 成功→clear。
- Base：已在看再“加入追番”→NOOP，不写入、不 409。
- Bad：把“我在看什么/追番日程”误路由到写入；CHANGE 不在预览展示就覆盖；`/save` 409 当成失败；基础设施不确定却宣称已写入。

##### 6. Tests Required

- `tests/agent/test_collection_type.py`：预览 ADD/NOOP/CHANGE 与状态错误、set 唯一精确/多候选(带 collection_type)/NOOP 清理/显式 id/无匹配、execute 成功/409/404/基础设施保留/无待确认、选择后按 collection_type 分派、SET_COLLECTION_TYPE 与 SUBJECT_RESOLUTION(带/不带 collectionType) 序列化往返、工具 schema 含 collection_type。
- `tests/agent/test_write_intent_routing.py`：写入短语命中（含插词）、否定不误触发、纯查询不误触发、SET_COLLECTION_TYPE 确认强制路由、非确认不强制。
- 运行 `uv run pytest tests/agent` 与 `uv run pytest`。

##### 7. Wrong vs Correct

##### Wrong

```python
# 直接把“追番/收藏”字样当写入意图，且不预览就覆盖类型
if "追番" in text or "收藏" in text:
    business.save_collection(sid, collection_type=3, token=token)  # 静默覆盖、无确认
```

##### Correct

```python
if _is_explicit_recommendation_request(text):   # 动词+类型名复合正则，排除查询
    route = "recommend_agent"
preview = build_collection_type_preview(sid, name, target, user, business)  # ADD/NOOP/CHANGE
if preview["action"] == "CHANGE":
    show_user(f"从{preview['currentType']}改为{target}")   # 变更可见
# 仅在用户明确确认后：
result = business.save_collection(sid, collection_type=target, token=token)
```
