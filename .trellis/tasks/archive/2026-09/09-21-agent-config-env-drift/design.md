# 技术设计：Agent 配置与 env 漂移修复

对应 `prd.md` 的 R1–R5。本文只记技术决策与取舍，需求与验收标准在 PRD。

## 1. 边界与影响面

改动集中在两个文件加文档，不触及检索算法：

| 文件 | 改动 |
|---|---|
| `backend/agent/app/config.py` | 透传块新增 6 字段；`resolve_llm_provider` 两条显式分支改用 `*_model_route` |
| `backend/agent/main.py` | lifespan 解析 ACTIVE release 版本；`_subject_vector_lookup` 接受版本参数 |
| `backend/agent/.env.example` | 删 `RAG_INDEX_ALIAS`；补 2 个 route 键与 6 个透传键；修 RediSearch 注释 |
| `backend/agent/README.md`、`README.md`、`backend/README.md` | 删除失效警告段落；env 表补全 |
| `.trellis/spec/backend/rag-retrieval-contract.md` | 更新缺口表 `:20` 与模板漂移 `:34` |
| 新增测试 | `tests/test_env_template_contract.py`、`tests/rag/test_profile_vector_version.py`、`tests/test_llm_route_model.py` |

**不受影响**：`jobs/*` 的取值逻辑（继续 `os.getenv`）；`app/rag/retrieval.py` 主检索链的 `indexVersion` 处理（已正确，`retrieval.py:168-170`）；`extra="forbid"` 策略。

## 2. D1/D2/D3：模板与 `Settings` 对齐

### 2.1 透传字段的类型取舍

6 个新字段全部声明为 `str`，**不用** `int`/`bool`：

```python
# ponytail: jobs(索引器/调度/回填) 专用，仅为容身共享 .env；Agent 不读取，由 jobs 自行 str→数值转换
rag_profile_version: str = "subject-profile-v1"
search_index_lease_seconds: str = "300"
backfill_batch_size: str = "50"
backfill_max_batches: str = "10"
business_base_url: str = "http://127.0.0.1:8080"
rag_trusted_tag_min_count: str = "100"
```

理由：若声明为 `int`，非法值（如 `BACKFILL_BATCH_SIZE=abc`）会变成 **Agent 启动失败**，而它只该影响 scheduler 作业。透传字段的职责是「容忍键存在」，不应把 jobs 的取值有效性耦合到 Agent 启动。这与既有透传块（`animetracker_log: str = ""`）一致。

默认值逐一对齐各 `os.getenv` 兜底值，避免「声明默认值 ≠ jobs 实际默认值」制造新的漂移源。

### 2.2 `business_base_url` 与 `backend_base_url` 并存

前者是 `jobs/indexer/shadow_eval.py:334` 的 `--business-url` 默认值（`http://127.0.0.1:8080`），后者是 Agent 自身 `BACKEND_BASE_URL`（`http://localhost:8080`）。**必须保持两个独立字段、各自默认值**，不得合并或复用——同名合并会让其中一个静默走错地址。这是本设计最容易被后续维护者「顺手清理」掉的一点，需在代码注释中写明。

### 2.3 `extra="forbid"` 保持

不放宽为 `ignore`。理由：Agent 自身变量（`DEEPSEEK_MODEL` 等）拼错时能被启动拦截，这是当前刻意收紧的设计意图；D2 走「显式声明」而非「放宽校验」正是为了同时保住这两个属性。

### 2.4 防回归测试（AC2）

新增 `tests/test_env_template_contract.py`：

```python
# 以真实文件为输入，不复制键列表，避免测试自己成为第二个漂移源
tpl_keys = parse_keys(Path(".env.example"))
settings_fields = {f.upper() for f in Settings.model_fields}
assert tpl_keys <= settings_fields, tpl_keys - settings_fields
```

