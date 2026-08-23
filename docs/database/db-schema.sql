/*
 Navicat Premium Data Transfer

 Source Server         : 阿里云
 Source Server Type    : MySQL
 Source Server Version : 80409
 Source Host           : 47.96.127.231:3306
 Source Schema         : anime_tracker

 Target Server Type    : MySQL
 Target Server Version : 80409
 File Encoding         : 65001

 Date: 07/07/2026 17:28:21
*/

SET NAMES utf8mb4;
SET FOREIGN_KEY_CHECKS = 0;

-- ----------------------------
-- Table structure for episode
-- ----------------------------
DROP TABLE IF EXISTS `episode`;
CREATE TABLE `episode`  (
  `id` bigint NOT NULL AUTO_INCREMENT COMMENT '剧集ID',
  `subject_id` bigint NOT NULL COMMENT '所属条目ID',
  `bangumi_ep_id` int NULL DEFAULT NULL COMMENT 'Bangumi 剧集ID',
  `type` tinyint NOT NULL DEFAULT 0 COMMENT '剧集类型: 0=本篇, 1=SP, 2=OP, 3=ED, 4=预告',
  `sort` decimal(5, 1) NULL DEFAULT NULL COMMENT '集数序号（支持小数点: 1, 1.5, 2 等）',
  `name` varchar(255) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci NULL DEFAULT NULL COMMENT '日文/英文标题',
  `name_cn` varchar(255) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci NULL DEFAULT NULL COMMENT '中文标题',
  `duration` varchar(16) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci NULL DEFAULT NULL COMMENT '时长（如 \"24m\"）',
  `airdate` date NULL DEFAULT NULL COMMENT '播出日期',
  `description` text CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci NULL COMMENT '剧情简介',
  `status` varchar(5) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci NOT NULL DEFAULT 'NA' COMMENT '播出状态: Air=已播出, Today=今日播出, NA=未播出',
  `created_at` datetime NOT NULL COMMENT '创建时间',
  PRIMARY KEY (`id`) USING BTREE,
  INDEX `idx_ep_subject_sort`(`subject_id` ASC, `sort` ASC) USING BTREE,
  INDEX `idx_ep_airdate`(`airdate` ASC) USING BTREE,
  INDEX `idx_ep_status`(`status` ASC) USING BTREE,
  CONSTRAINT `fk_ep_subject` FOREIGN KEY (`subject_id`) REFERENCES `subject` (`id`) ON DELETE CASCADE ON UPDATE CASCADE
) ENGINE = InnoDB AUTO_INCREMENT = 1 CHARACTER SET = utf8mb4 COLLATE = utf8mb4_unicode_ci COMMENT = '剧集表' ROW_FORMAT = Dynamic;

-- ----------------------------
-- Table structure for import_record
-- ----------------------------
DROP TABLE IF EXISTS `import_record`;
CREATE TABLE `import_record`  (
  `id` bigint NOT NULL AUTO_INCREMENT COMMENT '记录ID',
  `mode` varchar(16) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci NOT NULL COMMENT '导入模式: full, recent, season, since',
  `season_key` varchar(32) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci NULL DEFAULT NULL COMMENT '季度标识（如 2026-spring）',
  `started_at` datetime NOT NULL COMMENT '开始时间',
  `completed_at` datetime NULL DEFAULT NULL COMMENT '完成时间',
  `status` varchar(16) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci NOT NULL DEFAULT 'RUNNING' COMMENT '状态: RUNNING, COMPLETED, FAILED',
  `subject_count` int NOT NULL DEFAULT 0 COMMENT '本次导入的条目数',
  `error_message` text CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci NULL COMMENT '错误信息（失败时记录）',
  `checkpoint_json` json NULL COMMENT '导入断点 JSON',
  `scanned_count` int NOT NULL DEFAULT 0 COMMENT '已扫描条目数',
  `success_count` int NOT NULL DEFAULT 0 COMMENT '成功处理条目数',
  `failure_count` int NOT NULL DEFAULT 0 COMMENT '失败处理条目数',
  `skipped_count` int NOT NULL DEFAULT 0 COMMENT '跳过条目数',
  `source_snapshot_at` datetime NULL DEFAULT NULL COMMENT '源数据快照时间',
  `heartbeat_at` datetime NULL DEFAULT NULL COMMENT '最近任务心跳时间',
  `created_at` datetime NOT NULL COMMENT '创建时间',
  PRIMARY KEY (`id`) USING BTREE,
  INDEX `idx_import_status`(`status` ASC) USING BTREE,
  INDEX `idx_import_started_at`(`started_at` ASC) USING BTREE
) ENGINE = InnoDB AUTO_INCREMENT = 1 CHARACTER SET = utf8mb4 COLLATE = utf8mb4_unicode_ci COMMENT = '导入记录表' ROW_FORMAT = Dynamic;

