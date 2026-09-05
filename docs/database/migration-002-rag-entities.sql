-- ============================================================================
-- 前向迁移 002：新增 Person/Character 实体、关系表与通用任务表
-- ============================================================================
-- 适用场景：已有数据的存量库（非空库）
-- 前置条件：
--   1. 已完成可恢复备份，记录备份位置
--   2. 确认当前库中 subject/subject_credit/rag_index_job 表存在且有数据
--   3. 应用版本已兼容新表（本迁移只新增，不修改旧表）
--
-- 回滚策略：
--   本迁移只新增表和索引，不修改/删除任何旧表或旧数据。
--   若需回滚，直接 DROP 新增表即可恢复原状（旧表未受影响）。
--   回滚 DDL 见文件末尾 [ROLLBACK] 部分。
--
-- 执行顺序：
--   Step 1: 新增 person 表
--   Step 2: 新增 character 表
--   Step 3: 新增 person_alias 表
--   Step 4: 新增 character_alias 表
--   Step 5: 新增 subject_person_credit 表
--   Step 6: 新增 subject_character 表
--   Step 7: 新增 character_actor 表
--   Step 8: 新增 entity_detail_job 表
--   Step 9: 新增 search_index_job 表
--   Step 10: 为旧 subject 表新增索引（可选，提升新查询路径性能）
--   Step 11: 回填校验
-- ============================================================================

-- Step 1: person
CREATE TABLE IF NOT EXISTS `person` (
  `id` bigint NOT NULL AUTO_INCREMENT COMMENT '人物ID',
  `bangumi_person_id` int NOT NULL COMMENT 'Bangumi 人物ID',
  `person_type` varchar(16) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci NOT NULL DEFAULT 'PERSON' COMMENT '人物类型: PERSON=个人, COMPANY=公司, GROUP=组合',
  `name` varchar(255) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci NOT NULL COMMENT '名称',
  `summary` text CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci NULL COMMENT '简介',
  `career_json` json NULL COMMENT '职业 JSON（来自上游 infobox）',
  `infobox_json` json NULL COMMENT '完整 infobox JSON 快照',
  `image` varchar(512) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci NULL DEFAULT NULL COMMENT '图片URL',
  `image_source_url` varchar(512) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci NULL DEFAULT NULL COMMENT '原始图片 URL',
  `image_storage_status` varchar(24) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci NOT NULL DEFAULT 'PENDING' COMMENT '图片存储状态: PENDING/STORED/FAILED/ABSENT',
  `detail_status` varchar(16) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci NOT NULL DEFAULT 'SUMMARY_ONLY' COMMENT '详情状态: SUMMARY_ONLY/PENDING/COMPLETE/FAILED',
  `source_hash` char(64) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci NULL DEFAULT NULL COMMENT '来源数据哈希（用于变更检测）',
  `source_fetched_at` datetime NULL DEFAULT NULL COMMENT '最近成功抓取源详情时间',
  `last_seen_import_id` bigint NULL DEFAULT NULL COMMENT '最近一次发现该实体的 import_record.id',
  `source_active` tinyint(1) NOT NULL DEFAULT 1 COMMENT '上游是否仍然活跃: 0=已失效, 1=活跃',
  `created_at` datetime NOT NULL COMMENT '创建时间',
  `updated_at` datetime NOT NULL COMMENT '更新时间',
  PRIMARY KEY (`id`) USING BTREE,
  UNIQUE INDEX `uk_bangumi_person_id`(`bangumi_person_id` ASC) USING BTREE,
  INDEX `idx_person_name`(`name` ASC) USING BTREE,
  INDEX `idx_person_type`(`person_type` ASC) USING BTREE,
  INDEX `idx_person_detail_status`(`detail_status` ASC) USING BTREE,
  INDEX `idx_person_source_active`(`source_active` ASC) USING BTREE
) ENGINE = InnoDB AUTO_INCREMENT = 1 CHARACTER SET = utf8mb4 COLLATE = utf8mb4_unicode_ci COMMENT = '人物/公司/组合表' ROW_FORMAT = Dynamic;

