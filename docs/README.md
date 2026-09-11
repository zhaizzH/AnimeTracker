# AnimeTracker 文档目录

> **一句话定位**：本目录存放项目级文档——数据库建表脚本与版本化迁移、OpenAPI 接口规范、后端编码规范，以及复盘与规划记录。

> 返回项目总览：[`../README.md`](../README.md)

## 适用场景

- **新环境搭建**：用 `database/db-schema.sql` 初始化 MySQL 库表。
- **存量库升级**：按版本执行 `database/migration-002-rag-entities.sql` 与 `database/migration-003-search-projection.sql`。
- **接口对接**：用 `spec/openapi.yaml` 查看 business 对外 REST 接口的请求与响应结构。
- **后端开发**：用 `conventions/backend-conventions.md` 对齐错误拦截与代码注释规范。
- **了解项目演进**：用 `retrospective/` 与 `superpowers/` 回溯设计决策与实施计划。

---

## 子目录

| 目录 | 说明 | 是否纳入版本控制 |
|------|------|-----------------|
| [`conventions/`](conventions/) | 项目规范：[`backend-conventions.md`](conventions/backend-conventions.md)（后端错误拦截与代码注释规范） | 是 |
| [`database/`](database/) | 数据库脚本：`db-schema.sql`（完整建表）与两份版本化前向迁移 | 是 |
| [`spec/`](spec/) | API 规范：[`openapi.yaml`](spec/openapi.yaml)（OpenAPI 3.0 接口定义，共 68 个路径） | 是 |
| [`retrospective/`](retrospective/) | 项目复盘：[`项目复盘.md`](retrospective/项目复盘.md) | 是 |
| `superpowers/` | 规划文档：`handoff/`（交接说明）、`plans/`（实施计划）、`specs/`（设计文档），按日期命名 | **否**（已被 `.gitignore` 忽略） |
| `api/` | 第三方 Bangumi API 文档（独立 Git 仓库，非本项目源码） | **否**（已被 `.gitignore` 忽略） |

> 历史上提到的 `architecture/`（模块边界与 ADR）与 `test/`（测试计划与报告）目录在当前代码树中不存在，相关链接已移除。模块边界约束现已由 `backend/business/app/src/test/java/top/zhaizz/app/architecture/ArchitectureBoundaryTest.java` 以 ArchUnit 落地强制。

---

## 前置依赖

查阅与执行本文档所需的工具：

| 用途 | 工具 |
|------|------|
| 执行建表与迁移脚本 | MySQL **8.4** 客户端（`mysql`）；迁移脚本使用 `INFORMATION_SCHEMA` 条件 DDL，需要 8.x 支持 |
| 查看接口规范 | 任意 OpenAPI 3.0 查看器（Swagger UI、VS Code 插件或在线编辑器） |
| 其余文档 | 任意 Markdown 阅读器 |

---

## 数据库

数据库名统一为 `anime_tracker`。business 与 agent 均不使用 Flyway / Liquibase（`spring.sql.init.mode: never`）。

| 脚本 | 用途 | 幂等性 |
|------|------|--------|
| [`db-schema.sql`](database/db-schema.sql) | **全新空库**的完整结构事实来源，共 23 张表 | 否，必须空库执行 |
| [`migration-002-rag-entities.sql`](database/migration-002-rag-entities.sql) | 存量库：新增 9 张实体 / 关系 / 任务表与 `source_active` 兼容列 | 是（`CREATE TABLE IF NOT EXISTS` + 条件 DDL） |
| [`migration-003-search-projection.sql`](database/migration-003-search-projection.sql) | 存量库：新增检索投影表 `search_document`、`search_index_release` | 是（`CREATE TABLE IF NOT EXISTS`） |

核心表共 23 张，按引入顺序分为三组：

### 原有业务表（12）