-- ----------------------------
-- Table structure for subject
-- ----------------------------
DROP TABLE IF EXISTS `subject`;
CREATE TABLE `subject`  (
  `id` bigint NOT NULL AUTO_INCREMENT COMMENT '条目ID',
  `bangumi_id` int NOT NULL COMMENT 'Bangumi API 条目ID',
  `name` varchar(255) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci NOT NULL COMMENT '日文/英文名',
  `name_cn` varchar(255) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci NULL DEFAULT NULL COMMENT '中文名',
  `summary` text CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci NULL COMMENT '简介/描述',
  `type` tinyint NOT NULL DEFAULT 2 COMMENT '条目类型: 2=动画（本项目仅使用动画类型）',
  `eps` int NULL DEFAULT NULL COMMENT '总集数',
  `volumes` int NULL DEFAULT NULL COMMENT '总卷数',
  `air_date` date NULL DEFAULT NULL COMMENT '播出日期',
  `air_weekday` tinyint NULL DEFAULT NULL COMMENT '播出星期（0=周日, 1=周一 ... 6=周六）',
  `image` varchar(512) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci NULL DEFAULT NULL COMMENT '封面图URL',
  `score` decimal(3, 1) NULL DEFAULT NULL COMMENT 'Bangumi 评分（0.0~10.0）',
  `rank` int NULL DEFAULT NULL COMMENT 'Bangumi 排名',
  `collection_total` int NULL DEFAULT NULL COMMENT '收藏数',
  `rating_total` int NULL DEFAULT NULL COMMENT '评分总人数',
  `rating_count_json` json NULL COMMENT '各评分人数 JSON',
  `collection_wish` int NULL DEFAULT NULL COMMENT '想看人数',
  `collection_collect` int NULL DEFAULT NULL COMMENT '看过人数',
  `collection_doing` int NULL DEFAULT NULL COMMENT '在看人数',
  `collection_on_hold` int NULL DEFAULT NULL COMMENT '搁置人数',
  `collection_dropped` int NULL DEFAULT NULL COMMENT '抛弃人数',
  `image_source_url` varchar(512) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci NULL DEFAULT NULL COMMENT '原始封面 URL',
  `image_storage_status` varchar(24) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci NOT NULL DEFAULT 'PENDING' COMMENT '封面存储状态',
  `image_checked_at` datetime NULL DEFAULT NULL COMMENT '最近封面检查时间',
  `source_fetched_at` datetime NULL DEFAULT NULL COMMENT '本系统最近成功抓取源详情时间',
  `nsfw` tinyint(1) NOT NULL DEFAULT 0 COMMENT '是否 NSFW: 0=否, 1=是',
  `import_status` tinyint NOT NULL DEFAULT 0 COMMENT '导入状态: 0=待导入, 1=已导入',
  `last_imported_at` datetime NULL DEFAULT NULL COMMENT '最近导入时间',
  `created_at` datetime NOT NULL COMMENT '创建时间',
  `updated_at` datetime NOT NULL COMMENT '更新时间',
  PRIMARY KEY (`id`) USING BTREE,
  UNIQUE INDEX `uk_bangumi_id`(`bangumi_id` ASC) USING BTREE,
  INDEX `idx_subject_air_date`(`air_date` ASC) USING BTREE,
  INDEX `idx_subject_score`(`score` ASC) USING BTREE,
  INDEX `idx_subject_rank`(`rank` ASC) USING BTREE,
  INDEX `idx_subject_name_cn`(`name_cn` ASC) USING BTREE,
  INDEX `idx_subject_type`(`type` ASC) USING BTREE,
  INDEX `idx_subject_import_status`(`import_status` ASC) USING BTREE,
  INDEX `idx_subject_air_weekday`(`air_weekday` ASC) USING BTREE
) ENGINE = InnoDB AUTO_INCREMENT = 1 CHARACTER SET = utf8mb4 COLLATE = utf8mb4_unicode_ci COMMENT = '条目表（动漫）' ROW_FORMAT = Dynamic;

