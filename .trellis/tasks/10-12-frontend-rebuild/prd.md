# 重建前端两端 UI（父任务）

> 本任务是**父任务**，不直接实施。它拥有源需求集、任务地图、跨子任务验收标准与最终集成验收。实施在 5 个子任务中完成。

## Goal

删除 `frontend/client/src` 的全部现有实现，保留 `packages/shared`，为其引入 Tailwind CSS v4 + shadcn 基础设施并重建 UI：

- 用户端（client）用 `@efferd/app-shell-2` 作应用外壳；
- 管理端（admin）**不重建**——经核验已是改造完成的 `@efferd/dashboard-5` + `app-shell-5`，改为一轮核验（见任务地图与范围修正）；
- 重建后**行为对齐现状**：client 全部页面重新接回 `@shared` 的真实 API，后端契约不变；
- 视觉改用 efferd / shadcn 默认外观，放弃 `od-*` 暖纸玻璃令牌与 Noto Serif SC 品牌字体。

用户价值：两端 UI 收敛到同一套 Tailwind/shadcn 技术栈与组件语言，消除 Ant Design 与 shadcn 并存的维护成本。

## Background

### 现状（已确认）

- `frontend/` 是 npm workspaces 单仓（`frontend/package.json:4`）：`client`（Vite :5173，Ant Design 5 + `od-*` 样式，`client/src/index.css` 857 行）、`admin`（:5174，已是 shadcn + Tailwind v4）、`packages/shared`（`@animetracker/shared`）。
- `packages/shared` 承载鉴权协调（`auth/coordinator.ts`）、SSE 消费（`sse.ts`、`hooks/useAgentChat.ts`）、HTTP 解包（`api/http.ts`）、theme store（`store/theme.ts`）与后端契约类型（`types/index.ts`）；被两端以 `@shared` 引用 62 处。
- client 无 Tailwind、无 `components.json`、无 `@/` 别名（`client/vite.config.mts:7`、`client/tsconfig.json:18-21` 只有 `@shared`）。
- admin 已是 shadcn 项目，`admin/components.json:21-23` 已配置 `@efferd` registry；`admin/src/components/dashboard/*` 的 11 个组件已接真实后端数据；`admin/src/components/app-sidebar.tsx:23` 是真实的 7 条管理路由。
- 规模基线：`client/src` + `admin/src` + `packages/shared/src` 共 127 个文件、约 9,499 行 TS/TSX、16 个测试文件。
- 现有 spec 约束「client 用 AntD、admin 用 shadcn，两套 UI 体系不混用」（`index.md`、`component-guidelines.md:31-34`）——本次变更推翻该约束，收尾需同步更新。

### 模板能力边界（已核对 registry 元数据）

- `@efferd/app-shell-2`、`@efferd/dashboard-5` 均为 `registry:block`，`dependencies` 为空，`files` 全部 `registry:component`：**不含 HTTP / 鉴权 / SSE / 类型层**，导航、图表、指标皆为模板 demo 数据。
- `dashboard-5` 只覆盖 admin 的**看板**页；admin 另有六个页面，模板无对应块。
- `dashboard-5` 依赖 `@efferd/app-shell-5`，与 client 的 `app-shell-2` 不同源，两端外壳视觉各自以模板为准。
- ~~`dashboard-5` 演示实现含外部依赖与多图标集~~ **已核实为不适用**：现有 admin 早已移除 `flag.vercel.app` 并将图标收敛到 lucide（见 `rebuild-prep/research/dashboard5-gaps.md`）。

### 决策记录（2026-10-12）

| # | 决策 | 结论 |
|---|---|---|
| D1 | 重建范围 | 删除两端 `src` 全部实现并重建（非渐进迁移）。**2026-10-12 修正：admin 不删**——现有 admin 已是 `dashboard-5` 终态，改为核验（见任务地图） |
| D2 | 共享层 | 保留 `packages/shared`，重建后接回 `@shared` 引用 |
| D3 | 用户端外壳 | `@efferd/app-shell-2` |
| D4 | 管理端 | `@efferd/dashboard-5`（连带 `app-shell-5`） |
| D5 | 视觉身份 | 改用 efferd / shadcn 默认外观 |
| D6 | 行为保真度 | 行为对齐：全部页面重接真实 API |
| D7 | 任务结构 | 父任务 + 5 个可独立验收的子任务，逐个完成后汇总父任务做集成验收 |

## Task Map

| 子任务 | 目录 | 交付 | 前置 |
|---|---|---|---|
| 1 重建准备 | `10-12-rebuild-prep` | 回滚 tag、核对表、`dashboard-5` 字段核对、shared 清 antd、删除 client 旧实现 | 无 |
| 2 基础设施 | `10-12-ui-infra` | client Tailwind v4 + shadcn 骨架、admin 加固、主题统一 `.dark`、两端空壳可启动 | 1 |
| 3 用户端外壳与路由 | `10-12-client-shell` | `app-shell-2` 外壳、导航改写、12 条路由与守卫 | 1、2 |
| 4 用户端页面 | `10-12-client-pages` | 认证 5 页 + 业务 7 页接真实 API、三态、测试重写 | 1、2、3 |
| 5 管理端核验 | `10-12-admin-verify` | 核验现有 admin 已对齐 `dashboard-5` + `app-shell-5`，产出差异清单（**不重写**） | 1 |

依赖只以「前置」列表达（Trellis 父子结构不是依赖系统）；子任务 5 与 2/3/4 无相互依赖，可并行。

