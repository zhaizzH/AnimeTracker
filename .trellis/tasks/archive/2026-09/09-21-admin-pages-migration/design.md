# Design：admin 其余页面迁移与依赖清理

> 需求与验收见 `prd.md`（R1–R19 / AC1–AC8）。本设计覆盖阶段 E（页面迁移）、F（依赖清理）、G（spec 修订）。

## 1. 现状事实（本会话直读源码）

### 1.1 antd 引用清单（`grep -rn "from 'antd'" src/`）

| 文件 | antd 符号 |
|---|---|
| `guards.tsx` | `message` |
| `pages/AdminLogin.tsx` | `Button, Card, Form, Input, message` |
| `pages/AgentChat.tsx` | `Button, Collapse, Input, Layout, List, Space, Typography` |
| `pages/AgentConfig.tsx` | `Button, Card, Col, Descriptions, Form, Input, InputNumber, List, Popconfirm, Row, message` |
| `pages/Import.tsx` | `Button, Form, Input, InputNumber, Radio, Select, Space, Table, message` |
| `pages/Logs.tsx` | `Card, Col, DatePicker, Input, Row, Select, Space, Statistic, Table` |
| `pages/Subjects.tsx` | `Button, Form, Input, InputNumber, Modal, Popconfirm, Select, Space, Table, message` |
| `pages/Users.tsx` | `Popconfirm, Select, Switch, Table, message` |
| **`router.tsx`** | **`Spin`** |

> ⚠️ **PRD 缺口**：`router.tsx` 未在 R1–R9 列出，但 R10/AC4 要求 `admin/src` 全目录无 antd。本设计将 `router.tsx` 的 `Spin` → `Skeleton` 纳入范围（属 E 阶段的最小补齐，不改变业务逻辑）。若判定应单独成任务，需在实现前确认。

### 1.2 现有 shadcn primitive（`src/components/ui/`，共 24 个）

`alert-dialog avatar badge breadcrumb button card chart dialog dropdown-menu input input-group kbd label radio-group scroll-area select separator sheet sidebar skeleton switch table textarea tooltip`

### 1.3 缺失映射（antd → 现有 primitive）

| antd | shadcn 现状 | 处理 |
|---|---|---|
| `Button` `Card` `Input` `Select` `Switch` `Table` `Modal` `Popconfirm` `Radio` `Spin` | 已有 `button/card/input/select/switch/table/dialog/alert-dialog/radio-group/skeleton` | 直接替换 |
| `Input.TextArea` | `textarea` | 直接替换 |
| `DatePicker.RangePicker` | **缺** | 见 §2.3 |
| `Form` / `Form.Item` | **缺**（且不引入 RHF） | 见 §2.1 |
| `InputNumber` | **缺** | 见 §2.2 |
| `Collapse` | **缺** | 见 §2.4 |
| `List` | **缺** | 用语义 `ul/li` + tailwind，不装组件 |
| `Space` / `Row` / `Col` | 不需要 | 用 `flex`/`grid` class |
| `Typography` | 不需要 | 用 `p`/`span` + class |
| `Descriptions`（AgentConfig 导入了但**未实际使用**） | 不需要 | 直接删除该 import |
| `Statistic`（Logs） | 不需要 | 用现有 `card` + 文本 |

> `Descriptions` 是死 import：`AgentConfig.tsx` 中无任何 `<Descriptions` 用法。迁移时直接移除，不需要替代实现。

## 2. 关键设计决策

### 2.1 表单：不引入 react-hook-form

antd `Form` 提供受控取值 + 校验。现有 5 个表单（AdminLogin / Subjects / Import / AgentConfig / 各处筛选）大多字段少、校验简单。

**决策**：用受控 `useState` + 原生 `<form onSubmit>` 重写，校验用最小内联断言（必填 / 数值范围）。不新增 `react-hook-form` / `zod` 依赖。

理由：项目 spec 明确「当前没有 Zod 等运行时 schema」（`component-guidelines.md` 类型安全章节），且这些表单的字段数量与规则复杂度不足以摊平一个表单库的成本。

