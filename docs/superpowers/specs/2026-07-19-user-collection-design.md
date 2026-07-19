---
name: user-collection-feature
description: 用户追番收藏功能设计——状态管理、评分、剧集进度
metadata:
  type: spec
  status: draft
  created: 2026-07-19
---

# 用户追番功能设计

## 概述

为用户提供追番收藏功能，参考 Bangumi 收藏体系，支持状态管理、评分和剧集进度追踪。

## 数据库

### user_collection 表

```sql
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
```

- 不冗余 subject 字段，列表查询时 JOIN subject 表取番剧信息
- UNIQUE 约束确保一人一条目一条记录
- `type` 值与 Bangumi 一致：1=想看, 2=看过, 3=在看, 4=搁置, 5=抛弃

## 后端

### 模块归属

所有新增代码放在 `subject` 模块。`user` 模块不依赖 `subject`，而收藏逻辑需要 JOIN subject 表，放在 subject 模块可以直接使用 SubjectMapper。

### POJO（animetracker-pojo）

**Entity** — `top.zhaizz.pojo.entity.UserCollection`

| 字段 | 类型 | 说明 |
|---|---|---|
| id | Long | 主键 |
| userId | Long | 用户 ID |
| subjectId | Long | 条目 ID |
| type | Integer | 1=想看 2=看过 3=在看 4=搁置 5=抛弃 |
| rate | Integer | 评分 0-10，0 未评分 |
| epStatus | Integer | 剧集进度 |
| createdAt | LocalDateTime | |
| updatedAt | LocalDateTime | |

**DTO** — `top.zhaizz.pojo.dto.CollectionUpdateDTO`

| 字段 | 类型 | 必填 | 说明 |
|---|---|---|---|
| type | Integer | 是 (@NotNull @Min(1) @Max(5)) | 收藏类型 |
| rate | Integer | 否 (@Min(0) @Max(10)) | 评分，null 不修改 |
| epStatus | Integer | 否 (@Min(0)) | 剧集进度，null 不修改 |

**VO** — `top.zhaizz.pojo.vo.UserCollectionVO`

| 字段 | 类型 | 说明 |
|---|---|---|
| id | Long | |
| subjectId | Long | |
| type | Integer | |
| rate | Integer | |
| epStatus | Integer | |
| subject | SubjectListVO | 复用的番剧基本信息（name, nameCn, image, score, eps 等） |

### Mapper（subject 模块）

- `CollectionMapper extends BaseMapper<UserCollection>`
- XML JOIN 查询返回扁平中间结果，通过 CollectionConverter 映射为 UserCollectionVO

**扁平中间 VO** — `pojo` 模块 `vo/UserCollectionSubjectVO.java`（仅 mapper 内部使用，含 JOIN 查出的 subject 字段）：

```java
@Data
public class UserCollectionSubjectVO {
    private Long id;            // user_collection.id
    private Long userId;
    private Long subjectId;
    private Integer type;
    private Integer rate;
    private Integer epStatus;
    private LocalDateTime createdAt;
    private LocalDateTime updatedAt;
    // subject 表的字段（扁平化）
    private String name;
    private String nameCn;
    private String image;
    private BigDecimal score;
    private Integer eps;
    private LocalDate airDate;
    private Integer subjectType;    // subject.type 别名
}
```

**XML 查询**：

```xml
<select id="selectCollectionPage" resultType="top.zhaizz.pojo.vo.UserCollectionSubjectVO">
    SELECT c.*, s.name, s.name_cn, s.image, s.score, s.eps, s.air_date,
           s.type AS subject_type
    FROM user_collection c
    JOIN subject s ON s.id = c.subject_id
    WHERE c.user_id = #{userId}
    <if test="type != null"> AND c.type = #{type} </if>
    ORDER BY c.updated_at DESC
</select>
```

### Converter（subject 模块）

