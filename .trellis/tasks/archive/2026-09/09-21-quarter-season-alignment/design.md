# 设计：季度/档期映射跨层对齐

## 问题本质

权威约定是「动漫季 == 日历季度」：winter=1-3月(Q1)、spring=4-6月(Q2)、summer=7-9月(Q3)、autumn=10-12月(Q4)。Python 侧 5 处各自手写了错一季的映射（spring=Q1 起步），且 3 处测试把错误行为钉成预期。修法不是"改 5 个数字"，而是**建立唯一词表来源 + 全量改引用 + 源码级跨层回归**，让未来任何一端改动都会在 `uv run pytest` 里爆炸。

## 边界与不动点

- **权威侧不动**：Business `SeasonUtil.java`、MySQL `QUARTER()` 存储（`jobs/indexer/repository.py:127`）、已写入 Redis/RediSearch 的 quarter 属性（日历季度值）全部不变 → **无需重建索引**，本次修复是纯查询侧对齐。
- **wire 契约不动**：Agent↔Business 只传字符串标签（`spring|summer|autumn|winter`），数字季度永不跨进程。
- **`_item_quarter` 日历算法不动**（`retrieval.py:964-981` 的 `((month-1)//3)+1` 已正确）；仅其字符串分支引用的映射表随词表更新。

## 规范词表：新模块 `app/rag/seasons.py`

放置决策：候选是 `app/rag/schemas.py`（RetrievalQuery 所在）或新建 `app/rag/seasons.py`。选**新模块**，理由：

1. 消费方含 `jobs/importer/main.py`，它当前不 import pydantic 模型层；独立纯 Python 模块避免给导入链加 pydantic 权重，也避免 jobs↔app 耦合扩大。
2. 其余 4 个消费方（retrieval、subject_index、shadow_eval、query_planner）本就读 `app.rag.*`，import 路径自然。
3. `schemas.py` 保持"请求模型单一职责"，词表是领域知识不是请求结构。

模块内容（刻意最小）：

```python
SEASON_QUARTERS: dict[str, int] = {"winter": 1, "spring": 2, "summer": 3, "autumn": 4}

def season_month_range(season: str) -> tuple[int, int]:
    """由季度号派生月份段：(3q-2, 3q)，与 MySQL QUARTER() 同语义。"""
```

月份段**派生**自季度号而非第二张字面量表——消除"两个真相源"风险；回归测试用显式四季表格钉死派生结果。

## 数据流与消费方改造

```
用户文本 ──query_planner──> 标签(label) ──RetrievalQuery.quarter──┐
                                                                 │
  label→number:  retrieval._build_expression (RediSearch @quarter)│ 全部改读
                 subject_index._vector_filter  (Vector FILTER)    │ SEASON_QUARTERS
                 retrieval._matches_query_filters (Evidence 过滤)  │
  label→months:  shadow_eval.build_shadow_sql  (MONTH BETWEEN)    │ 改读
                 importer.parse_season_key     (--mode season)    │ season_month_range
  storage:       indexer QUARTER(air_date)  ◄── 不动，已是日历季度
```

1. `app/rag/retrieval.py`：删 `_QUARTERS`（`:17`），`:520`、`:797`、`:969-970` 改 `SEASON_QUARTERS`。
2. `app/adapters/redis/subject_index.py:239`：内联 dict 改 `SEASON_QUARTERS[query.quarter]`。
3. `jobs/indexer/shadow_eval.py:153-158`：`quarter_bounds` 字面量改 `season_month_range(query.quarter)`。
4. `jobs/importer/main.py:55-60`：`SEASON_MONTHS` 删除，`parse_season_key`（`:343-345`）改用 `season_month_range`；season 合法性校验用 `SEASON_QUARTERS` 的键集。
5. `app/rag/query_planner.py:27-32`：季节词（春季/春番…）保留；"第N季度/几季度/QN" 标记**从 `SEASON_QUARTERS` 派生**（q=1→winter、q=2→spring、q=3→summer、q=4→autumn），不再手写数字。匹配语义（恰好 1 个命中才落结构化字段）不变。
6. `tests/evals/generate_golden_cases.py:232`：`autumn` 的证据参数 `quarter: 3→4`。

## 跨层回归测试设计（核心交付）

新文件 `tests/rag/test_season_alignment.py`，分四组：

**A. 词表自身**：`SEASON_QUARTERS` 精确等于 `{winter:1, spring:2, summer:3, autumn:4}`；`season_month_range` 四季输出 == 显式表 `(1,3)/(4,6)/(7,9)/(10,12)`。

