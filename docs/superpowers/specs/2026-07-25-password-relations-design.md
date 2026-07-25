# 密码管理 + 条目关联后端设计

## 1. 密码管理

### 1.1 修改密码

**端点**：`PUT /api/user/me/password`

**认证**：需登录

**DTO** (`ChangePasswordDTO`)：

| 字段 | 类型 | 必填 | 约束 |
|------|------|------|------|
| oldPassword | String | 是 | — |
| newPassword | String | 是 | @Size(min=6, max=128) |

**返回**：`Result<Void>`

**逻辑**：
1. 从 `SecurityUtil.getCurrentUserId()` 获取当前用户
2. `passwordEncoder.matches(oldPassword, user.password)` — 不匹配抛 `UNAUTHORIZED`
3. 新密码 BCrypt 加密，更新 DB

**VO**：无（返回 `Result<Void>`）

### 1.2 忘记密码 — 发送重置验证码

**端点**：`POST /api/user/auth/forgot-password`

**认证**：公开

**DTO** (`ForgotPasswordDTO`)：

| 字段 | 类型 | 必填 | 约束 |
|------|------|------|------|
| email | String | 是 | @Email |

**返回**：`Result<Void>`

**逻辑**：
1. 查邮箱是否存在，不存在静默返回成功（防枚举）
2. 生成 6 位验证码，存入 Redis key `auth:password-reset:{email}`，TTL 5 分钟
3. 发邮件

### 1.3 忘记密码 — 重置密码

**端点**：`POST /api/user/auth/reset-password`

**认证**：公开

**DTO** (`ResetPasswordDTO`)：

| 字段 | 类型 | 必填 | 约束 |
|------|------|------|------|
| email | String | 是 | @Email |
| code | String | 是 | @Size(min=6, max=6) |
| newPassword | String | 是 | @Size(min=6, max=128) |

**返回**：`Result<Void>`

**逻辑**：
1. 从 Redis 取 `auth:password-reset:{email}` 验证码，校验
2. 查用户
3. BCrypt 加密新密码，更新 DB
4. 通过 Redis Set `auth:user-tokens:{userId}` 获取该用户所有活跃 token hash，逐个删除 `auth:token:{hash}`，最后删除 Set（全部登出）
5. 删除验证码 key

### 1.4 代码变动

| 模块 | 文件 | 变更 |
|------|------|------|
| pojo | `ChangePasswordDTO.java` | 新建 |
| pojo | `ForgotPasswordDTO.java` | 新建 |
| pojo | `ResetPasswordDTO.java` | 新建 |
| client | `AuthController.java` | 加 `forgotPassword`、`resetPassword` |
| client | `UserController.java` | 加 `changePassword` |
| client | `AuthService.java` | 加 `forgotPassword`、`resetPassword` |
| client | `AuthServiceImpl.java` | 实现 `forgotPassword`、`resetPassword`；`login` 中新增维护 `auth:user-tokens:{userId}` Set；`logout` 中新增从 Set 移除 |
| client | `ClientUserService.java` | 加 `changePassword` |
| client | `ClientUserServiceImpl.java` | 实现 |
| client | `VerificationService.java` | 加 `sendPasswordResetCode`、`verifyPasswordResetCode` |
| client | `VerificationServiceImpl.java` | 实现。注意 `verifyPasswordResetCode` 只校验验证码，不修改 `email_verified` 字段 |
| common | `SecurityConfig.java` | 公开 `/api/user/auth/forgot-password`、`/api/user/auth/reset-password` |

### 1.5 Redis Key 设计

| 用途 | Key 格式 | TTL |
|------|----------|-----|
| 重置密码验证码 | `auth:password-reset:{email}` | 5min |
| 已有 token 白名单 | `auth:token:{sha256(token)}` | 沿用 jwt.expiration |
| 用户活跃 token 索引 | `auth:user-tokens:{userId}` | 无（Set） |

`auth:user-tokens:{userId}` 是一个 Redis Set，存该用户所有活跃 token 的 SHA256。
- **登录时**：`sadd` + 写入 `auth:token:{hash}`
- **注销时**：从 Set 移除 + 删除 `auth:token:{hash}`
- **重置密码时**：`smembers` 遍历删除所有 `auth:token:{hash}` + 删除 Set

现有 `AuthServiceImpl.login` 和 `logout` 需同步修改以维护此 Set。

## 2. 条目关联

### 2.1 数据库

```sql
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
```

### 2.2 后端代码变动

| 模块 | 文件 | 变更 |
|------|------|------|
| pojo | `SubjectRelation.java` | 新建 Entity：id, subjectId, relatedSubjectId, relation |
| pojo | `SubjectRelationVO.java` | 新建 VO：relation, relatedSubject (SubjectListVO) |
| pojo | `SubjectDetailVO.java` | 加 `List<SubjectRelationVO> relations`（默认为空列表） |
| client | `SubjectRelationMapper.java` | 新建，`BaseMapper<SubjectRelation>` + `findBySubjectId` |
| client | `SubjectConverter.java` | 加 `toSubjectRelationVO` 方法：接收 relation entity + relatedSubject entity → SubjectRelationVO |
| client | `ClientSubjectServiceImpl.java` | `getSubjectDetail` 中先查 relation 列表，再逐个查 relatedSubject，最后拼入 VO |

组装方式（Service 层）：

```java
List<SubjectRelation> relations = subjectRelationMapper.findBySubjectId(id);
List<SubjectRelationVO> relationVOs = relations.stream().map(rel -> {
    Subject related = subjectMapper.selectById(rel.getRelatedSubjectId());
    return SubjectConverter.toSubjectRelationVO(rel, related);
}).filter(Objects::nonNull).collect(Collectors.toList());
detailVO.setRelations(relationVOs);
```

relations 数量很少（通常 <10），单个 selectById 即可，无需批量优化。

### 2.3 导入脚本变动

| 文件 | 变更 |
|------|------|
| `client.py` | 加 `get_relations(subject_id)` → `GET /v0/subjects/{subject_id}/subjects` |
| `db.py` | 加 `upsert_relations(session, subject_id, relations)` — 先删原条目的全部关联后插。**双向写入**：A→prequel→B 时同时写 A→prequel→B 和 B→sequel→A。**FK 保护**：写入前检查 `related_subject_id` 在 subject 表是否存在，不存在则跳过该条 |
| `main.py` | `import_single_subject` 中获取剧集后调用 `client.get_relations(bangumi_id)` + `upsert_relations(db, subject_id, relations)` |

### 2.4 Mapper XML

路径：`backend/business/client/src/main/resources/mapper/SubjectRelationMapper.xml`

```xml
<select id="findBySubjectId" resultType="top.zhaizz.pojo.entity.SubjectRelation">
    SELECT * FROM subject_relation WHERE subject_id = #{subjectId}
</select>
```

### 2.5 只读约定

关联数据仅由导入同步写入，后端不暴露写 API（无管理端点）。详情页 GET 时自动返回 `relations` 字段。

## 3. 不包含范围

- 前端修改（由后续前端计划覆盖）
- 评论/吐槽
- 用户统计
- 单条目手动同步
