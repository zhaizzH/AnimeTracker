-- =====================================================================
-- AnimeTracker 演示数据（仅 tools profile 下由 demo-seeder 执行）
-- 演示用户密码哈希由 entrypoint.sh 运行时生成并替换占位符，绝不落库明文。
-- 全部使用 INSERT IGNORE 保证重复执行幂等。
-- 依赖：业务库已由 docs/database/db-schema.sql 建表。
-- =====================================================================

SET NAMES utf8mb4;

-- 演示用户（密码哈希占位符在运行时替换）
INSERT IGNORE INTO `user`
  (`id`, `username`, `password`, `email`, `nickname`, `role`, `email_verified`, `created_at`, `updated_at`)
VALUES
  (1, 'demo', '__DEMO_USER_PASSWORD_HASH__', 'demo@example.com', '演示用户', 'USER', 1, NOW(), NOW());

-- 演示番剧（5 条，分别对应五种收藏状态，供仪表盘样例）
INSERT IGNORE INTO `subject`
  (`id`, `bangumi_id`, `name`, `name_cn`, `summary`, `type`, `eps`, `air_date`, `air_weekday`, `score`, `rank`, `nsfw`, `import_status`, `created_at`, `updated_at`)
VALUES
  (1, 100001, 'Demo Anime One', '演示番剧·其一', '演示用的科幻番剧。', 2, 12, '2026-04-01', 6, 8.5, 120, 0, 1, NOW(), NOW()),
  (2, 100002, 'Demo Anime Two', '演示番剧·其二', '演示用的冒险番剧。', 2, 24, '2025-10-01', 2, 7.8, 340, 0, 1, NOW(), NOW()),
  (3, 100003, 'Demo Movie', '演示剧场版', '演示用的剧场版动画。', 2, 1, '2026-01-15', NULL, 9.0, 25, 0, 1, NOW(), NOW()),
  (4, 100004, 'Demo Anime Four', '演示番剧·其四', '演示用（搁置状态）。', 2, 13, '2024-07-01', 5, 7.0, 800, 0, 1, NOW(), NOW()),
  (5, 100005, 'Demo Anime Five', '演示番剧·其五', '演示用（抛弃状态）。', 2, 12, '2023-01-08', 0, 6.0, 1500, 0, 1, NOW(), NOW());

-- 演示剧集（番剧 1 的前 4 话）
INSERT IGNORE INTO `episode`
  (`id`, `subject_id`, `bangumi_ep_id`, `type`, `sort`, `name`, `name_cn`, `duration`, `airdate`, `description`, `status`, `created_at`)
VALUES
  (1, 1, 100, 0, 1.0, 'Episode 1', '第1话', '24m', '2026-04-01', '演示剧集。', 'Air', NOW()),
  (2, 1, 101, 0, 2.0, 'Episode 2', '第2话', '24m', '2026-04-08', NULL, 'Air', NOW()),
  (3, 1, 102, 0, 3.0, 'Episode 3', '第3话', '24m', '2026-04-15', NULL, 'Air', NOW()),
  (4, 1, 103, 0, 4.0, 'Episode 4', '第4话', '24m', '2026-04-22', NULL, 'Air', NOW());

-- 演示标签
INSERT IGNORE INTO `subject_tag` (`id`, `subject_id`, `name`, `count`) VALUES
  (1, 1, '科幻', 12),
  (2, 1, '战斗', 8),
  (3, 2, '冒险', 10),
  (4, 3, '剧场版', 6),
  (5, 4, '日常', 7);

-- 演示条目关联
INSERT IGNORE INTO `subject_relation` (`id`, `subject_id`, `related_subject_id`, `relation`) VALUES
  (1, 1, 2, 'sequel'),
  (2, 3, 1, 'side_story');

-- 演示收藏（覆盖 在看/看过/想看/搁置/抛弃 五种状态）
INSERT IGNORE INTO `user_collection`
  (`id`, `user_id`, `subject_id`, `type`, `rate`, `ep_status`, `created_at`, `updated_at`)
VALUES
  (1, 1, 1, 3, 0, 4, NOW(), NOW()),
  (2, 1, 2, 2, 9, 24, NOW(), NOW()),
  (3, 1, 3, 1, 0, 0, NOW(), NOW()),
  (4, 1, 4, 4, 0, 2, NOW(), NOW()),
  (5, 1, 5, 5, 0, 0, NOW(), NOW());
