# 0010 — 主创关系单表 + 生成列 `dedup_key`，允许未解析占位行

- **状态**：accepted
- **记录日期**：2026-10-12
- **相关规范**：[backend/database-guidelines.md](../backend/database-guidelines.md#scenario-主创关系单表-subject_person_credit)

## 背景

「作品—主创」关系有两种形态：Person 已解析（有 `person_id` FK）与未解析（只知道一个名字）。此外需要防重——同一条主创关系重复导入不应产生重复行。

## 决策

- **单表 `subject_person_credit`** 表达两种行形态：已解析行写 `person_id` FK、`name` 为 NULL；未解析行 `person_id` 为 NULL、`name` 存占位名。旧兼容表 `subject_credit` 已删除。
- 去重依赖 **`dedup_key char(64)` 生成列**：对 `subject_id/role/person_id/name` 拼接后取 sha256 定长哈希，配唯一索引。用定长哈希而非明文拼接，是为了避免生成列长度受拼接字段的隐式约束（真实踩过 MySQL 严格模式的 1406 截断）。

## 备选方案

1. **拆两张表（已解析 / 未解析）。** 未采纳——摘要与查询要 UNION 两表，且「同一关系从占位升级为 FK」会跨表迁移。
2. **单表 + 明文拼接 dedup key。** 未采纳——拼接字段长度一变，生成列长度就可能溢出；分隔符也可能与字段内容冲突。
3. **单表 + sha256 生成列（采纳）。**

## 后果

**正面**

- 两种行形态由列值表达，摘要查询单表即可（`IFNULL(person.name, spc.name)`）。
- 去重键定长、无分隔符歧义、长度与拼接字段解耦。

**代价与陷阱**

- **没有代码会把占位行提升为 FK 行**：占位行靠下一次 full import 自愈——届时写入的是 `dedup_key` 不同的 FK 行，与旧占位行并存，而函数开头的 `UPDATE ... SET source_active=0` 会把旧占位行标为失效。因此同一 credit 可能短暂存在「一条 inactive 占位行 + 一条 active FK 行」，摘要按 `source_active=1` 过滤只读后者。
- **不存在 backfill 回填路径**，不要再假设有。

**约束**

- 改 `dedup_key` 拼接字段时必须**同步改生成列表达式**，否则唯一索引语义失真。
- 不得新建第二张 credit 表或双写。
