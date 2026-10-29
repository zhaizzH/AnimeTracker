# Journal - zhaizzH (Part 2)

> Continuation from `journal-1.md` (archived at ~1200 lines)
> Started: 2026-10-29

---



## Session 41: retro 收口：删手抄基线、审查证据要求、变异还原核对、journal 降阈值
<!-- trellis-session: v=2 fp=cad523bf8cd8bf7f -->

**Date**: 2026-10-29
**Task**: retro 收口：删手抄基线、审查证据要求、变异还原核对、journal 降阈值
**Branch**: `main`

### Summary

本轮 retro 四条全部落地。最重的一条是自己立的规矩没执行：本会话早先刚写下「环境事实不入 spec」并清掉了后端 quality-guidelines 的数字，前端同类文件却没动——它是全仓最后一个手抄测试数量的地方，本会话改过 5 次、审查抓到 3 次（202 vs 205、32 vs 33 文件、文件清单漏掉新增的 auth/stream.test.ts）。现在删掉数字与文件枚举，只留口径与现场命令。第二条：审查结论必须带 file:line 或测试名，无证据的结论按假设处理、先对源码核实——本会话曾被一条无证据的运行时断言带偏，写进归档附注后才发现与源码相反。第三条：变异验证结束必须核对 git diff --stat 与预期文件集，漏还原与套件全绿看起来一模一样。第四条：max_journal_lines 从 2000 降到 1200，本会话已 1263 行。

### Main Changes

- .trellis/spec/frontend/quality-guidelines.md：删「共 N 个文件 + 逐个文件名 + 用例数」，改为口径 + 现场命令 + 「新增测试文件无需回来改本文档」
- .trellis/workflow.md：Review evidence（结论必须带证据）与 Mutation checks（变异轮结束核对 diff）两条
- .trellis/config.yaml：max_journal_lines 2000 → 1200

### Git Commits

| Hash | Message |
|------|---------|
| `3e8ff339` | chore(spec): 删前端手抄测试基线，补审查证据与变异还原两条硬要求 |

### Testing

- [OK] 未跑测试：仅改文档与配置；spec 链接与锚点检查通过

### Status

[OK] **Completed**

### Next Steps

- 下一次 add_session 应自动开 journal-2.md（当前 1263 行 > 新阈值 1200）
