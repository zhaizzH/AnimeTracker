-- ========================================================================
-- AnimeTracker 数据库完整建表脚本
-- ========================================================================
-- 版本:    2.0（重构版）
-- 日期:    2026-07-03
-- 数据库:  MySQL 8.0
-- 字符集:  utf8mb4（支持 Emoji 和全角字符）
-- 引擎:    InnoDB（支持事务和外键）
-- 归档位置: backend/data/schema/init.sql
-- 关联文档: docs/base/Scope.md, docs/base/PRD/
-- ========================================================================
--
-- 【设计原则】
-- 1. 所有表使用 InnoDB 引擎以支持外键约束和事务
-- 2. 所有表使用 utf8mb4 字符集，支持 Emoji 和 CJK 扩展字符
-- 3. subject 和 episode 的 name/name_cn 允许为 NULL（部分条目可能缺少中文名）
-- 4. bangumi_id 在 subject 表上有 UNIQUE 约束，确保数据导入不会重复
-- 5. episode.subject_id 和 subject_tag.subject_id 设置了 ON DELETE CASCADE
--    删除条目时自动删除关联的剧集和标签数据
-- 6. subject_tag 的 (subject_id, name) 组合有 UNIQUE 约束，确保同一标签不会重复
-- 7. 不改数据库表结构（重构规范——字段名、类型、索引与旧库完全兼容）
--
-- 【实体 ↔ 表 映射】
-- | Java 实体 (package)         | 数据库表          | 说明                          |
-- |-----------------------------|------------------|-------------------------------|
-- | user.entity.User            | `user`           | 用户账号，含角色权限              |
-- | subject.entity.Subject      | `subject`        | 动漫条目，数据来自 Bangumi API   |
-- | subject.entity.Episode      | `episode`        | 剧集，通过 subject_id 关联条目   |
-- | subject.entity.SubjectTag   | `subject_tag`    | 社区标签，多对多关联条目和标签    |
-- | —                           | `import_record`  | 导入记录（Phase 4 数据导入器使用）|
-- ========================================================================

CREATE DATABASE IF NOT EXISTS `anime_tracker`
    DEFAULT CHARACTER SET utf8mb4
    DEFAULT COLLATE utf8mb4_unicode_ci;

USE `anime_tracker`;

