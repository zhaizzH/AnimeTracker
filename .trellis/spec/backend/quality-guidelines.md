# 后端质量与 Java 注释规范

同层相关规范按主题合并；目标设计与当前实现的状态标记保留，各章节约束继续有效。

- [后端质量门禁](#后端质量门禁)
- [Java 后端 Javadoc 规范](#java-后端-javadoc-规范)

## 后端质量门禁

### 质量门禁分层

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

### 当前测试基线

2026-09-10 的历史审计曾因 `tests/agent/test_capability_route.py` 导入缺失符号而收集失败；该测试已按当前 graph/runtime 契约重写。

2026-09-12 最终复核在 `backend/agent` 执行 `\.venv\Scripts\python.exe -m pytest`，结果为 284 passed；运行环境为已有 Agent `.venv`。此前 271 passed 是排除失效测试文件后的历史诊断数，不替代本次结果。

- Java `app` 模块包含配置迁移回归测试：`AppConfigurationBindingTest`、`SecurityConfigAuthorizationTest`、`CookieOriginFilterTest`、`AgentConfigTest` 与 `ArchitectureBoundaryTest`。
- Python 已有 importer、indexer gate、shadow eval、release store、容量报告和 RAG 故障矩阵回归用例；任务归档的 2026-09-07 证据为 Agent `268 passed, 1 deselected`、Business `37` tests。该数字是带日期的历史验证，不替代本次变更重新运行测试。
- Python 还有 `tests/jobs/backfill`、`tests/jobs/scheduler`、`tests/adapters`、`tests/entities`、`tests/evals` 与 `tests/agent`。Prompt 字符串断言只证明文件内容，不能证明模型始终使用中文，也不能证明进程已经刷新 Prompt。
- Java 配置迁移必须使用 `clean`，避免旧 `target/classes` 中的配置类造成重复 Bean 或假成功。
- MyBatis `type-aliases-package` 会把实体简单类名注册为不区分大小写的别名；实体类名若与 MyBatis/JDK 内置类型冲突，必须显式使用 `@Alias` 绑定业务别名，并用 `TypeAliasRegistry.registerAliases` 回归测试扫描结果。
- 这些用例覆盖配置绑定、授权矩阵、Cookie Origin、Agent 超时/Trace/SSE 和模块边界；不启动完整 `AppApplication`，不连接真实 MySQL、Redis、MinIO 或 Python Agent。
- 新增业务分支应补最小回归测试；修复契约漂移时优先增加跨层或适配器测试。
- `ArchitectureBoundaryTest` 必须排除测试类，否则测试夹具中的 `app` 引用会污染下层边界判断。

### 已知覆盖债务

- Java 已补充登录、刷新和注销编排单测，以及认证存储/绝对寿命、导入错误分类和 Converter 边界回归；仍缺收藏进度事务、管理写操作和完整 Controller 集成回归。SSE 控制器单测不替代真实代理集成。
- Python 已有 Agent 图路由、SSE 持久化失败单测，但尚无 SSE 断开、真实 Redis/Business/Embedding 集成、灰度告警采集、importer 锁/恢复和 scheduler 重叠场景的完整自动化覆盖。
- 当前测试基线只能证明列出的配置与指标用例通过，不能替代上述高风险路径；新改动必须按风险补测试。

### Scenario: RAG 发布完成与灰度质量证据

#### 1. Scope / Trigger

- 触发：准备激活 MySQL `search_index_release`、打开 `RAG_ENABLED`、完成 24 小时灰度或清理旧投影。

#### 2. Signatures

- Gate 报告：`quality/capacity/eval/latency/human`，必须共享 `indexVersion/profileVersion`。
- 灰度记录：观察起止时间、release、功能开关状态、成功/错误率、P95、Evidence completeness、告警和回滚结果。

#### 3. Contracts

- gate PASS 后才能激活 release；release ACTIVE 不代表 `RAG_ENABLED` 默认开启。
- 至少 24 小时灰度稳定且 release/功能开关回滚确认通过后，任务才可标记完成。
- 回滚窗口结束前不得删除旧 `search_document`、Vector Set 或表；灰度记录不得虚构未采集的数值。

#### 4. Validation & Error Matrix

| 条件 | 必须行为 |
|---|---|
| gate 未通过 | 拒绝激活，保留旧 release |
| 灰度异常 | 关闭 RAG 开关并切回已验证 release |
| 缺少灰度起止或回滚记录 | 任务保持未完成，不得归档 |
| 请求清理旧投影 | 检查回滚窗口与独立确认，否则拒绝 |

#### 5. Good / Base / Bad Cases

- Good：gate PASS → 激活 → 单独开启开关 → 观察 24 小时 → 记录回滚演练 → 再规划清理。
- Base：release ACTIVE 但开关关闭，记录为“索引已发布、Agent RAG 未默认启用”。
- Bad：用 gate PASS 代替灰度确认，或用人工口头结论补写不存在的 P95/错误率。

#### 6. Tests Required

- gate 单测覆盖版本、阈值、报告缺失和 `RELEASE_CANDIDATE` 门禁。
- release store 单测覆盖 ACTIVE 唯一性、事务切换和已验证版本 rollback。
- 交付复核运行 `mvn -B clean test`、`uv run pytest`、gate CLI、健康检查和词法 API；把灰度/回滚结果写入运行审计。

#### 7. Wrong vs Correct

```text
Wrong: gate=PASS 后直接宣称 RAG 已默认启用，并删除旧投影。
Correct: 明确区分 release ACTIVE、RAG_ENABLED 和灰度完成；异常先关闭开关、再切回 MySQL release，保留旧投影。
```

### Scenario: 可追溯 Golden Case 评测数据集

#### 1. Scope / Trigger

- 触发：新增、重建或审核 RAG golden cases；尤其是将离线定义集提升为真实发布门禁时。
- 目的：防止用脱离真实数据库的占位 Subject ID 或 mock 结果冒充 120-case 线上评测。

#### 2. Signatures

- 生成命令：`python -m tests.evals.generate_golden_cases --output tests/evals/golden_cases.json`。
- `load_golden_dataset(path) -> {metadata, cases}`；旧数组格式只允许兼容读取，生产数据集必须使用 envelope。
- `GoldenTrace` 必须包含 `snapshot_id`、`captured_at`、`evidence_id`、`sql_template`、`parameters`、`source_tables`、`result_count`、`result_ids_hash`、`index_version`、`profile_version`。

#### 3. Contracts

- 生成器只能执行只读 SQL；真实快照不足恰好 120 条时必须失败，不得补写虚构用例。
- 生产数据集必须包含恰好 120 条 case，且每条 evidence ID 唯一；所有 case 绑定同一 snapshot/index/profile 版本。
- `DEFINITION_ONLY` 只表示事实快照定义完成；只有 ACTIVE release、真实服务回放和五份同版本 gate 报告通过后，才可标记评测通过。

#### 4. Validation & Error Matrix

| 条件 | 必须行为 |
|---|---|
| 结果集无法由当前快照查询得到 | 拒绝生成或退出非零，不写入不完整数据集 |
| schema signature 未覆盖 case 使用的实体表 | 拒绝生成，补齐 `subject/episode/person/character` 等来源表 |
| case 数量不是 120 | 拒绝生成；不得用 placeholder ID 填充 |
| 无 ACTIVE release | 保持 `DEFINITION_ONLY`/`BLOCKED_NO_ACTIVE_RELEASE`，不得生成通过型 gate 报告 |

#### 5. Good/Base/Bad Cases

- Good：从真实 Subject、alias、关系和实体表查询结果生成 case，并保存结果 ID hash 与 SQL 模板。
- Base：只有定义集完成、release 尚未激活时，报告明确写出阻断原因。
- Bad：复制旧的经典作品 ID、把离线 mock 指标写成 120/120，或跳过真实 SQL 验证。

#### 6. Tests Required

- 断言生产数据集为 120 条、分类配额正确、evidence ID 唯一、快照和版本一致。
- 断言生成器在不足 120 条或 SQL 结果为空时拒绝写入。
- 真实 release 激活后再运行 Business → Vector Set → Evidence 回放，并断言五份报告版本一致。

#### 7. Wrong vs Correct

##### Wrong

```python
expected_subject_ids = [1, 2, 3]  # 复制旧 mock case，未绑定当前快照
```

##### Correct

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

### Java 注释质量

Java 后端统一遵循 [Javadoc 规范](./quality-guidelines.md#java-后端-javadoc-规范)，包括 pojo 全部字段、类型及手写成员。接口契约、实现继承说明与源码行为必须一致；字段行尾注释不满足 pojo 文档要求。方法体算法说明不冒充声明 Javadoc。

本规则是已确认的项目要求；2026-09-14 最终修复后，AST 检查 255 个 Java 文件、1658 个声明，违规 0，JDK doclint 通过。早期文本扫描的“缺失 0”结论已被替换，后续以可重复检查命令和人工语义审查为准。项目尚未配置自动覆盖门禁，审查仍须检查格式与契约真实性，普通测试通过不能替代文档检查。

### 代码审查清单

- 依赖方向符合 `directory-structure.md`，外部能力经 Gateway/Protocol 注入。
- API 路径、字段、错误码与 OpenAPI、前端 shared、Java/Python 路由保持一致。
- Agent 写操作仍需预览与确认，执行参数来自系统状态。
- 日志不包含敏感数据，traceId 跨 Spring ↔ Agent ↔ Business 回查可关联。
- Schema、事务、幂等和清理路径具有失败收尾与回滚方式。
- 待确认动作写入失败不得被裸 `except: pass` 隐藏；健康探针必须核对 Security 放行和匿名响应。

### 验证粒度

- Java 接口改动：至少运行 Maven，并手工核对 Controller → Service → Mapper。
- Agent 图/工具改动：运行 pytest，并验证 SSE start/delta/end 与断开路径。
- importer/indexer 改动：测试 dry-run、锁释放、断点续传或 fail-closed gate。
- 跨层改动：从浏览器 API 调用一路核对到存储，再核对返回类型。
- 配置改动：同步示例文件，确认日志不会打印真实密钥；若是 Java 配置迁移，补齐上述五类测试并运行 `mvn -B clean test`。

#### MyBatis 类型别名冲突

- 错误：在 `mybatis-plus.type-aliases-package` 扫描包中直接新增名为 `Character`、`String` 等与内置别名冲突的实体类，依赖默认简单类名注册。
- 正确：为业务实体显式指定不冲突别名，例如 `@Alias("BangumiCharacter")`，并保留 Mapper/XML 使用的全限定类名兼容。
- 验证：至少断言业务别名解析到实体类、内置别名仍解析到 JDK 类型，再运行 `mvn -B clean test`。

### Git 提交信息

- 首行使用 `.gitmessage` 约定：`<type>(<scope>): <中文描述>`，描述不超过 50 个字符；`type` 使用 `feat`、`fix`、`docs`、`style`、`refactor`、`perf`、`test`、`chore` 或 `ci`。
- 项目内 Trellis 自动提交也必须使用中文描述，例如 `chore(任务): 归档 xxx`、`chore: 记录开发日志`，不能保留英文 `archive` 或 `record journal`。
- 新克隆仓库首次提交前执行 `git config --local commit.template .gitmessage`；提交前用 `git log -1 --format=%s` 自检主题。

## Java 后端 Javadoc 规范

状态：规范已实施，2026-09-14 已完成存量声明修复及 AST/doclint 验证；适用于 backend/business 全部 Java 模块。新增或修改声明必须继续执行下述规则与检查。

### 覆盖范围

Java 声明统一使用 `/** ... */` Javadoc，采用中文说明。不得用普通块注释、声明上方单行注释或字段行尾注释替代声明文档。

| 声明 | 要求 |
|---|---|
| 类、接口、枚举、record、注解类型，含嵌套类型 | 说明职责与必要的使用边界 |
| 手写方法、构造器，含 private 方法和工具类私有构造器 | 说明行为；有参数、返回值和重要异常时补齐对应契约 |
| 手写字段、常量、枚举成员 | 说明含义；配置与数据字段补充单位、范围、空值或特殊值语义 |
| pojo 的 DTO/VO/Entity 全部字段 | 必须使用字段上方 Javadoc，不以注解 message 或行尾注释代替 |
| record 组件 | 在 record 的 Javadoc 中使用 `@param` 逐一说明 |

Lombok/编译器生成的构造器、访问器不要求手工重写来添加注释；需要说明的数据语义放在字段或类型上。手写测试代码同样遵循声明格式，测试方法说明验证的场景与预期。

Javadoc 紧邻声明，放在注解之前。方法体内的步骤、算法理由仍使用普通行注释，因为方法体中的 `/** ... */` 不会成为声明文档；不能将所有 `//` 机械替换成 Javadoc。这里区分注释用途，不豁免任何类型、字段或手写方法的声明说明。

### 内容密度与建议篇幅

采用“声明全覆盖，内容按复杂度写”：覆盖范围不缩减，但不要求每处都写长篇。简单字段一句即可；复杂业务接口写清调用者无法从签名判断的契约，避免为了行数复述代码。

| 对象 | 建议篇幅与内容 |
|---|---|
| 简单字段、依赖字段、常量 | 1 句说明含义；有单位、范围或特殊值时补充 |
| 普通类型 | 1–3 句说明职责与必要边界 |
| 简单方法、构造器 | 1 句摘要，加适用的参数、返回值和异常标签 |
| Service/Gateway 接口、Converter | 通常 5–12 行，优先写输入约束、结果与边界行为 |
| 复杂事务、认证、外部调用 | 按实际需要补充副作用、失败行为和幂等约束 |

以上是写作建议，不是最低行数、上限或自动检查阈值。超过约 15–20 行时，检查是否混入长期架构背景或逐步实现说明：架构决策放到对应 spec，声明旁保留使用该声明所需的契约。不能为了缩短注释省略必要标签或边界。

简单声明允许单行 Javadoc，仍放在注解之前：

```java
/** 条目 ID。 */
@NotNull(message = "条目 ID 不能为空")
private Long subjectId;

/** 图片存储网关。 */
private final ImageStorageGateway imageStorageGateway;
```

上述片段仅示意声明格式；不得由示例推断其他字段也必填。拒绝“执行更新业务流程”“数据对象中的 type 属性”等机械模板，不逐行解释赋值或循环。方法体注释重点解释不明显的原因、取舍和算法约束，继续使用普通行注释。

### 按职责选择说明重点

以下是审查关注点，只记录源码和测试证实的行为；不为每个声明机械填满所有项目。

| 位置 | 应优先核对并说明 |
|---|---|
| pojo DTO/VO/Entity | null 是未提供、清空还是保留原值；编码与特殊值、分页起点、时间单位 |
| client/admin Service 接口 | 数据归属与权限前提、无结果行为、重要业务异常、写操作副作用 |
| 各模块 Converter | null 与空集合行为、顺序、嵌套字段、是否修改源对象；遵守纯映射边界 |
| infrastructure 与 agent Gateway | Redis 过期时间单位、限流窗口、上传限制、邮件或外部调用的失败反馈 |
| auth 与 log | 会话消耗或撤销语义、日志采集范围、敏感信息输出限制 |

接口承载公共契约，实现方法继承并补充必要差异；同一契约不复制维护两份。测试方法用一句话说明验证场景与预期。注释不替代权限校验、事务控制、序列化限制或测试。

### 统一内容与标签

- 首句简洁说明职责或行为，以中文句号结束；不要只把类名、字段名、方法名翻译一遍。
- `@param` 按签名顺序逐项说明参数及泛型参数；写明必要的取值、单位、可空性、缺省语义。
- 非 void 方法使用 `@return`，说明返回内容、无结果时返回 null/空集合等行为；构造器与 void 方法不写 `@return`。
- 使用 `@throws` 说明实际可发生且调用方需要处理的异常条件，包括重要业务运行时异常；同为 BizException 时写明相关错误类型和触发条件，不凭空补异常。
- 代码值、类型表达式和特殊字符用 `{@code ...}`，相关声明用 `{@link ...}`。多段说明使用 `<p>`，列表使用标准 HTML 列表，避免将 Markdown 围栏直接放进 Javadoc。

不强制 `@author`、`@since`、`@version`，不添加虚构作者、日期和版本。弃用声明使用 `@Deprecated`，并用 `@deprecated` 说明替代方式。标签必须与当前参数和实现同步，不能保留改名前的参数名或失效链接。

### 接口与实现

Service、Gateway 等接口是调用契约的主要位置：参数约束、返回语义、错误、副作用、幂等或事务边界等按实际行为说明。

实现方法在接口契约完整且适用时，使用显式 `/** {@inheritDoc} */`，避免复制一份后逐渐不一致；存在实现特有约束时，在继承说明后补充相应内容。没有可继承契约的方法，包括私有辅助方法和构造器，必须写自己的 Javadoc。

不得通过 `{@inheritDoc}` 掩盖上游接口缺失的文档；类型、字段和构造器不能以此替代自身说明。实现算法理由与局部步骤可在方法体内补充普通注释。

### pojo 字段契约

DTO/VO/Entity 均遵守以下内容规则，按实际适用项填写，不机械生成空模板：

- 枚举或数值编码：解释有效值与特殊值，例如收藏状态 1–5、评分 0 表示未评分。
- 可空字段：写清 null 是未提供、未知、清空还是保留原值；创建与更新语义不同时分别说明，不能只凭包装类型猜测。
- 时间、数值和分页：标明秒/毫秒、时区、起始页和取值范围等真实约束。
- 业务默认值与数据库默认值分开描述；校验注解、数据库映射和实际赋值存在差异时先核对，不编造一致性。
- 敏感字段和内部字段注明用途及输出限制；Javadoc 不替代实际序列化控制与权限校验。

示例依据现有 CollectionUpdateDTO.type，展示注释应放在校验注解之前：

```java
/**
 * 收藏状态，必填。
 *
 * <p>取值：1=想看，2=看过，3=在看，4=搁置，5=抛弃。
 */
@NotNull(message = "收藏类型不能为空")
@Min(value = 1, message = "收藏类型范围 1-5")
@Max(value = 5, message = "收藏类型范围 1-5")
private Integer type;
```

错误：`private Integer type; // 收藏状态`。正确：字段上方有完整语义的 Javadoc，校验注解继续保留。

### Converter 与方法示例

Converter 必须说明 null 输入、空集合、顺序、嵌套字段和副作用等实际行为。单对象 null 返回 null 与列表 null 返回空集合是不同契约，不能用同一套泛化描述。

以下仅展示已存在方法的声明文档，不是新增实现：

```java
/**
 * 将收藏与条目联合数据转换为用户收藏展示对象。
 *
 * <p>仅映射传入数据，不查询数据库或修改源对象。
 *
 * @param vo 收藏与条目联合数据，允许为 {@code null}
 * @return 新的收藏展示对象；输入为 {@code null} 时返回 {@code null}
 */
public static UserCollectionVO toUserCollectionVO(UserCollectionSubjectVO vo) {
    // 沿用现有方法体；此处省略。
}
```

该片段是注释格式示意，省略的方法体不能直接作为可编译实现。避免“执行转换”“获取数据”等没有额外信息的注释。

### 存量迁移与审查

先核对实现，再补全文档：pojo 行尾字段注释迁至字段上方；接口的一句话说明补齐参数/返回/错误；实现方法继承完整契约；私有方法和 Converter 补充自身语义。不能仅批量添加 `/** */` 外壳就认定规范化完成。

修改代码行为、字段、参数或返回类型时同步更新 Javadoc。存量声明已完成本轮修复与验证；新增或修改代码时同步维护 Javadoc，不因补注释改变接口行为。

| 检查 | 通过条件 |
|---|---|
| 覆盖 | 类型、手写成员和 pojo 字段符合声明文档要求 |
| 语法 | 标签正确、参数匹配、引用可解析、HTML 合法 |
| 真实性 | 空值、单位、错误、边界、副作用与实现及测试一致 |
| 继承 | 接口契约完整，覆盖方法显式继承或补充，未复制失效说明 |
| 维护 | 不含空模板、无意义复述、虚构异常或历史作者信息；篇幅与复杂度匹配，不为满足行数重复契约 |

### 可重复的声明与语法检查

在仓库根目录执行：

```bash
# 先完成 Java 完整回归，再校验文档
mvn -B clean test -f backend/business/pom.xml
python backend/business/tools/check_javadoc.py
python backend/business/tools/test_check_javadoc.py
```

`check_javadoc.py` 使用 JDK 21 语法树遍历全部 Java 源码（含测试和工具，排除 target），检查类型、手写构造器、字段、方法、record 组件的声明文档，以及参数顺序、返回标签、中文摘要和已知机械模板。继承文档只允许出现在显式覆盖的方法上。随后读取 app 的 Surefire 报告中实际构建类路径，运行 JDK `javadoc -private -Xdoclint:all,-missing -Werror`，校验 HTML、标签语法和引用；缺失检查由前一阶段执行，避免 Lombok 生成成员导致误报。任一阶段失败都返回非零。

结果写入 `backend/business/target/javadoc-check/coverage.txt` 与 `doclint.txt`；HTML 文档和参数文件也位于该临时目录。`clean` 会清理报告，交付记录需保存日期、命令和结果摘要。检查器回归覆盖中文和 record、私有构造器和枚举、参数/返回错配、继承限制、模板及损坏源码。

该命令是提交前独立检查，尚未接入 Maven 默认生命周期或 CI。自动检查不证明业务语义、异常条件或数据单位正确，也不能穷举无意义表述；仍需对照实现和测试人工审查。纯注释修改不机械新增业务单元测试；检查器自身的正反例用于证明门禁能发现已知遗漏。

语法依据：[JDK 21 标准 Javadoc 规范](https://docs.oracle.com/en/java/javase/21/docs/specs/javadoc/doc-comment-spec.html)。覆盖范围、中文风格和审查要求是本项目约定。

注释编辑必须以语法树定位或逐处核对，不能用跨行正则将字符串中的路径通配符误当注释起点。批量编辑后先运行声明/Java 语法检查，再进行完整构建；不得在最后一次验证后继续修改代码而沿用旧通过记录。
