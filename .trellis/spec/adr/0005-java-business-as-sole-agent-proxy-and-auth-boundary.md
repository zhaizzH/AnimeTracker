# 0005 — Java business 是 Python Agent 之前唯一的代理与认证边界

- **状态**：accepted
- **记录日期**：2026-10-12
- **相关规范**：`backend/business/` README、[backend/agent-guidelines.md](../backend/agent-guidelines.md)

## 背景

系统有两个后端：Java `business`（Spring Boot，业务与认证）与 Python `agent`（FastAPI + LangGraph，LLM 推理）。浏览器需要流式对话能力，而 Agent 监听在独立端口 `:8090`。

最直接的做法是让浏览器直接连 `:8090`。

## 决策

浏览器**只访问 `/api/**`**，一律经 Nginx → Java business `:8080`。Java 代理 Agent 的流式接口（以不设读超时的 RestTemplate 原样转发 SSE），并在这一层完成认证与权限。前端**不直连** `:8090`；Agent 也不直接暴露给公网。

## 备选方案

1. **浏览器直连 FastAPI `:8090`。** 未采纳——那会把认证、CORS、限流、审计拆成两套并各自漂移；Agent 将暴露为第二个公网入口，权限模型不再单一。
2. **Java 作为唯一入口与认证/代理边界（采纳）。** 换取「一个入口、一套认证」的结构，代价是多一跳与跨语言排障。

## 后果

**正面**

- 单一入口、单一认证与权限模型；CORS 与限流只需要在一处配置。
- Agent 可以被部署在只允许 Java 访问的内网位置。
- 审计与追踪在入口处统一。

**代价**

- 一次 Agent 对话的数据要在 前端 → Java → Python → Java → Python → Java → 前端 之间折返，延迟与排障成本明显上升。
- SSE 转发必须保持流式（不能缓冲成普通 JSON），且代理侧不能用普通读超时掐断长流。

**约束**

- 新增 Agent 能力时必须同时经 Java 代理暴露，不得为省事给 `:8090` 开公网通道。
- 前端代码中不得出现对 `:8090` 的直连。