新增 `CollectionConverter`，沿用现有 `SubjectConverter` 模式，将扁平结果 `UserCollectionSubjectVO` 转换为 `UserCollectionVO`（含嵌套 `SubjectListVO`）。

### Service（subject 模块）

`CollectionService`:

| 方法 | 说明 |
|---|---|
| `listCollections(userId, type, page, size)` | 分页查询，可选类型筛选，JOIN subject 表 |
| `getCollection(userId, subjectId)` | 查单个条目收藏，无则返回 null |
| `saveOrUpdate(userId, subjectId, dto)` | @Transactional，PUT 语义——先校验 subject 是否存在，不存在 INSERT，存在 UPDATE |
| `deleteCollection(userId, subjectId)` | 删除收藏 |
| `updateEpStatus(userId, subjectId, epStatus)` | 只更新剧集进度（快捷操作） |

### Controller

`CollectionController` — 路由前缀 `/api/user/collections`，需登录：

| 方法 | 路径 | 说明 |
|---|---|---|
| GET | `/api/user/collections` | 列表，?type=&page=&size= |
| GET | `/api/user/collections/{subjectId}` | 查单条收藏状态 |
| PUT | `/api/user/collections/{subjectId}` | 添加/修改收藏 |
| DELETE | `/api/user/collections/{subjectId}` | 删除收藏 |
| PATCH | `/api/user/collections/{subjectId}/ep-status` | 快捷更新剧集进度 |

## 前端

### 新增路由

```
/my-collections → MyCollections.vue，meta: { requiresAuth: true }
```

### 导航

Header 导航增加"我的追番"入口。

### MyCollections 页面

- 顶部 Tabs：全部 | 在看 | 想看 | 看过 | 搁置 | 抛弃
- 每个 tab 显示该状态下的收藏数量
- 卡片网格布局，复用 SubjectCard 样式
- 每张卡片展示：当前状态标签、评分（如有）、进度（如 "3/24 话"）
- 空状态提示

### SubjectDetail 追加区域

番剧详情页封面图下方增加追番操作区：

**未追番**：点击"追番"按钮展开状态选择菜单（想看/在看/看过/搁置/抛弃）

**已追番**：行内显示状态标签、评分、进度，提供修改状态下拉、评分编辑、进度 +1 快捷按钮、删除收藏

### 新增前端 API 类型

`types/index.ts` 新增：

```ts
export interface UserCollectionVO {
  id: number
  subjectId: number
  type: number       // 1=想看 2=看过 3=在看 4=搁置 5=抛弃
  rate: number
  epStatus: number
  subject: SubjectListItem
}

export interface CollectionUpdateDTO {
  type: number
  rate?: number
  epStatus?: number
}
```

### 新增前端 API 模块

`api/collections.ts`：

```ts
import http from './http'
import type { ApiResponse, UserCollectionVO, CollectionUpdateDTO, PageResult } from '@/types'

export const collectionsApi = {
  list(params: { type?: number; page?: number; size?: number }) {
    return http.get<ApiResponse<PageResult<UserCollectionVO>>>('/api/user/collections', { params })
  },
  get(subjectId: number) {
    return http.get<ApiResponse<UserCollectionVO>>(`/api/user/collections/${subjectId}`)
  },
  saveOrUpdate(subjectId: number, data: CollectionUpdateDTO) {
    return http.put<ApiResponse<void>>(`/api/user/collections/${subjectId}`, data)
  },
  remove(subjectId: number) {
    return http.delete<ApiResponse<void>>(`/api/user/collections/${subjectId}`)
  },
  updateEpStatus(subjectId: number, epStatus: number) {
    return http.patch<ApiResponse<void>>(`/api/user/collections/${subjectId}/ep-status`, { epStatus })
  },
}
```

## 数据库变更

新增一张表 `user_collection`，无其他 DDL 变更。

## 不包含的范围（后续考虑）

- 用户自定义标签
- 评论/短评
- 与 Bangumi 双向同步收藏
