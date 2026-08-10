# AnimeTracker 测试报告

- 日期 / 执行人 / 分支 / commit：2026-08-10 / Codex / main / 25b4269
- 环境：源码方式运行 local profile；内存峰值未单独采集；MySQL 8、Redis、MinIO 就绪（经登录、验证码限流、会话等链路验证）；服务端口 8080（business）、8090（agent）、5173（client）、5174（admin）。
- 执行范围：按 `docs/test-plan.md` v1.2 顺序执行 L0 → L1 → L2 → L3 → L4；按执行约定只记录缺陷、不修改代码，未执行 git 提交。

## 一、总览

| 分层 | 用例数 | 通过 | 失败 | 跳过 | 通过率 |
|---|---|---|---|---|---|
| L0 Java 单测 | 30 | 27 | 3 | 0 | 90.0% |
| L1 Agent pytest | 100 | 97 | 3 | 0 | 97.0% |
| L2 前端 tsc+build | 2 | 2 | 0 | 0 | 100% |
| L3 API 冒烟 | 27 | 25 | 2 | 0 | 92.6% |
| L4 E2E 关键链路 | 18 | 17 | 1 | 0 | 94.4% |
| **合计** | 177 | 168 | 9 | 0 | 94.9% |

## 二、关键链路结果

| 链路 | A 登录 | B 番剧 | C 收藏 | D Agent SSE | E 管理端 |
|---|---|---|---|---|---|
| 结论 | ❌ | ✅ | ❌ | ✅ | ✅ |
| 失败步骤 | A3 | - | C2 | - | - |

- L0：`backend/business` 11 个测试类全部执行，`ImportServiceImplTest` 有 3 条过时单测失败。
- L1：`backend/agent` 20 个 pytest 文件 100 条用例全部收集，3 条过时断言失败。
- L2：client 与 admin 的 `tsc -b && vite build` 均通过，产物生成正常。
- L3：认证、列表、详情、季度/标签筛选、收藏、Agent SSE、管理端 API 按端点实际行为验证。
- L4：client 与 admin 前端关键页面已用浏览器实测，9 张关键页面截图已保存至 `C:\Users\zzz\.codex\visualizations\2026\08\10\019feac5-f212-7770-a481-0739ed879d03\`。

## 三、失败明细（P0 阻断 → P1 → P2）

| 编号 | 分层 | 链路 | 期望 | 实际 | 严重度 |
|---|---|---|---|---|---|
| 1 | L3 | A3 | 密码错误 5 次后第 6 次起锁定 | 连续 6 次错误密码均返回 401，随后使用正确密码仍登录成功并下发 JWT，无锁定逻辑 | P1 |
| 2 | L3 / L4 | C2 | 重复收藏返回 409 | 重复收藏返回 200 并执行 upsert；前端再次收藏同一状态仍提示“保存成功”，无 409 提示 | P2 |
| 3 | L0 | - | 30 条单测全过 | `ImportServiceImplTest` 3 条 mock URL 未同步带 `?mode=season&key=2026-summer&workers=3` 的实现改动 | P2 |
| 4 | L1 | - | 100 条 pytest 全过 | 3 条过时断言：模型槽位期望 `ChatTongyi`、`model_kwargs["temperature"]` KeyError、flusher 返回签名不匹配 | P2 |
| 5 | L3 | D8 | health 降级状态与真实能力一致 | `/health` 返回 `llm_configured:false`，但真实对话与工具调用可用（模型走 opencode.ai deepseek），Agent 配置页同样显示“LLM 未配置” | P2 |

复现说明：

1. A3：对 `POST /api/client/auth/login` 连续发送 6 次错误密码，均为 401；第 7 次使用正确密码返回 200 且 `data.token` 非空。
2. C2：对同一 `subjectId` 相同收藏状态连续提交两次，第一次 200，第二次仍 200；按计划应返回 409。
3. L0：重跑 `mvn test` 后 `ImportServiceImplTest` 固定失败，失败断言均为 mock 的导入 URL 缺少 query 参数。
4. L1：重跑 pytest 后 3 条失败均为对旧实现的期望，不涉及真实 LLM 网络调用。
5. D8：`GET /api/client/agent/health` 返回 `llm_configured:false`，但实际 Agent 能完成“搜索 SpongeBob anime”并调用收藏工具，配置状态与能力不一致。

## 四、环境受限项（跳过原因）

| 项 | 原因 | 能否补测 |
|---|---|---|
| E3 新番剧出现在用户端 | `since=2026-08-10` 导入任务 `import_record id=37` 执行成功但 `subjectCount=0`，当日无增量数据 | 可补测：有增量数据或改用更早 `since` 后重测 |
| D2 事件类型 | 实际 SSE 事件为 `thinking` / `function_call(start/end)` / `answer`，计划写的是 `tool_status`；前端 `Agent.tsx` 已消费 `function_call` | 可补测：按代码实际事件名更新计划措辞 |
| D8 降级场景 | 环境实际可调用真实 LLM，无法复现“无 DASHSCOPE key”的降级路径；health 状态与能力不一致已记入缺陷 | 可补测：切换空 key 环境后验证兜底 |
| D7 日志无堆栈 | SSE 中断后 8090 `/health` 正常且端口仍监听，但测试机日志文件未定位，未能核实“日志无堆栈” | 可补测：定位 agent 日志后复测中断场景 |

## 五、风险遗留

- A3 登录防爆破未实现，属安全链路 P1 缺陷，当前版本存在账号口令被持续尝试的风险。
- C2 重复收藏为 upsert 语义，接口行为与计划不一致，前端无法向用户反馈重复状态。
- 6 条过时单测（L0 3 条、L1 3 条）削弱回归保护，建议随实现同步更新。
- Agent `/health` 与配置页的 `llm_configured` 状态与真实可用性不一致，可能误导运维判断。
- 前端当前无组件/单元测试，本次按计划仅覆盖 tsc、构建与浏览器关键链路。

## 六、上线建议（P0 清零前不建议发布）

- 未发现 P0；但 A3 为 P1 安全缺陷，建议在修复并复测通过前不要发布。
- 建议优先修复 A3 登录锁定，再按计划补上 C2 的 409 语义，并同步更新 L0/L1 过时断言。
- 修复后重跑 L3 的 A/C 链路与 L4 对应页面，确认锁定、409、Agent health 状态一致后再进入发布评审。
- 本次未修改代码、未提交 git，报告与证据留待人工 review。
