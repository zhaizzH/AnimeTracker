# 运行时验证记录(免登录)

日期:2026-10-12
环境:本地服务已在运行(client Vite :5173、admin Vite :5174、business :8080、agent :8090、MinIO :9000)。
方法:真实浏览器(Playwright 驱动)访问,观察 URL 落定、无障碍树与 `document.documentElement` 状态;未登录,不触碰任何账号。

凭据可用性:仓库内**无**任何可用登录凭据 —— 无 seed/data.sql、无 docker-compose、无默认管理员创建代码;`spring.sql.init.mode: never`;注册强制 `role=USER`。首任管理员需按 `docs/deploy/部署方案.md:311` 手工 `UPDATE user SET role='ADMIN', email_verified=1 WHERE id=1;`。故本次仅做免登录验证。

## 观测结果

| # | 访问 | 观测 | 结论 |
|---|---|---|---|
| 1 | `:5173/login` | 整屏认证面板(左品牌面板含 2 个 Background Paths + 右表单);无侧边栏/外壳;标题 `AnimeTracker` | 登录页提示到外壳之外、整屏 — 成立 |
| 2 | `:5173/register` | URL 落定为 `/login`;页面即登录面板 | `/register` redirect 到 `/login` — 成立 |
| 3 | `:5173/login` 点「创建新账号」 | 面板内切换为「创建 AnimeTracker 账号」表单(用户名/邮箱/密码/确认密码);URL 仍为 `/login` | 注册是**面板内**行为 — 成立 |
| 4 | `:5173/forgot-password` | 独立小页(标题「找回密码」,link「回到登录」→ `/login`);无外壳 | 认证子页在外壳之外 — 成立 |
| 5 | `:5173/this-path-does-not-exist-xyz` | 整屏 404;link「返回首页」→ `/`、「浏览番剧」→ `/anime`;**未**重定向到 `/login` | client 顶层 404 在 ClientLayout 外 — 成立 |
| 6 | `:5174/nope-not-here` | 整屏 404,无 AdminLayout 外壳;link「返回面板」→ `/dashboard`、「番剧管理」→ `/subjects` | admin 404 在外壳外、无 `/admin` 前缀 — 成立 |
| 7 | `:5174/admin/dashboard` | 落到 404 | `/admin` 前缀确已移除 — 成立 |
| 8 | `:5174/login` | 整屏登录面板(仅登录,无注册/找回);文案「仅限管理员账号访问」「后台账号由管理员统一开通」 | admin 登录页在外壳外、仅登录 — 成立 |
| 9 | 主题:localStorage `animetracker-theme` 置 `followSystem:true` + 系统 dark 后重载 `:5173/login` | `html.className='dark'`、`style.colorScheme='dark'`、`meta[theme-color]='#0A0A0A'`、body 背景 `oklch(0.145 0 0)` | 外壳之外页面跟随系统 dark — 成立 |
| 10 | 同法看 `:5174/nope-not-here` | `html.dark` 生效 | admin 外壳外页面也跟随 — 成立 |

## 健康检查

| 服务 | 端点 | 结果 |
|---|---|---|
| client | `http://localhost:5173/` | 200 |
| admin | `http://localhost:5174/` | 200 |
| business | `http://localhost:8080/actuator/health` | 200 `{\"status\":\"UP\"}` |
| agent | `http://localhost:8090/api/client/agent/health` | 200 `{status:ok, llm_configured:true, checks:{redis:ok,business:ok,rag:ok,llm:ok}}` |

## 以源码为准(免登录不可验证)

- 登录成功后的跳转与 `location.state.from` 回退(`:5173` → `from ?? '/'`;`:5174` → `/dashboard`)。
- admin 角色门(非 ADMIN 拒绝)。
- 认证路由的 `PublicOnly` 包裹行为(已登录访问 `/login` 的去向)。
- 上述均以 `frontend/client/src/router.tsx`、`frontend/admin/src/router.tsx`、`frontend/admin/src/guards.tsx`、两端 `components/auth/auth-page.tsx` 源码为准。

## 附:控制台噪声(非缺陷)

- `:5173` 有 `favicon.ico` 404 与未登录时 `POST /api/client/auth/refresh` 401 —— 均为预期的匿名态探测。