-- ========================================================================
-- 1. 用户表 (user)
-- 存储用户账号信息和角色权限
-- Java 实体: top.zhaizz.animetracker.user.entity.User
-- MyBatis Mapper: user.mapper.UserMapper
-- ========================================================================
CREATE TABLE `user` (
    `id`          BIGINT        NOT NULL AUTO_INCREMENT  COMMENT '用户ID',
    `username`    VARCHAR(32)   NOT NULL                 COMMENT '用户名（唯一）',
    `password`    VARCHAR(255)  NOT NULL                 COMMENT '密码（BCrypt 加密存储）',
    `email`       VARCHAR(128)  DEFAULT NULL             COMMENT '邮箱',
    `nickname`    VARCHAR(64)   DEFAULT NULL             COMMENT '昵称',
    `avatar`      VARCHAR(512)  DEFAULT NULL             COMMENT '头像URL',
    `role`        VARCHAR(16)   NOT NULL DEFAULT 'USER'  COMMENT '角色: USER=普通用户, ADMIN=管理员',
    `created_at`  DATETIME      NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
    `updated_at`  DATETIME      NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间',
    PRIMARY KEY (`id`),
    UNIQUE KEY `uk_username` (`username`),
    INDEX `idx_user_role` (`role`),
    INDEX `idx_user_created_at` (`created_at`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci
  COMMENT='用户表';


-- ========================================================================
-- 2. 条目表 (subject)
-- 存储动漫条目信息，数据源自 Bangumi API 或管理员手动添加
-- Java 实体: top.zhaizz.animetracker.subject.entity.Subject
-- MyBatis Mapper: subject.mapper.SubjectMapper
-- ========================================================================
CREATE TABLE `subject` (
    `id`                BIGINT        NOT NULL AUTO_INCREMENT  COMMENT '条目ID',
    `bangumi_id`        INT           NOT NULL                 COMMENT 'Bangumi API 条目ID（Integer 类型）',
    `name`              VARCHAR(255)  NOT NULL                 COMMENT '日文/英文名',
    `name_cn`           VARCHAR(255)  DEFAULT NULL             COMMENT '中文名',
    `summary`           TEXT          DEFAULT NULL             COMMENT '简介/描述',
    `type`              TINYINT       NOT NULL DEFAULT 2       COMMENT '条目类型: 2=动画（本项目仅使用动画类型）',
    `eps`               INT           DEFAULT NULL             COMMENT '总集数',
    `volumes`           INT           DEFAULT NULL             COMMENT '总卷数',
    `air_date`          DATE          DEFAULT NULL             COMMENT '播出日期（LocalDate 类型）',
    `air_weekday`       TINYINT       DEFAULT NULL             COMMENT '播出星期（0=周日, 1=周一 ... 6=周六）',
    `image`             VARCHAR(512)  DEFAULT NULL             COMMENT '封面图URL（字段名 image，非 imageUrl）',
    `score`             DECIMAL(3,1)  DEFAULT NULL             COMMENT 'Bangumi 评分（0.0~10.0，BigDecimal）',
    `rank`              INT           DEFAULT NULL             COMMENT 'Bangumi 排名',
    `collection_total`  INT           DEFAULT NULL             COMMENT '收藏数',
    `nsfw`              TINYINT(1)    NOT NULL DEFAULT 0       COMMENT '是否 NSFW: 0=否, 1=是',
    `import_status`     TINYINT       NOT NULL DEFAULT 0       COMMENT '导入状态: 0=待导入, 1=已导入',
    `last_imported_at`  DATETIME      DEFAULT NULL             COMMENT '最近导入时间',
    `created_at`        DATETIME      NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
    `updated_at`        DATETIME      NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间',
    PRIMARY KEY (`id`),
    UNIQUE KEY `uk_bangumi_id` (`bangumi_id`),
    INDEX `idx_subject_air_date` (`air_date`),
    INDEX `idx_subject_score` (`score`),
    INDEX `idx_subject_rank` (`rank`),
    INDEX `idx_subject_name_cn` (`name_cn`),
    INDEX `idx_subject_type` (`type`),
    INDEX `idx_subject_import_status` (`import_status`),
    INDEX `idx_subject_air_weekday` (`air_weekday`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci
  COMMENT='条目表（动漫）';


-- ========================================================================
-- 3. 剧集表 (episode)
-- 存储每个条目的剧集列表，通过 subject_id 关联条目
-- Java 实体: top.zhaizz.animetracker.subject.entity.Episode
-- MyBatis Mapper: subject.mapper.EpisodeMapper
-- ========================================================================
CREATE TABLE `episode` (
    `id`              BIGINT        NOT NULL AUTO_INCREMENT  COMMENT '剧集ID',
    `subject_id`      BIGINT        NOT NULL                 COMMENT '所属条目ID',
    `bangumi_ep_id`   INT           DEFAULT NULL             COMMENT 'Bangumi 剧集ID（字段名 bangumiEpId）',
    `type`            TINYINT       NOT NULL DEFAULT 0       COMMENT '剧集类型: 0=本篇, 1=SP, 2=OP, 3=ED, 4=预告',
    `sort`            DECIMAL(5,1)  DEFAULT NULL             COMMENT '集数序号（BigDecimal，支持 1.5 等小数）',
    `name`            VARCHAR(255)  DEFAULT NULL             COMMENT '日文/英文标题',
    `name_cn`         VARCHAR(255)  DEFAULT NULL             COMMENT '中文标题',
    `duration`        VARCHAR(16)   DEFAULT NULL             COMMENT '时长（如 "24m"）',
    `airdate`         DATE          DEFAULT NULL             COMMENT '播出日期（字段名 airdate，小写 d，非 airDate）',
    `description`     TEXT          DEFAULT NULL             COMMENT '剧情简介',
    `status`          VARCHAR(4)    NOT NULL DEFAULT 'NA'    COMMENT '播出状态: Air=已播出, Today=今日播出, NA=未播出',
    `created_at`      DATETIME      NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
    -- 注意：Episode 实体无 updatedAt 字段，表内也无 updated_at 列
    PRIMARY KEY (`id`),
    INDEX `idx_ep_subject_sort` (`subject_id`, `sort`),
    INDEX `idx_ep_airdate` (`airdate`),
    INDEX `idx_ep_status` (`status`),
    CONSTRAINT `fk_ep_subject` FOREIGN KEY (`subject_id`) REFERENCES `subject`(`id`)
        ON DELETE CASCADE ON UPDATE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci
  COMMENT='剧集表';


-- ========================================================================
-- 4. 社区标签表 (subject_tag)
-- 存储条目关联的社区标签，每个条目可关联多个标签，每个标签可被多个条目使用
-- Java 实体: top.zhaizz.animetracker.subject.entity.SubjectTag
-- MyBatis Mapper: subject.mapper.SubjectTagMapper
-- ========================================================================
CREATE TABLE `subject_tag` (
    `id`          BIGINT       NOT NULL AUTO_INCREMENT  COMMENT '标签关联ID',
    `subject_id`  BIGINT       NOT NULL                 COMMENT '条目ID',
    `name`        VARCHAR(32)  NOT NULL                 COMMENT '标签名',
    `count`       INT          NOT NULL DEFAULT 0       COMMENT '该标签在此条目上的使用次数（来自 Bangumi API）',
    PRIMARY KEY (`id`),
    UNIQUE KEY `uk_subject_tag` (`subject_id`, `name`),
    INDEX `idx_tag_name` (`name`),
    INDEX `idx_tag_subject_id` (`subject_id`),
    CONSTRAINT `fk_tag_subject` FOREIGN KEY (`subject_id`) REFERENCES `subject`(`id`)
        ON DELETE CASCADE ON UPDATE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci
  COMMENT='条目-标签关联表';


-- ========================================================================
-- 5. 导入记录表 (import_record)
-- 记录每次数据导入的执行情况，用于查看导入状态
-- Phase 4 数据导入器使用此表记录导入日志
-- ========================================================================
CREATE TABLE IF NOT EXISTS `import_record` (
    `id`             BIGINT       NOT NULL AUTO_INCREMENT  COMMENT '记录ID',
    `mode`           VARCHAR(16)  NOT NULL                 COMMENT '导入模式: full, recent, season, since',
    `season_key`     VARCHAR(32)  DEFAULT NULL             COMMENT '季度标识（如 2026-spring）',
    `started_at`     DATETIME     NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT '开始时间',
    `completed_at`   DATETIME     DEFAULT NULL             COMMENT '完成时间',
    `status`         VARCHAR(16)  NOT NULL DEFAULT 'RUNNING' COMMENT '状态: RUNNING, COMPLETED, FAILED',
    `subject_count`  INT          NOT NULL DEFAULT 0       COMMENT '本次导入的条目数',
    `error_message`  TEXT         DEFAULT NULL             COMMENT '错误信息（失败时记录）',
    `created_at`     DATETIME     NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
    PRIMARY KEY (`id`),
    INDEX `idx_import_status` (`status`),
    INDEX `idx_import_started_at` (`started_at`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci
  COMMENT='导入记录表';


-- ========================================================================
-- 6. 收藏表 (collection) — 预留，第二阶段实现
-- 表结构尚未最终定稿，以下仅为预留占位
-- ========================================================================
-- CREATE TABLE `collection` (
--     `id`          BIGINT    NOT NULL AUTO_INCREMENT,
--     `user_id`     BIGINT    NOT NULL,
--     `subject_id`  BIGINT    NOT NULL,
--     `type`        TINYINT   NOT NULL DEFAULT 0  COMMENT '0=想看, 1=在看, 2=看过, 3=搁置, 4=抛弃',
--     `rate`        TINYINT   DEFAULT NULL         COMMENT '评分 (1-10)',
--     `comment`     TEXT      DEFAULT NULL         COMMENT '评论',
--     `created_at`  DATETIME  NOT NULL DEFAULT CURRENT_TIMESTAMP,
--     `updated_at`  DATETIME  NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
--     PRIMARY KEY (`id`),
--     UNIQUE KEY `uk_user_subject` (`user_id`, `subject_id`),
--     FOREIGN KEY (`user_id`) REFERENCES `user`(`id`) ON DELETE CASCADE,
--     FOREIGN KEY (`subject_id`) REFERENCES `subject`(`id`) ON DELETE CASCADE
-- ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci
--   COMMENT='用户收藏表（预留）';


-- ========================================================================
-- 初始化种子数据
-- ========================================================================

-- 创建默认管理员账号
-- 密码: admin123 (BCrypt hash)
-- 注意: 生产环境请务必修改此密码
INSERT INTO `user` (`username`, `password`, `email`, `nickname`, `role`, `created_at`, `updated_at`)
VALUES (
    'admin',
    '$2a$10$N9qo8uLOickgx2ZMRZoMyeIjZAgcfl7p92ldGxad68LJZdL17lhWy',
    'admin@animetracker.local',
    '管理员',
    'ADMIN',
    NOW(),
    NOW()
) ON DUPLICATE KEY UPDATE `nickname` = VALUES(`nickname`);


-- ========================================================================
-- 字段兼容性速查（重构版 Java 实体 ↔ 数据库字段映射）
-- ========================================================================
--
-- Subject.java 实体字段 ↔ subject 表字段:
--   bangumiId (Integer)   ↔ bangumi_id (INT, NOT NULL, UNIQUE)
--   image (String)        ↔ image (VARCHAR(512))   — 字段名为 image，非 imageUrl
--   airDate (LocalDate)   ↔ air_date (DATE)
--   score (BigDecimal)    ↔ score (DECIMAL(3,1))
--   eps (Integer)         ↔ eps (INT)
--   volumes (Integer)     ↔ volumes (INT)
--   rank (Integer)        ↔ rank (INT)
--   nsfw (Boolean)        ↔ nsfw (TINYINT(1))
--   importStatus (Integer)↔ import_status (TINYINT)
--
-- Episode.java 实体字段 ↔ episode 表字段:
--   bangumiEpId (Integer) ↔ bangumi_ep_id (INT)    — 字段名为 bangumiEpId，非 bangumiId
--   sort (BigDecimal)     ↔ sort (DECIMAL(5,1))    — 支持 1.5 等小数排序
--   airdate (LocalDate)   ↔ airdate (DATE)          — 字段名为 airdate（小写 d）
--   无 updatedAt 字段     ↔ 无 updated_at 列        — Episode 实体无更新时间
--   description (String)  ↔ description (TEXT)
--   status (String)       ↔ status (VARCHAR(4))
--
-- SubjectTag.java:
--   实体字段与表字段一一对应，无差异
-- ========================================================================
