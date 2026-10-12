# 前端 Spec 漂移审计报告

日期:2026-10-12
方法:对 `.trellis/spec/frontend/` 五个文档 + `GLOSSARY.md` + ADR 0017/0018 的每一条事实性断言,逐条对照当前代码核验(读源码 + `find`/`grep` + 端口/健康实测)。

范围注记:最近四个提交(`62354fa4`、`ca920141`、`e432ece1`、`657f8ffe`)不作二次推导,仅作为漂移成因引用。

## 最高影响漂移(按影响排序)

1. **`quality-guidelines.md:24` 指向不存在的文件** —— 写的是 `client/src/test/matchMedia.ts`,该文件不存在;matchMedia shim 内联在 `frontend/client/src/test/setup.ts`。照 spec 编辑的人会找错地方。
2. **`quality-guidelines.md:22` 测试计数过时** —— spec 写「共 18 个:shared 3 / client 5 / admin 10」;实际 **20**(shared 3 / client **6** / admin **11**)。新增两份:`client/src/test/not-found.test.tsx`(ca920141)、`admin/src/components/auth/auth-page.test.tsx`(62354fa4)。
3. **`hook-guidelines.md:116` 事实错误** —— spec 说 followSystem「只读取一次媒体查询值,未订阅系统主题变化」;两端 `theme-bridge.tsx` 现已 `media.addEventListener('change', apply)` 订阅并清理。由 ca920141 修复。整段读起来像已完成的 to-do。
4. **`component-guidelines.md:41` 对原语 ref 契约描述有误** —— 文中点名 `button.tsx`、`badge.tsx`、`breadcrumb.tsx`「必须显式 `React.forwardRef`」。实测只有 `button.tsx` 用 `forwardRef`;`badge.tsx`/`breadcrumb.tsx` 是普通函数组件(`asChild ? Slot.Root : span/a`,无 ref),且**无任何消费方给它们传 ref**。按 spec 自定判据(「是否真的传 ref」),应是文档清单有误,非代码有误。
5. **`hook-guidelines.md` 是混合行尾文件**(27 CRLF / 89 裸 LF),五个前端 spec 中唯一非纯 CRLF 者。

## 逐文件核验

### index.md —— 全数 HOLDS(无漂移)

核验通过项包括:`http.ts`/`useAgentChat.ts` 路径存在;API 相对路径 `/api` + Vite 代理到 8080;token 仅存内存、legacy localStorage 删除;`ApiResult` 解包 + SSE fetch;shared 命名空间导出;client/admin 不互导;shadcn/ui + Tailwind v4、Ant Design 全移除;外壳为本地代码;`@efferd` 是 components.json 的 registry 源(`https://efferd.com/r/{style}/{name}.json`);CI 仅强制 `npm run typecheck`。

### directory-structure.md

| 行 | 断言 | 判定 | 反证 |
|---|---|---|---|
| :7/:9/:12 | 各工作区目录构成 | HOLDS | 目录存在 |
| :15 | `file:../packages/shared` 依赖 | HOLDS | 两端 package.json |
| :22 | 认证/角色重定向在 `guards.tsx` | HOLDS | 两端存在 |
| :23 | shared 同目录测试、client 集中 `src/test` | PARTIALLY-STALE | 未记 admin 就近约定(admin 测试分散在 `src/guards.test.tsx`、`src/pages/*.test.tsx`、`src/components/auth/*.test.tsx`) |
| :27 | `@animetracker/shared` 名入口无人用,用 `@shared` | HOLDS | src 内零引用 |
| :28 | `@` 别名,admin 已在 vite+tsconfig 配置 | HOLDS | 两端 vite 配 `@` |
| :29 | 命名空间导出 `authApi/subjectsApi/adminUsersApi` | HOLDS | `index.ts:18-29` |
| :36 | admin 页面含 `AdminLogin` | HOLDS(命名歧义,见下) | `AdminLogin` 实际是 `components/auth/auth-page.tsx`,非 `pages/` 下文件 |
| :37 | 除 `AdminLogin` 外全 lazy+Suspense | HOLDS | `admin/router.tsx:6,8-15` |
| :38 | `AdminLogin` 无外壳;`NotFound`(`path:'*'`)在 AdminLayout 外 | HOLDS | `router.tsx:20,21,32` |
| :39 | admin 无 `/admin` 前缀;生产 :8081 站点根,开发 :5174 | HOLDS | nginx `listen 8081`;vite `port:5174`;router 无前缀 |