-- Step 2: character
CREATE TABLE IF NOT EXISTS `character` (
  `id` bigint NOT NULL AUTO_INCREMENT COMMENT '角色ID',
  `bangumi_character_id` int NOT NULL COMMENT 'Bangumi 角色ID',
  `character_type` varchar(16) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci NOT NULL DEFAULT 'CHARACTER' COMMENT '角色类型: CHARACTER=角色, ORGANIZATION=作品内组织',
  `name` varchar(255) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci NOT NULL COMMENT '名称',
  `summary` text CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci NULL COMMENT '简介',
  `infobox_json` json NULL COMMENT '完整 infobox JSON 快照',
  `image` varchar(512) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci NULL DEFAULT NULL COMMENT '图片URL',
  `image_source_url` varchar(512) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci NULL DEFAULT NULL COMMENT '原始图片 URL',
  `image_storage_status` varchar(24) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci NOT NULL DEFAULT 'PENDING' COMMENT '图片存储状态: PENDING/STORED/FAILED/ABSENT',
  `detail_status` varchar(16) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci NOT NULL DEFAULT 'SUMMARY_ONLY' COMMENT '详情状态: SUMMARY_ONLY/PENDING/COMPLETE/FAILED',
  `source_hash` char(64) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci NULL DEFAULT NULL COMMENT '来源数据哈希（用于变更检测）',
  `source_fetched_at` datetime NULL DEFAULT NULL COMMENT '最近成功抓取源详情时间',
  `last_seen_import_id` bigint NULL DEFAULT NULL COMMENT '最近一次发现该实体的 import_record.id',
  `source_active` tinyint(1) NOT NULL DEFAULT 1 COMMENT '上游是否仍然活跃: 0=已失效, 1=活跃',
  `created_at` datetime NOT NULL COMMENT '创建时间',
  `updated_at` datetime NOT NULL COMMENT '更新时间',
  PRIMARY KEY (`id`) USING BTREE,
  UNIQUE INDEX `uk_bangumi_character_id`(`bangumi_character_id` ASC) USING BTREE,
  INDEX `idx_character_name`(`name` ASC) USING BTREE,
  INDEX `idx_character_type`(`character_type` ASC) USING BTREE,
  INDEX `idx_character_detail_status`(`detail_status` ASC) USING BTREE,
  INDEX `idx_character_source_active`(`source_active` ASC) USING BTREE
) ENGINE = InnoDB AUTO_INCREMENT = 1 CHARACTER SET = utf8mb4 COLLATE = utf8mb4_unicode_ci COMMENT = '角色表' ROW_FORMAT = Dynamic;

-- Step 3: person_alias
CREATE TABLE IF NOT EXISTS `person_alias` (
  `id` bigint NOT NULL AUTO_INCREMENT COMMENT '别名ID',
  `person_id` bigint NOT NULL COMMENT '人物ID',
  `name` varchar(255) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci NOT NULL COMMENT '别名',
  `language` varchar(8) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci NOT NULL DEFAULT 'und' COMMENT '语言',
  `source` varchar(32) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci NOT NULL DEFAULT 'infobox' COMMENT '来源',
  `source_active` tinyint(1) NOT NULL DEFAULT 1 COMMENT '上游是否仍然活跃',
  `created_at` datetime NOT NULL COMMENT '创建时间',
  `updated_at` datetime NOT NULL COMMENT '更新时间',
  PRIMARY KEY (`id`) USING BTREE,
  UNIQUE INDEX `uk_person_alias`(`person_id` ASC, `name` ASC) USING BTREE,
  INDEX `idx_person_alias_name`(`name` ASC) USING BTREE,
  CONSTRAINT `fk_person_alias_person` FOREIGN KEY (`person_id`) REFERENCES `person` (`id`) ON DELETE CASCADE
) ENGINE = InnoDB AUTO_INCREMENT = 1 CHARACTER SET = utf8mb4 COLLATE = utf8mb4_unicode_ci COMMENT = '人物别名表' ROW_FORMAT = Dynamic;

