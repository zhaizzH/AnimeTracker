# Agent 模块优化：拆 subject_resolution + PreviewableAction 抽象 + 契约测试

> 这是一份父任务 PRD。具体技术设计、执行步骤、回滚点在各子任务的 `prd.md` / `design.md` / `implement.md` 中展开。

## Background · 为什么是现在

来自 5 轮拷问会话的根因诊断。当前 agent 模块的「总出错」不是单元逻辑烂（585 个测试全绿），而是：

| 根因 | 证据 | 后果 |
|---|---|---|
| **契约靠默契** | `business_http.py` 字段名硬编码字符串、SSE 帧协议靠 `useAgentChat` 前端去对齐、`PendingAction` 4 类判别联合没有 schema 快照 | 跨层字段改名/语义漂移，CI 拦不住，靠用户发现 |
| **prompt 是代码但不受工程约束** | 路由判断写在 prompt 里，模型升级/prompt 调整即翻车 | 无类型检查、无回归测试、改完无法 diff 影响范围 |
| **写操作工具数 = 3N** | wishlist/collection_type/collection_progress 各写一遍「预览/确认/取消」三件套，共 9 个工具 | 每加新写业务 prompt 长度 +3 工具描述，模型选错率上升 |
| **历史包袱文件** | `subject_resolution.py` 564 行单文件，作者本人「三句话讲不清契约」（Q3=C） | 调用方误用、跨层 bug、改动恐惧症 |
| **反馈回路靠用户** | Q5=A 「用户反馈/手动测试发现」 | bug 上线才知道，「总出错」的主观感受被放大 |

## Goal · 目标

把 agent 模块的工程质量从「契约靠默契、发现靠用户」提升到「契约靠 CI、发现靠自动化」。

**核心动机**（来自拷问 Q5=C）：能把 564 行历史包袱拆成「三句话能讲清契约」的模块，写进简历。

**愿景陈述**（来自拷问 Q5=D+C 组合）：
> 跨层契约错从「靠事后 fix」变成「靠事前 CI 拦截」（主），加一个写操作的成本从「改 3 文件 / 写 3 工具」降到「改 1 文件 / 声明 1 个 PreviewableAction 子类」（辅）。

## Scope · 范围

### In Scope（本任务覆盖）

| # | 优化项 | 类型 | 子任务 |
|---|---|---|---|
| 0 | 风险盘点（每个 >100 行的文件问一句「改坏了影响什么」） | 30 分钟盘点 | 不开任务，journal 追加 |
| 1 | 拆 `subject_resolution.py` 为 4 个单一职责模块 | 文件级拆分 | `10-20-opt-split-subject-resolution` |
| 2 | PendingAction 生命周期管理器（把 ContextVar/Redis/state 三层同步显性化） | 设计显性化 | `10-20-opt-pending-action-lifecycle` |
| 3 | PreviewableAction 抽象 + 三业务对齐矩阵 | 模板方法模式 | `10-20-opt-previewable-action` |
| 4 | agent↔business 契约测试（OpenAPI/SSE/previewId 协议） | CI 拦截 | `10-20-opt-contract-tests` |

### Out of Scope（明确不做）

- **不做 prompt 回归评测套件**（evals 扩充）——属于下一轮优化
- **不动 subject_resolution 的算法逻辑**——只拆文件，不改召回策略
- **不动路由节点的 LLM 判断方式**——契约测试只保证「输出符合 schema」，不保证「路由选对」
- **不重写 admin 节点**——范围控制在 client 写操作链路
- **不动 business 侧 Java 代码**——契约测试只在 agent 侧跑，business 只负责导出 OpenAPI

## Constraints · 约束

来自拷问 Q4=B（接受模块内重构，不动整体架构）：

1. **不许动 LangGraph 状态图拓扑**——节点数量、路由判断方式不变
2. **不许动 SSE 帧协议本身**——只能加契约测试锁定现有协议，不能改协议
3. **不许动 Redis 键格式 / TTL**——持久层兼容，旧 JSON 仍能解析
4. **不许改业务方 `business` Spring Boot 代码**——只能消费它的 OpenAPI 导出
5. **不许改现有 585 个测试，除非测试本身在测三件套复制粘贴**——重构必须保持测试全绿

## Acceptance Criteria · 验收信号

### 主信号（来自拷问 Q5=D 为主）

