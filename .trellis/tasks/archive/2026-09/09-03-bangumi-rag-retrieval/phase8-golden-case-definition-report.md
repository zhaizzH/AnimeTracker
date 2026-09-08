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

- 这是“真实事实快照定义集”，仍保持 `DEFINITION_ONLY`；120-case 真实检索通过报告单独记录在 `research/eval-v1.json`。
- 当前 v1 `search_index_release` 已为 ACTIVE，线上 Business lexical 实测返回 HTTP 200。正式发布评测不应等待 ACTIVE：它已先对未激活的同版本 candidate 运行并输出 `status=RELEASE_CANDIDATE`；五份报告通过 gate 后才执行激活。
- 2026-09-07 回放达到 120/120；capacity/latency/human 报告已补齐并通过 gate（human 为 20 条、严重错误 0），随后完成 v1 release 激活。本轮未修改索引内容或 Redis Vector Set。

## Shadow 回放补充（2026-09-06）

- 已使用未发布的 `v1/subject-profile-v1` 候选索引完成 120 条只读 shadow 回放，结果为 `120` 通过、`0` 失败；正式 candidate 报告同步记录相同指标。
- 指标为 Recall@20=`0.9847`、MRR@10=`0.8803`、nDCG@10=`0.8716`、hard-filter accuracy=`0.9667`、Evidence completeness=`1.0`。
- 输出 [research/eval-shadow-v1.json](./research/eval-shadow-v1.json) 明确标记 `status=SHADOW_ONLY`；gate 要求激活前提供 `RELEASE_CANDIDATE`，因此这不是正式评测通过报告。
