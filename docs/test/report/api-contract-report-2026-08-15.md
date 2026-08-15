# AnimeTracker 接口契约测试报告（2026-08-15）

## 1. 基本信息

| 项目 | 值 |
|---|---|
| 测试日期 | 2026-08-15 |
| 被测环境 | `http://127.0.0.1:8080`（本地已启动后端） |
| 测试账号 | 普通用户 `test1`，管理员 `admin` |
| 测试脚本 | `docs/test/scripts/api_contract_test.py` |
| 结果数据 | `docs/test/report/api-contract-results-2026-08-15.json` |
| 规范依据 | `docs/spec/openapi.yaml`（60 个路径操作） |
| 执行耗时 | 约 15 秒 |

## 2. 结果汇总

| 指标 | 数值 |
|---|---|
| 用例总数 | 85 |
| PASS | 70 |
| FAIL | 1 |
| LIMITED | 14 |
| 通过率（不计 LIMITED） | 98.6%（70/71） |
| 规范操作覆盖 | 52/60（86.7%） |

覆盖范围包括：登录/注册/刷新/登出/改密、用户信息、标签与条目查询、收藏 CRUD、文件上传、管理员仪表盘/用户/条目/日志/角色、Agent 服务探活等。

## 3. 真实缺陷

| 用例 ID | 接口 | 现象 | 定位 |
|---|---|---|---|
| API-LOGS-001 | `GET /api/admin/logs` | 返回 `HTTP 200`、`code=200`，但响应缺少 `data`，未按规范返回分页日志与聚合统计 | `AdminLogServiceImpl.listLogs()` 目前直接 `return null`，属于未实现的服务桩，见 `backend/business/admin/src/main/java/top/zhaizz/admin/service/impl/AdminLogServiceImpl.java` |

## 4. 环境受限（LIMITED）

| 用例 ID | 接口 | 原因 |
|---|---|---|
| API-AGENT-SESSIONS-001 等 6 个探针 | Agent 会话/流式接口 | Python Agent 服务 `:8090` 未启动，业务网关返回包装后的 `500`；`GET /api/client/agent/health` 本身返回 `200` 且 `data.status=ok` |
| API-AGENT-HISTORY-001 等 8 个用例 | 会话历史/删除、Prompt 更新/重置、Agent 配置更新 | 依赖正在运行的 Agent 服务及真实 session/prompt key，未执行 |

## 5. 观察项（非 FAIL）

- `POST /api/client/me/update-password`：旧密码错误时后端返回 `401 UNAUTHORIZED`（消息“旧密码不正确”），而 OpenAPI 仅文档化 `200` 成功响应。该行为有明确业务语义，暂不计为缺陷；若前端约定使用 `400`，建议后端或规范二选一对齐。

## 6. 结论

接口整体可用，鉴权、参数校验、收藏、管理员条目/角色等主要链路均通过；`POST /api/client/auth/forgot-password` 本次重跑也通过。唯一真实缺陷是管理端操作日志接口未实现。Agent 相关接口需启动 `:8090` Agent 服务后补测。
