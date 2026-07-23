CREATE TABLE `user_collection` (
  `id` bigint NOT NULL AUTO_INCREMENT,
  `user_id` bigint NOT NULL COMMENT '用户 ID',
  `subject_id` bigint NOT NULL COMMENT '条目 ID',
  `type` tinyint NOT NULL COMMENT '收藏类型: 1=想看 2=看过 3=在看 4=搁置 5=抛弃',
  `rate` tinyint NOT NULL DEFAULT 0 COMMENT '评分 0-10，0 表示未评分',
  `ep_status` int NOT NULL DEFAULT 0 COMMENT '看到第几集',
  `created_at` datetime NOT NULL,
  `updated_at` datetime NOT NULL,
  PRIMARY KEY (`id`),
  UNIQUE KEY `uk_user_subject` (`user_id`, `subject_id`),
  KEY `idx_user_type` (`user_id`, `type`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='用户收藏表';
