# 跨层开发指南

本目录用于不属于单一前端或后端层的决策。实现前先读对应层的 `index.md`，再用这里的指南检查端到端一致性。

## 指南

| 文档 | 适用场景 |
|---|---|
| [跨层契约检查](./cross-layer-thinking-guide.md) | API、认证、SSE、数据库字段或 Agent 写协议变化 |
| [代码复用检查](./code-reuse-thinking-guide.md) | 新增类型、常量、API、组件、Gateway 或转换逻辑 |

## 开发前检查

1. 写出请求从 UI 到存储再返回 UI 的完整路径。
2. 标出每个边界的事实来源、验证位置和错误语义。
3. 搜索已有 API、类型、常量、Gateway、Converter 和组件。
4. 确认安全约束：认证、权限、待确认动作、敏感日志。
5. 列出每一层的验证命令和回滚点。

## 质量检查

- 前端：`cd frontend && npm run typecheck && npm test`
- Java：`cd backend/business && mvn -B test`
- Python：`cd backend/agent && uv run pytest`
- 契约：核对 `docs/spec/openapi.yaml` 与三端实现
- 数据：核对 `docs/database/db-schema.sql` 与所有映射
