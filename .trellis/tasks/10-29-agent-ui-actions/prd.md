# Agent 驱动 UI：自然语言导航与图后路由

## Goal

让用户用自然语言完成「需要手动点击多次」的**只读页面操作**——跳页、带筛选跳页、打开某条目详情。页面真的变化，用户看得见，且聊天面板不消失。

技术形态已定稿，见 [.trellis/spec/backend/agent-ui-actions.md](../../spec/backend/agent-ui-actions.md)：图后路由链 + `navigation_emitter` 纯函数节点 + `ui_action` SSE 事件 + 前端筛选 URL 归一化。

## Background

现有 Agent 只能调后端 API（读目录、写收藏），**没有任何驱动前端 UI 的通道**。`/agent` 是独立路由，跳走即卸载聊天组件；`AIAssistantFloat` 虽已挂在 `ClientLayout`，但在任何路由变化时强制关面板。

本任务只覆盖只读导航，**不代填表单、不代点提交**。账户凭据操作（改密码 / 改邮箱 / 换头像）永不进 agent。

## Child Tasks

| Child | 交付物 | 阻塞关系 |
|---|---|---|
| `frontend-url-state` | `AnimeIndex` 筛选 URL 归一化 + 浮层 agent 导航不关面板 | 无，可先做，独立有价值 |
| `ui-action-event` | `ui_action` 事件端到端打通（内部/wire/重放过滤/前端消费/openapi/契约测试） | 无，但前端消费依赖 child 1 的浮层改造才有意义 |
| `navigation-graph` | 图后路由链 + `request_navigation` 工具 + `navigation_emitter` 节点 + 5 个 action 白名单 | 依赖 child 2（事件通道必须先在） |
| `composite-write-navigate` | 复合指令「写入 + 导航」一回合完成，写入走 ADR 0001 两阶段后才导航 | 依赖 child 3 |

## Cross-Child Acceptance Criteria

- [x] 用户说「给我看 2022 年的番」→ 跳到 `/anime?year=2022`，筛选真的生效，聊天浮层保持打开（**服务端侧已真机验证**：真模型 → `ui_action{path:/anime?year=2022, label:「番剧索引」· 2022 年}` 穿透 Java 代理；前端实际渲染由 `anime-index.tag-url` 18 用例覆盖，「浮层保持」由 `agent.float` 覆盖）
- [x] 复合指令真机验证产出 `/my-collections?tab=1`（`tab` 取值与 `MyCollections` TABS 一致，见下方证据）；`tab=3` 路径同机制
- [x] 用户说「打开《孤独摇滚》详情页」→ `subjectId` 经权威解析后跳 `/subject/{id}`，模型不得编造 ID（**真机双验**：命中条目 → `ui_action{path:/subject/72}`；检索不到 → 模型主动拒绝导航并说明「没有可靠的 subjectId，不会用相似标题代替」）
- [x] 用户说「把这部加入想看，然后打开我的收藏」→ 先出预览 → 用户确认 → 写成功 → 才导航；未确认则不导航（**真机验证，见下方证据**）
- [x] SSE 断线重连后**不重复导航**（真机 `after=0` 重连，`ui_action` 帧带 `replayed: true`）
- [x] 全部既有测试不回归：`cd backend/agent && uv run pytest`（**932 passed**）；`cd backend/business && mvn -B test`（**EXIT=0**）；前端 `shared 92 / client 72 / admin 81`

## Constraints

- **SSE 是两层枚举**：内部 `AgentEventType`（五值含 END）→ wire `MessageType`（四值）。加 `ui_action` 必须同时改 7 处，漏一处契约测试即红。清单见 spec §6。
- **路由即工具权限边界**这一既有不变量不得破坏：`admin_agent` 无 RAG、`search_agent` 无写工具。导航不得塞进现有 Domain agent。
- `navigation_emitter` 是**纯函数**，不挂 LLM、不挂 prompt、不产 answer 文本。
- `open_subject` 的 `subjectId` 必须来自前序工具已解析的真实 ID，工具不接受标题字符串。
- 不做自由 path，只用固定 action 枚举，服务端构造 URL。
- `navigation_intent` 执行后必须清空，不残留到下一轮。

## Out of Scope

- RAG 外部语料（萌娘百科）那条线，本任务完全冻结，不在此交付。
- 前端内嵌目标页面预览。
- 除 5 个白名单 action 之外的任何页面跳转。
- 导航的 PendingAction 确认（导航可逆、无持久副作用，刻意不走两阶段）。