| 表 | 说明 | 主要写入方 |
|----|------|-----------|
| `user` | 用户信息、认证、角色、启用状态与邮箱验证状态 | business |
| `subject` | 番剧条目（Bangumi ID、标题、封面、季度、评分等） | importer |
| `episode` | 番剧剧集（集数、类型、播出状态、时长） | importer |
| `subject_tag` | 番剧—标签关联（自由标签） | importer |
| `subject_meta_tag` | 番剧—官方元标签关联 | importer |
| `subject_alias` | 番剧别名 | importer |
| `subject_credit` | 番剧主创关联（旧结构） | importer |
| `subject_relation` | 番剧间关联关系（仅保留动画关系） | importer |
| `user_collection` | 用户收藏与观看进度 | business |
| `import_record` | 数据导入批次记录（模式、数量、状态、断点） | importer |
| `rag_index_job` | 旧索引任务队列（含状态、重试次数、租约） | importer / indexer |
| `operation_log` | 操作审计日志（登录、条目增删改、角色变更、导入等） | business |

### migration-002 新增实体与关系表（9）

| 表 | 说明 | 主要写入方 |
|----|------|-----------|
| `person` | Bangumi 人物 / 公司 / 组合摘要与详情状态 | importer / backfill |
| `character` | Bangumi 角色与作品内组织摘要与详情状态 | importer / backfill |
| `person_alias` | 人物别名及来源有效状态 | importer / backfill |
| `character_alias` | 角色别名及来源有效状态 | importer / backfill |
| `subject_person_credit` | 作品—人物主创职责关系 | importer |
| `subject_character` | 作品—角色关系 | importer |
| `character_actor` | 作品限定的角色—声优/演员关系 | importer |
| `entity_detail_job` | Person / Character 详情渐进回填任务 | importer / backfill |
| `search_index_job` | SUBJECT / EPISODE / PERSON / CHARACTER 通用索引任务 | importer / indexer |

### migration-003 新增检索投影表（2）

| 表 | 说明 | 主要写入方 |
|----|------|-----------|
| `search_document` | MySQL `ngram` FULLTEXT 词法投影（按实体类型与版本分行） | indexer |
| `search_index_release` | 索引激活版本指针（**唯一权威**，替代已废弃的 Redis alias） | indexer |

> entity 的 Javadoc 注释需按本脚本描述撰写，详见 [`conventions/backend-conventions.md`](conventions/backend-conventions.md)。

---

## 快速开始

### 初始化数据库（全新空库）

```bash
mysql -u root -p
CREATE DATABASE anime_tracker DEFAULT CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
mysql -u root -p anime_tracker < docs/database/db-schema.sql
```

> 脚本不含幂等 DDL，请勿对非空库执行。

### 存量库前向迁移

```bash
# 1. 先完成可恢复备份，记录备份位置，并确认目标库不是生产库
# 2. 按版本顺序执行
mysql -u root -p anime_tracker < docs/database/migration-002-rag-entities.sql
mysql -u root -p anime_tracker < docs/database/migration-003-search-projection.sql
```

`migration-002` 面向已有 `subject`、`subject_alias`、`subject_meta_tag`、`subject_credit` 和 `rag_index_job` 的库，只新增实体/关系/任务表与兼容列；`migration-003` 面向已执行 `migration-002` 的库，只新增两张投影表。两者均支持重复执行，且**不回改也不删除任何旧表旧数据**。

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

`spec/openapi.yaml` 共 68 个路径，按前缀分布：

| 前缀 | 数量级 | 说明 |
|------|-------|------|
| `/api/client/auth/*` | 8 | 注册、登录、邮箱验证、刷新、登出、找回与重置密码 |
| `/api/client/subjects/*` | 7 | 列表、搜索、**词法检索**、季度、放送表、批量、详情、年份、剧集 |
| `/api/client/collections/*` | 8+ | 收藏 CRUD、计数、追番日程、剧集状态、进度预览与执行 |
| `/api/client/me/*` | 4 | 个人信息、改密、邮箱验证码 |
| `/api/client/evidence/*` | 2 | `batch`（批量取证据）、`resolve`（解析指定实体证据） |
| `/api/client/agent/*` | 5+ | 流式对话与会话管理（由 business 代理到 Agent） |
| `/api/admin/*` | 10+ | 仪表盘、条目、用户、导入、日志 |
| `/api/admin/agent/*` | 6+ | 提示词、模型配置、管理员会话 |

