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
  `status` varchar(4) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci NOT NULL DEFAULT 'NA' COMMENT '播出状态: Air=已播出, Today=今日播出, NA=未播出',
  `created_at` datetime NOT NULL COMMENT '创建时间',
  PRIMARY KEY (`id`) USING BTREE,
  INDEX `idx_ep_subject_sort`(`subject_id` ASC, `sort` ASC) USING BTREE,
  INDEX `idx_ep_airdate`(`airdate` ASC) USING BTREE,
  INDEX `idx_ep_status`(`status` ASC) USING BTREE,
  CONSTRAINT `fk_ep_subject` FOREIGN KEY (`subject_id`) REFERENCES `subject` (`id`) ON DELETE CASCADE ON UPDATE CASCADE
) ENGINE = InnoDB AUTO_INCREMENT = 7467 CHARACTER SET = utf8mb4 COLLATE = utf8mb4_unicode_ci COMMENT = '剧集表' ROW_FORMAT = Dynamic;

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
  `created_at` datetime NOT NULL COMMENT '创建时间',
  PRIMARY KEY (`id`) USING BTREE,
  INDEX `idx_import_status`(`status` ASC) USING BTREE,
  INDEX `idx_import_started_at`(`started_at` ASC) USING BTREE
) ENGINE = InnoDB AUTO_INCREMENT = 12 CHARACTER SET = utf8mb4 COLLATE = utf8mb4_unicode_ci COMMENT = '导入记录表' ROW_FORMAT = Dynamic;

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
) ENGINE = InnoDB AUTO_INCREMENT = 1871 CHARACTER SET = utf8mb4 COLLATE = utf8mb4_unicode_ci COMMENT = '条目表（动漫）' ROW_FORMAT = Dynamic;

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
) ENGINE = InnoDB AUTO_INCREMENT = 52899 CHARACTER SET = utf8mb4 COLLATE = utf8mb4_unicode_ci COMMENT = '条目-标签关联表' ROW_FORMAT = Dynamic;

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
  `created_at` datetime NOT NULL COMMENT '创建时间',
  `updated_at` datetime NOT NULL COMMENT '更新时间',
  PRIMARY KEY (`id`) USING BTREE,
  UNIQUE INDEX `uk_username`(`username` ASC) USING BTREE,
  INDEX `idx_user_role`(`role` ASC) USING BTREE,
  INDEX `idx_user_created_at`(`created_at` ASC) USING BTREE
) ENGINE = InnoDB AUTO_INCREMENT = 3 CHARACTER SET = utf8mb4 COLLATE = utf8mb4_unicode_ci COMMENT = '用户表' ROW_FORMAT = Dynamic;

SET FOREIGN_KEY_CHECKS = 1;
