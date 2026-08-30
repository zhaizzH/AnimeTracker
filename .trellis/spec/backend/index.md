# 后端开发规范

适用范围：`backend/business`（Java 21 / Spring Boot 3.2）与 `backend/agent`（Python 3.10+ / FastAPI / LangGraph）。本目录记录当前仓库已经采用的边界和约定，不是通用框架教程。

## 开发前检查

1. 判断改动属于 Business API、Agent 在线服务、离线任务，还是跨层契约。
2. 先读对应主题文件，再读其中列出的源码证据；不要只依赖 README。
3. 涉及接口字段或路径时，同时核对 `docs/spec/openapi.yaml`、Spring Controller、Python Router 与 `frontend/packages/shared/src`。
4. 涉及持久化时先核对 `docs/database/db-schema.sql`；项目没有 Flyway/Liquibase。
5. 涉及 Agent 写操作时，必须保留“预览 → 用户确认 → 执行”协议。

## 规范索引

| 主题 | 内容 |
|---|---|
| [目录与依赖边界](./directory-structure.md) | Java 六模块、Python 端口与适配器、代码放置规则 |
| [Agent 编排与流式协议](./agent-guidelines.md) | LangGraph、SSE、工具权限、待确认动作 |
| [数据与存储](./database-guidelines.md) | MySQL、MyBatis、SQLAlchemy、Redis、MinIO |
| [错误处理](./error-handling.md) | Java 统一响应、Python API/工具错误语义 |
| [日志与可观测性](./logging-guidelines.md) | `X-Request-ID`、结构化事件、隐私红线 |
| [质量门禁](./quality-guidelines.md) | 校验命令、测试现状、审查清单 |

## 不可破坏的系统约束

- 浏览器只访问 `/api/**`；Spring Business 代理 Agent，前端不直连 `:8090`。
- Access Token 只保存在前端内存；刷新凭据只使用 `at_refresh` HttpOnly Cookie。
- Business 与 Agent 使用同一 JWT 密钥；Agent 在本地验签，避免回调代理环路。
- Java API 成功/失败统一为 `{code, message, data}`；SSE 除外。
- 写工具不能接受模型自行构造的确认参数，必须使用系统注入的待确认状态。

## 质量检查

```bash
cd backend/business && mvn -B test
cd ../../backend/agent && uv run pytest
```

当前仓库 Java 尚无实际测试类；Python 当前仅有导入指标测试。测试命令通过不等于业务覆盖充分，新功能应补最小回归用例。
