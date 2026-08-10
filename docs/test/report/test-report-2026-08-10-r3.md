# AnimeTracker 测试报告（第三轮 · 回归）

- 日期 / 执行人 / 分支 / commit：2026-08-10 / Hermes / main / **cd876f3**（fix: 统一收藏类型语义）
- 环境：本机 192.168.0.110，源码运行 local profile；MySQL 8.4.9 / Redis 8.8.0 / MinIO 就绪；服务 8080（business）、8090（agent，已重启加载新代码）、80（client）、81（admin）
- 执行范围：`docs/test/plan/test-plan-2026-08-10.md` v1.2 分层执行 L0 → L4
- 前置：agent 服务重启加载最新 collections.py；client/admin 前端重建 dist

## 一、总览

| 分层 | 用例数 | 通过 | 失败 | 通过率 |
|---|---|---|---|---|
| L0 Java 单测 | 33 | 33 | 0 | 100% |
| L1 Agent pytest | 100 | 100 | 0 | 100% |
| L2 前端 tsc+build | 4 | 4 | 0 | 100% |
| L3 API 冒烟 | 10 | 10 | 0 | 100% |
| L4 E2E 浏览器 | 6 | 6 | 0 | 100% |
| **合计** | **153** | **153** | **0** | **100%** |

## 二、回归项验证（前三轮缺陷）

| 项 | 验证方式 | 结果 |
|---|---|---|
| A3 登录防爆破（P1） | 错 6 次后第 7 次正确密码被拒，返回"登录失败次数过多" | ✅ |
| C2 重复收藏 409（P2） | 同 subject 同 type 二次提交返回 409 | ✅ |
| D8 agent /health（P2） | llm_configured=true，与真实能力一致 | ✅ |
| L0/L1 过时断言 | 33/33 + 100/100 全过 | ✅ |
| **#7 收藏类型语义（P1，cd876f3）** | 三方核对：数据库 type=3×4 ↔ 接口 `?type=3` 返回 4 条 ↔ client「在看」tab 4 条 ↔ admin 仪表盘「想看 1 在看 4」 | ✅ |

## 三、失败明细

无。

## 四、环境受限项

无。

## 五、风险遗留

- 全部 153 用例通过，无遗留缺陷。
- 收藏类型语义已四方统一（client/后端 Java/db-schema/admin/agent/openapi），前后端联调数据一致。
