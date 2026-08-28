# AnimeTracker 文档目录

> **一句话定位**：本目录存放项目级文档——数据库建表脚本、OpenAPI 接口规范、后端编码规范，以及复盘与规划记录。

> 返回项目总览：[`../README.md`](../README.md)

## 适用场景

- **新环境搭建**：用 `database/db-schema.sql` 初始化 MySQL 库表。
- **接口对接**：用 `spec/openapi.yaml` 查看 business 对外 REST 接口的请求与响应结构。
- **后端开发**：用 `conventions/backend-conventions.md` 对齐错误拦截与代码注释规范。
- **了解项目演进**：用 `retrospective/` 与 `superpowers/` 回溯设计决策与实施计划。

---

## 子目录

| 目录 | 说明 | 是否纳入版本控制 |
|------|------|-----------------|
| [`conventions/`](conventions/) | 项目规范：[`backend-conventions.md`](conventions/backend-conventions.md)（后端错误拦截与代码注释规范） | 是 |
| [`database/`](database/) | 数据库脚本：[`db-schema.sql`](database/db-schema.sql)（含 `operation_log` 等操作审计表） | 是 |
| [`spec/`](spec/) | API 规范：[`openapi.yaml`](spec/openapi.yaml)（OpenAPI 3.0 接口定义，共 65 个路径） | 是 |
| [`retrospective/`](retrospective/) | 项目复盘：[`项目复盘.md`](retrospective/项目复盘.md) | 是 |
| `superpowers/` | 规划文档：`handoff/`（交接说明）、`plans/`（实施计划）、`specs/`（设计文档），按日期命名 | **否**（已被 `.gitignore` 忽略） |
| `api/` | 第三方 Bangumi API 文档（独立 Git 仓库，非本项目源码） | **否**（已被 `.gitignore` 忽略） |

> 历史上提到的 `architecture/`（模块边界与 ADR）与 `test/`（测试计划与报告）目录在当前代码树中不存在，相关链接已移除。

---

## 前置依赖

查阅与执行本文档所需的工具：

| 用途 | 工具 |
|------|------|
| 执行建表脚本 | MySQL 8 客户端（`mysql`） |
| 查看接口规范 | 任意 OpenAPI 3.0 查看器（Swagger UI、VS Code 插件或在线编辑器） |
| 其余文档 | 任意 Markdown 阅读器 |

---

## 数据库

数据库名统一为 `anime_tracker`，建表脚本位于 [`database/db-schema.sql`](database/db-schema.sql)。该脚本是库表结构的**唯一事实来源**：business 与 agent 均不使用 Flyway / Liquibase（`spring.sql.init.mode: never`），结构变更直接修改该脚本。

核心表共 12 张：

| 表 | 说明 | 主要写入方 |
|----|------|-----------|
| `user` | 用户信息、认证、角色、启用状态与邮箱验证状态 | business |
| `subject` | 番剧条目（Bangumi ID、标题、封面、季度、评分等） | importer |
| `episode` | 番剧剧集（集数、类型、播出状态、时长） | importer |
| `subject_tag` | 番剧—标签关联（自由标签） | importer |
| `subject_meta_tag` | 番剧—官方元标签关联 | importer |
| `subject_alias` | 番剧别名 | importer |
| `subject_credit` | 番剧主创关联 | importer |
| `subject_relation` | 番剧间关联关系（仅保留动画关系） | importer |
| `user_collection` | 用户收藏与观看进度 | business |
| `import_record` | 数据导入批次记录（模式、数量、状态、断点） | importer |
| `rag_index_job` | RAG 索引任务队列（含状态、重试次数、租约） | importer / indexer |
| `operation_log` | 操作审计日志（登录、条目增删改、角色变更、导入等） | business |

> entity 的 Javadoc 注释需按本脚本描述撰写，详见 [`conventions/backend-conventions.md`](conventions/backend-conventions.md)。

---

## 快速开始

### 初始化数据库

```bash
mysql -u root -p
CREATE DATABASE anime_tracker DEFAULT CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
mysql -u root -p anime_tracker < docs/database/db-schema.sql
```

> 脚本可重复执行前的库必须为空；已有库请手动比对结构差异后再执行，脚本本身不含幂等 DDL。

### 浏览接口规范

```bash
# 方式一：直接用编辑器查看
code docs/spec/openapi.yaml

# 方式二：起一个本地 Swagger UI（需 Docker）
docker run -p 8081:8080 -e SWAGGER_JSON=/spec/openapi.yaml \
  -v "$PWD/docs/spec:/spec" swaggerapi/swagger-ui
```

