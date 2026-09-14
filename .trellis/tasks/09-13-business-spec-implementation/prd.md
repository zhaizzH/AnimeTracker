# 落实 Business 模块分层与 Javadoc 规范

## 目标
将本会话逐项确认并合并到 .trellis/spec 的 Java Business 规范落实到代码，降低 common 职责混杂，保持用户端和管理端各自业务职责。

## 授权与范围
用户已逐项确认模块设计、pojo/Converter/Javadoc 规则，并在最终规范整理后明确要求“按照规划文档，创建任务，实现规范”。本任务执行该已批准方案，不重新发起产品设计。

## 要求
- R1：新增 infrastructure/auth/log，形成九模块；迁移现有实现而非保留并行副本；依赖无环，common 仅基础定义，app 装配和 HTTP 异常适配。
- R2：auth 统一 Token/会话/身份机制，log 统一采集/存储/清理/查询；依赖 log→auth→infrastructure→common。client/admin 保留账户与管理业务决策。
- R3：通用技术接口与实现归 infrastructure，导入通信接口与实现归 agent，admin→agent；配置唯一注册，业务不引用供应商实现或 app 类型。
- R4：DTO/VO/Entity 统一在 pojo；Converter 按模块管理，迁出 ServiceImpl/Controller 内纯映射，保留业务判断。
- R5：全部手写 Java 类型、字段、方法、构造器使用有实际含义的中文 Javadoc，pojo 字段同样覆盖；接口完整契约与实现继承同步。

## 验收
- Maven reactor 含九模块，完整 clean test 通过；架构验证覆盖允许依赖、反向依赖禁止、common 精简与旧路径清理。
- 登录刷新/撤销、日志查询与清理、导入失败分类、配置唯一性、Converter 空值/字段行为有针对性验证。
- HTTP 路由、DTO/VO 字段、权限、Cookie、Redis key/TTL、SSE 行为保持既有契约；不将注释说明误当新增业务行为。
- Javadoc 完整性和语法有可重复检查，不能以空模板或纯名称翻译完成覆盖。
- spec 的迁移状态、源码证据和任务执行记录与最终结果一致。

## 非目标
不改前端或 Python Agent 业务，不变更数据库 Schema，不新增产品功能，不推送或未经确认提交 Git。原有 spec 未提交变更继续保留。