-- Step 4: character_alias
CREATE TABLE IF NOT EXISTS `character_alias` (
  `id` bigint NOT NULL AUTO_INCREMENT COMMENT '别名ID',
  `character_id` bigint NOT NULL COMMENT '角色ID',
  `name` varchar(255) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci NOT NULL COMMENT '别名',
  `language` varchar(8) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci NOT NULL DEFAULT 'und' COMMENT '语言',
  `source` varchar(32) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci NOT NULL DEFAULT 'infobox' COMMENT '来源',
  `source_active` tinyint(1) NOT NULL DEFAULT 1 COMMENT '上游是否仍然活跃',
  `created_at` datetime NOT NULL COMMENT '创建时间',
  `updated_at` datetime NOT NULL COMMENT '更新时间',
  PRIMARY KEY (`id`) USING BTREE,
  UNIQUE INDEX `uk_character_alias`(`character_id` ASC, `name` ASC) USING BTREE,
  INDEX `idx_character_alias_name`(`name` ASC) USING BTREE,
  CONSTRAINT `fk_character_alias_character` FOREIGN KEY (`character_id`) REFERENCES `character` (`id`) ON DELETE CASCADE
) ENGINE = InnoDB AUTO_INCREMENT = 1 CHARACTER SET = utf8mb4 COLLATE = utf8mb4_unicode_ci COMMENT = '角色别名表' ROW_FORMAT = Dynamic;

-- Step 5: subject_person_credit
CREATE TABLE IF NOT EXISTS `subject_person_credit` (
  `id` bigint NOT NULL AUTO_INCREMENT COMMENT '关联ID',
  `subject_id` bigint NOT NULL COMMENT '条目ID',
  `person_id` bigint NOT NULL COMMENT '人物ID',
  `role` varchar(64) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci NOT NULL COMMENT '职责（如导演、脚本）',
  `relation` varchar(32) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci NOT NULL DEFAULT 'MAIN' COMMENT '关系类型: MAIN=主要, SUB=次要',
  `sort_order` int NOT NULL DEFAULT 0 COMMENT '来源排序',
  `source_active` tinyint(1) NOT NULL DEFAULT 1 COMMENT '上游是否仍然活跃',
  `created_at` datetime NOT NULL COMMENT '创建时间',
  `updated_at` datetime NOT NULL COMMENT '更新时间',
  PRIMARY KEY (`id`) USING BTREE,
  UNIQUE INDEX `uk_subject_person_credit`(`subject_id` ASC, `person_id` ASC, `role` ASC) USING BTREE,
  INDEX `idx_spc_person`(`person_id` ASC) USING BTREE,
  INDEX `idx_spc_subject_active`(`subject_id` ASC, `source_active` ASC) USING BTREE,
  CONSTRAINT `fk_spc_subject` FOREIGN KEY (`subject_id`) REFERENCES `subject` (`id`) ON DELETE CASCADE,
  CONSTRAINT `fk_spc_person` FOREIGN KEY (`person_id`) REFERENCES `person` (`id`) ON DELETE CASCADE
) ENGINE = InnoDB AUTO_INCREMENT = 1 CHARACTER SET = utf8mb4 COLLATE = utf8mb4_unicode_ci COMMENT = '条目-人物主创关联表' ROW_FORMAT = Dynamic;

-- Step 6: subject_character
CREATE TABLE IF NOT EXISTS `subject_character` (
  `id` bigint NOT NULL AUTO_INCREMENT COMMENT '关联ID',
  `subject_id` bigint NOT NULL COMMENT '条目ID',
  `character_id` bigint NOT NULL COMMENT '角色ID',
  `relation` varchar(32) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci NOT NULL DEFAULT 'MAIN' COMMENT '角色在作品中的定位: MAIN=主角, SUPPORTING=配角, GUEST=客串',
  `sort_order` int NOT NULL DEFAULT 0 COMMENT '来源排序',
  `source_active` tinyint(1) NOT NULL DEFAULT 1 COMMENT '上游是否仍然活跃',
  `created_at` datetime NOT NULL COMMENT '创建时间',
  `updated_at` datetime NOT NULL COMMENT '更新时间',
  PRIMARY KEY (`id`) USING BTREE,
  UNIQUE INDEX `uk_subject_character`(`subject_id` ASC, `character_id` ASC) USING BTREE,
  INDEX `idx_sc_character`(`character_id` ASC) USING BTREE,
  INDEX `idx_sc_subject_active`(`subject_id` ASC, `source_active` ASC) USING BTREE,
  CONSTRAINT `fk_sc_subject` FOREIGN KEY (`subject_id`) REFERENCES `subject` (`id`) ON DELETE CASCADE,
  CONSTRAINT `fk_sc_character` FOREIGN KEY (`character_id`) REFERENCES `character` (`id`) ON DELETE CASCADE
) ENGINE = InnoDB AUTO_INCREMENT = 1 CHARACTER SET = utf8mb4 COLLATE = utf8mb4_unicode_ci COMMENT = '条目-角色关联表' ROW_FORMAT = Dynamic;

