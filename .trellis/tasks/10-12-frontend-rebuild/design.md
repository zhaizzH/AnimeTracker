# 技术设计：两端 UI 重建（父任务，共享技术设计）

> 本文件是**全部子任务共享的技术设计**（边界、不变量、架构、主题机制、风险）。子任务各自的 `design.md` 只写其特有细节并引用本文。对应 `prd.md` 的 D1–D7 与 Cross-Child AC。执行排序见 `implement.md`。

## 1. 边界与不变量

**保留不动**：`packages/shared/**`（鉴权协调、SSE、HTTP 解包、类型、theme store）、`docs/`、`backend/`、`frontend/package.json`（workspaces 定义）。

**删除**：`client/src/**`、`admin/src/**`（含各自 `index.css`、`index.html` 内联脚本以外的构建配置按需改）、16 个测试文件、client 的 `od-*` 样式与 `antdTheme`/`antdThemeDark` 消费点。

**必须继续成立的硬约束**（来自 `.trellis/spec/frontend/index.md`）：
- API 只用相对路径 `/api/**`；access token 只存内存，禁止恢复到 localStorage。
- 普通 JSON 由 shared HTTP 拦截器解包（`ApiResult<T> → T`），组件不二次访问 `.data`。
- SSE 单独走 `streamSse`，不与 JSON 混用。
- shared API 以命名空间导出（`authApi` / `subjectsApi` / `adminUsersApi` …）。
- client 与 admin 不互相导入源码。

> 本次变更**推翻**「client 用 AntD、admin 用 shadcn，两套 UI 体系不混用」这条 spec 约束，Phase 3 必须同步更新 `frontend/index.md` 与 `component-guidelines.md`。

## 2. 目标架构

```
frontend/
├── package.json                 # workspaces 保持：packages/*, client, admin
├── packages/shared/             # 不动
├── client/                      # Tailwind v4 + shadcn + @efferd/app-shell-2
│   └── src/{components/{ui,...},layouts,pages,test,lib/{utils,theme-bridge}}
└── admin/                       # Tailwind v4 + shadcn + @efferd/app-shell-5 + dashboard-5
    └── src/{components/{ui,dashboard,...},layouts,pages,lib}
```

两端各装一套 shadcn 基础设施（`components.json`、`@/` 别名、`cn()`、runner CSS）——与 admin 现状一致，不抽公共 UI 包。理由：两端 UI 体系在本任务后虽同为 Tailwind，但外壳不同源（`app-shell-2` vs `app-shell-5`），过早抽公共包会把耦合固化；遵循现有 spec「资源和全局样式保留在所有者应用」。

### 2.1 client 基础设施（照 admin 模板）

| 项 | admin 现状（模板） | client 需要 |
|---|---|---|
| Vite 插件 | `@tailwindcss/vite` | 同 |
| 别名 | `@` → `./src`，`@shared` → shared src | 加 `@`，保留 `@shared` |
| tsconfig | `paths: {"@/*": ["./src/*"]}` | 同 |
| components.json | new-york / neutral / lucide + `@efferd` | 同（新建） |
| runner CSS | `@import "tailwindcss"` + `tw-animate-css` + `@custom-variant dark (&:is(.dark *))` | 同（替换 857 行 `od-*`） |
| 依赖 | `tailwindcss`/`@tailwindcss/vite`/`radix-ui`/`cva`/`clsx`/`tailwind-merge`/`lucide-react`/`next-themes`/`sonner` | 新增（client 现无） |

`vitest.config.mts` 也需补 `@` 别名（现仅 `@shared`）。

### 2.2 主题机制

保留 `useThemeStore` + `resolveMode`（shared），**统一到 `.dark` 类**，与 Tailwind `@custom-variant dark (&:is(.dark *))` 对齐：

- 移植 admin 的 `theme-bridge.tsx`（`useResolvedAdminTheme` + `matchMedia` change 监听）到两端，替换 client `main.tsx` 里裸的 DOM 写入。这同时修掉 spec 已记录的债务「`client/src/main.tsx` 在主题同步上直接操作 DOM，后续修复必须补对应测试」。
- 删除 shared `src/theme.ts` 的 `antdTheme`/`antdThemeDark` 与 `index.ts:11` 的导出、`packages/shared/package.json` 的 `antd` 依赖——唯一消费方 `client/src/main.tsx` 随重建消失，已核对无其他引用。`SubjectCard.tsx` 的注释（`packages/shared/src/components/SubjectCard.tsx:6`）引用 `--od-*`，需一并改写。
- `.dark` 变量由 shadcn 默认 neutral 提供（D5）；不再手写镜像 antd token。

### 2.3 外壳与路由的衔接

**client**：`@efferd/app-shell-2` 的 `AppShell`（`SidebarProvider` + 侧栏 + `AppHeader`）替换 `ClientLayout`。`registry:block` 不带路由，需要改写：

- 外壳保留在 `layouts/ClientLayout.tsx` 位置，继续作 router 的父级 `element`，继续渲染 `<Outlet />`。
- 导航数据从模板 demo（product/workspace/admin 分组 + changelog 卡片 + dashboard 骨架）改写为真实三项：**首页 `/`、每周日程 `/schedule`、番剧索引 `/anime`**，加登录后入口（我的追番 / AI 助手 / 个人中心）。
- 模板的自带 `dashboard-skeleton.tsx`、`latest-change.tsx` 在 client **不接线**（非看板应用），落地后删除。
- `app-breadcrumbs.tsx` 按路径映射为中文面包屑。
- 保留 `<AgentChatProvider key={user?.id ?? 'anonymous'}>` 与 `{user && <AIAssistantFloat />}` 的挂载位置（浮窗不依赖外壳 markup，只依赖被渲染）。

