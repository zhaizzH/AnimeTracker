# Agent 配置与 env 漂移修复

## Goal

`backend/agent` 的配置模板（`.env.example`）、`Settings` 声明与文档三者在多处互相漂移：模板含已删除键导致照抄即启动失败；共享 `.env` 中多个 jobs 专用键未声明，写进去同样致命；两个 route 模型变量被声明且被文档要求，却在显式 `LLM_PROVIDER` 路径被静默忽略；画像向量链用配置版本猜测在线索引版本，版本漂移时个性化静默降级。本任务把这三方对齐，并让画像向量链改用权威激活版本。

## Background（本会话已核实）

证据均为本会话实测或源码直读，非文档转述。

| # | 缺陷 | 证据 | 当前表现 |
|---|---|---|---|
| D1 | 模板含已删除的 `RAG_INDEX_ALIAS` | `.env.example:43`；`app/config.py:44` 注释「Redis alias was removed」 | **致命**：`extra="forbid"` 下照抄模板启动即 `ValidationError: extra_forbidden`（已实测复现） |
| D2 | 6 个 jobs 专用键未在 `Settings` 声明 | `RAG_PROFILE_VERSION`(indexer/main.py:709, importer/quality.py:321)、`SEARCH_INDEX_LEASE_SECONDS`(indexer/search_repository.py:24)、`BACKFILL_BATCH_SIZE`/`BACKFILL_MAX_BATCHES`(scheduler/main.py:90-91)、`BUSINESS_BASE_URL`(indexer/shadow_eval.py:334)、`RAG_TRUSTED_TAG_MIN_COUNT`(importer/repository.py:101, indexer/repository.py:62) | **潜在致命**：`jobs/*` 只 `load_dotenv()` + `os.getenv`，不 import `Settings`，故当前可用；但运维若把这些键写进共享 `.env`，Agent 启动即崩（与 D1 同一机制，已实测复现） |
| D3 | 模板缺 2 个 route 模型键 | `.env.example` 无 `DEEPSEEK_MODEL_ROUTE`/`DASHSCOPE_MODEL_ROUTE`；`app/config.py:20,14` 有声明；`README.md:309,312` 已把它们写成必配项 | 模板与文档不一致 |
| D4 | 显式 `LLM_PROVIDER` 路径忽略 route 模型 | `app/config.py:124` 传 `route_model=s.deepseek_model`、`:132` 传 `route_model=s.dashscope_model`（应为 `*_model_route`）；`app/adapters/llm/agent_factory.py:126` 实际消费 `resolved.route_model` 作兜底 | **静默错误**：实测 `model='MODEL-X' route_model='MODEL-X'`（显式路径）对比 `route_model='ROUTE-Y'`（key 兜底路径，`config.py:101,107` 正确） |
| D5 | 画像向量链用配置版本而非激活版本 | `backend/agent/main.py:172` 硬编码 `f"rag:vectors:SUBJECT:{settings.rag_index_version}"`；权威指针在 `app/adapters/mysql/release_store.py:22-31`（MySQL `search_index_release` ACTIVE） | **静默降级**：release 激活新版本后，`_subject_vector_lookup` 仍读旧版本 key，`VEMB` 取不到向量 → 画像构建失败 → 个性化静默失效 |
| D6 | 模板注释过期 | `.env.example:38`「RAG 索引需 RediSearch/Redis Stack」、`:41`「可单独配置启用 RediSearch 的索引 Redis」 | 实际依赖为 Redis 8 Vector Set（`app/config.py:44`、`README.md:250`） |

补充事实：

- Vector Set key 后缀确为 `index_version`：`jobs/indexer/gate.py:280` 打印 `rag:vectors:SUBJECT:{args.index_version}`，测试断言 `rag:vectors:PERSON:v-test`（`tests/jobs/indexer/test_main_multi_entity.py:375`）。故 D5 的目标版本可直接取 `search_index_release.index_version`。
- spec 自身已判定「禁止使用 `RAG_INDEX_VERSION` 猜测在线版本」：`.trellis/spec/backend/rag-retrieval-contract.md:79`；缺口表 `:20` 明确记录画像链「仍可能与 active release 不同」。
- 主检索链**不是**本任务范围：`app/rag/retrieval.py:168-170` 已从 Business lexical 响应取 `indexVersion` 并在缺失时拒绝查询，符合 `rag-retrieval-contract.md:79,96`。本任务只修画像链。
- 文档把 D1/D2 当作已知问题反复标注但未修：`README.md:245,336,434`、`backend/README.md:104,231`、`backend/agent/README.md:334,373,476,517`、`jobs/importer/README.md:48,125`，以及 `rag-retrieval-contract.md:34`。其中 `README.md:434` / `backend/README.md:231` / `agent/README.md:517` 三处均写「未直接修改，建议同步修正」。

## Requirements

### R1 模板与 `Settings` 对齐（消除致命键）

- 从 `.env.example` 删除 `RAG_INDEX_ALIAS`。
- 补入 `DEEPSEEK_MODEL_ROUTE`、`DASHSCOPE_MODEL_ROUTE`（默认值与 `app/config.py:20,14` 一致）。
- 补入 R2 新增的透传键，使模板成为「可照抄即启动成功」的完整集合。