-- Step 7: character_actor
CREATE TABLE IF NOT EXISTS `character_actor` (
  `id` bigint NOT NULL AUTO_INCREMENT COMMENT '关联ID',
  `subject_id` bigint NOT NULL COMMENT '条目ID（声优关系限定于特定作品版本）',
  `character_id` bigint NOT NULL COMMENT '角色ID',
  `person_id` bigint NOT NULL COMMENT '声优人物ID',
  `actor_relation` varchar(32) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci NOT NULL DEFAULT 'VA' COMMENT '演员关系: VA=声优, ACTOR=真人演员',
  `sort_order` int NOT NULL DEFAULT 0 COMMENT '来源排序',
  `source_active` tinyint(1) NOT NULL DEFAULT 1 COMMENT '上游是否仍然活跃',
  `created_at` datetime NOT NULL COMMENT '创建时间',
  `updated_at` datetime NOT NULL COMMENT '更新时间',
  PRIMARY KEY (`id`) USING BTREE,
  UNIQUE INDEX `uk_character_actor`(`subject_id` ASC, `character_id` ASC, `person_id` ASC) USING BTREE,
  INDEX `idx_ca_person`(`person_id` ASC) USING BTREE,
  INDEX `idx_ca_character`(`character_id` ASC) USING BTREE,
  INDEX `idx_ca_subject_active`(`subject_id` ASC, `source_active` ASC) USING BTREE,
  CONSTRAINT `fk_ca_subject` FOREIGN KEY (`subject_id`) REFERENCES `subject` (`id`) ON DELETE CASCADE,
  CONSTRAINT `fk_ca_character` FOREIGN KEY (`character_id`) REFERENCES `character` (`id`) ON DELETE CASCADE,
  CONSTRAINT `fk_ca_person` FOREIGN KEY (`person_id`) REFERENCES `person` (`id`) ON DELETE CASCADE
) ENGINE = InnoDB AUTO_INCREMENT = 1 CHARACTER SET = utf8mb4 COLLATE = utf8mb4_unicode_ci COMMENT = '角色-声优关联表（限定于特定作品）' ROW_FORMAT = Dynamic;

