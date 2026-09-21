# 按标题设置收藏类型与写入意图路由

## Goal

让用户用单个番剧标题请求写入任意收藏类型（想看/看过/在看/搁置/抛弃，type=1..5）时，Agent 能安全解析到正确条目、预览“当前状态 → 目标类型”、经明确确认后通过 Business `POST /api/client/collections/{subjectId}/save` 幂等落地；同时修复 gateway 路由，使含“加入/添加到/标记为 追番·在看·看过·搁置…”等写入意图的请求确定性进入 recommend_agent，而不是落到纯查询的 search_agent。复用 09-16 已建立的标题解析链路（Business 优先、成功空结果才回退 RAG、`/batch` 权威校验、`SUBJECT_RESOLUTION` 候选状态、预览→明确确认）。

## Background

- 复现：用户说“把《相反的你和我 第二季》添加到我的追番”，被 gateway 路由到 search_agent（工具集只有查询类），该节点没有写工具，因此只检索、未写入。
- 能力缺口：Agent 现有收藏写工具只有想看（`/wishlist`，type=1，幂等不覆盖）与进度更新（对既有在看条目改 epStatus）。type=2..5 的写入、以及任何“改类型”在 Agent 侧完全没有工具。
- Business 已存在写接口 `POST /api/client/collections/{subjectId}/save`（`CollectionUpdateDTO{type:1..5 必填, rate:0..10 可选, epStatus:>=0 可选}`），返回 `Result<Void>`。其语义（源码 `CollectionServiceImpl.saveOrUpdate`）：
  - 条目不存在 → 404「条目不存在」；`/save` **不做** active/type=2/nsfw 安全过滤，安全边界仍由 Agent 侧 `/batch` 承担。
  - 已收藏且**同类型、rate/epStatus 均无变化** → 409「该条目已收藏，请勿重复收藏」。
  - 已收藏但**类型不同或 rate/epStatus 变化** → UPDATE，**覆盖**类型/评分/进度。
  - 未收藏 → INSERT，rate/epStatus 缺省为 0。
- 路由缺口：`app/agent/client/gateway.py::_is_explicit_recommendation_request` 只识别想看/收藏类词，不含“追番/在看/看过/搁置/抛弃/标记为”；`resources/prompt/client/gateway_prompt.md` 里 recommend_agent 仅描述为“推荐番剧”，无写入路由说明，LLM 会判给 search_agent。
- 术语：追番=在看(3)；收藏类型 1=想看 2=看过 3=在看 4=搁置 5=抛弃（与 DTO 注释、`collection_progress` 一致）。

## Resolved Decisions（原 Open Questions，已由用户确认）

1. **已收藏处理：按用户意图操作。** 预览阶段查询当前收藏状态，明确展示“当前类型 → 目标类型”的变更（含 rate/epStatus 是否改动），经用户确认后用 `/save` 覆盖；已是目标类型且无变化时视为无需写入并如实告知（避免触发 409）。绝不静默覆盖——任何类型变更都必须在预览中可见并二次确认。
2. **写入范围：全部类型 1..5。** 做成通用“按标题设置收藏类型”，由模型把用户措辞映射到目标类型（想看1/看过2/在看3/搁置4/抛弃5），映射不确定时先向用户澄清而非猜测。
3. **路由修复：词表 + 提示词双保险。** 扩充 `_is_explicit_recommendation_request` 的确定性写入词表（加入/添加到/标记为 + 追番/在看/看过/搁置/抛弃/想看），并在 gateway 提示词补“写入收藏”路由说明；同时显式排除“查追番进度/追番日程/我收藏了什么”等非写入查询意图，避免误触发。

## Requirements

1. 复用 09-16 的解析原语（安全归一化、唯一精确匹配、去重、`/batch` 权威校验、候选选择、`SUBJECT_RESOLUTION`）把标题解析为唯一安全候选；显式 `subjectId` 跳搜索但仍 `/batch`；仅 Business 成功空结果才回退 RAG；接口异常不伪装无结果、不回退、不预览。
2. 新增“按标题设置收藏类型”的预览→确认→写入链路：预览展示目标类型与当前收藏状态（未收藏 / 已在目标类型 / 从 A 改为 B），确认后调用 `/save`；正确解释 None=成功、409=已收藏无变化、404=条目不存在。
3. `SUBJECT_RESOLUTION` 需承载“选中后要执行的目标类型”，使多候选选择后仍能进入正确类型的预览；保持 09-16 想看链路语义与既有 JSON 向后兼容（新增字段带默认值）。
4. 想看(type=1) 的普通“加入想看”仍走 09-16 的幂等 `/wishlist` 链路（不覆盖）；“把 X 改成/标记为 <类型>”等显式设置意图走新的 `/save` 链路。两条路径的边界在设计中明确，不得互相回归。
5. 修复 gateway 路由（词表 + 提示词），写入意图确定性进入 recommend_agent，非写入查询不被误触发；`SUBJECT_RESOLUTION` 的选择/确认语义沿用 09-16。
6. recommend_agent 注册新工具并在提示词说明：单标题写入必须走确定性解析入口、候选选择、目标类型映射与两段式确认；不得用检索/推荐工具替代写入解析，不得编造 subjectId 或类型。
7. 09-16 的想看链路、多番剧推荐批量加入想看、进度更新流程与其回归测试保持不变。

## Acceptance Criteria

- [ ] “把 X 添加到追番/在看”“把 X 标记为看过”等被确定性路由到 recommend_agent；“我的追番进度/追番日程/我收藏了啥”仍走查询节点，不误触发写入路由。
- [ ] 单标题写入先 Business `/search`、成功空结果才回退 RAG；Business 异常不触发 RAG、不预览；候选经 `/batch` 只留 `active/type=2/nsfw=false`，`excludeCollected=false`。
- [ ] 唯一精确候选进入对应类型预览；多个/歧义进入 `SUBJECT_RESOLUTION`（携带目标类型），选择后重新 `/batch` 再预览；无有效候选回复“没有找到匹配项”。
- [ ] 预览正确展示：未收藏→将设为<类型>；已在目标类型→无需写入并告知；不同类型→从<当前>改为<目标>并要求确认。
- [ ] 明确确认后经 `/save` 写入目标类型；409/404 被正确解释；未确认或取消绝不写入；不静默覆盖。
- [ ] 目标类型只能来自受控枚举(1..5)与用户措辞映射，模型不能提交任意 subjectId 或越界类型。
- [ ] 复用而非复制 09-16 解析/归一化/候选构件；想看链路与多番剧推荐收藏、进度更新回归测试全部通过。
- [ ] `uv run pytest tests/agent` 与 `uv run pytest` 全绿；未改 Business API/OpenAPI/前端（仅新增 Agent 侧网关方法与工具）。

## Out of Scope

- 不改 09-16 想看写链路语义（仅复用其解析/候选构件）。
- 不改 Business `/save`、DTO、Controller、Schema、OpenAPI 或前端（endpoint 已存在，仅 Agent 消费）。
- 不重写通用 RAG 检索，不启用未接入的实体名称解析器，不新增收藏类型枚举。

## Notes

- 复杂任务：`task.py start` 前必须补齐 `design.md` 与 `implement.md` 并通过规划摘要审核 + 用户批准。
- 相关既有实现：`app/agent/client/actions/subject_resolution.py`、`wishlist.py`、`collection_progress.py`、`app/agent/client/gateway.py`、`app/chat/pending_action.py`、`app/agent/ports.py` + `app/adapters/business_http.py`（新增 save 方法）、Business `CollectionController#/save` 与 `CollectionServiceImpl.saveOrUpdate`。
