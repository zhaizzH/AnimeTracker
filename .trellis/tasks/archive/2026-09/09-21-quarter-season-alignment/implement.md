# 执行计划：季度/档期映射跨层对齐

前置：用户已批准规划摘要；当前在 `feat/write-confirmation-hard-gate`（工作树干净）。

## 0. 分支与任务激活

```bash
git checkout -b feat/quarter-season-alignment   # 叠在 T3 之上，保持堆叠拓扑
python ./.trellis/scripts/task.py set-branch 09-21-quarter-season-alignment feat/quarter-season-alignment
python ./.trellis/scripts/task.py validate 09-21-quarter-season-alignment
python ./.trellis/scripts/task.py start 09-21-quarter-season-alignment
```

（Windows 下 python 命令前加 `PYTHONIOENCODING=utf-8 PYTHONUTF8=1`。）

## 1. 代码改造（按序）

1. 新建 `backend/agent/app/rag/seasons.py`：`SEASON_QUARTERS={"winter":1,"spring":2,"summer":3,"autumn":4}` + `season_month_range(season)`（由季度号派生 `(3q-2, 3q)`），模块 docstring 写明权威来源（SeasonUtil + MySQL QUARTER()）。
2. `app/rag/retrieval.py`：删 `:17` `_QUARTERS`；`:520`、`:797`、`:969-970` 改引用 `SEASON_QUARTERS`。
3. `app/adapters/redis/subject_index.py:239`：内联 dict 改 `SEASON_QUARTERS[query.quarter]`。
4. `jobs/indexer/shadow_eval.py:153-159`：`quarter_bounds` 改 `season_month_range(query.quarter)`。
5. `jobs/importer/main.py:55-60,343-345`：删 `SEASON_MONTHS`；校验键集与取月份段改经 `app.rag.seasons`。
6. `app/rag/query_planner.py:27-32`：保留季节词标记；"第N季度/几季度/QN" 标记改从 `SEASON_QUARTERS` 派生（Q1→winter…Q4→autumn）。
7. `tests/evals/generate_golden_cases.py:232`：autumn 证据参数 `3→4`（不动已入库 JSON 快照）。

## 2. 测试

1. 新建 `tests/rag/test_season_alignment.py`（四组：词表/Java 源码解析/QUARTER() 公式/六处消费方一致性，见 design.md）。
2. 更新 `tests/jobs/indexer/test_shadow_eval.py:30-31,40-43` 为权威月份段。
3. 更新 `tests/rag/test_query_planner.py:18-23`："Q4" 期望 winter→autumn，补 Q1→winter。
4. 更新 `tests/rag/test_evidence_contract.py:220`：quarter `spring→winter`（保持 2024-01-01 季内语义，测试意图不变）。

## 3. 验证命令

```bash
cd backend/agent
uv run pytest tests/rag/test_season_alignment.py -q          # 新回归
uv run pytest tests/jobs/indexer/test_shadow_eval.py tests/rag/test_query_planner.py tests/rag/test_evidence_contract.py -q
uv run pytest -q                                              # 全量（基线 351 passed + 新增）
```

残留检查（应只剩 `app/rag/seasons.py` 一处数字映射）：

```bash
grep -rn "_QUARTERS\|SEASON_MONTHS\|quarter_bounds" backend/agent/app backend/agent/jobs
grep -rn "'spring': 1\|\"spring\": 1\|spring.*(1, 3)" backend/agent/app backend/agent/jobs
```

## 4. 质量检查 → spec 同步 → 提交（Phase 2.2 / 3.3 / 3.4）

- trellis-check：spec 符合性 + 跨层一致性（加载 `.trellis/spec/backend/rag-retrieval-contract.md`、`agent-guidelines.md`、`guides/cross-layer-thinking-guide.md`）。
- spec 同步（随代码同批提交，属本任务的持久契约变化）：
  - `rag-retrieval-contract.md:26-29`「日期与状态的已知偏差」季度段 → 改为已对齐事实 + 词表位置（`app/rag/seasons.py`）+ 回归测试锚点。
  - `guides/cross-layer-thinking-guide.md:99`「当前两端映射不一致」→ 更新为一致，保留"季度映射须核对 Java SeasonUtil 与 Python 词表"的检查动作。
- 提交计划（Phase 3.4 一次性确认）：
  1. `fix(agent): 季度映射对齐权威动漫季约定(winter=1..autumn=4)` — seasons.py + 5 消费方 + 3 测试更新 + 新回归测试 + 生成器修正 + 2 处 spec。
  2. `chore(trellis): finalize 09-21 季度映射跨层对齐` — 任务簿记（task.json/journal 等，随 finish-work 一批）。
- 完成后提醒 `/trellis:finish-work`。

## 回滚点

- 步骤 1-2 任一环节出错：`git checkout -- backend/agent` 即可，无 DB/索引/配置副作用。
- 全量测试若出现预期外失败：先确认是否漏改手写映射（步骤 3 的 grep），再决定是否回滚重审设计。

## 风险文件

- `app/rag/retrieval.py`（3 处引用点分散，注意 `:969-970` 字符串分支语义）
- `tests/rag/test_evidence_contract.py`（只许改标签，不许动测试结构/意图）
- `app/rag/query_planner.py`（标记派生逻辑不得改变"恰好 1 个命中才落字段"的匹配语义）
