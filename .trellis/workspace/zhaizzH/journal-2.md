# Journal - zhaizzH (Part 2)

> Continuation from `journal-1.md` (archived at ~1200 lines)
> Started: 2026-10-29

---



## Session 41: retro 收口：删手抄基线、审查证据要求、变异还原核对、journal 降阈值
<!-- trellis-session: v=2 fp=cad523bf8cd8bf7f -->

**Date**: 2026-10-29
**Task**: retro 收口：删手抄基线、审查证据要求、变异还原核对、journal 降阈值
**Branch**: `main`

### Summary

本轮 retro 四条全部落地。最重的一条是自己立的规矩没执行：本会话早先刚写下「环境事实不入 spec」并清掉了后端 quality-guidelines 的数字，前端同类文件却没动——它是全仓最后一个手抄测试数量的地方，本会话改过 5 次、审查抓到 3 次（202 vs 205、32 vs 33 文件、文件清单漏掉新增的 auth/stream.test.ts）。现在删掉数字与文件枚举，只留口径与现场命令。第二条：审查结论必须带 file:line 或测试名，无证据的结论按假设处理、先对源码核实——本会话曾被一条无证据的运行时断言带偏，写进归档附注后才发现与源码相反。第三条：变异验证结束必须核对 git diff --stat 与预期文件集，漏还原与套件全绿看起来一模一样。第四条：max_journal_lines 从 2000 降到 1200，本会话已 1263 行。

### Main Changes

- .trellis/spec/frontend/quality-guidelines.md：删「共 N 个文件 + 逐个文件名 + 用例数」，改为口径 + 现场命令 + 「新增测试文件无需回来改本文档」
- .trellis/workflow.md：Review evidence（结论必须带证据）与 Mutation checks（变异轮结束核对 diff）两条
- .trellis/config.yaml：max_journal_lines 2000 → 1200

### Git Commits

| Hash | Message |
|------|---------|
| `3e8ff339` | chore(spec): 删前端手抄测试基线，补审查证据与变异还原两条硬要求 |

### Testing

- [OK] 未跑测试：仅改文档与配置；spec 链接与锚点检查通过

### Status

[OK] **Completed**

### Next Steps

- 下一次 add_session 应自动开 journal-2.md（当前 1263 行 > 新阈值 1200）


## Session 42: SSE 刷新成功但重放仍 401：置为未认证交 guard 跳登录页
<!-- trellis-session: v=2 fp=5e340c88b707976c -->

**Date**: 2026-10-29
**Task**: SSE 刷新成功但重放仍 401：置为未认证交 guard 跳登录页
**Branch**: `main`

### Summary

收口 SSE 401 闭环的最后一环。此前只有「刷新失败」会置未认证；「刷新成功换到新令牌、重放仍被拒」这条路谁也没置位，store 停在 authenticated + 死令牌，用户对着必然失败的操作反复重试。改为在 streamSseWithAuth 的 retry catch 里，仅在重放也是 401 时调 setUnauthenticated()，由既有 guard 跳登录页。刻意不广播 signed-out——那个事件语义是用户主动登出，令牌失效与网络抖动只影响当前标签，广播会让别的标签在用户操作中被一起踢走；这条口径写进了 hook-guidelines。审查补了两条变异缺口：重放 502 不得登出、刷新失败不得额外踢人，并把重复的「重放仍 401」用例合并。另注意：工作树里 .trellis/spec/GLOSSARY.md 有 8 行非本会话的改动（ExternalSource/ExternalReference，19:51 写入），未纳入本次提交。

### Main Changes

- shared/auth/stream.ts：retry catch 内仅对 401 调 setUnauthenticated()
- shared/auth/stream.test.ts：合并重复用例，补「重放 502」与「刷新失败不踢人」两条断言
- .trellis/spec/frontend/hook-guidelines.md：重放仍 401 → 置未认证；signed-out 广播只用于主动登出

### Git Commits

| Hash | Message |
|------|---------|
| `58a03cec` | fix(shared): 刷新成功但重放仍 401 时置为未认证 |

### Testing

- [OK] frontend: shared 88 / client 49 / admin 81 全绿；typecheck 零错误
- [OK] 变异：删置位、放宽为任何错误都置位、刷新失败也置位，三条均转红

