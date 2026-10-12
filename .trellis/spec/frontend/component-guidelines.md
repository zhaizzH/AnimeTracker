# 前端组件与类型规范

同层相关规范按主题合并；目标设计与当前实现的状态标记保留，各章节约束继续有效。

- [组件规范](#组件规范)
- [类型安全规范](#类型安全规范)

## 组件规范

### 组件职责

- Page 负责路由级数据组合；可复用交互拆到 `components`。
- client/admin 共同使用且不依赖单一应用路由、全局 CSS 或专属运行时的展示组件才进入 shared；`SubjectCard.tsx` 当前依赖 client 的 `.od-card-img` 样式和 `react-router-dom`，属于待治理的共享边界债务。
- shared 组件必须在 `packages/shared/package.json` 声明自身运行时依赖，不能依赖消费应用“碰巧”安装的包，也不能假设 client 的全局样式一定存在。历史漂移已收敛：shared 曾声明源码未使用的 `react-markdown`（实际使用方是 client/admin），该依赖现已在两个 consumer 的 `package.json` 中声明；`SubjectCard.tsx` 使用的 `react-router-dom` 已在 shared 声明。shared 已不再声明 `antd` 依赖（`antdTheme`/`antdThemeDark` 随本次重建移除），亦不 import 任何 UI 库运行时组件。
- 复杂状态共享优先 Provider + 自定义 Hook，参考 `AgentChatProvider` 与 `useClientAgentChat`。
- 路由页面使用 `lazy + Suspense`（client 全量；admin 除 `AdminLogin` 外，该页是静态导入）；fallback 保持接近最终内容宽度，避免布局跳动。
- 不把 API URL、鉴权刷新或 SSE 解析复制进页面组件。

### Props 与渲染

- Props 使用显式 interface/type；children 使用 `ReactNode`。
- 有限状态使用联合类型，不用自由字符串，例如 role、collection type、stream status。
- 异步内容显式渲染 loading、empty、error/disabled 状态。
- 多张卡片共享同一批 query 时，状态按卡片独立渲染，不提升为整页门控；复合卡片需同时考虑其全部依赖的 loading/error（参考 `admin/src/components/dashboard/card-state.tsx`）。
- 统计值 `0` 是有效业务数据，不得以 truthiness 判断为空态。
- 列表 key 使用稳定业务 ID；聊天临时消息才使用本地生成 ID。
- 由用户输入触发的异步操作要阻止空值、重复提交和未就绪状态。

### 样式

- **client 与 admin 使用同一套 UI 栈（shadcn/ui + Tailwind v4 + shadcn 令牌），不要引入其他 UI 库：**
  - admin：shadcn/ui（`admin/src/components/ui/*`）+ Tailwind CSS v4 + shadcn 令牌。UI 基础使用 `components/ui` 下的 primitive，不要在新代码里引入其他 UI 库。
  - client：与 admin 同栈——shadcn/ui（`client/src/components/ui/*`）+ Tailwind CSS v4 + shadcn 令牌，外壳为 `@efferd/app-shell-2`。
- client 的页面样式使用 shadcn/Tailwind 令牌（`bg-background`、`text-foreground`、`text-muted-foreground`、`border` 等）；不要在组件中扩散大段重复 inline style。
- 深色模式由两端的 `ThemeBridge` 同步 `html.dark` 与 `color-scheme`（唯一写入点）。
- 两端均支持暗色（Tailwind `dark:` 变体 + `@custom-variant dark (&:is(.dark *))`），统一以 `html.dark` 为切换开关。
- 令牌来源：各应用 `src/index.css` 的 `@theme inline` 块（shadcn CSS 变量，light/`.dark` 双套）；新颜色/圆角一律用令牌，不要硬编码色值。

### UI 原语契约（admin）

- `admin/src/components/ui/*` 是本仓库自己维护的 shadcn 派生代码，**不是**可随意上手的上游产物。改动 instance 渲染路径的原语（`button.tsx`、`badge.tsx`、`breadcrumb.tsx`）时必须显式 `React.forwardRef`，其余原语（如 `input.tsx`、`textarea.tsx`）是普通函数组件，不要为了“统一”给它们加 ref。
- 判据不是“是否导出了 ref 类型”，而是“消费方是否真的传 ref”。当前取消确认弹窗都写成 `<AlertDialogTrigger asChild><Button …/></AlertDialogTrigger>`（`AgentConfig`/`Subjects`/`Users`），而 `AlertDialogTrigger` 必须拿到子节点的 DOM ref 才能定位锚点，所以按钮必须前向 ref。
- 新增任何 `<X asChild>` 组合（radix `Slot`）时，先确认 `<X>` 的子节点能把 ref 落到真实 DOM；否则改用 `<Button onClick>` 手动受控，或把 asChild 放到真正的前向 ref 组件上。
- 该 ref 链在 jsdom 下不报错也不告警：未前向 ref 时 radix 只是拿不到锚点，jsdom 没有真实布局，测试仍会通过。因此**功能正常不等于契约成立**，判定只能靠读源码或真实浏览器。

### 可访问性

- 图标按钮提供可读 label/tooltip，输入框提供 `aria-label` 或关联标签。
- 流式消息区使用 `aria-live="polite"`，参考 `AgentConversation`。
- 不只用颜色表达 running/success/error。
- 保留键盘提交与焦点可达性，不能用不可聚焦 div 替代 Button。
- modal/empty/loading 状态必须给用户明确文本。

### 副作用与当前债务

- DOM 写入、主题订阅和通知等副作用必须放在 effect 或用户事件中；不要在 render 阶段调用 `message`、导航或直接修改 DOM。
- 主题同步的唯一写入点是两端各自的 `src/components/theme-bridge.tsx`（含 `matchMedia` 跟随系统）；不得在 `main.tsx` 或 render 阶段直接操作 DOM。

### 常见错误

- 页面直接访问 `:8090`。
- guard 还在 checking 时错误重定向。
- mutation 成功后只改局部 UI，不失效权威 query。
- client 组件被复制到 admin，而不是提取真正共享部分。

## 类型安全规范

### 类型所有权

- 跨应用/跨页面 API 类型集中在 `packages/shared/src/types/index.ts`。
- 仅组件内部使用的 props、表单和视图状态留在组件附近。
- shared API 函数声明精确输入/输出泛型，调用方不重复写响应结构。
- ID 类型必须按领域核对，不能使用“Java Long 全部转 string”的笼统规则。当前 shared 类型中：`SubjectListItem`、`HotItemVO` 的业务 ID 为 `string`；`User`、`Episode`、`Collection`、`Tag`、`Log` 等 ID 仍为 `number`；`RelationVO` 不含独立 ID，只携带 `relatedSubject`；OpenAPI 的 `integer/int64` 不能自动推导前端最终类型。
- 修改 ID 序列化时必须同时核对 Java VO/DTO、Python schema、OpenAPI 和 `packages/shared/src/types/index.ts`；未完成统一前，保留现有领域映射并为大整数增加边界测试。
- 状态/角色/收藏类型使用联合类型，例如 `UserRole`、`CollectionType`。

### HTTP 边界

- `http.ts` 将 `ApiResult<T>` 解包为 `T`；普通 API 函数不要再次访问 `.data`。
- 上传使用 `postForm`，普通 JSON 使用 `get/post`；SSE 单独走 `streamSse`。
- 未知 JSON 先用 `unknown` 或最小接口收窄；避免 `any`。
- 类型断言只允许在 Axios/SSE 等边界，收窄后不要向组件继续传播 `Record<string, unknown>`。
- 当前没有 Zod 等运行时 schema；服务端字段变化必须靠端到端核对与测试补足。
- `packages/shared/src/hooks/useAgentChat.ts::parseEvent` 当前仅做 JSON.parse 后断言，`SsePayload.type/state` 仍为可选 string；这不是已实现的判别联合校验。`ToolStep.status` 只有 running/done，新增 error 状态需同时修改事件处理和消费组件。

### 跨层同步

改字段时同时检查：

1. Java DTO/VO 或 Python Pydantic schema。
2. `docs/spec/openapi.yaml`。
3. shared types 与 API 函数。
4. Query key、表单初值和渲染分支。
5. 相关 Vitest/pytest 用例。

### 禁止做法

- 用非空断言掩盖实际可缺失的 API 字段。
- 将 `unknown` 直接强转成完整领域对象。
- 同一响应在 client/admin 分别定义两套近似类型。
- 用 `number` 接收可能超过 JS 安全范围的数据库 ID。
