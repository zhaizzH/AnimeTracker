-- ============================================================
-- subject_relation: 条目关联表
-- 用于存储动漫条目之间的关联关系（前传、续集、番外等）
-- ============================================================
CREATE TABLE `subject_relation` (
  `id`                 bigint       NOT NULL AUTO_INCREMENT COMMENT '关联ID',
  `subject_id`         bigint       NOT NULL COMMENT '当前条目ID',
  `related_subject_id` bigint       NOT NULL COMMENT '关联条目ID',
  `relation`           varchar(32)  NOT NULL COMMENT '关联类型: prequel, sequel, side_story 等',
  PRIMARY KEY (`id`),
  UNIQUE KEY `uk_subject_relation` (`subject_id`, `related_subject_id`),
  KEY `idx_sr_subject` (`subject_id`),
  KEY `idx_sr_related` (`related_subject_id`),
  CONSTRAINT `fk_sr_subject` FOREIGN KEY (`subject_id`) REFERENCES `subject` (`id`) ON DELETE CASCADE,
  CONSTRAINT `fk_sr_related` FOREIGN KEY (`related_subject_id`) REFERENCES `subject` (`id`) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='条目关联表';
