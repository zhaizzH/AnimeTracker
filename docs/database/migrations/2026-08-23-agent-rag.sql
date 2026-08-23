-- Agent RAG 数据模型：仅向前新增，禁止在此迁移中删除既有数据或结构。

ALTER TABLE `subject`
  ADD COLUMN IF NOT EXISTS `rating_total` INT NULL,
  ADD COLUMN IF NOT EXISTS `rating_count_json` JSON NULL,
  ADD COLUMN IF NOT EXISTS `collection_wish` INT NULL,
  ADD COLUMN IF NOT EXISTS `collection_collect` INT NULL,
  ADD COLUMN IF NOT EXISTS `collection_doing` INT NULL,
  ADD COLUMN IF NOT EXISTS `collection_on_hold` INT NULL,
  ADD COLUMN IF NOT EXISTS `collection_dropped` INT NULL,
  ADD COLUMN IF NOT EXISTS `image_source_url` VARCHAR(512) NULL,
  ADD COLUMN IF NOT EXISTS `image_storage_status` VARCHAR(24) NOT NULL DEFAULT 'PENDING',
  ADD COLUMN IF NOT EXISTS `image_checked_at` DATETIME NULL,
  ADD COLUMN IF NOT EXISTS `source_fetched_at` DATETIME NULL;

ALTER TABLE `import_record`
  ADD COLUMN IF NOT EXISTS `checkpoint_json` JSON NULL,
  ADD COLUMN IF NOT EXISTS `scanned_count` INT NOT NULL DEFAULT 0,
  ADD COLUMN IF NOT EXISTS `success_count` INT NOT NULL DEFAULT 0,
  ADD COLUMN IF NOT EXISTS `failure_count` INT NOT NULL DEFAULT 0,
  ADD COLUMN IF NOT EXISTS `skipped_count` INT NOT NULL DEFAULT 0,
  ADD COLUMN IF NOT EXISTS `source_snapshot_at` DATETIME NULL,
  ADD COLUMN IF NOT EXISTS `heartbeat_at` DATETIME NULL;

CREATE TABLE IF NOT EXISTS `subject_alias` (
  `id` BIGINT NOT NULL AUTO_INCREMENT,
  `subject_id` BIGINT NOT NULL,
  `name` VARCHAR(255) NOT NULL,
  `language` VARCHAR(8) NOT NULL DEFAULT 'und',
  `source` VARCHAR(32) NOT NULL,
  `created_at` DATETIME NOT NULL,
  `updated_at` DATETIME NOT NULL,
  PRIMARY KEY (`id`),
  UNIQUE KEY `uk_subject_alias` (`subject_id`, `name`),
  KEY `idx_alias_name` (`name`),
  CONSTRAINT `fk_alias_subject` FOREIGN KEY (`subject_id`) REFERENCES `subject` (`id`) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE TABLE IF NOT EXISTS `subject_meta_tag` (
  `id` BIGINT NOT NULL AUTO_INCREMENT,
  `subject_id` BIGINT NOT NULL,
  `name` VARCHAR(255) NOT NULL,
  `created_at` DATETIME NOT NULL,
  PRIMARY KEY (`id`),
  UNIQUE KEY `uk_subject_meta_tag` (`subject_id`, `name`),
  KEY `idx_meta_tag_name` (`name`),
  CONSTRAINT `fk_meta_tag_subject` FOREIGN KEY (`subject_id`) REFERENCES `subject` (`id`) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE TABLE IF NOT EXISTS `subject_credit` (
  `id` BIGINT NOT NULL AUTO_INCREMENT,
  `subject_id` BIGINT NOT NULL,
  `bangumi_person_id` INT NULL,
  `name` VARCHAR(255) NOT NULL,
  `role` VARCHAR(64) NOT NULL,
  `credit_type` VARCHAR(16) NOT NULL,
  `sort_order` INT NOT NULL DEFAULT 0,
  `created_at` DATETIME NOT NULL,
  `updated_at` DATETIME NOT NULL,
  PRIMARY KEY (`id`),
  UNIQUE KEY `uk_subject_credit` (`subject_id`, `name`, `role`),
  KEY `idx_credit_name_role` (`name`, `role`),
  CONSTRAINT `fk_credit_subject` FOREIGN KEY (`subject_id`) REFERENCES `subject` (`id`) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE TABLE IF NOT EXISTS `rag_index_job` (
  `id` BIGINT NOT NULL AUTO_INCREMENT,
  `subject_id` BIGINT NOT NULL,
  `index_version` VARCHAR(32) NOT NULL,
  `content_hash` CHAR(64) NOT NULL,
  `embedding_provider` VARCHAR(32) NOT NULL,
  `embedding_model` VARCHAR(64) NOT NULL,
  `embedding_dimensions` INT NOT NULL,
  `status` VARCHAR(16) NOT NULL DEFAULT 'PENDING',
  `attempts` INT NOT NULL DEFAULT 0,
  `last_error_code` VARCHAR(64) NULL,
  `last_error_message` VARCHAR(512) NULL,
  `next_retry_at` DATETIME NULL,
  `indexed_at` DATETIME NULL,
  `created_at` DATETIME NOT NULL,
  `updated_at` DATETIME NOT NULL,
  PRIMARY KEY (`id`),
  UNIQUE KEY `uk_rag_job_subject_version` (`subject_id`, `index_version`),
  KEY `idx_rag_job_status_retry` (`status`, `next_retry_at`),
  CONSTRAINT `fk_rag_job_subject` FOREIGN KEY (`subject_id`) REFERENCES `subject` (`id`) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
