# 后端质量门禁

## 质量门禁分层

```bash
cd backend/business
mvn -B clean test

cd ../agent
uv run pytest
```

命令按变更范围分层，不要把 CI 当前状态误读成完整交付门禁：

| 层级 | 当前命令/要求 | 适用范围 |
|---|---|---|
| CI 强制 | 前端 `npm run typecheck`；Java `mvn -B test`；Python `uv run pytest` | 每次 push/PR 的现行工作流 |
| 提交前 | 运行受影响模块的测试；跨层改动至少补一条成功和一条权限/失败路径 | 普通代码改动 |
| 交付前 | Java 配置迁移/模块边界运行 `mvn -B clean test`；前端可交付变更运行 `npm run build` | 配置、边界、构建产物或跨层契约变更 |

CI 使用 Java 21、Node 22 与 `uv sync --dev`，配置见 `.github/workflows/ci.yml`。CI 尚未强制前端 Vitest/build；不要在 spec 中声称它们已经是 CI 门禁。

## 当前测试基线

- Java `app` 模块包含配置迁移回归测试：`AppConfigurationBindingTest`、`SecurityConfigAuthorizationTest`、`CookieOriginFilterTest`、`AgentConfigTest` 与 `ArchitectureBoundaryTest`。
- Python 当前只有 `tests/jobs/importer/test_subject_metrics.py`。
- Java 配置迁移必须使用 `clean`，避免旧 `target/classes` 中的配置类造成重复 Bean 或假成功。
- 这些用例覆盖配置绑定、授权矩阵、Cookie Origin、Agent 超时/Trace/SSE 和模块边界；不启动完整 `AppApplication`，不连接真实 MySQL、Redis、MinIO 或 Python Agent。
- 新增业务分支应补最小回归测试；修复契约漂移时优先增加跨层或适配器测试。
- `ArchitectureBoundaryTest` 必须排除测试类，否则测试夹具中的 `app` 引用会污染下层边界判断。

## 已知覆盖债务

- Java 尚无认证刷新、收藏进度事务、管理写操作和完整 Controller 集成回归。
- Python 尚无 Agent 图路由、SSE 断开、PendingAction 持久化失败、Redis 降级、importer 锁/恢复、indexer gate 和 scheduler 重叠场景的自动化覆盖。
- 当前测试基线只能证明列出的配置与指标用例通过，不能替代上述高风险路径；新改动必须按风险补测试。

## 代码审查清单

- 依赖方向符合 `directory-structure.md`，外部能力经 Gateway/Protocol 注入。
- API 路径、字段、错误码与 OpenAPI、前端 shared、Java/Python 路由保持一致。
- Agent 写操作仍需预览与确认，执行参数来自系统状态。
- 日志不包含敏感数据，traceId 跨 Spring ↔ Agent ↔ Business 回查可关联。
- Schema、事务、幂等和清理路径具有失败收尾与回滚方式。
- 待确认动作写入失败不得被裸 `except: pass` 隐藏；健康探针必须核对 Security 放行和匿名响应。

## 验证粒度

- Java 接口改动：至少运行 Maven，并手工核对 Controller → Service → Mapper。
- Agent 图/工具改动：运行 pytest，并验证 SSE start/delta/end 与断开路径。
- importer/indexer 改动：测试 dry-run、锁释放、断点续传或 fail-closed gate。
- 跨层改动：从浏览器 API 调用一路核对到存储，再核对返回类型。
- 配置改动：同步示例文件，确认日志不会打印真实密钥；若是 Java 配置迁移，补齐上述五类测试并运行 `mvn -B clean test`。

## Git 提交信息

- 首行使用 `.gitmessage` 约定：`<type>(<scope>): <中文描述>`，描述不超过 50 个字符；`type` 使用 `feat`、`fix`、`docs`、`style`、`refactor`、`perf`、`test`、`chore` 或 `ci`。
- 项目内 Trellis 自动提交也必须使用中文描述，例如 `chore(任务): 归档 xxx`、`chore: 记录开发日志`，不能保留英文 `archive` 或 `record journal`。
- 新克隆仓库首次提交前执行 `git config --local commit.template .gitmessage`；提交前用 `git log -1 --format=%s` 自检主题。
