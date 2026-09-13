# 前端组件与类型规范

同层相关规范按主题合并；目标设计与当前实现的状态标记保留，各章节约束继续有效。

- [组件规范](#组件规范)
- [类型安全规范](#类型安全规范)

## 组件规范

### 组件职责

- Page 负责路由级数据组合；可复用交互拆到 `components`。
- client/admin 共同使用且不依赖单一应用路由、全局 CSS 或专属运行时的展示组件才进入 shared；`SubjectCard.tsx` 当前依赖 client 的 `.od-card-img` 样式和 `react-router-dom`，属于待治理的共享边界债务。
- shared 组件必须在 `packages/shared/package.json` 声明自身运行时依赖，不能依赖消费应用“碰巧”安装的包，也不能假设 client 的全局样式一定存在。
- 复杂状态共享优先 Provider + 自定义 Hook，参考 `AgentChatProvider` 与 `useClientAgentChat`。
- 路由页面使用 `lazy + Suspense`；fallback 保持接近最终内容宽度，避免布局跳动。
- 不把 API URL、鉴权刷新或 SSE 解析复制进页面组件。

### Props 与渲染

- Props 使用显式 interface/type；children 使用 `ReactNode`。
- 有限状态使用联合类型，不用自由字符串，例如 role、collection type、stream status。
- 异步内容显式渲染 loading、empty、error/disabled 状态。
- 列表 key 使用稳定业务 ID；聊天临时消息才使用本地生成 ID。
- 由用户输入触发的异步操作要阻止空值、重复提交和未就绪状态。

### 样式

- UI 基础使用 Ant Design 与 shared 主题 token。
- client 的页面视觉使用 `index.css` 中 `od-*` 类名；不要在组件中扩散大段重复 inline style。
- 少量一次性布局可使用 AntD props 或 inline style，重复后提取 class/组件。
- 深色模式由 client `Shell` 同步 `html.dark` 与 `color-scheme`。
- admin 当前只使用 shared light theme；不要假设已支持暗色。

### 可访问性

- 图标按钮提供可读 label/tooltip，输入框提供 `aria-label` 或关联标签。
- 流式消息区使用 `aria-live="polite"`，参考 `AgentConversation`。
- 不只用颜色表达 running/success/error。
- 保留键盘提交与焦点可达性，不能用不可聚焦 div 替代 Button。
- modal/empty/loading 状态必须给用户明确文本。

### 副作用与当前债务

- DOM 写入、主题订阅和通知等副作用必须放在 effect 或用户事件中；不要在 render 阶段调用 `message`、导航或直接修改 DOM。
- 当前 `admin/src/guards.tsx` 在 render 阶段触发非管理员通知，`client/src/main.tsx` 在主题同步上直接操作 DOM；后续修复必须补对应测试。

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
- ID 类型必须按领域核对，不能使用“Java Long 全部转 string”的笼统规则。当前 shared 类型中：Subject/HotSubject/Relation 的业务 ID 多为 `string`；User、Episode、Collection、Tag、Log 等 ID 仍为 `number`；OpenAPI 的 `integer/int64` 不能自动推导前端最终类型。
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