### Status

[OK] **Completed**

### Next Steps

- GLOSSARY.md 的 ExternalSource/ExternalReference 改动来源未知，待确认是否由其它会话写入


## Session 43: retro 收口：按路径暂存、否定断言先建基线
<!-- trellis-session: v=2 fp=1e5dc96f935421b6 -->

**Date**: 2026-10-29
**Task**: retro 收口：按路径暂存、否定断言先建基线
**Branch**: `main`

### Summary

本轮 retro 两条落地。第一条是真实污染风险：本会话前八个提交都用 git add -A，而 .trellis/spec/GLOSSARY.md 在会话外被写入 8 行（ExternalSource/ExternalReference，19:51），若它早出现二十分钟就会被捆进我的提交。workflow.md 提交步骤因此加「先 git status --short，出现不属于自己的脏路径就按路径显式 add」。第二条踩过一次：断言「刷新失败不应登出」却忘了 beforeEach 已把 store 复位成 unauthenticated，断言恒红与实现无关，白跑一轮；前端质量门禁加「否定断言前先建立正向基线」。

### Main Changes

- .trellis/workflow.md：提交步骤新增 Staging scope（按路径暂存）
- .trellis/spec/frontend/quality-guidelines.md：新增「否定断言前先建立正向基线」

### Git Commits

| Hash | Message |
|------|---------|
| `3024f514` | chore(spec): 提交按路径暂存，否定断言需先建正向基线 |

### Testing

- [OK] 未跑测试：仅改文档；spec 链接与锚点检查通过

### Status

[OK] **Completed**

### Next Steps

- GLOSSARY.md 的 8 行改动仍未确认来源，保持未提交

---

## Session 43 - 2026-10-30

### 任务

`10-29-frontend-url-state`（Agent 驱动 UI 五任务树的第一个 child）：`AnimeIndex` 筛选 URL 归一化 + 浮层 agent 导航保持与系统提示。

### 关键决策

- **hint 作废时机**（原设计遗漏）：用户手动路由变化时 `clearNavHint()`。不能改成「开面板时清空」——prd 要求「面板关闭时收到 hint，下次打开显示」，两者冲突。
- **关键词框跟随 q**：用 effect 同步而非 `key={q}` 重挂（后者丢焦点）。child 2 的 `open_anime_index` 带 `q?`，不修会被踩。
- **URL 数值收窄**：`Number.isFinite`，非法值视为未筛选，不让 `NaN` 进 queryKey/请求。

### 流程

1. `trellis-implement` 首轮：63 用例，但 `navHint` 无清空路径（真 bug）
2. `trellis-check` 独立审：确认该 bug + 发现 S1/S2/S3/S4，并用 3 个变异验证 D4 四条断言真能杀
3. 派回修 4 项：70 用例
4. 自己抽验 3 个变异（删 `clearNavHint` / 删 keyword 同步 / 去掉 `Number.isFinite`）全部转红，`cp` 还原后 diff stat 一致

### Spec 更新

- `frontend/quality-guidelines.md`：**修正与事实相反的说法**——CI 早已强制 `npm test` + `npm run build`（commit `e1aa3142`），原文写「CI 当前未强制」。另注明本地无 pre-commit hook。
- `frontend/hook-guidelines.md`：新增「URL → 控件的回显是双向的」「非法 URL 值必须收尾」「模块级瞬时 UI 状态的生命周期」三节，后者给出新增这类状态必答的四个问题（谁写/谁读/何时清空/跨测试残留）。

### Testing

- [OK] `npm test -w client`：11 文件 / 70 用例（基线 49 → 63 → 70）
- [OK] `npm run typecheck -w client`：无错误
- [OK] `npm run build -w client`：通过
- [OK] 变异验证 3 条，全部转红并还原

### Next Steps

- `10-29-ui-action-event` 可开工（与前端无交叠）；接上 `onUiAction` 时只需调 `markAgentNavigation` → `navigate(meta.path)` → `showNavHint(label)`，不必再改 `AIAssistantFloat.tsx`

---

## Session 44 - 2026-10-30

### 任务

`10-29-ui-action-event`：`ui_action` SSE 事件端到端打通（第二棵子树）。

