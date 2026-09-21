# 技术设计：按标题设置收藏类型与写入意图路由

## 1. 边界与目标

只在 Agent 侧新增“按标题写入任意收藏类型(1..5)”的确定性链路，并修复 gateway 对写入意图的路由。Business `/api/client/collections/{subjectId}/save` 已存在，不改 Business/DTO/Controller/Schema/OpenAPI/前端；Agent 仅新增一个网关消费方法。09-16 的想看写链路语义与回归测试保持不变，本任务只复用其解析原语，并按需做行为保持的小重构。

复用点：`subject_resolution.py` 的安全归一化、唯一精确匹配、去重、`/batch` 权威校验、候选选择、`_business_lookup`/`_rag_lookup`、`SUBJECT_RESOLUTION` 状态；`wishlist.py` 的收藏状态检查与预览→确认骨架。

## 2. 数据流

```text
用户单标题写入请求(含目标类型) / 显式 subjectId
  -> gateway：写入意图(词表+提示词)确定性路由 recommend_agent
  -> set_subject_collection(title, collection_type=1..5, subject_id?)
       -> 复用 _resolve_candidates（Business /search → 唯一精确 / 成功空才回退 RAG → /batch 校验）
       -> 0 个：明确无匹配，停止
       -> 1 个(唯一精确)：进入 SET_COLLECTION_TYPE 预览
       -> 多个/歧义：保存 SUBJECT_RESOLUTION(collection_type=目标类型)，展示候选并停止
  -> 预览：查当前收藏状态
       -> 未收藏：将设为 <目标类型>
       -> 已在目标类型且无变化：无需写入，如实告知（不建待确认动作，避免 409）
       -> 已在他类型：从 <当前> 改为 <目标>（可见变更）
  -> 用户明确确认
  -> execute_set_collection_type（读注入的 SET_COLLECTION_TYPE）
  -> business.save_collection -> POST /collections/{id}/save {type,rate?,epStatus?}
       -> 成功(None)/409/404/基础设施错误 分别处理
```

想看(type=1)的普通“加入想看”仍走 09-16 的 `resolve_subject_by_title`→`/wishlist`（幂等、不覆盖）。“标记为/改成/设置为 <类型>”这类显式设置意图（含设为想看）走新的 `set_subject_collection`→`/save`。边界由提示词的动词规则区分，二者互不回归。

## 3. 解析与候选（复用 + 泛化）

- 从 `resolve_subject_by_title` 抽出内部 `_resolve_candidates(query, subject_id, user, business, retrieval) -> _Outcome`，产出：`error`（基础设施/RAG 不可用，直接返回不预览）、`no_match`、或 `survivors + exact_unique`。`resolve_subject_by_title`（想看）与 `set_subject_collection`（设类型）都调用它，保证解析顺序、归一化、`/batch` 安全边界只有一处实现。
- `SUBJECT_RESOLUTION` 泛化：`SubjectResolutionPendingAction` 新增可选字段 `collection_type: int | None`（alias `collectionType`）。None=看选择后回到想看预览（09-16 行为，旧 JSON 缺字段按默认 None 解析，向后兼容）；1..5=选择后进入该类型的 SET_COLLECTION_TYPE 预览。
- `select_resolved_subject` 依据 `pending.collection_type` 分派：None→`build_wishlist_preview`；否则→`build_collection_type_preview(target=collection_type)`。选择仍只接受注入状态、按序号或归一化唯一名称、重新 `/batch` 校验、校验用户/TTL。

## 4. 收藏状态检查与预览

- 抽出 `wishlist.py::_check_collection_state` 为共享 `check_collection_state(subject_id, user, business)`（放到 `app/agent/client/actions/collection_state.py`），wishlist 与 collection_type 复用；行为保持：404=未收藏，其它 4xx/5xx=真实错误，空成功信封(None)=未收藏，dict=已收藏并带 `type`。
- `build_collection_type_preview(subject_id, subject_name, target_type, user, business) -> dict`：
  - 查当前状态；错误→返回 error，不建动作。
  - 未收藏 → `{"action":"ADD","targetType":t}`，发 SET_COLLECTION_TYPE 待确认动作。
  - 已收藏且 `current==target` → `{"action":"NOOP","currentType":t}`，不发待确认动作（无写入，避免 409）。
  - 已收藏且 `current!=target` → `{"action":"CHANGE","currentType":c,"targetType":t}`，发 SET_COLLECTION_TYPE 待确认动作，预览明确展示变更。
  - 本任务不采集 rate/epStatus（保持最小）；`/save` 只传 type。若未来要改评分/进度另起任务。

## 5. 待处理状态：SET_COLLECTION_TYPE

在 `app/chat/pending_action.py` 判别联合新增：

```
SetCollectionTypePendingAction{
  type:"SET_COLLECTION_TYPE", user_id, expires_at,
  subjectId, subjectName, targetType(1..5), currentType(int|None), action("ADD"|"CHANGE")
}
```

