# Phase 8 MySQL 迁移验证报告

日期：2026-09-05

## 验证范围

- 连接本机 MySQL，服务版本：`8.4.9`。
- 使用临时库 `anime_tracker_verify_20260905`，验证结束后已删除。
- 未连接或修改开发/生产业务库 `anime_tracker`。

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