### 校验迁移结果

```sql
-- 确认 23 张表均已存在
SELECT TABLE_NAME FROM INFORMATION_SCHEMA.TABLES
WHERE TABLE_SCHEMA = DATABASE() ORDER BY TABLE_NAME;

-- 确认词法投影的 FULLTEXT 索引已建立
SHOW INDEX FROM search_document;

-- 确认当前激活的索引版本
SELECT * FROM search_index_release;
```

### 对照规范写后端代码

新增 Controller / Service 前先读 [`conventions/backend-conventions.md`](conventions/backend-conventions.md)，其中约定了：

- 错误码一律等于 HTTP 状态码，经 `ErrorType` 枚举 + `BizException` 抛出；
- 安全层 401/403 与业务异常的响应路径区别；
- 禁止向客户端透传 SQL、堆栈、resourcePath 等内部细节；
- 中文 Javadoc 注释规范（pojo 模块所有字段必须加注释）。

---

## 常见问题

**Q：初始化脚本和迁移脚本怎么选？**
A：全新空库执行 `database/db-schema.sql`；已有数据的库先备份，再按版本顺序执行前向迁移。不要对未知或非空库执行初始化脚本。

**Q：迁移脚本可以重复执行吗？**
A：可以。两份迁移均使用 `CREATE TABLE IF NOT EXISTS`，`migration-002` 的兼容列还额外使用 `INFORMATION_SCHEMA` 条件 DDL 判断后再添加。

**Q：`superpowers/` 目录里的计划文档为什么别人看不到？**
A：该目录已被根 `.gitignore` 忽略，属于本地工作产物，不进入版本控制。`api/`（第三方 Bangumi 文档）同理。

**Q：改了库表后 entity 注释对不上怎么办？**
A：`backend-business` 的 entity Javadoc 要求按 `db-schema.sql` 描述撰写，改表时应同步更新 `pojo/entity/` 下对应类的字段注释。当前 `pojo/entity/` 已有 20 个实体。

**Q：OpenAPI 文件会自动更新吗？**
A：不会。business 未集成 springdoc / Knife4j，`spec/openapi.yaml` 需手工维护，新增或修改接口后请同步更新。

**Q：`rag_index_job` 和 `search_index_job` 有什么区别？**
A：`rag_index_job` 是旧版索引任务队列；`search_index_job` 是新的通用索引任务队列，支持 SUBJECT / EPISODE / PERSON / CHARACTER 四类实体。`jobs/indexer` 的 `--queue` 参数可选 `legacy` / `search` / `both`（默认 `both`）来分别消费，`search_document` 与 `search_index_release` 只由新链路写入。

**Q：怎么判断检索索引是否处于可用状态？**
A：查 `search_index_release` 中的激活版本，并确认 `search_document` 有对应版本的行。Agent 侧还会探测 Redis 8 的 Vector Set 能力，任一不满足即保持检索关闭（fail-closed）。

---

## 与相邻模块的关联

| 文档 | 关联对象 |
|------|---------|
| [`database/db-schema.sql`](database/db-schema.sql) 与两份迁移 | `backend/business`（读写业务表）、`backend/agent/jobs/*`（写入导入、回填、索引表） |
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

1. **迁移版本的完整清单**：`database/` 下当前有 `migration-002` 与 `migration-003`，但**不存在 `migration-001`**。推测 001 对应的变更已并入 `db-schema.sql` 或未被使用，编号起点与后续迁移的命名规则待维护者确认。
2. **迁移的执行记录归档位置**：`migration-002` 涉及 9 张新增表与 3 个兼容列，其验证报告目前只存在于 `.trellis/` 任务目录中（属于开发流程产物），`docs/` 下没有迁移执行记录的长期归档位置。
3. **接口规范的完整性**：`spec/openapi.yaml` 为手工维护，与 `backend/business` 现有 Controller 的一致性未经自动校验，可能存在遗漏或过期定义。
4. **`rag_index_job` 的退役计划**：新旧索引任务表并存，`--queue` 默认 `both`；旧链路何时下线、`rag_index_job` 何时可删除未在代码或文档中标注。