**B. Java 源码级对齐**（无需 JDK/Maven）：读取 `backend/business/client/src/main/java/top/zhaizz/client/util/SeasonUtil.java`（路径相对测试文件定位，parents 上溯到 repo root），正则解析 `case "xxx" -> new LocalDate[]{LocalDate.of(year, M1, ..), LocalDate.of(year, M2, ..)}`，断言：
- 四季 case 齐全；
- 每季 `(M1,M2)` == `season_month_range(season)`；
- `SEASON_QUARTERS[season]` == `((M1-1)//3)+1` == `((M2-1)//3)+1`（即与 MySQL `QUARTER()` 公式一致）。
Java 侧任何改动（哪怕只改一个月份）都会让本组失败——这是"跨层回归"的关键，也是 PRD 要求 6 的实现方式（相对运行 Java 单测，源码解析零环境依赖；`09-10-refresh-source-backed-specs` 已有源码锚定先例）。

**C. MySQL QUARTER() 语义对齐**：对 month=1..12，断言 `((month-1)//3)+1` 等于该月所属季节的 `SEASON_QUARTERS` 值；并抽查 `_item_quarter({"airDate": ...})` 四季各一个日期。

**D. 六处消费方一致性**：对四季参数化断言同一标签处处同值——
- `_vector_filter` 含 `.quarter == {n}`；
- `RagRetrievalService._build_expression` 含 `@quarter:[{n} {n}]`（用 dummy ports 构造 service，同 `test_evidence_contract.py` 模式）；
- `_matches_query_filters`（static）对季内/季外 airDate 的接受/拒绝；
- `build_shadow_sql` 参数 `quarter_month_from/to` == `season_month_range`；
- `parse_season_key("2026-<season>")` 月份段一致；
- `plan_retrieval_query` 对 `QN/第N季度/季节词` 文本解析到正确标签。

## 既有测试更新（钉住错误行为的 3 处）

| 文件 | 现状 | 改法 |
|---|---|---|
| `tests/jobs/indexer/test_shadow_eval.py:30-31,40-43` | autumn→(7,9) 等 | 改为权威月份段，断言值改从 `season_month_range` 语义来的显式表 |
| `tests/rag/test_query_planner.py:18-23` | "Q4"→winter | 期望改 autumn；补 Q1→winter 用例 |
| `tests/rag/test_evidence_contract.py:170-224` | airDate=2024-01-01 + spring 期望通过 | 标签 spring→winter（1 月属冬季），保持"结构化过滤在 Evidence 后执行"的原测试意图不变 |

## 兼容性 / 行为变化

- **检索结果变化（预期内的修复）**：带季度条件的 RAG 检索、新番/日程之外的结构化过滤，结果从"错一季"变为正确。这是本任务的目的。
- **importer 行为变化**：未来 `--mode season --key 2026-summer` 扫描 7-9 月（原来扫 4-6 月）。已入库条目不受影响（air_date 是事实数据，与扫描窗口无关）；scheduler quarterly_full 走 full 模式不受影响。
- **query_planner 行为变化**："Q1/第一季度" 现在解析为 winter（原 spring）。中文语境 "第N季度" == 日历 QN == 动漫季 winter/spring/summer/autumn，此变化是纠错。
- **无需重建索引**：存储侧 quarter 一直是 MySQL `QUARTER()` 日历值，与修复后的查询侧一致。
- **golden_cases.json 快照不动**：`DEFINITION_ONLY` 状态、单测只做结构校验；7 条 `filter_quarter_tag_*` 仍是旧参数，属于历史快照。下次 live shadow eval 前用修正后的生成器重放（运维动作，另起任务/会话）。

## 回滚

单一代码提交 + 簿记提交；回滚 = revert 代码提交即可，无 DB/索引迁移、无配置变更。

## 风险与缓解

- **风险**：`_item_quarter` 字符串分支（item 里 quarter 为英文标签字符串时）返回值变化。评估：Evidence/详情上游不产出英文标签字符串 quarter（Business 传数字或不传），分支仅为防御；变化方向是从错到对。缓解：D 组测试显式覆盖该分支。
- **风险**：漏改第 6 处手写映射。缓解：完成后 `grep -rn "spring.*1\|SEASON_MONTHS\|quarter_bounds\|_QUARTERS"` 验证词表外无残留；spec 同步记录词表位置。
- **风险**：Java 文件挪动导致 B 组测试路径失效。缓解：路径解析失败时测试报清晰错误信息（fail loud，不 skip）。
