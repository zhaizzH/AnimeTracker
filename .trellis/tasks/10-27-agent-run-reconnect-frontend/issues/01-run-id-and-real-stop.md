# 01: 记录 run_id 并让「停止」真的停

**What to build:** 用户点停止时，后端 run 真的被标记取消，而不是被当成掉线继续烧 token。前端从首帧 `meta.run_id` 拿到当前 run 的身份，一直持有到该 run 结束；期间点停止会先通知后端停 run，再断开本地连接。

**Blocked by:** None (can start immediately)

**Status:** ready-for-agent

- [ ] 首帧 payload 里的 `meta.run_id` 被记录；run 结束（正常结束、出错、用户 abort 三条路）后清空
- [ ] 有测试分别在「首帧到达后」与「run 结束后」断言 `run_id` 的有无
- [ ] 点停止时调用顺序为「先停 run，再 abort 本地连接」，用调用序列数组断言
- [ ] 首帧之前点停止只 abort，不调用停 run（此时后端还没有 run 可停）
- [ ] 停 run 抛错时仍然 abort，用户不会被卡在「停止中」；错误可诊断但不弹阻塞提示
- [ ] 既有 SSE 行为不回归：事件白名单、`is_end` 锁、401/403 文案、主动 abort 不写中断文案
