# AnimeTracker 测试报告（第二轮 · 修复回归）

- 日期 / 执行人 / 分支 / commit：2026-08-10 / Hermes(hermes+codex) / main / **04ce534f**（fix: 修复 2026-08-10 测试报告缺陷）
- 环境：本机 192.168.0.110（Debian 13，3.8G RAM + 11G swap），源码运行 local profile；MySQL 8.4.9 / Redis 8.8.0 / MinIO 就绪；服务端口 8080（business）、8090（agent）、5173（client）、5174（admin）
- 执行范围：按 `docs/test/plan/test-plan-2026-08-10.md` v1.2 分层执行 L0 → L1 → L2 → L3 → L4
- 前置：测试期间已停用 animetracker-*.service 与 nginx，释放内存；swap 扩至 11G

## 一、总览

| 分层 | 用例数 | 通过 | 失败 | 通过率 |
|---|---|---|---|---|
| L0 Java 单测 | 33 | 33 | 0 | 100% |
| L1 Agent pytest | 100 | 100 | 0 | 100% |
| L2 前端 tsc+build | 4 | 4 | 0 | 100% |
| L3 API 冒烟 | 12 | 12 | 0 | 100% |
| L4 E2E 浏览器 | 6 | 6 | 0 | 100% |
| **合计** | 155 | 155 | 0 | **100%** |

## 二、关键链路结果

| 链路 | A 登录 | B 番剧 | C 收藏 | D Agent | E 管理端 |
|---|---|---|---|---|---|
| 结论 | ✅ | ✅ | ✅ | ✅ | ✅ |

- **A3 登录防爆破（P1，上次失败）**：连续 6 次错误密码均 401；第 7 次正确密码返回 `{"code":401,"message":"登录失败次数过多，请5分钟后再试"}` —— **已修复** ✅
- **C2 重复收藏 409（P2，上次失败）**：同 subject 同收藏类型二次提交返回 `{"code":409,"message":"该条目已收藏，请勿重复收藏"}` —— **已修复** ✅
- **D8 agent /health（P2，上次失败）**：`llm_configured:true`，与真实能力一致；管理端 Agent 配置页显示"Agent 服务在线（ok），LLM 已配置" —— **已修复** ✅
- L1 上次 3 条过时断言 → 本次 100 passed —— **已修复** ✅

## 三、失败明细

| 编号 | 分层 | 用例 | 期望 | 实际 | 严重度 |
|---|---|---|---|---|---|
| 6 | L0 | `AuthServiceImplTest.locksAccountAfterFiveFailedAttempts` | verify `incr(FAIL_KEY, 5L, MINUTES)` | 实际 `LOGIN_FAIL_WINDOW_MINUTES` 为 @Value 注入字段，单测未赋值=0，与 5L 不匹配 | P2（测试代码缺陷，产品代码正确） |

处理：codex（新窗口）诊断 → 应用 `ReflectionTestUtils.setField(service, "LOGIN_FAIL_WINDOW_MINUTES", 5L)` 补丁 → 回归 **33/33 全过**。产品代码未改动。

## 四、环境受限项

无。本机依赖（MySQL/Redis/MinIO）与 4 服务全部就绪；本轮无 SKIP/LIMITED。

## 五、风险遗留

- 全部 155 用例通过，无遗留缺陷。
- 上次报告的 P1 安全缺陷（登录防爆破）已由产品提交 04ce534f 修复并经 L3 实测确认。
