-- Add account enable flag for session revocation and login checks.
ALTER TABLE `user`
  ADD COLUMN `enabled` tinyint(1) NOT NULL DEFAULT 1 COMMENT '账号是否启用' AFTER `email_verified`;