# admin 其余页面迁移与依赖清理

> 父任务：`09-21-admin-tailwind-shadcn-dashboard`。本子任务覆盖其 `implement.md` 的**阶段 E + F + G**，是整条链路的收尾。

## Goal

把 admin 剩余的 7 个页面从 Ant Design 迁移到 shadcn/ui，随后移除 antd / echarts 依赖并同步修订前端规范。

用户价值：admin 彻底摆脱 AntD，产物不再打包 antd 与 echarts，前端规范与实际实现重新对齐。

## Dependencies

**前置依赖：`09-21-admin-ui-foundation` 与 `09-21-admin-app-shell` 均须完成。** 需要 shadcn 地基、sonner toast 封装、`useAuthStatus()`，以及已替换为 AppShell 的外壳。

**与 `09-21-admin-dashboard-block` 的关系**：二者无互相依赖，但**都修改 `admin/package.json` 的依赖区**（本子任务移除 antd/echarts；dashboard 子任务不改依赖）。若并行执行需在合并时留意依赖区冲突。建议串行：先 dashboard，后本子任务，因为本子任务负责最终移除 echarts 依赖（需 dashboard 先删掉 `charts.tsx`）。

**被依赖**：无 —— 本子任务是父任务的收尾，完成后触发父任务的集成审查。

## Requirements

### E. 页面迁移（逐页替换，每页一次提交）

- R1：`AdminLogin.tsx` — Card + Input + Label + Button。保留：角色非 `ADMIN` 时的 `该账号无管理权限` 分支、`setUnauthenticated()`、`publishSessionAvailable()`、`location.state.from` 回跳（默认 `/admin/dashboard`）。
- R2：`Subjects.tsx` — Table + Dialog 表单 + 筛选控件。保留：全部筛选维度（`q` / `tag` 多选 / `scoreMin` / `scoreMax` / `year` / `weekday`）、分页、`invalidateQueries(['admin-subjects'])`、新建/编辑/删除确认、`id` 与 `bangumiId` 的必填校验。
- R3：`Users.tsx` — Table + Switch + Select。**必须保留** `pendingUserIds` + `pendingUserIdsSnapshot` 的防重复切换语义，以及禁用用户的确认文案：`禁用后，该用户将在所有设备上立即退出。确定继续吗？`；角色变更直接触发 mutation 且不做 Popconfirm 包裹。
- R4：`Import.tsx` — Radio group + Select + Input + Table。保留：`st` 的 3000ms 轮询、`totalLogs > 0` 时失效 `import-records` 的 effect、四种模式（full/season/recent/since）的条件字段、`runMut.isPending` 的加载态。
- R5：`Logs.tsx` — Card + Select + Input + Table + 日期区段。保留：4 个统计卡（总数/成功/失败/平均耗时）、模块与状态筛选、用户名 `onBlur` 触发筛选、action 列点击回填筛选并重置页码。
- R6：`AgentConfig.tsx` — Card + List + Textarea + 表单。保留：提示词列表加载与选中、保存/重置提示词、`staleTime: Infinity`、保存配置后失效 `agent-config`、`temperature` 的 0–2 范围校验。
- R7：`AgentChat.tsx` — 复刻 Sider + Content 布局。保留：思考过程折叠（流式期间展开、完成后自动收起）、流式消息区 `aria-live="polite"`、滚动到底、流式中禁用输入、发送/停止切换、会话新建/选择/删除（`e.stopPropagation()`）、高度 `calc(100vh - 120px)` 的等价布局语义。
- R8：`guards.tsx` — 替换 `message.error` 为新的 toast 封装，**并顺带修正 render 阶段副作用**（规范已记录的债务），补对应测试。
- R9：`admin/src/guards.test.tsx` — mock 目标从 `antd` 改为新的 toast 模块，**保留原有断言意图**。

### F. 依赖清理