-- ----------------------------
-- Table structure for subject_alias
-- ----------------------------
DROP TABLE IF EXISTS `subject_alias`;
CREATE TABLE `subject_alias`  (
  `id` bigint NOT NULL AUTO_INCREMENT COMMENT '别名 ID',
  `subject_id` bigint NOT NULL COMMENT '条目 ID',
  `name` varchar(255) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci NOT NULL COMMENT '别名',
  `language` varchar(8) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci NOT NULL DEFAULT 'und' COMMENT '语言',
  `source` varchar(32) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci NOT NULL COMMENT '来源',
  `created_at` datetime NOT NULL COMMENT '创建时间',
  `updated_at` datetime NOT NULL COMMENT '更新时间',
  PRIMARY KEY (`id`) USING BTREE,
  UNIQUE INDEX `uk_subject_alias`(`subject_id` ASC, `name` ASC) USING BTREE,
  INDEX `idx_alias_name`(`name` ASC) USING BTREE,
  CONSTRAINT `fk_alias_subject` FOREIGN KEY (`subject_id`) REFERENCES `subject` (`id`) ON DELETE CASCADE ON UPDATE CASCADE
) ENGINE = InnoDB AUTO_INCREMENT = 1 CHARACTER SET = utf8mb4 COLLATE = utf8mb4_unicode_ci COMMENT = '条目别名表' ROW_FORMAT = Dynamic;

-- ----------------------------
-- Table structure for subject_meta_tag
-- ----------------------------
DROP TABLE IF EXISTS `subject_meta_tag`;
CREATE TABLE `subject_meta_tag`  (
  `id` bigint NOT NULL AUTO_INCREMENT COMMENT '官方标签关联 ID',
  `subject_id` bigint NOT NULL COMMENT '条目 ID',
  `name` varchar(255) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci NOT NULL COMMENT '官方标签名',
  `created_at` datetime NOT NULL COMMENT '创建时间',
  PRIMARY KEY (`id`) USING BTREE,
  UNIQUE INDEX `uk_subject_meta_tag`(`subject_id` ASC, `name` ASC) USING BTREE,
  INDEX `idx_meta_tag_name`(`name` ASC) USING BTREE,
  CONSTRAINT `fk_meta_tag_subject` FOREIGN KEY (`subject_id`) REFERENCES `subject` (`id`) ON DELETE CASCADE ON UPDATE CASCADE
) ENGINE = InnoDB AUTO_INCREMENT = 1 CHARACTER SET = utf8mb4 COLLATE = utf8mb4_unicode_ci COMMENT = '条目官方标签表' ROW_FORMAT = Dynamic;

