# 前端 Hook 与状态管理

同层相关规范按主题合并；目标设计与当前实现的状态标记保留，各章节约束继续有效。

- [Hook 规范](#hook-规范)
- [状态管理规范](#状态管理规范)

## Hook 规范

### TanStack Query

- 服务端数据用 `useQuery`；queryKey 必须包含影响请求的全部筛选、分页和资源 ID。
- 写操作用 `useMutation`，成功后通过 `useQueryClient().invalidateQueries` 刷新权威数据。
- 所有服务端写入都必须处理权威缓存，不限于封装成 `useMutation` 的调用：收藏进度执行至少核对收藏详情、列表和计数；资料更新至少核对 `['me']` 与会话用户。
- queryFn 调用 shared API 命名空间，不在 Hook 内重复 axios 配置。
- 条件请求使用 `enabled`，参考 SubjectDetail 的 ID 与 CollectionActions 的登录态。
- 全局默认 `retry: 1`、`refetchOnWindowFocus: false`；单页面按真实需要覆写轮询/staleTime。
- 用 `useEffect` 把 query 数据回填到受控表单/state 时，门控必须只放行**首次到达**的数据；不能用“当前输入值是否为空”当判据，否则用户把字段清空后，下一次后台刷新会把它填回去。参考 `admin/src/pages/AgentConfig.tsx` 的 `cfgInitialized`（等价 antd `Form` 的 `initialValues` 语义）。
- 回填 effect 的依赖数组不要包含自己的写入结果，否则会形成“回填 → 触发 effect → 再回填”的覆盖循环；门控状态本身要能终止这个循环。

### 自定义 Hook

- 名称以 `use` 开头，返回稳定的领域动作与状态，不泄露底层 AbortController。
- `useAgentChat` 负责会话、历史、SSE、停止和工具状态；client/admin 只提供不同 API 适配对象。
- 长生命周期回调用 `useCallback`；外部传入但引用不稳定的适配对象可用 ref 保存最新值。
- 异步竞态要有序列号或取消信号，参考 `historyRequest` 与 `AbortController`。
- effect 卸载时停止流式请求；不要让卸载组件继续写状态。

### 认证 Hook

- `useBootstrapAuth` 每个应用 Shell 只调用一次。
- 刷新必须走 `refreshWithLock`，复用标签页内 Promise 与 Navigator Locks。
- 401 重试只允许一次，且刷新接口本身不能再次触发刷新。
- 网络失败进入 `retryable-error`，401/403 才进入 `unauthenticated`。
- 跨标签页只广播“会话可用/已退出”，不广播 Access Token。

#### Scenario: 前端 HTTP 与 SSE 认证/刷新契约

**1. Scope / Trigger**：改动 `packages/shared/src/api/http.ts`、`auth/coordinator.ts`、`sse.ts` 或 `hooks/useAgentChat.ts` 的请求注入、401 刷新或 SSE 帧消费行为时适用。这是前端 → Business/Agent 的跨层认证与流式契约。

**2. Signatures**：`http`（Axios 实例，`baseURL='/api'`、`withCredentials`）、`sessionHttp`（仅 refresh 等会话请求）、`streamSse({ url, body?, method?, token, signal, onEvent })`（原生 fetch；`method` 默认 `POST`，`GET` 用于重连回放）、`refreshWithLock()`（标签页内 Promise 复用 + Navigator Locks）。

**3. Contracts**：
- `http` 从内存 store 注入 `Authorization: Bearer`，解包 `ApiResult<T>.data`；`code!==200` 以 `message` 拒绝。
- 这些端点把 401/403 当业务结果、不触发静默刷新重试：`/client/auth/(login|register|verify-email|resend-code|refresh|forgot-password|reset-password)`；`logout` 不在列内（令牌过期仍应先刷新再重放）。
- `streamSse` 不发 Axios 拦截器，因此**不会**自动 401 刷新；消费方必须自行处理。
- SSE 事件 `type` 只有 `answer / thinking / function_call / status`，**不存在 `type=end`**；结束由 `is_end=true` 表达（生产者契约见 [Agent SSE 事件契约](../backend/agent-guidelines.md#scenario-agent-sse-事件契约)）。

**4. Validation & Error Matrix**：

| 情况 | 契约行为 |
|---|---|
| 普通 JSON 401（非 AUTH_ENDPOINT、未重试过） | `refreshWithLock()` 成功后重放原请求**一次** |
| 普通 JSON 401（已重试过 / 刷新失败） | 拒绝，进入未认证或 `retryable-error` |
| AUTH_ENDPOINT 401/403 | 直接拒绝，不刷新 |
| SSE 401/403 | 保留 Abort 语义：「刷新一次 → 重开同一流一次」或进入未认证；**禁止无限重试** |
| 工具失败 | `function_call` `state=end` + `result=error`（**不是** `state=error`；`state=error` 只在 `status` 事件） |
| 网络断开 / 解析失败 / 主动 Abort | 三者分别保留可重试的用户语义，不混为一类 |
| 收到 `is_end=true` | 停止写入；消费方不得假设后续无帧 |
| 字段缺失 | 生产者 `exclude_none`，`content` 子字段必须视为可选 |

**5. Good / Base / Bad Cases**：
- Good：SSE 401 时刷新一次并重开单条流，或直接进未认证；工具状态从不会永久停在 running。
- Base：普通 JSON 走 `http` 自动刷新，SSE 路径独立处理鉴权。
- Bad：对 SSE 401 无限重试；把 `type=end` 当真实帧；用当前输入值判据回填受控表单。

**6. Tests Required**：SSE 改动必须补 parser、状态机、断开与鉴权失败测试；对 HTTP 改动补 401/403、网络失败、Abort、尾帧与错误状态用例（见 [质量门禁](./quality-guidelines.md)）。

**7. Wrong vs Correct**：
- Wrong：假设 `streamSse` 会自动刷新，或把 `end` 当作 `type` 枚举值。
- Correct：SSE 独立处理 401；结束语义以 `is_end=true` 为准。

> **现状（10-19 已加固）**：`packages/shared/src/sse.ts` 以空行 `\r?\n\r?\n` 分帧（帧内多行 `data:` 按规范拼接）、校验响应 Content-Type 含 `text/event-stream`、流结束时 flush 尾帧残片，并用 `signal.aborted` 区分主动 Abort（`SseAbortError`）与故障（`SseError`，带 `status`）。`useAgentChat` 按 `type` 白名单分发（`answer` / `thinking` / `function_call` / `status`），不再用 `content.text` 兜底；`is_end=true` 通过局部 `ended` 同步锁住后续帧；工具失败以 `state=end` + `result=error` 落到 `ToolStep.status: 'error'`，而 `status` 事件的 `state=error` 把 `message` 追加到回答尾部（持久化失败提示不得静默丢弃）；401/403 走独立「未认证或无权限」文案，主动停止不写中断文案。测试见 `shared/src/sse.test.ts` 与 `shared/src/hooks/useAgentChat.events.test.tsx`。新增 SSE 改动仍须一并补测试。

#### Scenario: chat run 重连与并发冲突

**1. Scope / Trigger**：改动 `useAgentChat` 的订阅/停止/会话切换行为，或新增消费 run 重连、409 冲突的 UI 时适用。

**2. Contracts**：
- **断连不等于停止**。卸载、刷新、abort 都只退订；run 在后端继续跑并落库。停止必须显式调用停 run 接口。
- `stop()` 顺序是「先停 run，后 abort 本地连接」。先 abort 会让后端把它当掉线，run 继续跑完。`run_id` 尚未到达时降级为纯 abort，不排队重试。
- 首帧 `meta.run_id` 是前端唯一能拿到 run 身份的来源；它在该 run 结束（正常/出错/abort）后必须清空，否则下一次停止会停错对象。
- 重连游标 `after` 是**已收到的事件帧数**，与文本长度、token 数无关。服务端为截断降级插入的 `status`/`warning` 帧不占事件索引，**不得计入游标**，否则续订会重放已收内容。
- 回放必须新建一个**空** assistant 气泡：历史气泡里是已落库内容，回放会重推全量事件，复用会把正文拼两遍。
- 回放与实时共用同一把 `is_end` 锁，不另建判据。
- `status` 为 `failed` / `done` / `cancelled` 时**不订阅**，直接读历史；`failed` 多为进程重启后的懒收敛，额外给用户提示。
- 同一会话已有 run 时发送返回 409，body 为 `{code, message, data:{active_run_id, status, capabilities}}`。判据只能看 `status` 与结构化字段，**不得解析中文文案**。
- 409 的三条分支各自可断言：打断并插入 = 先停 `active_run_id` 再重发；等待 = 零发送；取消 = 零发送且不留空气泡。未发出的文本必须回到输入框，不能丢。

**3. Validation & Error Matrix**：

| 情况 | 契约行为 |
|---|---|
| 进入会话时该会话有 running run | 新建空气泡 + `after=0` 订阅回放，正文只出现一次 |
| 进入会话时 run 已 `failed`/`done`/`cancelled` | 只读历史；`failed` 加「上次回答未完成」提示 |
| 回放中途用户点停止 | 先停 run 再 abort；已生成正文保留，只收掉空气泡 |
| 切换会话时旧订阅仍在途 | 先掐订阅再加载历史；旧 run 的迟到帧不得写入新会话 |
| 发送返回 409 | 进入冲突选择态；收回本次的 user + 空 assistant 气泡，保留原文 |
| 409 的 `data.active_run_id` 缺失 | 只能等待/取消；「打断并插入」不得可点 |

**4. Tests Required**：重连与冲突改动必须补「正文不重复拼接」「游标是帧数而非字符数」「`is_end` 锁复用」「停止顺序」「三条冲突分支的请求次数」用例。断言要能杀掉变异：把「只收回本次气泡」改成清空整个会话、把游标改成文本长度，都必须转红。

**5. Wrong vs Correct**：
- Wrong：把 `after` 当文本游标；回放复用历史气泡；先 abort 再停 run；用 `message.includes('进行中')` 判冲突。
- Correct：`after` 计帧；回放新开气泡；先停 run 后 abort；判 `status===409` + `data.active_run_id`。

#### thinking 展示的现状

- `packages/shared/src/hooks/useAgentChat.ts` 按收到的 `content.text` 直接累加 thinking；没有翻译、空格修复或中文校验。
- client 的 `src/components/AgentChat.tsx` 与 admin 的 `src/pages/AgentChat.tsx` 分别渲染折叠区，不能只验证一端。
- 历史加载只恢复 role/content，不恢复 thinking；刷新后思考区域消失不是翻译成功或服务停止思考的证据。
- 排查连续英文单词时先确认模型原始 chunk：后端只丢弃空块与重复 payload，不补也不删空格（`normalized = raw.strip()` 仅用于去重比较，追加的是未处理的 `raw`）；不要先在前端插空格。完整链路见 [Agent 运行与提示词契约](../backend/agent-guidelines.md#agent-角色提示词与流式输出契约)。
- SSE 的 401/403 现已在客户端显式分类（`SseError.status` 判 401/403 → 「未认证或无权限」文案），但**仍未实现自动刷新重试**：没有 Axios 那套「刷新一次 → 重开同一条流」闭环。该闭环是后续应实现的契约（见任务 `10-19-sse-client-hardening` 的 P3 待办）。

#### 服务端写入缓存矩阵

| 写入 | 成功后的最低处理 |
|---|---|
| 收藏/进度执行 | 失效相关收藏详情、收藏列表、计数及受影响 Subject 查询 |
| 资料更新 | 更新 Zustand 会话用户，并失效 `['me']`，避免页面继续显示旧快照 |
| 其他 mutation | 根据实际 queryKey 列出最窄但完整的失效集合；不能只改局部 state |

当前 `ProgressPreviewModal` 执行成功后未刷新收藏查询，`Profile` 更新资料后未失效 `['me']`；后续修复应先补回归测试，再调整缓存策略。

### 常见错误

- queryKey 漏掉 page/filter，显示旧缓存。
- 在 render 中直接调用异步函数。
- effect 依赖不稳定对象导致自动创建多个 Agent 会话。
- 捕获所有错误后返回空数组，掩盖需要展示的错误。

## 状态管理规范

### 状态归属

| 状态 | 工具 | 例子 |
|---|---|---|
| 服务端缓存 | TanStack Query | 番剧、收藏、用户、导入状态、日志 |
| 跨应用会话状态 | Zustand 内存 store | token、user、auth status |
| 可持久化 UI 偏好 | Zustand persist | light/dark、跟随系统 |
| 单组件交互 | React state/ref | modal、输入、选中项、AbortController |
| 导航状态 | Router / URL | path 参数、返回地址、已实现的可分享筛选 |

### 鉴权状态机

`AuthStatus` 只有 `checking / authenticated / unauthenticated / retryable-error`。AuthGate 负责启动期门控，RequireAuth/RequireAdmin 只在确定状态后重定向。

- Access Token 只存 `useAuthStore` 内存，刷新凭据由 HttpOnly Cookie 承载。
- 初始化时主动删除旧 `animetracker-auth` localStorage，禁止重新启用 token 持久化。
- 登录成功设置 token/user 并广播 session available；退出成功清空并广播 signed out。
- 管理端同时验证 `status=authenticated` 与 `role=ADMIN`。
- 网络故障保留重试入口，不把它等同于退出登录。
- 跨标签页只同步会话事件；收到 `session-available` 后重新 refresh，不接收或持久化 Access Token。锁只串行刷新，不承诺跨标签页结果共享。

### Query 缓存

- 读取返回值视为服务端快照，不复制到 Zustand。
- mutation 后失效最窄但完整的 queryKey 集合。
- 轮询仅用于确有后台进度的资源，当前导入状态为 3 秒。
- 表单草稿保留本地，提交成功后再同步 Query。
- 不直接修改缓存来伪造 Agent 或 Business 写入成功。

#### URL 筛选的实现边界

- 当前 client AnimeIndex（`q/page`）、MyCollections（`tab/page`）与 Schedule（`year/quarter/tab`）已把筛选写入 URL；admin Subjects/Logs 的筛选仍主要保存在本地 state。规范中的“可分享筛选”是目标模式，不得当成所有页面的现行事实。
- 新增 URL 筛选时必须定义：字段编码、默认值、刷新/返回可恢复性，以及筛选变化时页码归零。

### 主题状态

`useThemeStore` 仅持久化非敏感 UI 偏好；`resolveMode` 在 followSystem 时读取 `prefers-color-scheme`。持久化新字段前先确认不含身份、令牌或服务端权威数据。
followSystem 已订阅系统主题变化：两端 `theme-bridge.tsx` 在 effect 内以 `media.addEventListener('change', apply)` 注册（旧浏览器回退 `addListener`），并在清理函数中注销监听。浏览器不支持 `matchMedia` 时的降级路径以各端源码为准。