-- Step 8: entity_detail_job
CREATE TABLE IF NOT EXISTS `entity_detail_job` (
  `id` bigint NOT NULL AUTO_INCREMENT COMMENT '任务ID',
  `entity_kind` varchar(16) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci NOT NULL COMMENT '实体类型: PERSON/CHARACTER',
  `entity_id` bigint NOT NULL COMMENT '本地实体ID',
  `source_id` int NOT NULL COMMENT 'Bangumi 上游ID',
  `status` varchar(16) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci NOT NULL DEFAULT 'PENDING' COMMENT '任务状态: PENDING/CLAIMED/RUNNING/COMPLETED/FAILED/ABANDONED',
  `attempts` int NOT NULL DEFAULT 0 COMMENT '尝试次数',
  `max_attempts` int NOT NULL DEFAULT 5 COMMENT '最大尝试次数',
  `next_retry_at` datetime NULL DEFAULT NULL COMMENT '下次重试时间',
  `last_error_code` varchar(64) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci NULL DEFAULT NULL COMMENT '最近错误码',
  `last_error_message` varchar(512) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci NULL DEFAULT NULL COMMENT '脱敏后的最近错误信息',
  `checkpoint_json` json NULL COMMENT '回填断点 JSON',
  `source_hash` char(64) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci NULL DEFAULT NULL COMMENT '完成时的来源数据哈希',
  `claimed_at` datetime NULL DEFAULT NULL COMMENT '认领时间',
  `completed_at` datetime NULL DEFAULT NULL COMMENT '完成时间',
  `created_at` datetime NOT NULL COMMENT '创建时间',
  `updated_at` datetime NOT NULL COMMENT '更新时间',
  PRIMARY KEY (`id`) USING BTREE,
  UNIQUE INDEX `uk_entity_detail_job`(`entity_kind` ASC, `entity_id` ASC) USING BTREE,
  INDEX `idx_edj_status_retry`(`status` ASC, `next_retry_at` ASC) USING BTREE,
  INDEX `idx_edj_source`(`entity_kind` ASC, `source_id` ASC) USING BTREE
) ENGINE = InnoDB AUTO_INCREMENT = 1 CHARACTER SET = utf8mb4 COLLATE = utf8mb4_unicode_ci COMMENT = '实体详情渐进回填任务表' ROW_FORMAT = Dynamic;

-- Step 9: search_index_job
CREATE TABLE IF NOT EXISTS `search_index_job` (
  `id` bigint NOT NULL AUTO_INCREMENT COMMENT '索引任务ID',
  `entity_kind` varchar(16) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci NOT NULL COMMENT '实体类型: SUBJECT/EPISODE/PERSON/CHARACTER',
  `entity_id` bigint NOT NULL COMMENT '本地实体ID',
  `index_version` varchar(32) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci NOT NULL COMMENT '索引版本',
  `profile_version` varchar(32) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci NOT NULL DEFAULT 'v1' COMMENT '档案模板版本',
  `content_hash` char(64) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci NOT NULL COMMENT '档案内容哈希',
  `embedding_provider` varchar(32) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci NOT NULL DEFAULT 'dashscope' COMMENT 'Embedding 供应商',
  `embedding_model` varchar(64) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci NOT NULL COMMENT 'Embedding 模型',
  `embedding_dimensions` int NOT NULL COMMENT '向量维度',
  `status` varchar(16) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci NOT NULL DEFAULT 'PENDING' COMMENT '任务状态: PENDING/CLAIMED/COMPLETED/FAILED/TOMBSTONE',
  `attempts` int NOT NULL DEFAULT 0 COMMENT '尝试次数',
  `max_attempts` int NOT NULL DEFAULT 5 COMMENT '最大尝试次数',
  `last_error_code` varchar(64) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci NULL DEFAULT NULL COMMENT '最近错误码',
  `last_error_message` varchar(512) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci NULL DEFAULT NULL COMMENT '脱敏后的最近错误信息',
  `next_retry_at` datetime NULL DEFAULT NULL COMMENT '下次重试时间',
  `claimed_at` datetime NULL DEFAULT NULL COMMENT '认领时间',
  `indexed_at` datetime NULL DEFAULT NULL COMMENT '完成索引时间',
  `created_at` datetime NOT NULL COMMENT '创建时间',
  `updated_at` datetime NOT NULL COMMENT '更新时间',
  PRIMARY KEY (`id`) USING BTREE,
  UNIQUE INDEX `uk_search_index_job`(`entity_kind` ASC, `entity_id` ASC, `index_version` ASC) USING BTREE,
  INDEX `idx_sij_status_retry`(`status` ASC, `next_retry_at` ASC) USING BTREE,
  INDEX `idx_sij_entity`(`entity_kind` ASC, `entity_id` ASC) USING BTREE
) ENGINE = InnoDB AUTO_INCREMENT = 1 CHARACTER SET = utf8mb4 COLLATE = utf8mb4_unicode_ci COMMENT = '通用搜索索引任务表' ROW_FORMAT = Dynamic;

-- Step 10: 为旧表补充索引（可选，提升新查询路径性能）
-- MySQL 8.4 不支持 ALTER TABLE ... ADD COLUMN IF NOT EXISTS；使用
-- INFORMATION_SCHEMA + PREPARE 保持空库前向迁移和重复执行都幂等。

