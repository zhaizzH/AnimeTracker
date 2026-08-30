# 后端目录与依赖边界

## 总体结构

```text
backend/
├── business/                 # Spring Boot 业务与鉴权，:8080
│   ├── pojo/                 # Entity / DTO / VO
│   ├── common/               # 跨模块平台能力
│   ├── client/               # 用户端 Controller / Service / Mapper / Store / Gateway
│   ├── admin/                # 管理端 Controller / Service / Mapper / Gateway
│   ├── agent/                # Python Agent 的 HTTP 代理
│   └── app/                  # 启动组合根与基础设施适配器
└── agent/                    # FastAPI + LangGraph，:8090
    ├── app/api/              # HTTP/SSE 边界
    ├── app/agent|chat|rag/   # 用例、状态、端口与领域逻辑
    ├── app/adapters/         # HTTP、Redis、MySQL、LLM、提示词、子进程实现
    └── jobs/                 # importer / indexer / scheduler
```

证据：`backend/business/pom.xml`、`backend/agent/main.py`、`backend/agent/app/agent/dependencies.py`。

## Spring Business 放置规则

- `pojo` 只放数据结构：请求用 DTO，响应用 VO，数据库映射用 Entity。
- `client/admin` 遵循 Controller → Service → Mapper/Store；Controller 只做绑定、鉴权上下文和响应包装。
- 外部系统先在消费模块定义 Gateway，实现在 `app.infrastructure`。参考 `ImportAgentGateway` → `HttpImportAgentGateway`。
- 只有多个业务模块共享的能力才放 `common`；模块私有端口不要上提。
- `app` 是组合根，聚合业务模块并承载 MinIO、Resend、Agent HTTP 等适配器。

## Python Agent 放置规则

- `app/api` 只负责协议、依赖注入与序列化，业务流程进入 `app/chat`、`app/agent`、`app/rag`。
- 领域层通过 `Protocol` 或 `AgentDependencies` 访问外部能力。
- Redis、HTTP、LLM、MySQL 和子进程实现只放 `app/adapters`，由 `main.py` lifespan 组装。
- importer/indexer/scheduler 属于 `jobs`，不要塞进 FastAPI 路由。
- 新 Agent 工具按最小权限放到 client/admin 对应节点，不创建全局万能工具集。

## 禁止做法

- `client/admin` 直接依赖 `app.infrastructure`。
- Python 领域节点直接创建 Redis、httpx 或 LLM 客户端。
- Controller/Router 内堆积事务、批处理或复杂状态转换。
- 因父 POM 已引入 ArchUnit 就声称边界已有自动保护；当前没有测试类落地。