-- ----------------------------
-- Table structure for subject_credit
-- ----------------------------
DROP TABLE IF EXISTS `subject_credit`;
CREATE TABLE `subject_credit`  (
  `id` bigint NOT NULL AUTO_INCREMENT COMMENT '主创关联 ID',
  `subject_id` bigint NOT NULL COMMENT '条目 ID',
  `bangumi_person_id` int NULL DEFAULT NULL COMMENT 'Bangumi 人物 ID',
  `name` varchar(255) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci NOT NULL COMMENT '主创或组织名称',
  `role` varchar(64) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci NOT NULL COMMENT '职责',
  `credit_type` varchar(16) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci NOT NULL COMMENT 'PERSON 或 ORGANIZATION',
  `sort_order` int NOT NULL DEFAULT 0 COMMENT '来源排序',
  `created_at` datetime NOT NULL COMMENT '创建时间',
  `updated_at` datetime NOT NULL COMMENT '更新时间',
  PRIMARY KEY (`id`) USING BTREE,
  UNIQUE INDEX `uk_subject_credit`(`subject_id` ASC, `name` ASC, `role` ASC) USING BTREE,
  INDEX `idx_credit_name_role`(`name` ASC, `role` ASC) USING BTREE,
  CONSTRAINT `fk_credit_subject` FOREIGN KEY (`subject_id`) REFERENCES `subject` (`id`) ON DELETE CASCADE ON UPDATE CASCADE
) ENGINE = InnoDB AUTO_INCREMENT = 1 CHARACTER SET = utf8mb4 COLLATE = utf8mb4_unicode_ci COMMENT = '条目主创表' ROW_FORMAT = Dynamic;

-- ----------------------------
-- Table structure for rag_index_job
-- ----------------------------
DROP TABLE IF EXISTS `rag_index_job`;
CREATE TABLE `rag_index_job`  (
  `id` bigint NOT NULL AUTO_INCREMENT COMMENT '索引任务 ID',
  `subject_id` bigint NOT NULL COMMENT '条目 ID',
  `index_version` varchar(32) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci NOT NULL COMMENT '索引版本',
  `content_hash` char(64) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci NOT NULL COMMENT '档案内容哈希',
  `embedding_provider` varchar(32) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci NOT NULL COMMENT 'Embedding 供应商',
  `embedding_model` varchar(64) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci NOT NULL COMMENT 'Embedding 模型',
  `embedding_dimensions` int NOT NULL COMMENT '向量维度',
  `status` varchar(16) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci NOT NULL DEFAULT 'PENDING' COMMENT '任务状态',
  `attempts` int NOT NULL DEFAULT 0 COMMENT '尝试次数',
  `last_error_code` varchar(64) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci NULL DEFAULT NULL COMMENT '最近错误码',
  `last_error_message` varchar(512) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci NULL DEFAULT NULL COMMENT '脱敏后的最近错误信息',
  `next_retry_at` datetime NULL DEFAULT NULL COMMENT '下次重试时间',
  `indexed_at` datetime NULL DEFAULT NULL COMMENT '完成索引时间',
  `created_at` datetime NOT NULL COMMENT '创建时间',
  `updated_at` datetime NOT NULL COMMENT '更新时间',
  PRIMARY KEY (`id`) USING BTREE,
  UNIQUE INDEX `uk_rag_job_subject_version`(`subject_id` ASC, `index_version` ASC) USING BTREE,
  INDEX `idx_rag_job_status_retry`(`status` ASC, `next_retry_at` ASC) USING BTREE,
  CONSTRAINT `fk_rag_job_subject` FOREIGN KEY (`subject_id`) REFERENCES `subject` (`id`) ON DELETE CASCADE ON UPDATE CASCADE
) ENGINE = InnoDB AUTO_INCREMENT = 1 CHARACTER SET = utf8mb4 COLLATE = utf8mb4_unicode_ci COMMENT = 'RAG 索引任务表' ROW_FORMAT = Dynamic;

-- ----------------------------
-- Table structure for subject_tag
-- ----------------------------
DROP TABLE IF EXISTS `subject_tag`;
CREATE TABLE `subject_tag`  (
  `id` bigint NOT NULL AUTO_INCREMENT COMMENT '标签关联ID',
  `subject_id` bigint NOT NULL COMMENT '条目ID',
  `name` varchar(32) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci NOT NULL COMMENT '标签名',
  `count` int NOT NULL DEFAULT 0 COMMENT '该标签在此条目上的使用次数（来自 Bangumi API）',
  PRIMARY KEY (`id`) USING BTREE,
  UNIQUE INDEX `uk_subject_tag`(`subject_id` ASC, `name` ASC) USING BTREE,
  INDEX `idx_tag_name`(`name` ASC) USING BTREE,
  INDEX `idx_tag_subject_id`(`subject_id` ASC) USING BTREE,
  CONSTRAINT `fk_tag_subject` FOREIGN KEY (`subject_id`) REFERENCES `subject` (`id`) ON DELETE CASCADE ON UPDATE CASCADE
) ENGINE = InnoDB AUTO_INCREMENT = 1 CHARACTER SET = utf8mb4 COLLATE = utf8mb4_unicode_ci COMMENT = '条目-标签关联表' ROW_FORMAT = Dynamic;

