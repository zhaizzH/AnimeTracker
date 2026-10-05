# 后端开发规范

适用范围：`backend/business`（Java 21 / Spring Boot 3.2）与 `backend/agent`（Python 3.10+ / FastAPI / LangGraph）。本目录记录当前仓库已经采用的边界和约定；各主题章节同时记录设计约束与当前实现状态，实现状态以当前代码、测试和任务记录为准。

## 开发前检查

1. 判断改动属于 Business API、Agent 在线服务、离线任务，还是跨层契约。
2. 先读对应主题文件，再读其中列出的源码证据；不要只依赖 README。
3. 涉及接口字段或路径时，同时核对 `docs/spec/openapi.yaml`、Spring Controller、Python Router 与 `frontend/packages/shared/src`。
4. 涉及持久化时先核对 `docs/database/db-schema.sql`；项目没有 Flyway/Liquibase。
5. 涉及 Agent 写操作时，必须保留“预览 → 用户确认 → 执行”协议。

## 规范索引

| 主题 | 内容 |
|---|---|
| [架构与模块边界](./directory-structure.md) | 目标九模块、现有实现对照、Auth/Infrastructure/Java Agent 设计、app/rag 拆分（ADR 0001）、pojo/Converter 与迁移验收 |
| [Agent 编排与运行](./agent-guidelines.md) | 角色工具、Prompt、运行契约、SSE 与编排 |
| [数据与存储](./database-guidelines.md) | MySQL、MyBatis、SQLAlchemy、Redis、Schema 与存储约束 |
| [RAG 检索与版本发布](./rag-retrieval-contract.md) | 检索、发布 gate、灰度、回滚与 Evidence 边界 |
| [错误、日志与可观测性](./error-handling.md) | 异常适配、统一响应、操作日志模块、追踪与隐私 |
| [质量与 Javadoc](./quality-guidelines.md) | 测试门禁、审查、Java 声明全覆盖、注释篇幅与 pojo 字段契约、AST/doclint 检查 |

## 不可破坏的系统约束

- 浏览器只访问 `/api/**`；Spring Business 代理 Agent，前端不直连 `:8090`。
- Access Token 只保存在前端内存；刷新凭据只使用 `at_refresh` HttpOnly Cookie。
- Business 与 Agent 使用同一 JWT 密钥；Agent 在本地验签，避免回调代理环路。
- Java API 成功/失败统一为 `{code, message, data}`；SSE 除外。
- 写工具不能接受模型自行构造的确认参数，必须使用系统注入的待确认状态。

## 质量检查

```bash
cd backend/business
mvn -B test
# 配置迁移或边界变更的交付前验证
mvn -B clean test

cd ../agent
uv run pytest
```

CI 当前执行 Java `mvn -B test`、Python `uv run pytest` 和前端 typecheck；`clean test` 与前端 build 属于相应变更的提交前/交付前验证。Python 已包含 importer/indexer/backfill/scheduler、RAG、适配器、eval 和 Agent Prompt 测试。详见 [质量门禁](./quality-guidelines.md#后端质量门禁)；不得沿用历史通过数。

### 2026-10-05 Backend 复核基线

- Business reactor 当前包含 `common`、`pojo`、`infrastructure`、`auth`、`log`、`agent`、`client`、`admin`、`app` 九个 Maven 模块；模块上限和实际职责以 [目录与依赖边界](./directory-structure.md) 及 `ArchitectureBoundaryTest` 为准
- `mvn -B test -f backend/business/pom.xml`：全 reactor 合计 220 个测试通过，0 失败，0 错误（Lombok 移除后各模块测试全部计入；2026-09-21 的 95 为历史基线）
- `uv run pytest`（`backend/agent`）：629 passed, 6 xfailed；2026-09-29 的 585 passed、2026-09-21 的 413 passed 为历史基线
- `check_javadoc.py` 自动化检查器已随提交 `721d5c71`（2026-10-04）删除；Javadoc 规范仍有效，恢复前以人工审查为准，详见 [质量门禁](./quality-guidelines.md#声明与语法检查自动化检查器已退役)
- `app/rag` 已于 2026-10-05 按管线阶段拆分（提交 `08799fdb`），详见 [app/rag 模块结构（ADR 0001）](./directory-structure.md#apprag-模块结构adr-00012026-10-05提交-08799fdb)

## 合并前路径对照

供历史任务和记录定位；归档引用保留原貌，重新启用旧任务时更新其上下文路径。

| 原文件 | 当前主题 |
|---|---|
| `auth-module-design.md` | [directory-structure.md](./directory-structure.md#business-auth-模块目标设计) |
| `infrastructure-module-design.md` | [directory-structure.md](./directory-structure.md#business-infrastructure-模块目标设计) |
| `business-agent-module-design.md` | [directory-structure.md](./directory-structure.md#business-java-agent-模块目标设计) |
| `agent-runtime-contract.md` | [agent-guidelines.md](./agent-guidelines.md#agent-角色提示词与流式输出契约) |
| `logging-guidelines.md` | [error-handling.md](./error-handling.md#日志与可观测性规范) |
| `java-javadoc-guidelines.md` | [quality-guidelines.md](./quality-guidelines.md#java-后端-javadoc-规范) |
