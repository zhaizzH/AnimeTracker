# 0011 — Evidence 是最终权威边界，部分失败也整批 fail-closed

- **状态**：accepted
- **记录日期**：2026-10-12
- **相关规范**：`app/rag/authority.py`、`app/rag/retrieval.py`、[backend/rag-retrieval-contract.md](../backend/rag-retrieval-contract.md)

## 背景

检索出的候选在送入模型前，会附上经 Business 权威回查 + Evidence API 校验的事实（Evidence）。这些事实直接进入模型上下文，模型据此作答。

回查可能部分成功：一部分候选拿到了 Evidence，另一部分超时或返回非法值。

## 决策

Evidence 是数据进入 Agent 上下文前的**最终权威边界**。一旦出现超时、错误、缺项，或命中非法 / inactive / NSFW / 重复 subjectId，**整批 fail-closed**：返回 `available=false` + 空候选，**绝不静默降级**取部分结果。代码注释明确「部分失败或整体失败的响应绝不能静默回退」。

## 备选方案

1. **降级：能拿到的先用，拿不到的丢弃。** 未采纳——模型拿到的是「不完整但看起来正常」的候选集，会给出以偏概全的推荐，且用户与开发者都无从察觉。
2. **整批 fail-closed（采纳）。** 宁可这一轮不检索，也不让半真半假的事实进入模型。

## 后果

**正面**

- 模型上下文里不存在「部分失效的权威事实」这一状态；要么是完整校验过的集合，要么没有。
- 故障可观测：整体 `available=false` 是显式信号，不是静默的候选缺失。

**代价**

- 一次上游抖动会损失整轮检索（换取正确性）。
- 与其它路径的失败取向**刻意不一致**：Redis 故障时检索对 Business 搜索**fail-open**（降级到既有搜索），而 Evidence 故障则 fail-closed。这个不对称是有意的——保护的是「模型上下文的正确性」，而非「检索的可用性」。

**约束**

- 不得在 Evidence 路径引入「部分结果也返回」的捷径；不得把 fail-open 的可用性策略套用到 Evidence 上。