-- ----------------------------
-- Table structure for user
-- ----------------------------
DROP TABLE IF EXISTS `user`;
CREATE TABLE `user`  (
  `id` bigint NOT NULL AUTO_INCREMENT COMMENT '用户ID',
  `username` varchar(32) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci NOT NULL COMMENT '用户名（唯一）',
  `password` varchar(255) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci NOT NULL COMMENT '密码（BCrypt 加密存储）',
  `email` varchar(128) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci NULL DEFAULT NULL COMMENT '邮箱',
  `nickname` varchar(64) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci NULL DEFAULT NULL COMMENT '昵称',
  `avatar` varchar(512) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci NULL DEFAULT NULL COMMENT '头像URL',
  `role` varchar(16) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci NOT NULL DEFAULT 'USER' COMMENT '角色: USER=普通用户, ADMIN=管理员',
  `email_verified` tinyint(1) NOT NULL DEFAULT 0 COMMENT '邮箱是否已验证',
  `created_at` datetime NOT NULL COMMENT '创建时间',
  `updated_at` datetime NOT NULL COMMENT '更新时间',
  PRIMARY KEY (`id`) USING BTREE,
  UNIQUE INDEX `uk_username`(`username` ASC) USING BTREE,
  UNIQUE INDEX `uk_email`(`email` ASC) USING BTREE,
  INDEX `idx_user_role`(`role` ASC) USING BTREE,
  INDEX `idx_user_created_at`(`created_at` ASC) USING BTREE
) ENGINE = InnoDB AUTO_INCREMENT = 3 CHARACTER SET = utf8mb4 COLLATE = utf8mb4_unicode_ci COMMENT = '用户表' ROW_FORMAT = Dynamic;

-- ----------------------------
-- Table structure for user_collection
-- ----------------------------
DROP TABLE IF EXISTS `user_collection`;
CREATE TABLE `user_collection`  (
  `id` bigint NOT NULL AUTO_INCREMENT COMMENT '收藏ID',
  `user_id` bigint NOT NULL COMMENT '用户ID',
  `subject_id` bigint NOT NULL COMMENT '条目ID',
  `type` tinyint NOT NULL COMMENT '收藏状态: 1=想看, 2=看过, 3=在看, 4=搁置, 5=抛弃',
  `rate` tinyint NOT NULL DEFAULT 0 COMMENT '评分（0~10, 0 表示未评分）',
  `ep_status` int NOT NULL DEFAULT 0 COMMENT '看到第几集',
  `created_at` datetime NOT NULL COMMENT '创建时间',
  `updated_at` datetime NOT NULL COMMENT '更新时间',
  PRIMARY KEY (`id`) USING BTREE,
  UNIQUE INDEX `uk_user_subject`(`user_id` ASC, `subject_id` ASC) USING BTREE,
  INDEX `idx_uc_user_id`(`user_id` ASC) USING BTREE,
  INDEX `idx_uc_subject_id`(`subject_id` ASC) USING BTREE,
  INDEX `idx_uc_type`(`type` ASC) USING BTREE,
  INDEX `idx_uc_updated_at`(`updated_at` ASC) USING BTREE,
  CONSTRAINT `fk_uc_user` FOREIGN KEY (`user_id`) REFERENCES `user` (`id`) ON DELETE CASCADE ON UPDATE CASCADE,
  CONSTRAINT `fk_uc_subject` FOREIGN KEY (`subject_id`) REFERENCES `subject` (`id`) ON DELETE CASCADE ON UPDATE CASCADE
) ENGINE = InnoDB AUTO_INCREMENT = 1 CHARACTER SET = utf8mb4 COLLATE = utf8mb4_unicode_ci COMMENT = '用户追番收藏表' ROW_FORMAT = Dynamic;