- 复用 Agent Redis 键与 600s TTL；camelCase by_alias；加入 `PendingAction` 联合，`parse_pending_action_json` 保持判别解析，旧类型 JSON 兼容。
- gateway `RECOMMEND_PENDING_ACTION_TYPES` 增加 `SET_COLLECTION_TYPE`，使明确确认能确定性路由 recommend_agent 执行写入；`SUBJECT_RESOLUTION` 的路由沿用 09-16。

## 6. 写入与失败矩阵

- 新增网关方法（`ports.py` + `business_http.py`）：
  `save_collection(subject_id, *, collection_type, token, rate=None, ep_status=None) -> dict|None`
  → `POST /api/client/collections/{subjectId}/save`，body `{"type":collection_type,"rate":rate,"epStatus":ep_status}`。
- `execute_set_collection_type(pending: SET_COLLECTION_TYPE, user)`：校验注入动作类型/用户；调用 save_collection；结果解释：

| 条件 | 必须行为 |
|---|---|
| 返回 None/成功信封 | 写入成功；`emit_pending_action_clear()`；汇报 ADD 或 CHANGE(旧→新) |
| 409「已收藏」 | 视为已在目标类型（并发/重复）；clear；如实告知，不当失败 |
| 404「条目不存在」 | clear；报错，不宣称写入 |
| 基础设施错误(code 为 None) | 保留待确认动作供重试；不宣称成功（对齐 wishlist infra_error 语义） |
| 用户未确认/取消 | 不写入；`cancel_set_collection_type` 仅 clear |

## 7. 路由修复（词表 + 提示词双保险）

- `gateway.py`：把 `_is_explicit_recommendation_request` 的写入词表从只看想扩到全类型的**复合动词短语**（如“加入追番/添加到追番/标记为在看/设为看过/改成搁置/标记想看/加入在看”等），保留既有前缀否定守卫（不要/别/取消/不想）。**只加复合短语，不加裸名词**，避免“追番进度/追番日程/我的追番”被误触发。
- `resources/prompt/client/gateway_prompt.md`：给 recommend_agent 补一句职责——“按标题写入/修改收藏类型（想看/看过/在看/搁置/抛弃）”，并显式说明纯查询（追番进度、追番日程、我收藏了什么、番剧详情/剧集）仍归 search/discover。
- 双保险含义：确定性词表覆盖高频措辞并可写稳定回归；提示词让 LLM 路由覆盖未列举措辞。二者都不得把非写入查询路由到写入。

## 8. Agent 组合与提示词

- `recommend.py` 注册 `set_subject_collection`、`execute_set_collection_type`、`cancel_set_collection_type`（与既有工具并列）。
- `run.py::_build_pending_context` 增加 `SET_COLLECTION_TYPE` 分支（展示条目、当前→目标类型、必须用注入动作执行、不得编造）；`SUBJECT_RESOLUTION` 分支在存在 `collection_type` 时补充“选择后将设为 <类型>”。
- `recommend_agent_prompt.md` 增加：单标题写入必须走 `set_subject_collection`，目标类型只能来自受控枚举与用户措辞映射（想看1/看过2/在看3/搁置4/抛弃5），映射不确定先澄清；“加入想看”仍用 `resolve_subject_by_title`；预览→明确确认→`execute_set_collection_type`；类型变更必须在预览可见。

## 9. 错误与回滚

- 检索/`/batch` 基础设施错误：返回错误语义，不回退 RAG、不建状态、不预览（复用 09-16 契约）。
- `/save` 基础设施不确定：保留待确认动作，不宣称成功。
- 无数据库迁移。回滚只需回滚 Agent 代码；旧版本遇到未知 `SET_COLLECTION_TYPE`/带 `collectionType` 的 `SUBJECT_RESOLUTION` 时，按既有“损坏/未知状态安全清理”处理，不触发写入。

## 10. 可观测性与隐私

沿用现有 tool 状态事件与 trace id；不新增记录完整标题、类型明细、token 或工具参数的日志。

## 11. 受影响文件

- 新增：`app/agent/client/actions/collection_type.py`、`app/agent/client/actions/collection_state.py`、`tests/agent/test_collection_type.py`、`tests/agent/test_write_intent_routing.py`
- 修改：`app/chat/pending_action.py`（SET_COLLECTION_TYPE + SUBJECT_RESOLUTION.collection_type）、`app/agent/client/actions/subject_resolution.py`（抽 `_resolve_candidates`、选择分派）、`app/agent/client/actions/wishlist.py`（`_check_collection_state`→共享）、`app/agent/ports.py` + `app/adapters/business_http.py`（save_collection）、`app/agent/client/gateway.py`（词表 + RECOMMEND_PENDING_ACTION_TYPES）、`app/agent/client/recommend.py`（注册）、`app/agent/run.py`（上下文）、`resources/prompt/client/gateway_prompt.md`、`resources/prompt/client/recommend_agent_prompt.md`
- 不改：Business 全部、OpenAPI、前端、DB Schema。
