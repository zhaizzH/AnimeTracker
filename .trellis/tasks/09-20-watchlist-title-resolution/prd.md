# 按标题加入追番(在看)与写入意图路由

## Goal

让用户用单个番剧标题请求“加入追番/在看”时，Agent 能安全解析到正确条目并写入 type=3 收藏，且这类写入意图能确定性路由到具备写能力的 recommend_agent，而不是落到纯查询的 search_agent。复用 09-16 已建立的标题解析链路（Business 优先、成功空结果才回退 RAG、`/batch` 权威校验、`SUBJECT_RESOLUTION` 候选状态、预览→明确确认）。

## Background

- 复现：用户说“把《相反的你和我 第二季》添加到我的追番”，实际被 gateway 路由到 search_agent（工具集只有 `rag_search_subjects / get_subject_detail / get_episodes / get_my_collections / get_my_collection / get_my_stats / get_my_watch_profile / get_current_time`），该节点没有任何写工具，因此只做了检索、没有写入。
- 能力缺口：Agent 现有收藏写工具只有 `preview_add_to_wishlist / execute_add_to_wishlist`（`POST /api/client/collections/{id}/wishlist`，只写想看 type=1）与 `collection_progress`（对既有在看条目做进度更新）。“加入追番/在看”（type=3）在整个 Agent 没有写工具。
- Business 侧已存在写接口：`POST /api/client/collections/{subjectId}/save`（`CollectionUpdateDTO`，可带收藏类型与可选评分/进度），但 Agent 从未接入。
- 路由缺口：`app/agent/client/gateway.py::_is_explicit_recommendation_request` 只识别“加入想看/添加到想看/加入愿望单/帮我收藏/添加收藏/收藏这些”，不含“追番/在看”；`resources/prompt/client/gateway_prompt.md` 里 recommend_agent 仅描述为“推荐番剧”，没有任何“写入收藏”的路由说明，LLM 路由会把此类请求判给 search_agent。
- 术语：本仓库中“追番”= 在看（type=3），见 `collection_progress.py` 的“本周追番进度”与 `listSchedule` 的“每周追番列表”；收藏类型 1=想看 2=看过 3=在看 4=搁置 5=抛弃。

## Requirements

1. 新增“按标题加入追番/在看”的确定性解析写链路，复用 09-16 的解析与候选状态：显式 `subjectId` 跳过名称搜索但仍 `/batch` 校验；只有标题时 Business `/search` 首查，仅“成功空结果”才回退 RAG；候选统一经 `POST /api/client/subjects/batch`（`active=true`、`type=2`、`nsfw=false`、`excludeCollected=false`）过滤。
2. 唯一精确候选进入“加入追番”预览；多个或歧义候选进入 `SUBJECT_RESOLUTION`，按序号或唯一名称选择后再预览；无唯一有效候选明确回复“没有找到匹配项”，不预览、不写入。
3. 预览→明确确认→幂等写入的边界不得绕过；写入通过 Business `POST /api/client/collections/{subjectId}/save` 落 type=3。既有收藏（任意类型）的处理策略（不覆盖 / 提示改类型 / 由用户确认）必须在 PRD 定稿前作为 Open Question 解决。
4. 修复 gateway 路由：含“加入/添加到 追番/在看”等写入意图的请求确定性路由到 recommend_agent；扩充 `_is_explicit_recommendation_request` 词表或在 gateway 提示词补充“写入收藏”路由说明，并保留否定/取消词不误触发。
5. recommend_agent 注册新写入工具，并在提示词中说明单标题“加入追番”必须走确定性解析入口、候选选择与两段式确认；不得用检索/推荐工具替代写入解析。
6. 09-16 的“加入想看”链路、多番剧推荐批量加入想看、进度更新流程与其回归测试保持不变。

## Acceptance Criteria

- [ ] “把 X 添加到追番/在看”被确定性路由到 recommend_agent（含否定词不误触发），不再落到 search_agent。
- [ ] 单标题“加入追番”先 Business `/search`、成功空结果才回退 RAG；Business 异常不触发 RAG、不预览。
- [ ] 候选经 `/batch` 只保留 `active/type=2/nsfw=false`，`excludeCollected=false`；唯一精确候选进入预览，多个/歧义进入 `SUBJECT_RESOLUTION`，无有效候选回复“没有找到匹配项”。
- [ ] 明确确认后经 `/collections/{id}/save` 写入 type=3；已收藏条目的处理符合定稿策略，不静默覆盖。
- [ ] 复用而非复制 09-16 的解析/归一化/候选状态；“加入想看”与多番剧推荐收藏回归测试全部通过。
- [ ] `uv run pytest tests/agent` 与 `uv run pytest` 全绿；如触及 Business DTO/Controller 或 OpenAPI，同步更新对应文档与测试。

## Out of Scope

- 不改动 09-16 已实现的“加入想看”写链路语义（仅复用其解析/候选构件）。
- 不重写通用 RAG 检索，也不启用当前未接入的实体名称解析器。
- 不新增收藏类型枚举，不改动 `SUBJECT_RESOLUTION` 的 TTL/绑定语义。

## Open Questions

1. 已收藏条目再次“加入追番”的期望行为：拒绝并提示、还是允许改类型（想看→在看）？需确认 `/save` 的幂等/覆盖语义。
2. 是否同时支持“加入看过/搁置/抛弃”等其它类型，还是本任务只做在看(type=3)。
3. 路由修复采用扩充确定性词表、补 gateway 提示词、还是两者结合；如何避免与“查询追番进度/追番日程”等非写入意图冲突。

## Notes

- 本任务涉及 Agent 工具、Business `/save` 适配、gateway 路由与提示词、Redis 候选状态复用与回归测试，属复杂任务：`task.py start` 前必须补齐 `design.md` 与 `implement.md`，并解决上述 Open Questions。
- 相关既有实现：`app/agent/client/actions/subject_resolution.py`、`app/agent/client/actions/wishlist.py`、`app/agent/client/gateway.py`、`app/chat/pending_action.py`、Business `CollectionController#/save` 与 `CollectionUpdateDTO`。
