# 后端质量门禁

## 必跑命令

```bash
cd backend/business
mvn -B test

cd ../agent
uv run pytest
```

CI 使用 Java 21、Node 22 与 `uv sync --dev`，配置见 `.github/workflows/ci.yml`。

## 当前测试基线

- Java 父 POM 已引入 JUnit、Spring Test 与 ArchUnit，但仓库当前没有实际测试类。
- Python 当前只有 `tests/jobs/importer/test_subject_metrics.py`。
- 因此“命令通过”只证明编译/现有用例通过，不代表控制器、鉴权、SSE 或写协议已覆盖。
- 新增业务分支应补最小回归测试；修复契约漂移时优先增加跨层或适配器测试。
- 不要在没有测试文件的情况下写“已有 ArchitectureBoundaryTest 保护”。

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
- 配置改动：同步示例文件，确认日志不会打印真实密钥。