- [ ] **CI 跑契约测试**，覆盖以下三个边界，全绿：
  - agent→business HTTP：所有 `business_http.py` 的 `request()` 调用，路径与字段在 business OpenAPI 里有定义
  - SSE 帧协议：`state` 字段取值域、`result=error` vs `state=error` 语义、`is_end` 帧序
  - previewId 写协议：Redis key 格式、TTL、确认时 payload 与 preview 版本绑定
- [ ] **business 改字段名 → agent 契约测试红**（手动验证一次，证明拦截有效）
- [ ] **agent 改路径拼写 → 契约测试红**（手动验证一次，证明拦截有效）

### 辅信号（来自拷问 Q5=C 为辅 + Q3 未来扩展需求）

- [ ] **subject_resolution.py 主文件 < 100 行**，每个新文件 docstring ≤ 3 句话讲清契约
- [ ] **现有 29 个 subject_resolution 测试全绿，不改测试**
- [ ] **新增一个写业务**（以「评分 rate 0-10」为例）：从「改 3 文件 / 写 3 工具」降到「改 1 文件 / 声明 1 个 PreviewableAction 子类」
- [ ] **现有 585 个测试全绿**（优化项 3 完成后）
- [ ] **工具代码里不再出现** `emit_pending_action_*` 或 `InjectedState("pending_action")`——统一走 lifecycle 入口（优化项 2 完成后）

### 简历一句话（最终交付）

> 把 564 行的 agent 历史包袱文件拆成 4 个单一职责模块，用三句话契约 docstring 替换口口相传；通过 PreviewableAction 模板方法模式把写操作工具数从 3N 收敛到 N，新增写业务只需声明一个子类；并落地 agent↔business 契约测试体系，把跨层字段漂移从「线上发现」提前到「CI 拦截」。

## Execution Order · 执行顺序

```
优化项 0 (风险盘点)         ← 30 分钟，journal 追加，不开任务
   ↓
优化项 1 (拆 subject_resolution)  ← 核心动机，先做这个攒动力
   ↓
优化项 2 (PendingAction 生命周期) ← 拆完 subject_resolution 自然看清三层
   ↓
优化项 3 (PreviewableAction)      ← 有 0/1/2 垫底，抽象有依据
   ↓
优化项 4 (契约测试)               ← 最后兜底，确保前面没引入新漂移
```

**理由**：1 是简历核心、风险最低（纯文件拆分）；2 是 1 的副产品（拆完才看清三层）；3 需要 1/2 的成果做基础（PendingAction 类型已知 + 三业务对齐矩阵）；4 是兜底，放最后才能拦截前面的改动。

## Risks · 风险

| 风险 | 影响 | 缓解 |
|---|---|---|
| 拆 subject_resolution 时暴露隐藏契约（某调用方依赖内部状态） | 测试红但报错难定位 | 优化项 0 先列调用方清单 |
| 三业务对齐矩阵做不好 → PreviewableAction 漏参数 | 抽象不完整，未来又要改 | 优化项 3 前置「对齐矩阵」步骤，逐字段决策 |
| 契约测试做太晚 → 前面优化引入新漂移 | 优化本身制造新 bug | 优化项 4 完成后，手动触发一次「business 改字段 → 测试红」验证拦截有效 |
| 范围蔓延到 prompt 工程 / evals | 任务永远做不完 | 在 Out of Scope 明确划出 |

## Open Questions · 待子任务回答

- 优化项 1：`subject_resolution.py` 的 564 行具体如何切到 4 个文件？切分点在哪里？（子任务 design.md 回答）
- 优化项 2：lifecycle 类的方法签名长什么样？同步还是异步？（子任务 design.md 回答）
- 优化项 3：三业务对齐矩阵的 5 个字段具体取值？哪些保留差异、哪些统一？（子任务 prd.md 回答）
- 优化项 4：business OpenAPI 导出格式是什么？agent 侧怎么消费？（子任务 design.md 回答）

## Related

- 拷问会话原始记录：本次对话（5 轮 Q&A）
- 历史证据：`.trellis/workspace/zhaizzH/journal-1.md` 的「修复 Agent 运行时与测试报告问题」「补 3 处此前零测试覆盖的 Agent 盲区」等条目
- 相关 spec：`.trellis/spec/backend/agent-guidelines.md`（优化完成后需要同步更新）