### R2 关闭 jobs 专用键这一类 landmine

- 在 `app/config.py::Settings` 的既有 `# ponytail:` 透传块中，声明 6 个 jobs 专用键（默认值与各 `os.getenv` 兜底值逐一对齐）：`rag_profile_version`、`search_index_lease_seconds`、`backfill_batch_size`、`backfill_max_batches`、`business_base_url`、`rag_trusted_tag_min_count`。
- 语义：Agent 不读取这些值，仅为容身共享 `.env`；`jobs/*` 继续走 `os.getenv`，其行为不得改变。
- `extra="forbid"` 保持不变（保留对 Agent 自身变量拼写错误的捕获能力）。
- 注：`business_base_url` 与既有 `backend_base_url` 语义不同（前者是 indexer 影子评估的默认业务地址），两者并存，不得合并。

### R3 修复 route 模型被忽略

- `resolve_llm_provider` 的两条显式分支改用 `deepseek_model_route` / `dashscope_model_route`。
- key 兜底分支（`:101,107`）已正确，保持不动。
- 行为判定：显式指定 `LLM_PROVIDER` 时，`route_model` 必须等于对应 `*_MODEL_ROUTE` 的取值，而不是 `*_MODEL`。

### R4 画像向量链改用权威激活版本

- `_subject_vector_lookup` 不再用 `settings.rag_index_version` 拼 Vector Set key，改为使用 MySQL `search_index_release` 的 ACTIVE `index_version`。
- 版本解析必须 fail-safe：解析失败（MySQL 不可达、无 ACTIVE release、返回非法值）时返回 `None`，不得抛出、不得中断 Agent 启动或请求。
- 版本解析失败导致的个性化缺失必须**可观测**（告警日志 + 既有 `personalizationNotice` 通道），不得静默当作「无个性化需求」。
- 「禁止用 `RAG_INDEX_VERSION` 猜测在线版本」这条 spec 契约必须继续成立。

### R5 文档与注释同步

- 更新 `.env.example` 中过期的 RediSearch / Redis Stack 注释（D6）。
- 更新 `README.md` / `backend/agent/README.md` 中「已知不一致、未修改」的失效警告段落——修完后这些警告必须删除或改写为已修复陈述，否则文档重新变成谎言。
- `rag-retrieval-contract.md:20`（画像链缺口行）与 `:34`（模板漂移行）随实现更新。

## Acceptance Criteria

- [ ] **AC1** 以 `.env.example` 为 `.env` 直接启动 Agent（无额外变量）不再出现 `extra_forbidden`；`RAG_INDEX_ALIAS` 不出现在模板中。
- [ ] **AC2** 新增自动化测试：对 `.env.example` 全量键做「模板键 ⊆ `Settings` 字段」的断言，任何未来新增的未声明键都会让该测试失败。测试以真实文件为输入，不复制键列表。
- [ ] **AC3** 覆盖 D2 的 6 个键各一条用例：这些键存在时 `Settings()` 构造成功；且断言它们确实是透传字段（Agent 侧无读取点）。
- [ ] **AC4** 自动化测试断言：`LLM_PROVIDER=deepseek` 且 `DEEPSEEK_MODEL_ROUTE` 与 `DEEPSEEK_MODEL` 取不同值时，`resolve_llm_provider(...).route_model == DEEPSEEK_MODEL_ROUTE`；dashscope 同理；key 兜底路径行为不变。
- [ ] **AC5** 画像向量链测试：当 ACTIVE release 版本与 `settings.rag_index_version` 不同时，`_subject_vector_lookup` 查询的 key 使用 **ACTIVE 版本**；无 ACTIVE release / MySQL 不可达时返回 `None` 且不抛异常，同时产生告警。
- [ ] **AC6** 既有测试不回归：`uv run pytest`（`backend/agent`）全绿；基线为 `index.md:50` 记录的 413 passed。
- [ ] **AC7** 文档不再含「`RAG_INDEX_ALIAS` 未修、需手动删除」类失效警告；三端 env 表格与 `Settings` 实际字段一致。

## Out of Scope

- 不改 `extra="forbid"` 策略本身（不改为 `ignore`）。
- 不改 `jobs/*` 的取值逻辑与默认值；本任务只做「声明容身」，不做 jobs 配置体系重构。
- 不修主检索链的 `indexVersion` 处理（`retrieval.py` 已正确）。
- 不给 Agent 增加 `profileVersion` 的独立校验（`rag-retrieval-contract.md:19` 记录为另一处债务，归后续任务）。
- 不做配置项的统一重命名（如 `business_base_url` vs `backend_base_url` 的收敛）。

## Notes

- **复杂任务**：`task.py start` 前需 `design.md`（版本解析放置点、缓存与 fail-safe 策略、D2 字段类型取舍、测试落点）与 `implement.md`（有序清单、验证命令、回滚点）。
- 本任务与 `09-21-rag-correctness-evidence-airstatus` 无交叠：后者改 `retrieval._enrich_evidence` 与 air-status 推断，本任务只碰 `main.py` 的画像链。
- 已定产品决策（本会话确认）：采用「声明透传字段」而非文档警告或放宽 `extra`；D4 纳入本任务而非另开任务。
