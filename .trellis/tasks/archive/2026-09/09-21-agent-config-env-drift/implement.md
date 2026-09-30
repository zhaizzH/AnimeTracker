# 执行计划：Agent 配置与 env 漂移修复

对应 `prd.md`（R1–R5 / AC1–AC7）与 `design.md`（§1–§7）。所有命令在 `backend/agent` 下执行。

## 前置

- 基线：`uv run pytest` 应为 413 passed（`.trellis/spec/backend/index.md:50`）。
- 确认工作区干净：`git status --short` 只应含 `.trellis/tasks/**` 未跟踪项。

## 验证命令

```bash
cd backend/agent
uv run pytest                                     # 全量（交付前，AC6）
uv run pytest tests/test_env_template_contract.py tests/test_llm_route_model.py tests/rag/test_profile_vector_version.py -v   # 本任务新增用例
```

配置漂移的**端到端人工验证**（AC1，无法只靠单测覆盖「照抄模板能启动」）：

```bash
cd backend/agent
cp .env.example /tmp/env_probe/.env    # 照抄模板
python -c "from app.config import Settings; Settings(_env_file='/tmp/env_probe/.env'); print('OK')"
# 期望输出 OK；修复前此处为 ValidationError: extra_forbidden
```

## 执行清单

### 阶段 1：模板与 Settings 对齐（R1/R2/R3，AC1/AC2/AC3）

- [ ] **1.1** `app/config.py`：在既有 `# ponytail:` 透传块内新增 6 个 `str` 字段，默认值逐一对齐 `os.getenv` 兜底值（`design.md` §2.1）；`business_base_url` 处写明与 `backend_base_url` 并存的原因（§2.2）。
- [ ] **1.2** `app/config.py`：`resolve_llm_provider` 显式分支 `:124` / `:132` 改用 `*_model_route`（R3）；不动 key 兜底分支。
- [ ] **1.3** `.env.example`：删除 `RAG_INDEX_ALIAS` 行；补 `DEEPSEEK_MODEL_ROUTE` / `DASHSCOPE_MODEL_ROUTE`（值同 `config.py:20,14`）；补 6 个透传键；重写 `:38` / `:41` 的 RediSearch/Redis Stack 注释为 Redis 8 Vector Set（R5/D6）。
- [ ] **1.4** 跑端到端验证命令，确认照抄模板可构造 `Settings`（AC1）。
- [ ] **1.5** 新增 `tests/test_env_template_contract.py`：模板键 ⊆ `Settings` 字段；6 键各一条构造成功用例；断言 Agent 侧无读取点（AC2/AC3）。
- [ ] **1.6** 新增 `tests/test_llm_route_model.py`：四组合断言 `route_model` 只由 `*_MODEL_ROUTE` 决定（AC4）。
- [ ] **1.7** `uv run pytest tests/test_env_template_contract.py tests/test_llm_route_model.py -v` 通过。

**回滚点 A**：阶段 1 独立成组；`git revert` 后回到 D1–D4 原状，无运行时副作用。

### 阶段 2：画像向量链版本（R4，AC5）

- [ ] **2.1** `main.py`：新增 `_resolve_active_index_version()`，按 `design.md` §4.2 的 fail-safe 与合法性校验实现（复用 `MySqlReleaseStore.active_version()`、`get_engine` 接线照 `jobs/indexer/gate.py:287-296`）。
- [ ] **2.2** `main.py`：`_subject_vector_lookup(rag_redis, index_version)` 增加版本参数；`index_version is None` 时直接返回 `None`，不发 `VEMB`。
- [ ] **2.3** `main.py`：`_build_agent_dependencies` 在 `settings.rag_enabled` 分支内解析版本并传入（`main.py:137` 调用点）。
- [ ] **2.4** 新增 `tests/rag/test_profile_vector_version.py`：替身 release store 三场景——版本 ≠ 配置版本时 key 用 ACTIVE 版本；无 ACTIVE / 抛异常 → `None` 且不抛；非法版本串（含 `:`、空白、空串）→ `None`（AC5）。不连真库。
- [ ] **2.5** `uv run pytest tests/rag/ -v` 通过，确认既有 RAG 测试不回归。

**回滚点 B**：阶段 2 独立成组；回滚即回到「配置版本」旧行为（降级而非故障）。

### 阶段 3：文档与 spec 同步（R5，AC7）

- [ ] **3.1** `backend/agent/README.md`：删除 `:334` 的 `RAG_INDEX_ALIAS` 警告；env 表补 route 键与透传键；修正 `:250` 附近与模板注释相关的过期表述。
- [ ] **3.2** `README.md`（根）：改写 `:245` / `:336` 的已知不一致警告；`:434` 的「未直接修改，建议同步修正」改为已修复。
- [ ] **3.3** `backend/README.md`：改写 `:104` / `:231` 同款段落。
- [ ] **3.4** `jobs/importer/README.md`：改写 `:48` / `:125` 中「需删除该行」的操作指引（已无需手动删）。
- [ ] **3.5** `.trellis/spec/backend/rag-retrieval-contract.md`：`:20` 缺口行改为已对齐并说明画像链取版本方式；`:34` 模板漂移行改为已修复；缺口表补 §4.4 的 `personalizationNotice` 歧义局限。

### 阶段 4：交付验证

- [ ] **4.1** `uv run pytest` 全量通过（AC6），对照基线 413 passed 记录实际数字。
- [ ] **4.2** 逐条核对 AC1–AC7，把实际证据（命令 + 结果）写入完成说明；不得只标「已完成」。
- [ ] **4.3** `git diff` 自查：确认未误改 `jobs/*` 取值逻辑、未放宽 `extra`、未动 `retrieval.py`。

## 审查门禁

- 阶段 1 完成后：核对 AC1–AC4，重点确认 `.env.example` 与 `config.py` 字段集合一致、route 修复未影响 key 兜底路径。
- 阶段 2 完成后：核对 AC5，重点确认 fail-safe（异常不外泄）与「非法版本不入 key」两点。
- 全部完成后：`trellis-check` 子代理复核，再按 Phase 3.4 提交。

## 已知不做（防范围蔓延）

- 不把 `extra="forbid"` 放宽为 `ignore`（`design.md` §2.3）。
- 不改 `jobs/*` 取值逻辑与默认值。
- 不修 `retrieval.py` 主检索链（已正确）。
- 不给 Agent 增加 `profileVersion` 独立校验（`rag-retrieval-contract.md:19` 另一处债务）。
- 不收敛 `business_base_url` / `backend_base_url` 命名。