- R10：`grep` 确认 `admin/src` 下无 `from 'antd'` 残留。
- R11：从 `admin/package.json` 移除 `antd`、`echarts`、`echarts-for-react`，以及未被使用的 `@ant-design/icons`（在 devDependencies）。
- R12：`admin/vite.config.mts` 的 `manualChunks` 白名单补 `recharts` 与 radix 系规则；`chunkSizeWarningLimit` 相应调整或给出说明。
- R13：检查 `admin/vitest.config.mts` 是否需要新增别名等配置。

### G. Spec 修订

- R14：`component-guidelines.md:29` — 区分 admin（shadcn/ui + Tailwind）与 client（AntD + `od-*`）。
- R15：`component-guidelines.md:33` — 更新 admin 暗色支持说明（D5 已推翻 light-only）。
- R16：`component-guidelines.md:14` — 更新 shared 运行时依赖规则（shared 已无 antd 运行时引用）。
- R17：`directory-structure.md` / `hook-guidelines.md` — 更新 admin 页面与路由清单、`@/` 别名约定。
- R18：`quality-guidelines.md:32` — 更新分包说明。
- R19：`index.md` 若有 admin 技术栈描述，一并更新。
      ⚠️ 这些文件为混合 CRLF/LF，Edit 会整体改写为 LF 并放大 diff —— 优先 Write 重写，或在提交信息中说明该现象。

## Acceptance Criteria

- [ ] AC1：7 个页面 + `guards.tsx` 均不再 `import ... from 'antd'`，且**每个页面给出迁移前后的行为对照证据**（不是断言）。
- [ ] AC2：逐页核对 R1–R9 列出的「保留」项，每项均有实际验证证据。特别地：
      - Users 的防重复切换：连续快速点击不产生第二次请求；
      - Import 的轮询与失效 effect 实际生效；
      - AgentChat 的流式折叠、自动收起、停止按钮行为正确；
      - Logs 的 action 列点击回填筛选并重置页码。
- [ ] AC3：`guards.tsx` 不再在 render 阶段产生副作用，且新增测试覆盖该行为。
- [ ] AC4：`grep -rn "from 'antd'" frontend/admin/src` 无结果。
- [ ] AC5：`admin/package.json` 已移除 `antd` / `echarts` / `echarts-for-react` / `@ant-design/icons`。
- [ ] AC6：`npm run build -w admin` 成功，产物中**不含 antd 与 echarts chunk**。
- [ ] AC7：`.trellis/spec/frontend/` 已按 R14–R19 修订，且与最终实现一致。
- [ ] AC8：`cd frontend && npm run typecheck` 通过；`npm test -w admin` 通过；`npm run build` 成功且分包体积无明显劣化。

## Out of Scope

- `Dashboard.tsx`（属 `09-21-admin-dashboard-block`）。
- `AdminLayout.tsx` / `main.tsx` 的外壳部分（属 `09-21-admin-app-shell`；本子任务只在其基础上确认无 antd 残留）。
- 迁移 `frontend/client`。
- 改动任何页面的业务逻辑或后端接口。
- `shared/package.json` 的 `antd` 依赖本身（`theme.ts` 仍需 `import type`；client 仍依赖 `antdTheme`）。

## Key Decisions（继承父任务）

- D2：迁移范围含全部 8 个页面（Dashboard 由兄弟子任务承担）。
- D5：admin 支持暗色，页面样式需在 light 与 dark 两套变量下都可读。

## 风险

| 风险 | 缓解 | 回滚 |
|---|---|---|
| 逐页行为不等价（Users 防重复 / Import 轮询 / AgentChat 流式是高风险点） | 每页一次提交；AC2 逐项证据 | 逐页回退 |
| 移除 antd 后仍有隐式引用 | `grep` + `build` 必须成功 | — |
| `guards.test.tsx` mock 目标变更致测试失效 | 保留断言意图，仅换 mock 目标 | — |
| spec 混合行尾致 diff 膨胀 | 优先 Write 重写或在提交信息中说明 | — |
| `manualChunks` 白名单未更新致分包劣化 | AC8 对比构建产物 | — |
