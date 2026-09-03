# 跨层开发指南

本目录用于不属于单一前端或后端层的决策。实现前先读对应层的 `index.md`，再用这里的指南检查端到端一致性。

## 指南

| 文档 | 适用场景 |
|---|---|
| [跨层契约检查](./cross-layer-thinking-guide.md) | API、认证、SSE、数据库字段或 Agent 写协议变化 |
| [代码复用检查](./code-reuse-thinking-guide.md) | 新增类型、常量、API、组件、Gateway 或转换逻辑 |

## Trellis 发现边界

- 当前项目处于 single-repo 模式，实际 spec layer 只有 backend/frontend；packages 配置仍未启用。
- shared guides 不一定会被自动注入任务上下文；涉及跨层、数据库、OpenAPI、认证或文档事实时，必须手动先读本索引和 [跨层契约检查](./cross-layer-thinking-guide.md)。
- 当前没有单独的 docs spec layer；README、OpenAPI、Schema 文档变更按跨层契约处理，并以源码、测试和配置事实为准。

## 开发前检查

1. 写出请求从 UI 到存储再返回 UI 的完整路径。
2. 标出每个边界的事实来源、验证位置和错误语义。
3. 搜索已有 API、类型、常量、Gateway、Converter 和组件。
4. 确认安全约束：认证、权限、待确认动作、敏感日志。
5. 列出每一层的验证命令和回滚点。

## 质量检查分层

| 层级 | 命令/检查 | 说明 |
|---|---|---|
| CI 强制 | 前端 `npm run typecheck`；Java `mvn -B test`；Python `uv run pytest` | 以 `.github/workflows/ci.yml` 当前实现为准 |
| 提交前 | 运行受影响 workspace 测试；跨层至少一条成功和一条权限/失败路径 | 普通代码或契约变更 |
| 交付前 | Java 配置/边界变更 `mvn -B clean test`；前端构建变更 `npm run build` | 交付产物、配置迁移或构建配置变更 |

- 契约：核对 `docs/spec/openapi.yaml`、Java/Python 实现和 shared 类型；OpenAPI 当前未被 CI 自动校验。
- 数据：核对 `docs/database/db-schema.sql` 与所有映射；非空库禁止直接执行初始化 Schema。
- 文档级校验：确认本目录链接、源码证据路径和命令仍存在；易腐的测试数量、路由数量和表数量必须附验证命令/核对日期。