**已确认的校验规则需原样保留**：
- AdminLogin：username、password 必填。
- Subjects：`bangumiId`、`name` 必填（仅新建时要求 `bangumiId`）；`type` min 1；`eps` min 0。
- AgentConfig：`temperature` ∈ [0,2]；`maxTokens` min 1；`thinkingBudget` min 0。
- Import：`mode` 必填；`workers` min 1。

### 2.2 InputNumber → 原生 `type="number"`

antd `InputNumber` 的 `min/max/step/precision` 直接映射到原生 input 属性（`step` 用 `0.1` 表示 `precision=1`）。取值需要 `onChange` 时做 `value === '' ? undefined : Number(value)` 收窄，避免 `NaN` 进入 queryKey 或 mutation。**不新增依赖。**

### 2.3 DatePicker.RangePicker（仅 `Logs.tsx`）

最省方案是两个原生 `<input type="date">`，直接产出 `YYYY-MM-DD`，与现有 `format('YYYY-MM-DD')` 输出完全一致，且无新依赖、可用键盘操作。

**决策**：用两个 `<input type="date">`，标签分别「起始日期」「结束日期」。不新增日期库（`dayjs` 已在 `package.json`，但此处不需要它）。

### 2.4 Collapse（仅 `AgentChat.tsx` 的思考过程）

只需一个可控展开/收起的区域，`activeKey`/`onChange` 语义等价于 `open` 布尔 + 按钮。

**决策**：用 `<button aria-expanded>` 头部 + 条件渲染内容区。保留 `useEffect(() => { if (!streaming) setOpen(false) }, [streaming])` 的「完成后自动收起」行为，`open` 初值 `true`。

### 2.5 反馈通道：统一 `@/lib/toast`

`@/lib/toast` 已存在并被 `AdminLayout.tsx` 与 `AdminLayout.test.tsx` 使用。所有 `message.success/error` 改为该封装导出的 `toastSuccess` / `toastError`。

### 2.6 `guards.tsx` render 阶段副作用（R8）

现状：`RequireAdmin` 在 render 中调用 `message.error('无管理权限')`。修正为在 `useEffect` 中触发，并保证只触发一次；`<Navigate>` 的返回保持原样。

`guards.test.tsx` 的 mock 目标从 `antd` 改为 `@/lib/toast`，**保留原有三条断言**（未登录跳转 / 非管理员拒绝 / 管理员放行）与 `location.state.from` 断言。

## 3. 逐页迁移要点与保留契约

每页一次提交；下表「保留」列即 AC2 的逐项证据目标。

| 页面 | 目标布局 | 必须保留 |
|---|---|---|
| `AdminLogin` | 居中 `Card` + 受控表单 | 非 ADMIN → toast「该账号无管理权限」+ `setUnauthenticated()`；成功 → `setAuthenticated` + `publishSessionAvailable()` + `location.state.from` 回跳（默认 `/admin/dashboard`） |
| `Subjects` | 筛选行 + `Table` + `Dialog` 表单 | 6 个筛选维度（`q`/`tag[]`/`scoreMin`/`scoreMax`/`year`/`weekday`）、`setFilter` 时 `setPage(1)`、`invalidateQueries(['admin-subjects'])`、新建/编辑/删除确认、`bangumiId` 与 `name` 必填 |
| `Users` | `Table` + `Switch` + `Select` | `pendingUserIds`(ref) + `pendingUserIdsSnapshot`(state) 防重复切换；禁用确认文案逐字保留「禁用后，该用户将在所有设备上立即退出。确定继续吗？」；角色变更直接 mutate、不包确认 |
| `Import` | inline 触发表单 + 提示行 + 筛选 + `Table` | `st` 3000ms 轮询；`totalLogs > 0` 时失效 `import-records` 的 effect；四种模式条件字段；`runMut.isPending` 加载态 |
| `Logs` | 筛选行 + 4 统计卡 + `Table` | 4 卡片口径（总数/成功/失败/平均耗时）；模块与状态筛选；用户名 `onBlur` 触发；action 列点击回填筛选**并 `setPage(1)`** |
| `AgentConfig` | 左提示词列表 + 右编辑区 + 模型配置表单 | 提示词加载与选中、保存/重置、`staleTime: Infinity`、保存配置后失效 `agent-config`、`temperature` 范围校验 |
| `AgentChat` | 等价 Sider + Content | 思考过程折叠（流式展开、完成收起）、消息区 `aria-live="polite"`、滚动到底、流式中禁用输入、发送/停止切换、会话新建/选择/删除（删除按钮 `e.stopPropagation()`）、高度等价 `calc(100vh - 120px)` |