补充(文档未覆盖的现状):client 认证路由结构已变 —— `/login` 与 `/register` 渲染同一个 `AuthPage`(注册为面板内切换,`/register` redirect 到 `/login`);`/verify-email`、`/forgot-password`、`/reset-password` 已提到 `ClientLayout` 之外、整屏渲染;client 404 现为**顶层** `path:'*'`(在 `ClientLayout` 外)。

### component-guidelines.md

| 行 | 断言 | 判定 | 反证 |
|---|---|---|---|
| :13 | `SubjectCard.tsx` 仍依赖 `react-router-dom`,属待治理债务 | HOLDS | `shared/src/components/SubjectCard.tsx:1` |
| :13 | `.od-card-img`/`--od-*` 层已退场 | HOLDS | grep 无 |
| :14 | `react-markdown` 在两消费方声明;shared 声明 `react-router-dom`;shared 不再声明 antd、无 UI 库运行时导入 | HOLDS | 两端 package.json + `shared/package.json:12` |
| :16 | 路由页 lazy+Suspense(client 全量;admin 除 AdminLogin) | HOLDS | 两端 router |
| :24 | `admin/.../dashboard/card-state.tsx` 存在 | HOLDS | 存在 |
| :35 | `ThemeBridge` 挂在 `main.tsx`、路由之上、不在外壳内 | HOLDS | 两端 `main.tsx:16` |
| :36 | `@custom-variant dark (&:is(.dark *))` | HOLDS | 两端 `index.css:4` |
| :37 | 令牌来自 `@theme inline` 块 | HOLDS | 两端 `index.css:6` |
| **:41** | `button.tsx`/`badge.tsx`/`breadcrumb.tsx` 必须 `forwardRef` | **STALE** | 仅 `button.tsx:40` 用 `forwardRef`;badge/breadcrumb 是普通函数组件且无消费方传 ref |
| :41 | `input.tsx`/`textarea.tsx` 为普通函数组件 | HOLDS | 两端 |
| :42 | 取消确认弹窗用 `<AlertDialogTrigger asChild><Button/></...>`(AgentConfig/Subjects/Users) | HOLDS | `AgentConfig.tsx:110`、`Subjects.tsx:228`、`Users.tsx:111` |
| :49 | 流式区 `aria-live="polite"`,参考 `AgentConversation` | HOLDS | `client/.../AgentChat.tsx:105` |
| :73 | ID 类型映射(SubjectListItem/HotItemVO 为 string;User/Episode/Collection/Tag/Log 为 number;RelationVO 无独立 id) | HOLDS | `types/index.ts` |
| :84 | `parseEvent` 仅 JSON.parse+断言;`SsePayload.type/state` 可选 string;`ToolStep.status` 仅 running/done | HOLDS | `useAgentChat.ts:6,8-17` |

### hook-guidelines.md

绝大多数 HOLDS(Query 默认、`cfgInitialized`、`useBootstrapAuth`、`refreshWithLock`、401 单次重试、网络→`retryable-error`/401·403→`unauthenticated`、跨标签页只广播会话事件、双 HTTP 客户端、SSE POST+Bearer+AbortSignal、事件四类无 `type=end`、`is_end`、`sse.ts` 已知债务、`AgentChat` 两端渲染 thinking、SSE 401/403 落通用分支、`ProgressPreviewModal` 与 `Profile` 未失效缓存、`AuthStatus` 四态、legacy key 删除、admin 校验 ADMIN、导入轮询 3s、URL 筛选页清单)。

| 行 | 断言 | 判定 | 反证 |
|---|---|---|---|
| **:116** | followSystem「只读一次,未订阅系统主题变化」 | **STALE** | 两端 `theme-bridge.tsx` 已 `media.addEventListener('change', apply)`(+ `addListener` 回退)并清理 |
| :110 | 「可分享筛选」是目标模式 | HOLDS(仍属目标) | 仅 3 个 client 页用 URL 筛选,admin 仍本地 state |
| :58 | SSE 401/403「刷新一次/停止重试是后续应实现的契约」 | HOLDS(仍属目标) | `sse.ts` 未实现 |

### quality-guidelines.md