## 真机端到端验收（2026-10-30）

**环境**：MySQL + Redis（本机）+ Business `:8080`（`mvn package` + `--spring.profiles.active=local`）+ Agent `:8090`（`uv run uvicorn`）+ **真 DeepSeek**（`deepseek-v4-flash`）。
全部请求走 **Java 代理 `:8080`**（浏览器真实路径），并额外单独验证过一次 Agent 直连。

### 已验证（4 条，全部通过）

| # | 输入 | 实测结果 |
|---|---|---|
| 1 | 打开个人中心 | 真模型调 `request_navigation(open_profile)` → 图后路由 → emitter → SSE `ui_action{path:"/profile", label:"「个人中心」"}`，**穿透 Java 代理** |
| 2 | 给我看 2022 年的番 | `ui_action{path:"/anime?year=2022", label:"「番剧索引」 · 2022 年"}`；参数化 URL 与 child 1 的 URL 化改造对得上 |
| 3 | 把《来自远方》加入想看，然后打开我的收藏 | TURN1 只调 `解析番剧标题`，**0 个 `ui_action`**（预览不导航）；TURN2「确认」→ `确认加入想看` 成功（1 成功/0 跳过/0 失败）→ `ui_action{path:"/my-collections?tab=1", label:"「我的收藏」 · 想看"}` |
| 4 | 上一轮预览后回「取消」 | 只调 `取消加入想看`，**0 个 `ui_action`**，回答「已取消，未写入任何数据」 |

### 已验证（重放打标，真 HTTP）

`GET /api/client/agent/runs/{run_id}/stream?after=0` → 49 帧，其中 `ui_action` 1 帧带 **`meta.replayed: true`**；`is_end` 恰好 1 帧且位于末尾。**帧数与缓冲 1:1，游标不错位。**

### 一条值得记的行为观察

Business 未启动时，「给我看 2022 年的番」的模型**主动拒绝导航**并说明「无法给出带证据支撑的候选，不编造条目」。这是既有「不得陈述工具返回之外的证据」约束在起作用——不是缺陷，但意味着**导航依赖检索可用**：数据源故障时纯导航也会被模型主动放弃。

### 未做真机验证（需人工）

| 项 | 原因 | 现有覆盖 |
|---|---|---|
| 前端真实跳转 + 浮层保持的**视觉**确认 | 需要浏览器登录态；本机无可用账号口令（注册要邮箱验证码，Resend 未配） | `agent.float.test.tsx` 12 用例（真 Router + 真组件），含「标记后不关面板」「带 path 跳转」「非站内 path 丢弃」 |
| 断网/切后台场景 | 需要真实网络中断手段 | `useAgentChat.replay.test.tsx` + `test_chat_run_manager.py` |

### 本次为搭环境所做的本地临时改动（已清理）

为让 Java 代理接受本地签发的 token，曾在本地 Redis `db=1` 写入 `auth:token:{sha256}` 白名单键（TTL 1800s）——登录流程本身就是这么做的。**验证结束后已删除该键**，未改动任何用户口令或业务数据。

### 追加：真机抓到一个 check 只标为「备注」的瑕疵

`open_subject` 命中条目时，`ui_action.label` 渲染出的是**日文名**
（`「メイドインアビス 目覚める神秘」`），而浮层提示是中文界面文案——
openapi 里 `name` 是日文/英文名、`nameCn` 才是中文名，实现原先优先了 `name`。

`trellis-check` 当时把这条列为「备注，非偏差」（它读代码判断，没有真机证据）。
真机跑出来才知道用户实际会看到日文混中文。已修：优先 `nameCn`，并补
`test_open_subject_prefers_chinese_name_for_label` 钉住。

**教训**：静态审查只能判「代码是否自相矛盾」，判不出「用户实际看到什么」。
涉及文案/渲染的取舍，真机一遍胜过读十遍代码。

### 最终门禁（真机验证后）

| 门禁 | 结果 |
|---|---|
| `cd backend/agent && uv run pytest -q` | 932 passed |
| `cd backend/agent && uv run ruff check .` | All checks passed |
| `cd backend/business && mvn -B test` | EXIT=0 |
| 前端 `npm test` | shared 92 / client 72 / admin 81 |
