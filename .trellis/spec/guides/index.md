# 跨层开发指南

本目录用于不属于单一前端或后端层的决策。实现前先读对应层的 `index.md`，再用这里的指南检查端到端一致性。

## 指南

| 主题 | 内容 |
|---|---|
| [跨层契约与代码复用](./cross-layer-thinking-guide.md) | 端到端契约、事实核对、复用所有者与重复检查 |
| [Agent 编排与运行](../backend/agent-guidelines.md) | 角色工具、Prompt 生效、日期与流式输出排障 |

## Trellis 发现边界

- 当前项目处于 single-repo 模式，实际 spec layer 只有 backend/frontend；packages 配置仍未启用。
- shared guides 不一定会被自动注入任务上下文；涉及跨层、数据库、OpenAPI、认证或文档事实时，必须手动先读本索引和 [跨层契约检查](./cross-layer-thinking-guide.md#跨层契约检查指南)。
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

## 合并后的写入路由

本索引是当前指南路径的事实来源。旧技能、历史任务或示例若要求读取/更新 `code-reuse-thinking-guide.md`，应定位到 [代码复用检查指南](./cross-layer-thinking-guide.md#代码复用检查指南) 并在该章节更新，不重新创建旧文件，也不复制出第二份规则。跨层契约继续在同文件的对应章节维护。

其他层同样按各自 index 的“合并前路径对照”解析旧路径；重新启用归档任务时同步其上下文清单。旧技能模板中的路径不代表对应文档仍应独立存在。

## 合并前路径对照

供历史任务和记录定位；归档引用保留原貌，重新启用旧任务时更新其上下文路径。

| 原文件 | 当前主题 |
|---|---|
| `code-reuse-thinking-guide.md` | [cross-layer-thinking-guide.md](./cross-layer-thinking-guide.md#代码复用检查指南) |
