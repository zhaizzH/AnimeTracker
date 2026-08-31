# 后端质量门禁

## 必跑命令

```bash
cd backend/business
mvn -B clean test

cd ../agent
uv run pytest
```

CI 使用 Java 21、Node 22 与 `uv sync --dev`，配置见 `.github/workflows/ci.yml`。

## 当前测试基线

- Java `app` 模块包含配置迁移回归测试：`AppConfigurationBindingTest`、`SecurityConfigAuthorizationTest`、`CookieOriginFilterTest`、`AgentConfigTest` 与 `ArchitectureBoundaryTest`。
- Python 当前只有 `tests/jobs/importer/test_subject_metrics.py`。
- Java 配置迁移必须使用 `clean`，避免旧 `target/classes` 中的配置类造成重复 Bean 或假成功。
- 这些用例覆盖配置绑定、授权矩阵、Cookie Origin、Agent 超时/Trace/SSE 和模块边界；不启动完整 `AppApplication`，不连接真实 MySQL、Redis、MinIO 或 Python Agent。
- 新增业务分支应补最小回归测试；修复契约漂移时优先增加跨层或适配器测试。
- `ArchitectureBoundaryTest` 必须排除测试类，否则测试夹具中的 `app` 引用会污染下层边界判断。

## 代码审查清单

- 依赖方向符合 `directory-structure.md`，外部能力经 Gateway/Protocol 注入。
- API 路径、字段、错误码与 OpenAPI、前端 shared、Java/Python 路由保持一致。
- Agent 写操作仍需预览与确认，执行参数来自系统状态。
- 日志不包含敏感数据，traceId 跨 Spring ↔ Agent ↔ Business 回查可关联。
- Schema、事务、幂等和清理路径具有失败收尾与回滚方式。

## 验证粒度

- Java 接口改动：至少运行 Maven，并手工核对 Controller → Service → Mapper。
- Agent 图/工具改动：运行 pytest，并验证 SSE start/delta/end 与断开路径。
- importer/indexer 改动：测试 dry-run、锁释放、断点续传或 fail-closed gate。
- 跨层改动：从浏览器 API 调用一路核对到存储，再核对返回类型。
- 配置改动：同步示例文件，确认日志不会打印真实密钥；若是 Java 配置迁移，补齐上述五类测试并运行 `mvn -B clean test`。
