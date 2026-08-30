# 状态管理规范

## 状态归属

| 状态 | 工具 | 例子 |
|---|---|---|
| 服务端缓存 | TanStack Query | 番剧、收藏、用户、导入状态、日志 |
| 跨应用会话状态 | Zustand 内存 store | token、user、auth status |
| 可持久化 UI 偏好 | Zustand persist | light/dark、跟随系统 |
| 单组件交互 | React state/ref | modal、输入、选中项、AbortController |
| 导航状态 | Router / URL | path 参数、返回地址、可分享筛选 |

## 鉴权状态机

`AuthStatus` 只有 `checking / authenticated / unauthenticated / retryable-error`。AuthGate 负责启动期门控，RequireAuth/RequireAdmin 只在确定状态后重定向。

- Access Token 只存 `useAuthStore` 内存，刷新凭据由 HttpOnly Cookie 承载。
- 初始化时主动删除旧 `animetracker-auth` localStorage，禁止重新启用 token 持久化。
- 登录成功设置 token/user 并广播 session available；退出成功清空并广播 signed out。
- 管理端同时验证 `status=authenticated` 与 `role=ADMIN`。
- 网络故障保留重试入口，不把它等同于退出登录。

## Query 缓存

- 读取返回值视为服务端快照，不复制到 Zustand。
- mutation 后失效最窄但完整的 queryKey 集合。
- 轮询仅用于确有后台进度的资源，当前导入状态为 3 秒。
- 表单草稿保留本地，提交成功后再同步 Query。
- 不直接修改缓存来伪造 Agent 或 Business 写入成功。

## 主题状态

`useThemeStore` 仅持久化非敏感 UI 偏好；`resolveMode` 在 followSystem 时读取 `prefers-color-scheme`。持久化新字段前先确认不含身份、令牌或服务端权威数据。
