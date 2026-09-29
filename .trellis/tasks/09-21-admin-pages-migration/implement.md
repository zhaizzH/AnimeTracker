# Implement：admin 其余页面迁移与依赖清理

> 需求见 `prd.md`（R1–R19 / AC1–AC8），技术方案见 `design.md`（§1–§7）。按顺序执行；**本计划不含 `task.py start`**，需经用户审阅后另行确认。

## 前置

- 依赖确认：`admin-ui-foundation`、`admin-app-shell`、`admin-dashboard-block` 均已归档完成；`charts.tsx` 已删除。
- 分支：在 `main` 之外新建 `feat/admin-pages-migration`（或复用当前 admin 特性分支，由用户确认）。
- 工作区基线：`git status --short` 只应含本任务 artifacts；`frontend/admin/package.json` 与 `frontend/package-lock.json` 的既有行尾噪声不纳入本任务提交。
- 全量基线：`cd frontend && npm run typecheck && npm test -w admin` 当前应通过（admin 3 文件 16 用例）。

## 验证命令（每阶段结束都跑）

```bash
cd frontend
npm run typecheck
npm test -w admin
npm run build          # 阶段 F 之后必须执行并对比产物
```

## 执行清单

### 阶段 E — 页面迁移（逐页一次提交）

每页完成标准：该页 `grep -n "from 'antd'"` 无命中；保留契约逐项核对；`typecheck` 通过；提交信息写明「迁移前 antd → 迁移后 primitive」对照。

- [ ] **E0 基础设施补齐**（先做，后续页面共用）
  - [ ] `guards.tsx`：`message.error` → `toastError`；副作用移入 `useEffect` 并只触发一次；`<Navigate>` 语义不变（R8）。
  - [ ] `guards.test.tsx`：mock 目标 `antd` → `@/lib/toast`；保留原三条断言语义与 `location.state.from` 断言（R9）。
  - [ ] `router.tsx`：`Spin` → `skeleton` 的 Suspense fallback（design §1.1 缺口；PRD R1–R9 未列但 R10/AC4 要求）。
  - [ ] 运行 `npm test -w admin`，确认 guards 测试仍通过。

- [ ] **E1 `AdminLogin.tsx`**（R1）
  - [ ] `Card` + 受控 `useState` 表单 + `Input`/`Label`/`Button`；校验 username/password 必填。
  - [ ] 保留：非 ADMIN → `toastError('该账号无管理权限')` + `setUnauthenticated()`；成功 → `setAuthenticated` + `publishSessionAvailable()` + `location.state.from` 回跳（默认 `/admin/dashboard`）。
  - [ ] 提交。

- [ ] **E2 `Users.tsx`**（R3，高风险）
  - [ ] `Table` + `Switch` + `Select`；禁用确认用 `AlertDialog`。
  - [ ] **逐行保留** `pendingUserIds`(ref) + `pendingUserIdsSnapshot`(state) + mutation `finally` 清理三段式。
  - [ ] 禁用确认文案逐字保留：`禁用后，该用户将在所有设备上立即退出。确定继续吗？`
  - [ ] 角色变更直接 `mutate`，**不**包确认。
  - [ ] 补测试：连续快速点击开关只产生一次请求。
  - [ ] 提交。

- [ ] **E3 `Import.tsx`**（R4，高风险）
  - [ ] inline 表单改受控 state；`Radio.Group` → `radio-group`；`InputNumber` → 原生 number（`'' → undefined` 收窄）。
  - [ ] 保留：`st` 3000ms 轮询；`totalLogs > 0` 时失效 `import-records` 的 effect；四种模式条件字段（`season`→key、`since`→since）；`runMut.isPending` 加载态。
  - [ ] 补测试：轮询配置与失效 effect 生效。
  - [ ] 提交。

- [ ] **E4 `Logs.tsx`**（R5）
  - [ ] 4 个统计卡改用 `card` + 文本，口径不变（总数/成功/失败/平均耗时）。
  - [ ] `DatePicker.RangePicker` → 两个 `<input type="date">`（design §2.3）。
  - [ ] 保留：模块与状态筛选；用户名 `onBlur` 触发；action 列点击回填筛选**并 `setPage(1)`**。
  - [ ] 补测试：action 点击后筛选与页码。
  - [ ] 提交。

- [ ] **E5 `Subjects.tsx`**（R2）
  - [ ] `Table` + `Dialog` 表单 + 筛选控件；`Modal` → `dialog`；`Popconfirm` → `alert-dialog`。
  - [ ] 保留：6 个筛选维度、`setFilter` 时 `setPage(1)`、`invalidateQueries(['admin-subjects'])`、新建/编辑/删除确认、`bangumiId`(仅新建) 与 `name` 必填。
  - [ ] `type` 默认 2、min 1；`eps` min 0。
  - [ ] 提交。

