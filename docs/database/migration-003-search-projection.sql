-- ============================================================================
-- 前向迁移 003：MySQL FULLTEXT shadow 投影与 active release 指针
-- ============================================================================
-- 适用场景：已执行 migration-002 的存量库；只新增表，不执行初始化 schema。
-- 执行前：完成可恢复备份并记录目标库状态。重复执行安全：CREATE IF NOT EXISTS。
-- 回滚：停止 lexical/indexer 使用后，按依赖顺序 DROP search_index_release、
-- search_document；不删除 subject 或其它事实表。

CREATE TABLE IF NOT EXISTS `search_document` (
  `id` bigint NOT NULL AUTO_INCREMENT COMMENT '投影行 ID',
  `entity_kind` varchar(16) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci NOT NULL COMMENT '实体类型: SUBJECT/EPISODE/PERSON/CHARACTER',
  `entity_id` bigint NOT NULL COMMENT '本地实体 ID',
  `index_version` varchar(32) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci NOT NULL COMMENT '索引版本',
  `profile_version` varchar(32) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci NOT NULL COMMENT '档案模板版本',
  `title` varchar(255) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci NOT NULL DEFAULT '' COMMENT '全文标题',
  `aliases` text CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci NULL COMMENT '全文别名串',
  `lexical_text` mediumtext CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci NULL COMMENT '全文规范化文本',
  `content_hash` char(64) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci NOT NULL COMMENT '档案内容哈希',
  `source_active` tinyint(1) NOT NULL DEFAULT 1 COMMENT '来源事实是否活跃',
  `source_fetched_at` datetime NULL DEFAULT NULL COMMENT '来源事实抓取时间',
  `created_at` datetime NOT NULL COMMENT '创建时间',
  `updated_at` datetime NOT NULL COMMENT '更新时间',
  PRIMARY KEY (`id`),
  UNIQUE INDEX `uk_search_document_entity_version` (`entity_kind`, `entity_id`, `index_version`),
  INDEX `idx_search_document_version_kind` (`index_version`, `entity_kind`, `source_active`),
  FULLTEXT INDEX `ft_search_document_text` (`title`, `aliases`, `lexical_text`) WITH PARSER ngram
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='版本化全文检索 shadow 投影';

CREATE TABLE IF NOT EXISTS `search_index_release` (
  `id` bigint NOT NULL AUTO_INCREMENT COMMENT '发布记录 ID',
  `index_version` varchar(32) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci NOT NULL COMMENT '索引版本',
  `profile_version` varchar(32) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci NOT NULL COMMENT '档案模板版本',
  `status` varchar(16) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci NOT NULL DEFAULT 'BUILDING' COMMENT '发布状态: BUILDING/ACTIVE/RETIRED/FAILED',
  `activated_at` datetime NULL DEFAULT NULL COMMENT '激活时间',
  `retired_at` datetime NULL DEFAULT NULL COMMENT '退役时间',
  `active_slot` tinyint GENERATED ALWAYS AS (CASE WHEN `status` = 'ACTIVE' THEN 1 ELSE NULL END) STORED COMMENT 'ACTIVE 唯一槽位',
  `created_at` datetime NOT NULL COMMENT '创建时间',
  `updated_at` datetime NOT NULL COMMENT '更新时间',
  PRIMARY KEY (`id`),
  UNIQUE INDEX `uk_search_release_version` (`index_version`),
  UNIQUE INDEX `uk_search_release_active_slot` (`active_slot`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='词法与向量索引发布指针';

-- 校验：
-- SELECT TABLE_NAME FROM INFORMATION_SCHEMA.TABLES WHERE TABLE_SCHEMA=DATABASE()
--   AND TABLE_NAME IN ('search_document','search_index_release');
-- SHOW INDEX FROM search_document;
-- 回滚（仅在确认不再使用投影后）：
-- DROP TABLE IF EXISTS `search_index_release`;
-- DROP TABLE IF EXISTS `search_document`;
