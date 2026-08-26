# backend/business 架构术语表

| 术语 | 在本项目中的含义 |
|---|---|
| 组合根（Composition Root） | 创建并连接运行时对象的最外层模块；本项目唯一组合根是 `app`。 |
| 契约（Contract） | 调用方和实现方共同依赖的稳定类型，例如 `Result`、`BizException`、注解和 Gateway 接口。 |
| 实现（Implementation） | 会执行 IO、读取运行时上下文或注册 Spring Bean 的代码，例如 Redis、MinIO、JWT Filter、Mapper 和 Aspect。 |
| 端口（Port/Gateway） | 业务模块声明的外部能力接口；实现由 app 提供，例如 `ImageStorageGateway`。 |
| 适配器（Adapter） | 对端口的技术实现，例如 `MinioImageStorageGateway`、`ResendEmailGateway`。 |
| 运行时 Bean | 由 Spring 容器创建或发现的类，包括 `@Component`、`@Service`、`@Configuration`、Advice、Aspect 和定时任务。 |
| 业务模块 | `admin`、`client`、`agent`；按使用者/入口划分，并保持互不依赖。 |
| common | 共享契约模块，不等于“两个地方用到就放进去”的工具箱。 |
| pojo | 共享 Entity/DTO/VO/枚举模块，只表达数据，不执行 IO 或业务流程。 |
| 横切能力 | 跨多个请求生效的运行时行为，例如异常处理、安全 Filter、审计 AOP 和 Trace 透传。其实现归 app。 |
| 依赖方向 | 编译期模块引用方向；外层 app 可以依赖内层业务模块，业务模块不得依赖 app。 |
| 循环依赖 | 两个 Maven 模块互相依赖。把 `ImageStorageGateway` 移到 app 会造成 `admin/client → app → admin/client`。 |
| 准入规则 | 判断代码是否允许进入某模块的可执行标准，本项目通过 ArchUnit 固化。 |
| 尽力而为审计 | 操作日志写入失败只记录告警，不影响原业务请求的成功或失败结果。 |