-- subject_alias 增加 source_active 列以支持 replace-set 语义
SET @sql = IF(
  (SELECT COUNT(*) FROM INFORMATION_SCHEMA.COLUMNS
   WHERE TABLE_SCHEMA = DATABASE() AND TABLE_NAME = 'subject_alias' AND COLUMN_NAME = 'source_active') = 0,
  'ALTER TABLE `subject_alias` ADD COLUMN `source_active` tinyint(1) NOT NULL DEFAULT 1 COMMENT ''上游是否仍然活跃'' AFTER `source`',
  'SELECT 1'
);
PREPARE stmt FROM @sql;
EXECUTE stmt;
DEALLOCATE PREPARE stmt;

-- subject_meta_tag 增加 source_active 列
SET @sql = IF(
  (SELECT COUNT(*) FROM INFORMATION_SCHEMA.COLUMNS
   WHERE TABLE_SCHEMA = DATABASE() AND TABLE_NAME = 'subject_meta_tag' AND COLUMN_NAME = 'source_active') = 0,
  'ALTER TABLE `subject_meta_tag` ADD COLUMN `source_active` tinyint(1) NOT NULL DEFAULT 1 COMMENT ''上游是否仍然活跃'' AFTER `name`',
  'SELECT 1'
);
PREPARE stmt FROM @sql;
EXECUTE stmt;
DEALLOCATE PREPARE stmt;

-- subject_credit 增加 source_active 列（兼容窗口内保留旧表读取）
SET @sql = IF(
  (SELECT COUNT(*) FROM INFORMATION_SCHEMA.COLUMNS
   WHERE TABLE_SCHEMA = DATABASE() AND TABLE_NAME = 'subject_credit' AND COLUMN_NAME = 'source_active') = 0,
  'ALTER TABLE `subject_credit` ADD COLUMN `source_active` tinyint(1) NOT NULL DEFAULT 1 COMMENT ''上游是否仍然活跃'' AFTER `sort_order`',
  'SELECT 1'
);
PREPARE stmt FROM @sql;
EXECUTE stmt;
DEALLOCATE PREPARE stmt;

-- ============================================================================
-- Step 11: 回填校验（执行后人工确认）
-- ============================================================================
-- 确认新表存在：
--   SELECT TABLE_NAME FROM INFORMATION_SCHEMA.TABLES
--   WHERE TABLE_SCHEMA = DATABASE()
--   AND TABLE_NAME IN ('person','character','person_alias','character_alias',
--                      'subject_person_credit','subject_character','character_actor',
--                      'entity_detail_job','search_index_job');
-- 期望返回 9 行。
--
-- 确认旧表未受影响：
--   SELECT COUNT(*) FROM subject;
--   SELECT COUNT(*) FROM subject_credit;
--   SELECT COUNT(*) FROM rag_index_job;
-- 期望与迁移前一致。
--
-- 确认旧表新增列默认值：
--   SELECT COUNT(*) FROM subject_alias WHERE source_active = 1;
-- 期望等于 SELECT COUNT(*) FROM subject_alias。

-- ============================================================================
-- [ROLLBACK] 回滚 DDL（仅在迁移失败且需恢复时执行）
-- ============================================================================
-- DROP TABLE IF EXISTS `search_index_job`;
-- DROP TABLE IF EXISTS `entity_detail_job`;
-- DROP TABLE IF EXISTS `character_actor`;
-- DROP TABLE IF EXISTS `subject_character`;
-- DROP TABLE IF EXISTS `subject_person_credit`;
-- DROP TABLE IF EXISTS `character_alias`;
-- DROP TABLE IF EXISTS `person_alias`;
-- DROP TABLE IF EXISTS `character`;
-- DROP TABLE IF EXISTS `person`;
-- ALTER TABLE `subject_alias` DROP COLUMN IF EXISTS `source_active`;
-- ALTER TABLE `subject_meta_tag` DROP COLUMN IF EXISTS `source_active`;
-- ALTER TABLE `subject_credit` DROP COLUMN IF EXISTS `source_active`;