**范围修正（2026-10-12）**：子任务 5 原为「重建 admin」，依 `rebuild-prep/research/dashboard5-gaps.md` 的发现改为「核验 admin」——现有 admin 经 `914f3237 feat(admin): dashboard-5 看板接入真实番剧运营数据` 已是改造完成的 `dashboard-5`（props 为后端真实类型、无 `flag.vercel.app`、图标已收敛 lucide）。删除重建会退回模板 demo 数据，故取消。admin 不进入删除/重建范围。

## Source Requirements

源需求 R1–R7 完整拆到子任务中，映射如下（原文与证据见各子任务 `prd.md`）：

| 源需求 | 落在 |
|---|---|
| R1 删除边界（保留 shared；仅删 client） | 子任务 1 |
| R2 client 基础设施 | 子任务 2 |
| R3 admin 形态 | 子任务 5（**核验**，不重建） |
| R4 数据层重接 | 子任务 3、4（client）；admin 由子任务 5 核验既有接线 |
| R5 路由 | 子任务 3（client 重建）；admin 由子任务 5 核验 |
| R6 Agent 能力保持 | 子任务 3（挂载）、4（行为） |
| R7 视觉替换 | 子任务 2（令牌）、3/4（应用）；admin 视觉不在本次变更范围 |

## Cross-Child Acceptance Criteria

以下为**只能在父任务层验证**的集成标准（子任务各自 AC 见其 `prd.md`）：

- **AC1 全量门禁**：`cd frontend && npm run typecheck && npm test && npm run build` 三 workspace 全绿。
- **AC2 无 antd 残留**：`frontend` 源码不再有 antd 运行时导入、antd 依赖与 `od-*` 样式引用。
- **AC3 `@shared` 全接回**：`@shared` 引用点全部有效，shared 除 antd 清理外无功能改动。
- **AC4 两端可启动**：`npm run dev:client` / `npm run dev:admin` 均可启动，`/api` 代理生效，守卫重定向正确（admin 侧为未改动基线）。
- **AC5 行为对齐**：client 12 页行为对齐现状（筛选、CRUD、日历、弹窗、Agent 流式）；admin 侧由子任务 5 核验「已对齐」并提供证据。
- **AC6 测试覆盖不减少**：原 16 用例对应覆盖全部存在（重写锚点不算减少）。
- **AC7 spec 同步**：`frontend/index.md`、`component-guidelines.md`、`directory-structure.md` 与 README 已更新（含移除「两套 UI 体系不混用」）。
- **AC8 deferred 登记**：已核实**无「后端缺字段」项**（现有 admin 已把模板演示指标替换为运营数据）；未完成项（如 AuthGate 调色板跟进）已在父任务层登记。

## Final Integration Review（父任务收尾）

全部子任务完成后，父任务执行：

1. 跑 AC1 全量门禁；失败则退回对应子任务，不在此修。
2. 核 AC2/AC3（残留与引用完整性）。
3. 两端冒烟走查 AC4/AC5 主链路。
4. 核 AC6 测试覆盖清单。
5. 更新 spec 与 README（AC7）。
6. 汇总 AC8 的 deferred 清单，确认无静默遗留。
7. 通过后 `task.py finish`，提交。

**父任务不是实现目标**：不得跳过子任务直接在父任务写代码；若某子任务验收不通过，退回该子任务修复后重跑集成验收。

## Deferred（本次未做，已登记）

| 项 | 来源 | 说明 |
|---|---|---|
| `admin/src/pages/Logs.tsx` 列表查询无 `isError` 分支 | `10-12-admin-verify/research/admin-diff.md` | 失败时只呈现空态，无法区分「无日志」与「加载失败」；小改动，建议后续单开任务 |
| admin header 无 Kbd 快捷键提示 / DecorIcon | 同上 | 纯外观差异，不影响功能；如需完全对齐 `app-shell-5` 观感再处理 |
| `packages/shared/src/components/AuthGate.tsx` 调色板硬编码「暖纸玻璃」色值 | `rebuild-prep`（已留 TODO 注释） | 两端统一 shadcn 令牌后应改为 `var(--background)` 等；当前不影响可用性 |
| client `AnimeIndex` 标签筛选改为胶囊多选 | `client-pages` 实施记录 | shadcn `Select` 无原生 multiple，改用 `aria-pressed` 胶囊，行为等价且可键盘操作 |

## Integration Verification（2026-10-12）

- **AC1** ✓ `npm run typecheck`（3 workspace）、`npm test`（shared 10 / client 14 / admin 55 = 79 用例）、`npm run build`（两端）全绿。
- **AC2** ✓ `grep` 源码无 `from 'antd'` / `@ant-design/icons` / `od-*` 残留；无任何 `package.json` 声明 `antd`。
- **AC3** ✓ `@shared` 引用 68 处全部解析（typecheck 佐证）；shared 仅移除 antd 主题，无功能改动。
- **AC4** ✓ `dev:client`(:5173) 与 `dev:admin`(:5174) 均返回 200，无启动错误。
- **AC5** ✓ client 12 页接真实 API；admin 由子任务 5 核验（`admin-diff.md`，结论「无需重建」）。
- **AC6** ✓ 原 3 个 client 用例（hero 轮播真实计时、浮窗 5 断言、markdown 表格区域）全部保留在新锚点上，覆盖不减少；新增守卫与基础设施用例。
- **AC7** ✓ `index.md`、`component-guidelines.md`、`directory-structure.md`、两个 README 已更新。
- **AC8** ✓ 见上方 Deferred。

## Out of Scope

- `backend/`、`docs/spec/openapi.yaml`、部署件。
- 新增业务功能；只做重建与接线，行为对齐现状。
- 后端契约变更。
