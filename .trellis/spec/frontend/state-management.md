# 状态管理规范

## 状态归属

| 状态 | 工具 | 例子 |
|---|---|---|
| 服务端缓存 | TanStack Query | 番剧、收藏、用户、导入状态、日志 |
| 跨应用会话状态 | Zustand 内存 store | token、user、auth status |
| 可持久化 UI 偏好 | Zustand persist | light/dark、跟随系统 |
| 单组件交互 | React state/ref | modal、输入、选中项、AbortController |
| 导航状态 | Router / URL | path 参数、返回地址、已实现的可分享筛选 |

## 鉴权状态机

`AuthStatus` 只有 `checking / authenticated / unauthenticated / retryable-error`。AuthGate 负责启动期门控，RequireAuth/RequireAdmin 只在确定状态后重定向。

- Access Token 只存 `useAuthStore` 内存，刷新凭据由 HttpOnly Cookie 承载。
- 初始化时主动删除旧 `animetracker-auth` localStorage，禁止重新启用 token 持久化。
- 登录成功设置 token/user 并广播 session available；退出成功清空并广播 signed out。
- 管理端同时验证 `status=authenticated` 与 `role=ADMIN`。
- 网络故障保留重试入口，不把它等同于退出登录。
- 跨标签页只同步会话事件；收到 `session-available` 后重新 refresh，不接收或持久化 Access Token。锁只串行刷新，不承诺跨标签页结果共享。

## Query 缓存

- 读取返回值视为服务端快照，不复制到 Zustand。
- mutation 后失效最窄但完整的 queryKey 集合。
- 轮询仅用于确有后台进度的资源，当前导入状态为 3 秒。
- 表单草稿保留本地，提交成功后再同步 Query。
- 不直接修改缓存来伪造 Agent 或 Business 写入成功。

### URL 筛选的实现边界

- 当前 client AnimeIndex 仅将 `q/page` 写入 URL；admin Subjects/Logs 的筛选仍主要保存在本地 state。规范中的“可分享筛选”是目标模式，不得当成所有页面的现行事实。
- 新增 URL 筛选时必须定义：字段编码、默认值、刷新/返回可恢复性，以及筛选变化时页码归零。

## 主题状态

`useThemeStore` 仅持久化非敏感 UI 偏好；`resolveMode` 在 followSystem 时读取 `prefers-color-scheme`。持久化新字段前先确认不含身份、令牌或服务端权威数据。
当前 followSystem 只读取一次媒体查询值，未订阅系统主题变化；补订阅时必须在 effect 中注册/清理监听，并覆盖浏览器不支持 matchMedia 的降级路径。