### 关键决策（实现前已定）

- **重放打标而非跳帧**：跳帧会让前端 `after`（已收帧数）与后端 `run.events` 下标错位，后续重连重复/遗漏正文。改 `meta.replayed=true`，帧数保持 1:1，执行权在前端。
- **前端直接用服务端 `meta.path`**，不重复实现 action→URL 映射；`label` 也由服务端下发。

### 实现期两处偏差（已回写 design.md）

- `onUiAction` 改单对象 `UiAction`——原位置参数装不下 `path`。
- `AgentChatProvider` 现在依赖 `useNavigate`，**必须在 Router 内**；测试须包 `MemoryRouter`。已写进 `frontend/component-guidelines.md`。

### 流程

1. `trellis-implement`：7 处契约改动 + 测试，后端 862→867
2. `trellis-check` 独立审：五个重点全部通过，两次变异（重放改跳帧 / 实时段也打标）均转红
3. check 报 2 必须修（spec 残留「四值」、测试文件路径不存在）+ 6 建议修，全部处理

### Spec 漂移修复（本轮最大收获）

实现让 8 处 spec 说法失效。最险的两处：
- `guides/cross-layer-thinking-guide.md:71` 仍写「type 四值」
- `agent-ui-actions.md` 的 Tests Required 指向 `tests/chat/test_runs_replay.py`（**该目录不存在**）
- `test_live_subscription_does_not_mark_ui_action` 只断言 `run_id`——`run_id` 是 `_with_run_id` 补的，证明不了 `ui_action` 载荷幸存；已补 `action`/`path`/`label` 断言

### Testing

- [OK] 后端 `uv run pytest -q`：867 passed；`tests/contracts`：154 passed；`ruff check`：All checks passed
- [OK] 前端 `npm test`：shared 92 / client 72 / admin 81
- [OK] `npm run typecheck`：三包无错误
- [OK] 变异 2 条由 check 执行，均转红并还原

### Next Steps

- `10-29-navigation-graph` 可开工：事件通道已通，`navigation_emitter` 只需 `emit_ui_action(action, params, path, label)`
- 注意 navigation-graph 的 D1（嵌套图 `navigation_intent` 必须由 `run_domain_agent` 显式回传）——不做这步整条链静默失效

---

## Session 45 - 2026-10-30

### 任务

`10-29-navigation-graph`：图后路由链 + `navigation_emitter` + `request_navigation` 工具（第三棵子树）。

### 关键决策

- **D1 嵌套图回传落地**：`run_domain_agent` / `agent_stream` 显式带出 `navigation_intent`。不做这步 emitter 永不执行且**零报错**。
- **D2 工具带 `ToolMessage`**：只写 intent 会 `ValueError`（探针实测）。
- **删掉 `gated` 占位参数**（偏离 design D6）：留一个调用期不读的开关，会让 child 4 传 `gated=True` 却静默不生效，比三行改动危险。已把变更同步到 child 4 的 design/implement。
- **`tab` 与 `weekday` 星期约定相反**（check 发现）：`open_schedule.tab` 0=周一…6=周日，`open_anime_index.weekday` 0=周日…6=周六。模型按一套填另一套会**整体错一天且 Pydantic 不报错**。已在工具 docstring 写明。

### 流程

1. `trellis-implement`：四切片，后端 867→898
2. `trellis-check`：0 必须修，3 建议 + 2 备注；**变异实测证明图测试走真实 Domain agent 路径**（删回传时 run 测试与三条图测试同时红）
3. 修 4 条建议：删 `gated`、docstring 写星期语义、补白名单外 action 用例、工具构建提到工厂体；899 passed

### Testing

- [OK] `uv run pytest -q`：899 passed；`tests/contracts`：156 passed；`ruff check`：All checks passed
- [OK] 变异 3 条由 check 执行（删回传 / 删 search 注册 / 注册到 admin），均按预期转红并还原

### Next Steps

- `10-29-composite-write-navigate` 是最后一个 child。开工前读它的 design.md D1/D2：**门控必须读 TurnState，不能读 `state["pending_action"]`**——后者是回合开始时的快照，写成功后不更新，会拦掉唯一该放行的那次导航
- 本 child 删掉了 `gated` 参数，child 4 需先加回
