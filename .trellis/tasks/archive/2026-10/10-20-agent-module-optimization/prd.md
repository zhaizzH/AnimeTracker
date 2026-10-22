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
| 4 | agent↔business 契约测试（OpenAPI/SSE/pending-action 协议） | CI 拦截 | `10-20-opt-contract-tests` |

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

- [x] **CI 跑契约测试**，覆盖以下三个边界，全绿：
  - agent→business HTTP：25 个出站调用点（24 属性 `.request` + 1 `asyncio.to_thread` 探针），路径与静态可判定字段在 business OpenAPI 里有定义
  - SSE 帧协议：`type` 四值枚举、`result=error` vs `state=error` 语义分离、`is_end` 帧序、`content` 子字段集
  - pending-action 写协议：Redis key 格式、600s TTL、确认时 payload 与 preview 版本绑定
- [x] **契约改字段名 → agent 契约测试红**（已验证：save 请求体 `epStatus`→`ep_status`，失败信息点名 `business_http.py:92`）
- [x] **agent 改路径拼写 → 契约测试红**（已验证：`/collections/counts`→`/collections/count`，失败信息点名 `collections.py:60`）

> 原始描述写的是「previewId 写协议」，但**代码中从未有过 `previewId`**。实际形态：business DTO 字段驼峰（`subjectId`/`summary`/`actionId`），agent 信封字段蛇形（`preview_id`/`user_id`/`expires_at`）。按实现现状修正描述，不改 runtime（Redis 存量兼容）。
>
> 漂移验证的**真实边界**：两次演练都只在「agent ↔ `openapi.yaml`」这条边上制造漂移，**未触及 Java 源码**。`openapi.yaml` 为手工维护，契约↔Java 仍无自动校验；套件也只断言 agent 实际发送的字段，不覆盖无人调用的响应字段。此边界已写入主 PRD 的 Risks 及 `contract-tests.md` 第 8 节。

### 辅信号（来自拷问 Q5=C 为辅 + Q3 未来扩展需求）

- [x] **`subject_resolution.py` 主文件从 564 行降至 403 行**，职责拆出三个独立模块：`title_normalizer.py`（30）、`candidate_matcher.py`（111）、`subject_authority.py`（79），每个 docstring ≤ 3 句话讲清契约。
  - ⚠️ **原 AC「主文件 < 100 行」未达成，且当初就不现实**：子任务自己的 PRD 已写明「拆分后主文件仍会有 ~330 行（主流程 + 工具入口是真正业务逻辑所在）」。真实收益不在行数，而在职责独立可测、可单独 import。**本条已按实际结果修正，不以未达成状态归档。**
- [x] **`subject_resolution` 相关测试 30 个全绿**（原 AC 写 29），拆分未改既有断言
- [x] **PreviewableAction 模板方法落地**：wishlist / collection_progress / collection_type 三业务已对齐，新增写业务只需声明一个子类
- [x] **全量测试 814 passed**（基线 668 + 契约 146，原 AC 写 585 已过期）
- [x] **`emit_pending_action_*` 直调的处置结论：保留并文档化，不以消除为目标**
  - 实测现状：**14 处调用点**、分布在 6 个文件：`subject_resolution.py`（7）、`previewable.py`（3）、`collection_type.py`（2）、`collection_progress.py`（1）、`wishlist.py`（1）。另有 import 与 docstring 提及不计入
  - 原因：优化项 2 最终选择「三层同步设计显性化文档」而非抽象类（要封住 emit + 流回调 + Redis 就必需动 `streaming.py`，**违反「不动 SSE 协议」约束**）。`pending_events.py` 三接口本身已是良好抽象，真正缺的是设计意图无人记录
  - 交付：`pending_action.py` / `pending_events.py` 顶部 docstring 写明 ContextVar → Redis → LangGraph state 三层时序
  - **本条已按实际决策修正：AC 从「不出现」改为「出现是已记录的决策，不得无说明新增」。**

### 简历一句话（最终交付）

> 把 564 行的 agent 历史包袱文件拆成主文件 403 行 + 3 个单一职责模块（归一化 / 候选匹配 / 权威校验），用三句话契约 docstring 替换口口相传；通过 PreviewableAction 模板方法模式把写操作工具数从 3N 收敛到 N，新增写业务只需声明一个子类；并落地 agent↔business 契约测试体系（146 个用例，25 个出站调用点全量校验），把跨层字段漂移从「线上发现」提前到「CI 拦截」。

> ⚠️ 降级说明：「主文件 < 100 行」当初的估计过于乐观（实际 403 行，且子任务已预先说明会导致此结果）；「彻底消除 `emit_pending_action_*` 直调」因与「不动 SSE 协议」约束冲突而改为文档化。两项均已在上面 AC 段落附原因，不以未达成状态归档。

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
