"""agent ↔ business 契约测试套件。

**本套件证明什么**：agent 侧对 business 的消费与仓库内 ``docs/spec/openapi.yaml``
保持一致——每个出站 HTTP 调用的 method+path 都能在契约里解析到唯一 operation，
静态可判定的请求字段都已在契约中声明，SSE 帧的 wire 形态与契约 ``SSEFrame`` 吻合，
预览→确认写协议的持久化契约（键模板、TTL、判别联合往返、preview 版本绑定）由测试锁定。
同时断言契约文件**自身**的结构完整性（``$ref`` 无悬空、无孤儿 schema、无测试夹具路径），
使「契约文件被再次整体改坏」本身成为红灯。

**本套件不证明什么**：它**不能**证明契约与 ``backend/business`` 的 Java 源码逐字段一致。
若某个 Java DTO 字段被改名而手工维护的契约没跟着改，agent 仍然匹配（已过时的）契约，
本套件依旧全绿。关闭该缺口需要 springdoc 自动导出或解析 Java 源码，两者均在本变更的
Out of Scope 内。详见 ``design.md`` → Risks / Trade-offs。

对应规范：``.trellis/spec/backend/contract-tests.md``。
"""
