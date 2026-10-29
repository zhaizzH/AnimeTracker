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


## Session 42: SSE 刷新成功但重放仍 401：置为未认证交 guard 跳登录页
<!-- trellis-session: v=2 fp=5e340c88b707976c -->

**Date**: 2026-10-29
**Task**: SSE 刷新成功但重放仍 401：置为未认证交 guard 跳登录页
**Branch**: `main`

### Summary

收口 SSE 401 闭环的最后一环。此前只有「刷新失败」会置未认证；「刷新成功换到新令牌、重放仍被拒」这条路谁也没置位，store 停在 authenticated + 死令牌，用户对着必然失败的操作反复重试。改为在 streamSseWithAuth 的 retry catch 里，仅在重放也是 401 时调 setUnauthenticated()，由既有 guard 跳登录页。刻意不广播 signed-out——那个事件语义是用户主动登出，令牌失效与网络抖动只影响当前标签，广播会让别的标签在用户操作中被一起踢走；这条口径写进了 hook-guidelines。审查补了两条变异缺口：重放 502 不得登出、刷新失败不得额外踢人，并把重复的「重放仍 401」用例合并。另注意：工作树里 .trellis/spec/GLOSSARY.md 有 8 行非本会话的改动（ExternalSource/ExternalReference，19:51 写入），未纳入本次提交。

### Main Changes

- shared/auth/stream.ts：retry catch 内仅对 401 调 setUnauthenticated()
- shared/auth/stream.test.ts：合并重复用例，补「重放 502」与「刷新失败不踢人」两条断言
- .trellis/spec/frontend/hook-guidelines.md：重放仍 401 → 置未认证；signed-out 广播只用于主动登出

### Git Commits

| Hash | Message |
|------|---------|
| `58a03cec` | fix(shared): 刷新成功但重放仍 401 时置为未认证 |

### Testing

- [OK] frontend: shared 88 / client 49 / admin 81 全绿；typecheck 零错误
- [OK] 变异：删置位、放宽为任何错误都置位、刷新失败也置位，三条均转红

### Status

[OK] **Completed**

### Next Steps

- GLOSSARY.md 的 ExternalSource/ExternalReference 改动来源未知，待确认是否由其它会话写入
