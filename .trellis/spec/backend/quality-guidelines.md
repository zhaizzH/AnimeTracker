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
- MyBatis `type-aliases-package` 会把实体简单类名注册为不区分大小写的别名；实体类名若与 MyBatis/JDK 内置类型冲突，必须显式使用 `@Alias` 绑定业务别名，并用 `TypeAliasRegistry.registerAliases` 回归测试扫描结果。
- 这些用例覆盖配置绑定、授权矩阵、Cookie Origin、Agent 超时/Trace/SSE 和模块边界；不启动完整 `AppApplication`，不连接真实 MySQL、Redis、MinIO 或 Python Agent。
- 新增业务分支应补最小回归测试；修复契约漂移时优先增加跨层或适配器测试。
- `ArchitectureBoundaryTest` 必须排除测试类，否则测试夹具中的 `app` 引用会污染下层边界判断。

## 已知覆盖债务

- Java 尚无认证刷新、收藏进度事务、管理写操作和完整 Controller 集成回归。
- Python 尚无 Agent 图路由、SSE 断开、PendingAction 持久化失败、Redis 降级、importer 锁/恢复、indexer gate 和 scheduler 重叠场景的自动化覆盖。
- 当前测试基线只能证明列出的配置与指标用例通过，不能替代上述高风险路径；新改动必须按风险补测试。

## Scenario: 可追溯 Golden Case 评测数据集

### 1. Scope / Trigger

- 触发：新增、重建或审核 RAG golden cases；尤其是将离线定义集提升为真实发布门禁时。
- 目的：防止用脱离真实数据库的占位 Subject ID 或 mock 结果冒充 120-case 线上评测。

### 2. Signatures

- 生成命令：`python -m tests.evals.generate_golden_cases --output tests/evals/golden_cases.json`。
- `load_golden_dataset(path) -> {metadata, cases}`；旧数组格式只允许兼容读取，生产数据集必须使用 envelope。
- `GoldenTrace` 必须包含 `snapshot_id`、`captured_at`、`evidence_id`、`sql_template`、`parameters`、`source_tables`、`result_count`、`result_ids_hash`、`index_version`、`profile_version`。

### 3. Contracts

- 生成器只能执行只读 SQL；真实快照不足恰好 120 条时必须失败，不得补写虚构用例。
- 生产数据集必须包含恰好 120 条 case，且每条 evidence ID 唯一；所有 case 绑定同一 snapshot/index/profile 版本。
- `DEFINITION_ONLY` 只表示事实快照定义完成；只有 ACTIVE release、真实服务回放和五份同版本 gate 报告通过后，才可标记评测通过。

### 4. Validation & Error Matrix

| 条件 | 必须行为 |
|---|---|
| 结果集无法由当前快照查询得到 | 拒绝生成或退出非零，不写入不完整数据集 |
| schema signature 未覆盖 case 使用的实体表 | 拒绝生成，补齐 `subject/episode/person/character` 等来源表 |
| case 数量不是 120 | 拒绝生成；不得用 placeholder ID 填充 |
| 无 ACTIVE release | 保持 `DEFINITION_ONLY`/`BLOCKED_NO_ACTIVE_RELEASE`，不得生成通过型 gate 报告 |

### 5. Good/Base/Bad Cases

- Good：从真实 Subject、alias、关系和实体表查询结果生成 case，并保存结果 ID hash 与 SQL 模板。
- Base：只有定义集完成、release 尚未激活时，报告明确写出阻断原因。
- Bad：复制旧的经典作品 ID、把离线 mock 指标写成 120/120，或跳过真实 SQL 验证。

### 6. Tests Required

- 断言生产数据集为 120 条、分类配额正确、evidence ID 唯一、快照和版本一致。
- 断言生成器在不足 120 条或 SQL 结果为空时拒绝写入。
- 真实 release 激活后再运行 Business → Vector Set → Evidence 回放，并断言五份报告版本一致。

### 7. Wrong vs Correct

#### Wrong

```python
expected_subject_ids = [1, 2, 3]  # 复制旧 mock case，未绑定当前快照
```

#### Correct

```python
result_ids = execute_snapshot_query(connection, params)
if not result_ids:
    raise RuntimeError("真实快照没有可验证结果")
trace = GoldenTrace(
    snapshot_id=snapshot_id,
    evidence_id=f"{snapshot_id}:{case_id}",
    result_ids_hash=sha256_ids(result_ids),
    index_version=index_version,
    profile_version=profile_version,
)
```

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

### MyBatis 类型别名冲突

- 错误：在 `mybatis-plus.type-aliases-package` 扫描包中直接新增名为 `Character`、`String` 等与内置别名冲突的实体类，依赖默认简单类名注册。
- 正确：为业务实体显式指定不冲突别名，例如 `@Alias("BangumiCharacter")`，并保留 Mapper/XML 使用的全限定类名兼容。
- 验证：至少断言业务别名解析到实体类、内置别名仍解析到 JDK 类型，再运行 `mvn -B clean test`。

## Git 提交信息

- 首行使用 `.gitmessage` 约定：`<type>(<scope>): <中文描述>`，描述不超过 50 个字符；`type` 使用 `feat`、`fix`、`docs`、`style`、`refactor`、`perf`、`test`、`chore` 或 `ci`。
- 项目内 Trellis 自动提交也必须使用中文描述，例如 `chore(任务): 归档 xxx`、`chore: 记录开发日志`，不能保留英文 `archive` 或 `record journal`。
- 新克隆仓库首次提交前执行 `git config --local commit.template .gitmessage`；提交前用 `git log -1 --format=%s` 自检主题。
