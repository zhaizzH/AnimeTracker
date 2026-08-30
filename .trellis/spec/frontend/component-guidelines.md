# 组件规范

## 组件职责

- Page 负责路由级数据组合；可复用交互拆到 `components`。
- client/admin 共同使用的展示组件进入 shared，参考 `SubjectCard.tsx` 与 `AuthGate.tsx`。
- 复杂状态共享优先 Provider + 自定义 Hook，参考 `AgentChatProvider` 与 `useClientAgentChat`。
- 路由页面使用 `lazy + Suspense`；fallback 保持接近最终内容宽度，避免布局跳动。
- 不把 API URL、鉴权刷新或 SSE 解析复制进页面组件。

## Props 与渲染

- Props 使用显式 interface/type；children 使用 `ReactNode`。
- 有限状态使用联合类型，不用自由字符串，例如 role、collection type、stream status。
- 异步内容显式渲染 loading、empty、error/disabled 状态。
- 列表 key 使用稳定业务 ID；聊天临时消息才使用本地生成 ID。
- 由用户输入触发的异步操作要阻止空值、重复提交和未就绪状态。

## 样式

- UI 基础使用 Ant Design 与 shared 主题 token。
- client 的页面视觉使用 `index.css` 中 `od-*` 类名；不要在组件中扩散大段重复 inline style。
- 少量一次性布局可使用 AntD props 或 inline style，重复后提取 class/组件。
- 深色模式由 client `Shell` 同步 `html.dark` 与 `color-scheme`。
- admin 当前只使用 shared light theme；不要假设已支持暗色。

## 可访问性

- 图标按钮提供可读 label/tooltip，输入框提供 `aria-label` 或关联标签。
- 流式消息区使用 `aria-live="polite"`，参考 `AgentConversation`。
- 不只用颜色表达 running/success/error。
- 保留键盘提交与焦点可达性，不能用不可聚焦 div 替代 Button。
- modal/empty/loading 状态必须给用户明确文本。

## 常见错误

- 页面直接访问 `:8090`。
- guard 还在 checking 时错误重定向。
- mutation 成功后只改局部 UI，不失效权威 query。
- client 组件被复制到 admin，而不是提取真正共享部分。
