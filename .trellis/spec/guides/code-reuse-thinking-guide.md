# 代码复用检查指南

## 写代码前搜索

```bash
rg "业务关键词|接口路径|字段名" frontend backend docs
rg "interface|class|def|export" 目标目录
```

先定位所有者，再决定复用、扩展或新建；不要按文件名猜测不存在。

## 已有单一来源

| 领域 | 所有者 |
|---|---|
| 前端跨应用 API 与类型 | `frontend/packages/shared/src` |
| Java 跨模块常量 | `backend/business/common/.../constant` |
| Agent 上游路径 | `AgentApiPaths.java`，并与 Python Router 同步 |
| 数据库结构 | `docs/database/db-schema.sql` |
| Agent 事件与 SSE | `app/chat/events.py`、`app/api/sse.py` |
| 外部系统抽象 | Java Gateway / Python Protocol + adapters |

## 应该复用或扩展

- client/admin 都需要的 API、类型、主题、鉴权或 SSE 能力进入 shared。
- Java 外部依赖沿用“消费模块 Gateway + app.infrastructure 实现”。
- Entity → VO 转换沿用对应 Converter，不在 Controller 手写重复映射。
- Python 新后端沿用领域端口，在 `app/adapters` 增加实现。
- 新日志事件沿用现有白名单和 trace context，不创建第二套 logger 协议。

## 不要过早抽象

- 仅一个页面使用且逻辑简单的展示状态保留本地。
- client/admin 视觉相似但业务与交互不同，不因“看起来像”强行共享整页。
- 单次可读常量不必提取；跨模块契约常量必须集中。
- 两个外部服务错误语义不同，不要只为减少行数合并异常处理。
- 抽象不能隐藏预览确认、权限或事务边界。

## 重复警报

出现以下任一情况先停下搜索：

1. 同一路径或字段结构在两个应用重复声明。
2. 多处把同一未知 payload 强转成不同类型。
3. Controller/Router 重复拼装相同响应或错误。
4. 多个 Agent 工具各自实现 token/header/trace 透传。
5. 同一状态值在 Java、Python、TypeScript 中出现不一致拼写。

复用后仍要运行所有受影响工作区的检查，公共代码通过自身测试不代表两个消费者都兼容。
