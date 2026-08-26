# ADR-0001：将 common 限定为共享契约模块

日期：2026-08-26  
状态：Accepted

## 背景

`backend/business/common` 当前有 29 个 Java 类、约 1,236 行代码，被 admin、client、agent、app 全部直接依赖。模块同时包含统一响应、异常、安全、Redis、限流、审计、MyBatis/CORS/HTTP 配置、图片存储端口和 Subject 转换器。

问题不是代码量本身，而是共同变化原因过多：修改一个具体业务或运行时实现会触碰所有业务模块共同依赖的模块，且“应该放在哪里”没有可执行的判断标准。

## 决策

1. 保留现有 `common` Maven 模块，但将其定义为稳定契约模块。
2. `common` 只保留结果/错误契约、Trace 常量、审计注解和共享图片存储端口。
3. Spring Bean、配置、AOP、Mapper、Redis/JWT 和领域 Converter 移至 app、client、admin 或 agent。
4. `ImageStorageGateway` 与 `ImageCategory` 保留在 `common.storage`；MinIO 实现继续位于 app。
5. 用 ArchUnit 将准入规则变成构建期约束。

## 选择理由

- 项目由个人维护、单体部署，不需要按领域或微服务增加 Maven 模块。
- admin/client 的划分保持不变，因此跨二者共享且由 app 实现的端口需要位于共同可依赖的内层模块。
- 契约与实现分离可以缩小 common 的变化原因，同时不改变公开 API 和数据库。
- ArchUnit 比依靠模块命名或评审记忆更可靠。

## 被否决的方案

### 按领域重组模块

否决原因：会改变现有 admin/client 组织方式，迁移范围和维护成本超过个人项目收益。

### 每个能力建立 Maven 模块

否决原因：当前约 7,000 行 Java，更多 POM 与跨模块类型暴露会增加构建和导航成本。

### 把 ImageStorageGateway 移到 app

否决原因：admin/client 编译时需要该接口，而 app 已依赖 admin/client，会形成 Maven 循环依赖。

### 只调整 common 子包，不迁移实现

否决原因：只能改善目录观感，无法降低运行时依赖和未来准入成本。

## 后果

正面影响：

- common 的职责可以通过依赖和注解规则自动验证。
- CORS、MyBatis、异常处理、安全过滤器和审计实现归入唯一组合根。
- 认证、Redis、限流与 client 的实际业务所有权一致。
- Agent 协议由 agent 模块拥有。

代价：

- admin/client 各自保留少量 Subject VO 转换代码。
- app 会显式依赖 client 的认证 Bean；这是现有 `app → client` 方向内的有意依赖。
- 操作日志写入 Mapper 与管理查询 Mapper 分开维护，但避免了业务模块依赖 app。
- 一次性迁移会修改较多 import，需要完整编译与回归测试。

## 约束

- 外部 REST API、JSON、HTTP 状态码和数据库结构不变。
- 现有 Service 接口保留。
- 实施规范以 [`backend-business-module-boundaries.md`](../backend-business-module-boundaries.md) 为准。