- [ ] **E6 `AgentConfig.tsx`**（R6）
  - [ ] 删除死 import `Descriptions`（design §1.3）。
  - [ ] `List` → 语义 `ul/li`；`Popconfirm` → `alert-dialog`；模型配置表单改受控 state。
  - [ ] 保留：提示词加载与选中、保存/重置、`staleTime: Infinity`、保存配置后失效 `agent-config`、`temperature` ∈ [0,2] 校验、`maxTokens` min 1、`thinkingBudget` min 0。
  - [ ] 提交。

- [ ] **E7 `AgentChat.tsx`**（R7，高风险）
  - [ ] 布局改等价 `flex` Sider + Content；高度保持 `calc(100vh - 120px)` 语义。
  - [ ] `Collapse` → 可控 `<button aria-expanded>` + 条件渲染（design §2.4）；保留 `useEffect`「非流式即收起」、初值 `true`。
  - [ ] 保留：消息区 `aria-live="polite"`、滚动到底、流式中禁用输入、发送/停止切换、会话新建/选择/删除（删除按钮 `e.stopPropagation()`）。
  - [ ] 补测试：折叠自动收起、流式中输入禁用、停止按钮。
  - [ ] 提交。

- [ ] **E8 收尾核对**
  - [ ] `grep -rn "from 'antd'" frontend/admin/src` 无结果（AC4）。
  - [ ] `npm run typecheck && npm test -w admin` 通过。

### 阶段 F — 依赖清理（R10–R13）

- [ ] **F1** 确认 E8 的 antd grep 为空后：`admin/package.json` 移除 `antd`、`echarts`、`echarts-for-react`、`@ant-design/icons`（AC5）。
- [ ] **F2** 安装/刷新 lockfile，运行 `npm run build`，确认产物**不含** antd/echarts chunk（AC6）：对比 `dist/assets/` 中 `vendor-antd*` 是否消失。
- [ ] **F3** `vite.config.mts`：删除已成死代码的 antd `manualChunks` 规则；补 `recharts` 与 radix 归属；按实测调整 `chunkSizeWarningLimit`（R12）。
- [ ] **F4** 检查 `vitest.config.mts` 是否需要新增别名等配置（R13）。
- [ ] **F5** 再跑 `npm run typecheck`、`npm test -w admin`、`npm run build`；记录产物体积对比（AC8）。
- [ ] **F6** 提交（含 lockfile 与本任务相关的 package.json 变更）。

**回滚点 F**：F1/F2 合并为一次提交，`git revert` 即可恢复到 antd 未移除状态，E 阶段成果不受影响。

### 阶段 G — Spec 修订（R14–R19）

- [ ] **G1** `component-guidelines.md:29`：拆分 admin（shadcn/Tailwind）与 client（AntD + `od-*`）（R14）。
- [ ] **G2** `component-guidelines.md:33`：更新 admin 暗色支持（R15）。
- [ ] **G3** `component-guidelines.md:14`：更新 shared 运行时依赖规则（R16）。
- [ ] **G4** `directory-structure.md` / `hook-guidelines.md`：admin 页面与路由清单、`@/` 别名约定（R17）。
- [ ] **G5** `quality-guidelines.md:32`：更新分包说明（R18）。
- [ ] **G6** `index.md`：admin 技术栈描述（R19）。
- [ ] **G7** 复核 spec 与实际实现一致；行尾噪声处理按 design §5（AC7）。
- [ ] **G8** 提交。

## 验证清单（交付前）

- [ ] `cd frontend && npm run typecheck` 通过（AC8）。
- [ ] `npm test -w admin` 通过，且新增测试覆盖 Users 防重复、Import 轮询/失效、AgentChat 折叠与停止、Logs action 回填（AC2/AC3）。
- [ ] `npm run build` 成功，产物无 antd/echarts chunk，体积无明显劣化（AC6/AC8）。
- [ ] 逐页给出「迁移前后行为对照」证据（AC1），保留项逐条有实际验证（AC2）。
- [ ] 按 AC1–AC8 逐项更新 PRD 验收记录。
- [ ] 最终全范围 check：确认未混入 `frontend/client`、`shared`、`Dashboard.tsx` 或其他任务的改动（Out of Scope）。

## 风险文件

- 主要改动：`admin/src/pages/{AdminLogin,Subjects,Users,Import,Logs,AgentConfig,AgentChat}.tsx`、`admin/src/guards.tsx`、`admin/src/guards.test.tsx`、`admin/src/router.tsx`、`admin/package.json`、`admin/vite.config.mts`、`admin/vitest.config.mts`、`.trellis/spec/frontend/**`。
- 被依赖但不在范围内：`components/dashboard/**`、`layouts/AdminLayout.tsx`、`frontend/client/**`、`packages/shared/**`。
- 逐页回滚：每页一次提交，可单独 `git revert`。