SET FOREIGN_KEY_CHECKS = 1;

-- ----------------------------
-- Table structure for subject_relation
-- ----------------------------
DROP TABLE IF EXISTS `subject_relation`;
CREATE TABLE `subject_relation`  (
  `id`                 bigint       NOT NULL AUTO_INCREMENT COMMENT '关联ID',
  `subject_id`         bigint       NOT NULL COMMENT '当前条目ID',
  `related_subject_id` bigint       NOT NULL COMMENT '关联条目ID',
  `relation`           varchar(32)  CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci NOT NULL COMMENT '关联类型: prequel, sequel, side_story 等',
  PRIMARY KEY (`id`) USING BTREE,
  UNIQUE INDEX `uk_subject_relation`(`subject_id` ASC, `related_subject_id` ASC) USING BTREE,
  INDEX `idx_sr_subject`(`subject_id` ASC) USING BTREE,
  INDEX `idx_sr_related`(`related_subject_id` ASC) USING BTREE,
  CONSTRAINT `fk_sr_subject` FOREIGN KEY (`subject_id`) REFERENCES `subject` (`id`) ON DELETE CASCADE ON UPDATE CASCADE,
  CONSTRAINT `fk_sr_related` FOREIGN KEY (`related_subject_id`) REFERENCES `subject` (`id`) ON DELETE CASCADE ON UPDATE CASCADE
) ENGINE = InnoDB AUTO_INCREMENT = 1 CHARACTER SET = utf8mb4 COLLATE = utf8mb4_unicode_ci COMMENT = '条目关联表' ROW_FORMAT = Dynamic;

-- ----------------------------
-- Table structure for operation_log
-- ----------------------------
DROP TABLE IF EXISTS `operation_log`;
CREATE TABLE `operation_log`  (
  `id`          bigint       NOT NULL AUTO_INCREMENT COMMENT '日志ID',
  `user_id`     bigint       NULL DEFAULT NULL COMMENT '用户ID（匿名失败登录为NULL）',
  `username`    varchar(64)  CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci NULL DEFAULT NULL COMMENT '用户名/邮箱快照',
  `action`      varchar(32)  CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci NOT NULL COMMENT '动作: LOGIN/LOGOUT/REGISTER/SUBJECT_CREATE/SUBJECT_UPDATE/SUBJECT_DELETE/ROLE_CHANGE/IMPORT_RUN',
  `module`      varchar(32)  CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci NOT NULL COMMENT '模块: AUTH/USER/SUBJECT/IMPORT/ADMIN',
  `method`      varchar(8)   CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci NULL DEFAULT NULL COMMENT 'HTTP 方法',
  `path`        varchar(128) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci NULL DEFAULT NULL COMMENT '请求路径',
  `params`      text         CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci NULL COMMENT '请求参数 JSON（脱敏）',
  `ip`          varchar(64)  CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci NULL DEFAULT NULL COMMENT '客户端 IP',
  `user_agent`  varchar(255) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci NULL DEFAULT NULL COMMENT 'User-Agent',
  `status`      tinyint      NOT NULL DEFAULT 0 COMMENT '0=成功, 1=失败',
  `error_msg`   text         CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci NULL COMMENT '失败原因',
  `duration_ms` bigint       NULL DEFAULT NULL COMMENT '耗时(毫秒)',
  `created_at`  datetime     NOT NULL COMMENT '创建时间',
  PRIMARY KEY (`id`) USING BTREE,
  INDEX `idx_ol_user`       (`user_id` ASC) USING BTREE,
  INDEX `idx_ol_action`     (`action` ASC) USING BTREE,
  INDEX `idx_ol_created_at` (`created_at` ASC) USING BTREE
) ENGINE = InnoDB CHARACTER SET = utf8mb4 COLLATE = utf8mb4_unicode_ci COMMENT = '操作/登录日志表' ROW_FORMAT = Dynamic;
