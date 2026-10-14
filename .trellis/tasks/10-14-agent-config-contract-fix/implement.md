# 执行计划：Admin Agent 配置页契约修复

## 前置

- 任务：`.trellis/tasks/10-14-agent-config-contract-fix`
- 契约与设计见 `prd.md` / `design.md`
- 目标文件：`frontend/admin/src/pages/AgentConfig.tsx`、`AgentConfig.test.tsx`
- 行尾：仓库内前端文件为 CRLF；用脚本改写后需保持 CRLF（避免整文件行尾翻转污染 diff）

## 步骤

### 1. 重写 AgentConfig.tsx（R1–R7）

- [x] R1 列表解析：`raw.map((x) => x.promptKey)`，删双分支
- [x] R2 `loaded` 状态 + 保存按钮禁用条件（防空内容覆盖）
- [x] R3 `serverCfg` 保留 GET 原始对象，提交时作为基底
- [x] R4 表单新增 `modelRoute`、`reasoningEffort` 两个 Input
- [x] R5 列表请求错误态 + 重试
- [x] R6 `seq` ref 竞态守卫
- [x] R7 `resetPrompt` 补 `onError`

### 2. 同步测试（R8）

- [x] 把 `adminAgentApi.prompts` 的 mock 从 `{keys: [...]}` 改为真实裸数组 `[{promptKey, promptContent}]`
- [x] 新增用例：
  - 真实响应形状下列表显示真实 key（AC1）
  - 详情 404 时保存按钮禁用（AC2）
  - 提交配置保留 `modelRoute`/`reasoningEffort`（AC3）
  - 列表失败显示错误态而非"暂无提示词"（AC5）
  - 快速切换 content 与标题一致（AC6）
- [x] 复核既有 7 条用例，断言仍成立

### 3. 校验

- [x] `cd frontend/admin && npm run typecheck`
- [x] `cd frontend/admin && npm test`（记录实际数字）
- [x] `git diff --numstat` 确认行尾未翻转（改动行数与实际相当）

### 4. 运行态复验（可选但推荐）

- [x] 用 test1 登录，`/agent-config` 左栏应显示 5 个真实 key
- [x] 用 curl 预置 `{model, modelRoute, reasoningEffort}`，在页面点保存，再 GET 确认三字段仍在
- [x] 复验后还原配置为 `{}`（保持环境原状）

## 验证命令

```bash
cd frontend/admin && npm run typecheck && npm test
```

## 回顾门

- R2 是本次唯一的**写入安全**项，必须有用例覆盖（AC2），不能只靠代码审阅。
- R3 的 AC3 必须在**修正后的 mock** 下断言，避免重蹈"测试固化错契约"的覆辙。
- 若 AC3 的实现改为提交前重新 GET，需回到 `design.md` 更新权衡段落。

## 回滚点

- 任一阶段失败：`git checkout -- frontend/admin/src/pages/AgentConfig.tsx frontend/admin/src/pages/AgentConfig.test.tsx`
- 无后端改动、无数据迁移，回滚无副作用。