断言方向是「模板键 ⊆ Settings 字段」：模板出现未声明键即失败。反向（Settings 有而模板无）不作为失败条件，因为 `*_MODEL_ROUTE` 这类字段在补齐后本就应在模板中，但若未来有纯内部字段（如 `animetracker_log`）不在模板也属合理。`animetracker_log` 也正是反向不设断言的原因。

## 3. D4：route 模型被忽略

`app/config.py:124` 与 `:132` 两处：

```python
# 现在（错）        route_model=s.deepseek_model
# 改为              route_model=s.deepseek_model_route
```

`:101` / `:107` 的 key 兜底路径已经正确传 `s.deepseek_model_route` / `s.dashscope_model_route`，**保持不动**。

判定语义（写入测试）：显式指定 `LLM_PROVIDER` 时，`route_model` 来自 `*_MODEL_ROUTE`；未指定时，两条路径都必须给出 `*_MODEL_ROUTE`，即「无论走哪条路径，route 模型都只由 `*_MODEL_ROUTE` 决定」。当前显式路径返回值等于 `*_MODEL` 是明确 bug，非有意设计。

## 4. D5：画像向量链改用权威激活版本

### 4.1 决策：启动时读 MySQL release（方案 A）

在 `_build_agent_dependencies` 中 `settings.rag_enabled` 为真时解析一次，闭包捕获：

```python
version = _resolve_active_index_version()   # 见 4.2
preference_provider = RedisUserPreferenceProvider(
    rag_redis, business=business, vector_lookup=_subject_vector_lookup(rag_redis, version))
```

`_subject_vector_lookup(rag_redis, index_version)` 在 `index_version` 为 `None` 时直接返回 `None`，不再执行 `VEMB`。

复用 `app/adapters/mysql/release_store.py::MySqlReleaseStore.active_version()`，接线方式照 `jobs/indexer/gate.py:287-296` 既有模式（`get_engine(...)` + `lambda: Session(engine)`）。引擎在函数内构造，不引入模块级全局。

### 4.2 fail-safe

```python
def _resolve_active_index_version() -> str | None:
    try:
        engine = get_engine(settings.db_host, settings.db_port, settings.db_user,
                            settings.db_password, settings.db_name)
        version = MySqlReleaseStore(lambda: Session(engine)).active_version()
    except Exception as exc:
        logger.warning("RAG active release 版本解析失败，个性化降级: %s", repr(exc))
        return None
    if not _is_valid_version(version):     # 空串/含 ':'/含空白 -> 非法
        logger.warning("RAG active release 版本非法: %r，个性化降级", version)
        return None
    return version
```

- 任何异常一律吞掉并返回 `None`，**绝不**中断 lifespan 或请求（与 PRD R4 一致）。
- 合法性校验参照 `release_store.activate()` 已有的同款约束（`release_store.py:34`：非空、不含 `:`、不含空白）。这条校验必要：版本串直接拼进 Redis key，含 `:` 会破坏 `rag:vectors:SUBJECT:{version}` 的 key 结构（`validate_version` 同族约束见 `app/adapters/redis/vector_set.py:30`）。
- 不抛异常的同时必须**可观测**：`logger.warning` 是「版本解析失败」与「用户本就无收藏」的唯一区分手段（两者在既有 `personalizationNotice` 通道上同形，见 4.4）。

### 4.3 与 spec 契约的一致性

`rag-retrieval-contract.md:79` 的「禁止使用 `RAG_INDEX_VERSION` 猜测在线版本」在本设计下**继续成立且被强化**：Agent 不再保留任何基于配置的版本猜测，画像链与主检索链一样以权威指针为准，只是主链经 Business lexical 响应、画像链直接读同一张表的同一事实（`search_index_release`，`database-guidelines.md:9` 已明示其为「唯一 active release 事实」）。

实现后需把 `rag-retrieval-contract.md:20` 从「缺口」改为「已对齐」，并说明画像链取版本的方式与主链不同、为何可接受。

### 4.4 可观测性的已知局限（记录，不在本轮解决）