| 行 | 断言 | 判定 | 反证 |
|---|---|---|---|
| :14 | CI 强制 `npm run typecheck` | HOLDS | `ci.yml` |
| :18 | CI 未强制 Vitest/build;无 lint/format | HOLDS | `ci.yml` 仅 typecheck |
| **:22** | 测试共 18(shared 3/client 5/admin 10) | **STALE** | 实际 20(3/6/11) |
| :23 | admin 曾只有 `guards.test.tsx`,重建后各页有测试 | HOLDS(历史) | 现有多份 |
| **:24** | shim 位于 `client/src/test/matchMedia.ts` | **STALE** | 文件不存在;shim 内联于 `client/src/test/setup.ts:11-24` |
| :25 | admin `vitest.setup.ts` 注册 jest-dom + pointerCapture/scrollIntoView + ResizeObserver | HOLDS | 全在 |
| :32 | 端口 5173/5174;两端代理 `/api`→8080;`@shared`→源码 | HOLDS | 两端 vite |
| :33 | 两端代理 `/media`→`localhost:9000/anime-tracker` 且 rewrite 去掉 `/media` | HOLDS | 两端 vite 精确一致 |
| **:34** | client `optimizeDeps.include` 预打包 React/Query/Axios/Zustand,不含 Ant Design | PARTIALLY-STALE | 还含 `react-router-dom`、`react-markdown`、`remark-gfm`、`sonner`、`react-dom/client`;「不含 antd」部分成立 |
| :34 | admin 分包 `vendor-react`/`vendor-data`/`vendor-ui`;`chunkSizeWarningLimit` 560 | HOLDS | 两端配置 |
| :35 | admin 去除 antd+ECharts,用 recharts 且不单独分包 | HOLDS | 无 antd/echarts;recharts 存在 |
| :36 | 根 `npm test` 遍历 workspaces | HOLDS | `frontend/package.json` |
| :40-43 | admin 守卫测试约定 | HOLDS | `guards.test.tsx` |

### GLOSSARY.md / ADR 0017 / ADR 0018

- GLOSSARY:frontend 相关词条(`Access token`/`Refresh token`/`AuthSessionStore`/`Superadmin`/`OperationLog`)均无漂移;按文件自定范围,外壳/主题/shadcn 属工程词,正确不在表内。
- ADR 0017:React 栈、shadcn/ui + Tailwind v4、antd 移除、`--od-*` 退场、`vendor-antd*` 回归判据 —— 均 HOLDS。
- ADR 0018:admin 生产 :8081 / 开发 :5174、非 `/admin` 子路径、`baseURL` 固定 `/api`、两个 server 块各自的 `/media/` 反代 —— 均 HOLDS。

## 行尾核验

| 文件 | CRLF | 裸 LF | 判定 |
|---|---|---|---|
| `frontend/index.md` | 50 | 0 | CRLF |
| `frontend/directory-structure.md` | 47 | 0 | CRLF |
| `frontend/component-guidelines.md` | 101 | 0 | CRLF |
| `frontend/hook-guidelines.md` | 27 | 89 | **MIXED** |
| `frontend/quality-guidelines.md` | 60 | 0 | CRLF |
| `GLOSSARY.md` | 191 | 0 | CRLF |
| `adr/0017-*.md` | 37 | 0 | CRLF |
| `adr/0018-*.md` | 35 | 0 | CRLF |

## 目标 / 现状 分项判定

| 断言 | 判定 |
|---|---|
| `hook-guidelines:116` followSystem 订阅「待实现」 | **现已实现** → 漂移 |
| `hook-guidelines:110` URL 筛选为「目标模式」 | 仍属目标(正确) |
| `component-guidelines:13` SubjectCard `react-router-dom` 债务 | 仍属债务(正确) |
| `hook-guidelines:58` SSE 401/403 自愈 | 仍属目标(正确) |
| `hook-guidelines:68` ProgressPreviewModal / Profile 缓存失效 | 仍属目标(正确) |
| `component-guidelines:14` shared 依赖收敛 | 已实现(与描述一致) |

## 建议的定点编辑清单

1. `quality-guidelines.md:24`:`client/src/test/matchMedia.ts` → `client/src/test/setup.ts`(matchMedia shim 内联)。
2. `quality-guidelines.md:22`:计数 18 → 20,分项 client 5→6、admin 10→11,点名 `not-found.test.tsx`、`auth-page.test.tsx`。
3. `quality-guidelines.md:34`:补全 client `optimizeDeps.include`。
4. `hook-guidelines.md:116`:改写为现状(已订阅 + 回退 + 清理)。
5. `component-guidelines.md:41`:仅保留 `button.tsx`。
6. `directory-structure.md`:admin `AdminLogin` 条目改为 `components/auth/auth-page.tsx`(并说明非路由页);补 client 认证路由结构与顶层 404;登记 efferd `header` 簇;补 admin 测试就近约定;:39 显式写出对 ADR 0018 的落地。
7. `hook-guidelines.md`:混合 CRLF/LF 规范化为 CRLF。
