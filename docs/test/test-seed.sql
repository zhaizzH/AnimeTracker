-- ============================================================
-- AnimeTracker 测试种子数据 (test-seed.sql)
-- 版本: v1 (2026-08-11)
-- 用途: 将测试库重置至统一干净基线, 幂等可重放
-- 执行: docker exec 1Panel-mysql-aeEP mysql -uroot -pZPQ0801yy anime_tracker < scripts/test-seed.sql
-- 注意: 仅操作测试数据(user/import_record/operation_log/user_collection), 不动 subject/episode 业务数据
-- ============================================================

-- 1. 用户基线: admin(id=0, ADMIN) / test1(id=1, USER) / test2(id=2, USER)
-- 密码均为 123456 (BCrypt)
INSERT INTO `user` (`id`, `username`, `password`, `email`, `nickname`, `role`, `email_verified`, `created_at`, `updated_at`) VALUES
(0, 'admin', '$2a$10$FT/Rb1RwEFTSPLOl.i26AuI/u3ZWM/XIgWg/1CqY9Y5Pd70Imu6l.', NULL, '管理员', 'ADMIN', 1, '2026-07-18 16:20:38', '2026-07-18 16:20:38'),
(1, 'test1', '$2a$10$FT/Rb1RwEFTSPLOl.i26AuI/u3ZWM/XIgWg/1CqY9Y5Pd70Imu6l.', NULL, '测试用户1', 'USER', 1, '2026-07-16 17:41:08', '2026-07-16 17:41:08'),
(2, 'test2', '$2a$10$HviMPW2KdeQaXTjJCuAt9ut0V3powMipnCOLS8OvkdzQmzFFUzqXC', NULL, '测试用户2', 'USER', 1, '2026-07-20 10:02:30', '2026-07-20 10:02:30')
ON DUPLICATE KEY UPDATE
  `password` = VALUES(`password`),
  `role` = VALUES(`role`),
  `email_verified` = VALUES(`email_verified`);

-- 2. 收藏基线: test1 共 5 条 (type: 1=想看 2=看过 3=在看 4=搁置 5=抛弃)
--    在看×4: 14749(尼古喵喵 rate8) / 12563(无职转生 rate1 ep6) / 1(皮丘与皮卡丘 ep1) / 15111(天子传奇 ep1)
--    想看×1: 14149(碧蓝之海 第三季)
DELETE FROM `user_collection`;
INSERT INTO `user_collection` (`id`, `user_id`, `subject_id`, `type`, `rate`, `ep_status`, `created_at`, `updated_at`) VALUES
(2084081144106135553, 1, 14749, 3, 8, 0, '2026-07-20 12:00:00', '2026-07-20 12:00:00'),
(2086092734257913857, 1, 1,    3, 0, 1, '2026-07-21 12:00:00', '2026-07-21 12:00:00'),
(2086092734257913860, 1, 15111, 3, 0, 1, '2026-07-21 12:00:00', '2026-07-21 12:00:00'),
(2086092734257913862, 1, 14149, 1, 0, 0, '2026-07-21 12:00:00', '2026-07-21 12:00:00'),
(2086092734257913863, 1, 12563, 3, 1, 6, '2026-07-21 12:00:00', '2026-07-21 12:00:00')
ON DUPLICATE KEY UPDATE
  `type` = VALUES(`type`),
  `rate` = VALUES(`rate`),
  `ep_status` = VALUES(`ep_status`),
  `updated_at` = VALUES(`updated_at`);

-- 3. 防爆破失败计数清空 (Redis 侧另行处理, 此处占位文档)
--    docker exec 1Panel-redis-HGyc redis-cli -a ZPQ0801yy --no-auth-warning -n 1 del auth:login-fail:test1

-- 4. 操作日志/导入记录不重置(历史审计), 测试中产生的脏记录在报告里注明
