# AnimeTracker 测试报告（第四轮 · 全量）

- 日期 / 执行人 / 分支 / commit：2026-08-10 / Hermes / main / **9749df0**（docs: 第三轮回归报告）
- 环境：本机 192.168.0.110（**注：IP 已漂移至 192.168.0.3**），源码运行 local profile；MySQL 8.4.9 / Redis 8.8.0 / MinIO 就绪；服务 8080（business）、8090（agent）、80（client）、81（admin）
- 执行范围：按**新计划** `docs/test/plan/test-plan-2026-08-10-r2.md`（v2.0 全量）执行 L0 → L4
- 前置：每次测试必写新计划；L4 浏览器实测强制

## 一、总览

| 分层 | 用例数 | 通过 | 失败 | 通过率 |
|---|---|---|---|---|
| L0 Java 单测 | 33 | 33 | 0 | 100% |
| L1 Agent pytest | 100 | 100 | 0 | 100% |
| L2 前端 tsc+build | 4 | 4 | 0 | 100% |
| L3 API 冒烟 | 10 | 10 | 0 | 100% |
| L4 E2E 浏览器（强制） | 6 | 6 | 0 | 100% |
| **合计** | **153** | **153** | **0** | **100%** |

## 二、本轮发现并修复

| 编号 | 层 | 问题 | 根因 | 处理 |
|---|---|---|---|---|
| 8 | L0 | `DashboardMapperTest` 连 MySQL 失败（Communications link failure） | 本机 IP 已从 192.168.0.110 漂移至 192.168.0.3，源码 `application-local.yml` 3 处 host 仍是旧 IP | 已改 `127.0.0.1`（MySQL/Redis/MinIO），重跑通过 |
| 9 | L4 | admin 仪表盘全部显示 0 | agent `.env` 中 REDIS_URL/DB_HOST/MINIO_ENDPOINT 仍指向旧 IP 192.168.0.110 → agent 连 MySQL 失败 → business 转发 `/api/admin/import/status` 500 → 前端 Promise.all 整体失败 | 已改 `.env` 3 处为 `127.0.0.1`，重启 agent，仪表盘恢复（用户 3 / 番剧 10,614 / 想看 1 在看 4） |

性质：均为**环境配置漂移**（非代码缺陷）；`application-local.yml` 已入库修复，`agent/.env` 未入库（本地配置）。

## 三、回归验证（前三轮缺陷全过）

| 项 | 结果 |
|---|---|
| A3 登录防爆破 | ✅ 错 6 次后第 7 次正确密码被拒 |
| C2 重复收藏 409 | ✅ 200 → 409 |
| D8 agent /health | ✅ llm_configured=true |
| #7 收藏类型语义 | ✅ 页面「在看」4 条 = 接口 type=3 = 库 type=3；admin「想看 1 在看 4」 |

## 四、环境受限项

- 本机 IP 漂移（192.168.0.110 → 192.168.0.3）：旧 IP 已被 DHCP 回收，外部访问用新 IP；所有配置已指向 127.0.0.1，不受影响。

## 五、风险遗留

- 全部 153 用例通过，无遗留代码缺陷。
- 建议：配置中避免硬编码局域网 IP，统一用 127.0.0.1/localhost（已全部改完）。