**admin**：`@efferd/dashboard-5` 依赖 `@efferd/app-shell-5`，用其作 `AdminLayout`；`dashboard-5` 的 9 张卡片组装成 Dashboard 页。其余六页（Subjects/Users/Import/Logs/AgentConfig/AgentChat）模板无对应块，用 shadcn 原语手工重建，路由表沿用 `/admin/*` 现状（`admin/src/router.tsx` 的 7 条 + 登录 + 捕获）。

### 2.4 演示资产的处理（重要）

`dashboard-5` 的卡片是**演示实现**：`top-countries.tsx` 用 `flag.vercel.app` 取国旗（外部请求），`delta.tsx` 的 `DeltaIcon` 支持 hugeicons/lucide/phosphor/remixicon/tabler 五套图标。行为对齐（PRD 决策 D6）要求接真实后端，因此：

- 卡片必须改为消费 shared 的 admin API（`admin/src/components/dashboard/*` 现状即真实接线，是重建的**参考实现**，见 git 历史 `27af8042`）。
- 移除 `flag.vercel.app` 外链依赖，国旗改为本地映射或纯文本国家名，避免隐私与可用性风险。
- 无后端字段支撑的模板卡片（如 Core Web Vitals 的 LCP/INP/CLS）需确认后端是否提供；不提供则该卡片降级为不渲染或在 design 记录为 deferred。

## 3. 数据流与契约

重建后两端的数据流**不变**，仍为：

```
页面/组件 → shared 命名空间 API（get/post/postForm）→ http.ts 拦截器解包 → 组件拿 T
Agent 页面 → useAgentChat → streamSse(fetch 流) → 事件 JSON.parse → 消息状态
登录态 → useAuthStore(status) ← coordinator（token 内存 + BroadcastChannel）
```

- `useBootstrapAuth()` 仍在应用根调用一次（client `main.tsx`、admin 待确认现有位置）。
- `AuthGate` 包在最外层；路由 guard 语义不变：`RequireAuth` 未认证 → `/login` 且 `state.from`；`PublicOnly` 已认证 → `/`。admin 侧 `RequireAdmin` 同理（`/admin/login`）。

## 4. 兼容性与迁移

- **不可逆**：`client/src`、`admin/src` 删除后仅存于 git（当前 HEAD `27af8042`）。实施前建议打 tag/分支，作为回滚点。
- **接口兼容**：后端契约不动；重建是纯前端适配，若发现 shared 类型与后端漂移（如 ID `string` vs `number`），按 `component-guidelines.md` 类型所有权逐字段核对，不在重建中顺手改契约。
- **测试策略**：原 16 个用例中，直接耦合旧 markup 的（`.od-hero__slide.is-active`、`od-agent-float-*` id、ClientLayout 的 antd 无障碍名）**按新语义重写，覆盖不减少**；与 shell 无关的（`http.test.ts`、`files.test.ts`、`useAgentChat.enabled.test.tsx`、shared 契约测试）保留不动。

## 5. 权衡与已取舍

| 取舍 | 选择 | 理由 |
|---|---|---|
| 是否抽公共 UI 包 | 不抽，两端各自维护 | 外壳不同源，抽了会耦合；遵循「样式保留在所有者应用」 |
| 是否保留 `od-*` | 删除 | D5 改用 efferd 默认外观 |
| shared 的 `antd` 依赖 | 移除 | 唯一消费方随重建消失，避免第二套令牌 |
| 删除方式 | 直接删 + git 回滚点 | 无渐进迁移价值（模板与旧实现无重叠） |

## 6. 风险与回滚

| 风险 | 影响 | 缓解 |
|---|---|---|
| 行为对齐工作量被低估 | 工期与质量 | 按页拆分验收；先接 client 主链路（登录/筛选/收藏/Agent） |
| `dashboard-5` 卡片依赖后端未提供的字段 | 看板缺项 | 实施前逐卡片核对后端字段，缺项降级并记 deferred |
| 国旗/图标外链（`flag.vercel.app`、5 套图标） | 隐私/体积 | 实施时移除外链，图标统一到 lucide |
| 主题双写（旧 DOM 写入 vs theme-bridge） | 暗色闪烁 | 统一 theme-bridge，删旧写入 |
| 62 处 `@shared` 引用需全部重接 | 遗漏导致运行期错误 | typecheck + 按页冒烟，`@shared` 导入清单作核对表 |

**回滚点**：实施前 `git tag`（如 `pre-frontend-rebuild`）；若中断，`git checkout <tag> -- frontend/` 整体恢复。

## 7. 待办（实施前确认）

- `dashboard-5` 各卡片所需后端字段逐项核对（visitors/online/pages/countries/referrers/sources/audience/browsers/web-vitals）。
- admin 的 `useBootstrapAuth` / `AdminLogin` 现状接线位置（git 历史）→ 重建时对齐。
- client 12 页各自的 API 依赖清单（作重接核对表）。
