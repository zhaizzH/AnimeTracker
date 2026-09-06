# Phase 8 Golden Case 定义集报告

日期：2026-09-06

## 本轮完成

- 使用只读 MySQL 查询重新生成 `backend/agent/tests/evals/golden_cases.json`。
- 当前数据集恰好 120 条：标题/别名 30、结构化过滤 35、主观语义 10、人物/角色/声优 25、系列关系 5、否定 10、降级 5。
- 每条 case 都绑定同一个 MySQL 快照、`indexVersion=v1`、`profileVersion=subject-profile-v1`，并包含唯一 `evidenceId`、SQL 模板 ID、参数、来源表、结果数量和结果 ID hash。
- 新增 `tests.evals.generate_golden_cases` 生成器；如果真实快照不能生成恰好 120 条，会拒绝写入不完整数据集。
- `load_golden_dataset()` 和评测测试现在会校验生产数据集的 120 条数量、快照一致性、版本一致性和 evidence 唯一性。

生成命令：

```powershell
cd backend/agent
\.venv\Scripts\python.exe -m tests.evals.generate_golden_cases `
  --output tests/evals/golden_cases.json
```

本次快照：`mysql-cb7f432eadfa885d`，抓取时间：`2026-09-06T06:51:35Z`，schema signature：
`f0db3fd691cacdb0a14cbad1e5fcb01131065f0320dce89e0d033bef46add4f3`。

## 仍未完成

- 这是“真实事实快照定义集”，不是 120-case 真实检索通过报告。
- 当前 `search_index_release` 没有 ACTIVE 版本，因此 Business lexical、同版本 VSIM、Evidence 回查和真实 Recall/MRR/nDCG 仍不能作为发布评测运行；Evidence batch 单独接口已通过 200 smoke。
- 本轮没有激活 release、修改数据库或写入 Redis；Phase 8 第一项仍需在 release 可用后完成五份同版本 gate 报告和至少 20 条人工证据检查。

## Shadow 回放补充（2026-09-06）

- 已使用未发布的 `v1/subject-profile-v1` 候选索引完成 120 条只读 shadow 回放，结果为 `115` 通过、`5` 失败。
- 指标为 Recall@20=`0.9847`、MRR@10=`0.8803`、nDCG@10=`0.8716`、hard-filter accuracy=`0.9667`、Evidence completeness=`1.0`。
- 输出 [research/eval-shadow-v1.json](./research/eval-shadow-v1.json) 明确标记 `status=SHADOW_ONLY`；没有 ACTIVE release，且 gate 不接受该状态，因此这不是正式评测通过报告。
