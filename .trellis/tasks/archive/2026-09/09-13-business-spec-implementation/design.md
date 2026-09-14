# 实施设计

## 权威规范
.trellis/spec/backend/directory-structure.md、error-handling.md、quality-guidelines.md 是本轮已批准方案。数据契约同时查 database-guidelines.md，Agent 协议查 agent-guidelines.md。

## 职责与依赖
common 不依赖其他项目模块；pojo 只承载数据类型；infrastructure 使用 common/pojo；auth 使用 infrastructure/common/pojo；log 使用 auth/common/pojo；agent 按需使用 log/auth/infrastructure/common/pojo；client 使用 auth/log/infrastructure/common/pojo；admin 另外依赖 agent；app 单向组合所有模块。

## 改动边界
改变实际声明、包路径、Maven 依赖及装配。认证规则实际分散在 common.security 与 client.AuthServiceImpl，迁移机制保留 client 账户校验。日志查询由 admin Mapper/Service 下沉 log 对外服务，admin 保留响应转换。现有 Redis/限流/MinIO/Resend 原实现迁 infrastructure，导入 HTTP 原实现迁 agent。

## 兼容与数据流
业务→公开能力服务→内部实现；HTTP 协议不变。刷新先原子消费，再业务校验账户，再签发并限制绝对寿命；日志写失败不替换业务结果；admin 校验导入参数后调用 agent。配置沿用 key 和默认值，通过 app 组装普通参数，禁止下层引用 app 配置类。

## 并行所有权
基础能力可按 infrastructure、auth、log 独立迁移。主代理负责现有模块 POM、app 装配、agent、跨模块 import、Converter 整合和全局架构检查；工作代理不得改其他代理模块。Javadoc 在目录归属稳定后按模块分片补齐，避免并行改同一文件。

## 验证与风险
先记录 clean test 基线，再迁移构建；针对刷新、日志、导入、Converter 添加语义测试。全局依赖及旧包名检查防止偶然编译成功。Javadoc 使用 JDK 工具或语法树检查，Lombok 生成成员无需重写。

## 回退
只回退本任务逻辑迁移，不覆盖既有用户改动或已批准 spec；不清理数据库/Redis 数据。各能力只有一份生效实现，不保留第二套生产装配作为兼容层。
