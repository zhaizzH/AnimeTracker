# Phase 8 MySQL 迁移验证报告

日期：2026-09-05

## 验证范围

- 连接本机 MySQL，服务版本：`8.4.9`。
- 使用临时库 `anime_tracker_verify_20260905`，验证结束后已删除。
- 随后按用户明确授权，直接对本机业务库 `anime_tracker` 执行前向迁移；未创建备份。

## 场景与结果

1. 临时空库执行 `docs/database/db-schema.sql`：通过。
2. 临时库模拟旧版本：删除 Person/Character/任务新表，并移除旧表的 `source_active` 三列：通过。
3. 执行 `docs/database/migration-002-rag-entities.sql`：通过。
4. 立即重复执行同一迁移：通过，确认幂等。
5. 断言 9 张新增表、3 个 `source_active` 列存在：通过；临时库共 21 张表。

## 修复记录

初次执行发现 MySQL 8.4 不接受 `ALTER TABLE ... ADD COLUMN IF NOT EXISTS`（错误 1064）。迁移已改为 `INFORMATION_SCHEMA.COLUMNS` 检查 + `PREPARE` 动态 DDL；列已存在时执行 `SELECT 1` 空操作。

## 未覆盖

- 真实存量业务数据备份/恢复演练。
- Person/Character 详情回填、MinIO 对象写入和 Redis/Embedding 索引发布。

## 运行中业务库观察（2026-09-05）

- `anime_tracker` 前向迁移已完成：当前共 21 张表，9 张实体/RAG 新表均存在，`subject_alias`、`subject_meta_tag`、`subject_credit` 均已增加 `source_active`。
- 迁移脚本已在真实库重复执行一次，二次执行通过，确认幂等；迁移前已有的 `subject` 数据共 220 条，未执行破坏性初始化脚本。
- 该次真实库操作遵循用户“无需备份，直接修改”的明确授权；生产环境仍必须遵守数据库备份门禁。
- Business 重启后 readiness 与 liveness 均返回 HTTP 200；`POST /api/client/evidence/resolve` 的 `PERSON`、`CHARACTER`、`ACTOR` `[1]` 请求均返回 HTTP 200（当前无匹配时返回空数组）。
- 修复了 MySQL 8.4 `ONLY_FULL_GROUP_BY` 下 `DISTINCT + ORDER BY s.score` 的 3065 错误：三个实体扩展查询改为 `GROUP BY s.id, s.score`。