版本解析失败与「用户无收藏/无足够样本」当前共用 `missing=True` → `personalizationNotice`，Agent 无法向用户区分两者。本轮通过 `logger.warning` 在运维侧区分，不改 `personalizationNotice` 的对外语义（改它会牵动 Prompt 与前端契约，超出本任务）。此局限写入 `rag-retrieval-contract.md` 缺口表。

### 4.5 已接受的取舍

| 取舍 | 后果 | 为何接受 |
|---|---|---|
| 启动时解析一次，非每请求 | release 切换后需重启 Agent 才生效 | 画像本就以 `_CACHE_TTL_SECONDS = 24h` 缓存（`user_preference.py:13`），向量读取的新鲜度量级远低于请求级；重启也是 release 切换的既有操作习惯 |
| 新增 Agent 启动时对 MySQL 的依赖 | 无 ACTIVE release 时个性化永久降级 | fail-safe 已保证不崩；且该状态本来就是「RAG 不可用」，降级为正确行为（`rag-retrieval-contract.md:95`） |
| Agent 直连 MySQL 读发布指针 | 与「Agent 经 Business 取业务数据」的一般倾向不同 | `app/adapters/mysql/` 是既有架构位（`directory-structure.md:251`），`MySqlReleaseStore` 就是为此存在；不新增跨层契约，也不增加 Business 端点 |

**替代方案 B（经 Business lexical 响应取版本）被否决**：需把版本穿过 `user_profile.py:48::build_preference` 的纯同步签名，或让 `RedisUserPreferenceProvider.load` 多发一次 Business 往返；后者给 recommend 路径增加失败面，收益仅是「版本更新鲜」，而 4.5 第一条已论证新鲜度不是瓶颈。

## 5. 测试设计

| 文件 | 覆盖 | 方式 |
|---|---|---|
| `tests/test_env_template_contract.py` | AC1/AC2/AC3 | 解析真实 `.env.example`；D2 六键各一条「存在即构造成功」；断言 Agent 侧无读取点（grep 源码） |
| `tests/test_llm_route_model.py` | AC4 | 显式 deepseek/dashscope 与 key 兜底四组合，断言 `route_model` 只由 `*_MODEL_ROUTE` 决定 |
| `tests/rag/test_profile_vector_version.py` | AC5 | 替身 release store：版本 ≠ `settings.rag_index_version` 时断言 key 用 ACTIVE 版本；无 ACTIVE / 抛异常 → `None` 且不抛；非法版本串 → `None` |

测试落点说明：`tests/` 下**当前无 `test_config*.py`**，故新建顶层 `tests/test_env_template_contract.py` 与 `tests/test_llm_route_model.py`；`tests/rag/` 已有 7 个文件，画像链测试归入该目录（`tests/rag/test_evidence_contract.py` 是同类契约测试的先例）。`tests/` 无 `conftest.py`，故测试不依赖共享 fixture，各自构造替身。

## 6. 回滚

改动分三组、可独立回滚（`git revert` 单组提交即可）：

1. 模板与文档（R1/R3/R5）——纯文本，回滚无运行时影响。
2. `config.py` 透传字段 + route 修复（R2/R3）——回滚后行为回到 D4 的静默错误，但不会更差。
3. 画像链版本（R4）——回滚即回到「配置版本」旧行为，同样是降级而非故障。

**无数据库、无 schema、无接口契约变更**，故无迁移与兼容窗口问题。

## 7. 风险

| 风险 | 缓解 |
|---|---|
| AC2 的测试若写成硬编码键列表，会变成新的漂移源 | 明确要求以真实文件为输入；设计已写明断言方向 |
| 后续维护者把 `business_base_url` 与 `backend_base_url` 合并 | 代码注释写明并存原因（2.2）；测试断言两者默认值不同 |
| 启动时 MySQL 探测拖慢启动 | `active_version()` 单条索引查询；仅在 `rag_enabled=True` 时执行（`rag_enabled` 默认 false，`config.py:48`） |
| AC5 测试若用真实 MySQL 则不可 CI 化 | 用替身 release store 注入，不连真库 |
