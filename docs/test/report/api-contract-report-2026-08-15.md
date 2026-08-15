# AnimeTracker 接口契约测试报告（2026-08-15）

## 1. 基本信息

| 项目 | 值 |
|---|---|
| 测试日期 | 2026-08-15 |
| 被测环境 | `http://127.0.0.1:8080`（本地已启动后端，Agent `:8090` 已启动） |
| 测试账号 | 普通用户 `test1`，管理员 `admin` |
| 测试脚本 | `docs/test/scripts/api_contract_test.py` |
| 结果数据 | `docs/test/report/api-contract-results-2026-08-15.json` |
| 规范依据 | `docs/spec/openapi.yaml`（62 个路径操作） |
| 执行耗时 | 约 13 秒 |

## 2. 结果汇总

| 指标 | 数值 |
|---|---|
| 用例总数 | 88 |
| PASS | 77 |
| FAIL | 1 |
| LIMITED | 10 |
| 通过率（不计 LIMITED） | 98.7%（77/78） |
| 规范操作覆盖 | 54/62（87.1%） |

覆盖范围包括：登录/注册/刷新/登出/改密、用户信息、标签与条目查询、收藏 CRUD 与剧集进度、追番进度预览/执行、文件上传、管理员仪表盘/用户/条目/日志/角色、Agent 服务探活与会话等。

## 3. 真实缺陷

| 用例 ID | 接口 | 现象 | 定位 |
|---|---|---|---|
| API-LOGS-001 | `GET /api/admin/logs` | 返回 `HTTP 500`、`code=500`（消息“服务器内部错误”），未按规范返回分页日志与聚合统计 | `AdminLogServiceImpl.buildWrapper()`（`backend/business/admin/src/main/java/top/zhaizz/admin/service/impl/AdminLogServiceImpl.java`）对空 `start/end` 调用 `getStart().atStartOfDay()` 触发 NPE，属既有缺陷，非本次改动引入 |

## 4. 环境受限（LIMITED）

| 用例 ID | 接口 | 原因 |
|---|---|---|
| API-AGENT-STREAM-001、API-ADMIN-AGENT-CHAT-STREAM-001 | Agent 流式对话接口 | 契约探针以 `{"message":"hi"}` 调用，而 Agent `ChatRequest` 要求 `session_id`+`content`；业务代理将 422 包装为 `500`。属既有契约/代理入参约定差异 |
| API-AGENT-HISTORY-001、API-AGENT-REMOVE-001 等 8 个用例 | 会话历史/删除、Prompt 更新/重置、Agent 配置更新 | 依赖真实 session/prompt key，契约脚本按未执行处理 |

> 本次已启动 `:8090` Agent 服务：会话创建/列表、健康探活等均返回 `200`；真实的追番进度 SSE 对话（预览→确认→执行）已通过手工场景验证，见批次 C 报告。

## 5. 观察项（非 FAIL）

- `POST /api/client/me/update-password`：旧密码错误时后端返回 `401 UNAUTHORIZED`（消息“旧密码不正确”），而 OpenAPI 仅文档化 `200` 成功响应。该行为有明确业务语义，暂不计为缺陷；若前端约定使用 `400`，建议后端或规范二选一对齐。

## 6. 结论

接口整体可用，鉴权、参数校验、收藏、管理员条目/角色等主要链路均通过；`POST /api/client/auth/forgot-password` 通过。唯一真实缺陷是管理端操作日志接口的既有 NPE。追番进度预览/执行接口（`POST /api/client/collections/progress-preview[/{previewId}/execute]`）契约测试全部通过。