> Users 的 `pendingUserIds` 三段式（ref + snapshot + `finally` 清理）是防重复的**唯一**机制，迁移时逐行保留，不得简化为单一 state。

## 4. 依赖清理（F 阶段）

1. `grep -rn "from 'antd'" src/` 必须为空后，才移除依赖。
2. `admin/package.json` 移除：`antd`、`echarts`、`echarts-for-react`、`@ant-design/icons`（devDependencies）。
3. `vite.config.mts` 的 `manualChunks`：现有 antd 规则变为死代码，应删除；补 `recharts` 与 radix 归属规则。`chunkSizeWarningLimit` 视实测产物调整。
4. 确认 `client` 仍需要 antd，**不动** `frontend/client` 与 `shared/package.json` 的 `antd` type 依赖（PRD Out of Scope）。

## 5. Spec 修订（G 阶段）

| 项 | 文件:行 | 方向 |
|---|---|---|
| R14 | `component-guidelines.md:29` | 拆分 admin（shadcn/Tailwind）与 client（AntD + `od-*`） |
| R15 | `component-guidelines.md:33` | admin 暗色已支持，删除 light-only 表述 |
| R16 | `component-guidelines.md:14` | shared 已无 antd 运行时引用（保留 `client` 对 `antdTheme` 的依赖说明） |
| R17 | `directory-structure.md` / `hook-guidelines.md` | admin 页面/路由清单、`@/` 别名约定 |
| R18 | `quality-guidelines.md:32` | 分包说明去掉 antd chunk |
| R19 | `index.md` | admin 技术栈描述 |

> 行尾：spec 文件为混合 CRLF/LF。为避免整文件重排放大 diff，**优先做定点 `edit`**；若某文件确实需要整段重写，在提交信息中注明行尾归一化。

## 6. 验证与门禁

```bash
cd frontend
npm run typecheck
npm test -w admin
npm run build          # 交付型变更，必须执行
```

- AC6 证据：build 产物中无 `vendor-antd*` / echarts chunk（对比迁移前后的 asset 列表）。
- AC1/AC2 证据：每页提交信息记录「迁移前 antd 组件 → 迁移后 primitive」对照，并对保留项给出实际验证（测试或可重复操作步骤），不使用断言代替。
- 高风险页（Users / Import / AgentChat / Logs）优先补最小测试。

## 7. 风险与回滚

| 风险 | 缓解 | 回滚 |
|---|---|---|
| 逐页行为不等价（Users 防重复 / Import 轮询 / AgentChat 流式） | 每页独立提交；逐项手动核对 R 列出的保留契约 | 逐页 `git revert` |
| 移除 antd 后仍有隐式引用 | 先 `grep` 清零，再删依赖，最后 `build` 验证 | 恢复 package.json |
| `guards.test.tsx` mock 目标变更致测试失效 | 只换 mock 目标，保留断言意图 | — |
| spec 行尾归一化放大 diff | 定点 `edit`；必要时提交信息说明 | — |
| `manualChunks` 未更新致分包劣化 | AC8 对比产物体积 | 调整白名单 |
| 表单改用受控 state 引入取值 bug（`NaN`/`undefined`） | 数值输入统一 `'' → undefined` 收窄；高风险表单补测试 | 单页回退 |