---

## 核心用法示例

### 按领域检索 OpenAPI 路径

`spec/openapi.yaml` 共 65 个路径，按前缀分布：

| 前缀 | 数量级 | 说明 |
|------|-------|------|
| `/api/client/auth/*` | 8 | 注册、登录、邮箱验证、刷新、登出、找回与重置密码 |
| `/api/client/subjects/*` | 6+ | 列表、搜索、季度、放送表、批量、详情、年份 |
| `/api/client/collections/*` | 8+ | 收藏 CRUD、计数、追番日程、剧集状态、进度预览与执行 |
| `/api/client/me/*` | 4 | 个人信息、改密、邮箱验证码 |
| `/api/client/agent/*` | 5+ | 流式对话与会话管理（由 business 代理到 Agent） |
| `/api/admin/*` | 10+ | 仪表盘、条目、用户、导入、日志 |
| `/api/admin/agent/*` | 6+ | 提示词、模型配置、管理员会话 |

### 对照规范写后端代码

新增 Controller / Service 前先读 [`conventions/backend-conventions.md`](conventions/backend-conventions.md)，其中约定了：

- 错误码一律等于 HTTP 状态码，经 `ErrorType` 枚举 + `BizException` 抛出；
- 安全层 401/403 与业务异常的响应路径区别；
- 禁止向客户端透传 SQL、堆栈、resourcePath 等内部细节；
- 中文 Javadoc 注释规范（pojo 模块所有字段必须加注释）。

---

## 常见问题

**Q：为什么没有迁移脚本（migrations）？**
A：项目不使用 Flyway / Liquibase，库表结构由 `database/db-schema.sql` 单次建表维护。结构变更请直接修改该脚本，新环境重新执行。

**Q：`superpowers/` 目录里的计划文档为什么别人看不到？**
A：该目录已被根 `.gitignore` 忽略，属于本地工作产物，不进入版本控制。`api/`（第三方 Bangumi 文档）同理。

**Q：改了库表后 entity 注释对不上怎么办？**
A：`backend-business` 的 entity Javadoc 要求按 `db-schema.sql` 描述撰写，改表时应同步更新 `pojo/entity/` 下对应类的字段注释。

**Q：OpenAPI 文件会自动更新吗？**
A：不会。business 未集成 springdoc / Knife4j，`spec/openapi.yaml` 需手工维护，新增或修改接口后请同步更新。

**Q：`rag_index_job` 表是做什么的？**
A：它是 importer 与 indexer 之间的任务队列。importer 写入待索引条目，indexer 分批次认领、生成向量并写回 Redis。business 不直接操作该表。

---

## 与相邻模块的关联

| 文档 | 关联对象 |
|------|---------|
| [`database/db-schema.sql`](database/db-schema.sql) | `backend/business`（读写业务表）、`backend/agent/jobs/*`（写入导入与索引表） |
| [`spec/openapi.yaml`](spec/openapi.yaml) | `backend/business` 的 Controller 层 |
| [`conventions/backend-conventions.md`](conventions/backend-conventions.md) | `backend/business` 全部 Java 代码 |
| `retrospective/`、`superpowers/` | 项目级决策记录，供全团队参考 |

其他入口：

- 项目总览：[`../README.md`](../README.md)
- 后端总览：[`../backend/README.md`](../backend/README.md)
- 业务后端：[`../backend/business/README.md`](../backend/business/README.md)
- AI Agent：[`../backend/agent/README.md`](../backend/agent/README.md)
- 数据导入器：[`../backend/agent/jobs/importer/README.md`](../backend/agent/jobs/importer/README.md)

---

## 待补充

1. **架构文档缺失**：历史文档引用的 `architecture/`（后端模块边界、ADR-0001、术语表）在当前代码树中不存在，模块边界约束目前仅体现在 `backend/business` 的分层约定与 ArchUnit 依赖声明（尚无测试类落地），需确认是否补写。
2. **测试工作区缺失**：历史文档引用的 `test/`（`plan/` 测试计划、`report/` 执行报告、`scripts/` 辅助脚本）不存在，测试策略与执行记录暂无归档位置。
3. **数据库脚本的幂等性**：`db-schema.sql` 不支持重复执行，升级路径（加字段、加索引）缺乏版本化的变更记录，存量库的升级方式待确认。
4. **接口规范的完整性**：`spec/openapi.yaml` 为手工维护，与 `backend/business` 现有 Controller 的一致性未经自动校验，可能存在遗漏或过期定义。
