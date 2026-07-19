# 用户追番收藏功能 Implementation Plan
# 使用中文commit message
> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 为用户提供番剧收藏功能，支持想看/在看/看过/搁置/抛弃五种状态，以及评分和剧集进度追踪。

**Architecture:** 后端在 `subject` 模块新增 CollectionController、CollectionService、CollectionMapper，通过 JOIN subject 表查询列表（不冗余字段）。前端新增 MyCollections 页面和 SubjectDetail 追番操作区，复用 SubjectCard 组件。

**Tech Stack:** Spring Boot 3.2 / MyBatis-Plus / MySQL / Vue 3 / Pinia

## Global Constraints

- POJO 实体使用 `@TableName` 注解 + camelCase-to-underscore 自动映射
- 所有 API 返回统一包装 `Result<T>` / `PageResult<T>`
- 错误抛出 `BizException(ErrorType.XXX)`，由 `GlobalExceptionHandler` 统一处理
- 当前用户 ID 从 `SecurityContextHolder` 获取（沿用现有私有方法模式）
- Controller 使用 `@RestController` + `@RequestMapping` + `@RequiredArgsConstructor` + `@Validated`（类级）
- DTO 使用 `jakarta.validation` 注解校验
- MyBatis Mapper XML 放在 `subject/src/main/resources/mapper/` 下

---

### Task 1: POJO 层 — Entity / DTO / VO

**Files:**
- Create: `backend/business/pojo/src/main/java/top/zhaizz/pojo/entity/UserCollection.java`
- Create: `backend/business/pojo/src/main/java/top/zhaizz/pojo/dto/CollectionUpdateDTO.java`
- Create: `backend/business/pojo/src/main/java/top/zhaizz/pojo/vo/UserCollectionVO.java`
- Create: `backend/business/pojo/src/main/java/top/zhaizz/pojo/vo/UserCollectionSubjectVO.java`

- [ ] **Step 1: Create entity, DTO, VOs**

UserCollection.java — entity with @TableName, fields: id, userId, subjectId, type, rate, epStatus, createdAt, updatedAt.

CollectionUpdateDTO.java — @Data, fields: type (@NotNull @Min(1) @Max(5)), rate (@Min(0) @Max(10)), epStatus (@Min(0)).

UserCollectionVO.java — @Data, fields: id, subjectId, type, rate, epStatus, subject (SubjectListVO).

UserCollectionSubjectVO.java — flat JOIN result: all UserCollection fields + name, nameCn, image, score, eps, airDate, subjectType.

- [ ] **Step 2: Commit**

```bash
git add backend/business/pojo/src/main/java/top/zhaizz/pojo/entity/UserCollection.java
git add backend/business/pojo/src/main/java/top/zhaizz/pojo/dto/CollectionUpdateDTO.java
git add backend/business/pojo/src/main/java/top/zhaizz/pojo/vo/UserCollectionVO.java
git add backend/business/pojo/src/main/java/top/zhaizz/pojo/vo/UserCollectionSubjectVO.java
git commit -m "feat: add UserCollection entity, DTO, and VOs"
```

---

### Task 2: Mapper + XML

**Files:**
- Create: `backend/business/subject/src/main/java/top/zhaizz/subject/mapper/CollectionMapper.java`
- Create: `backend/business/subject/src/main/resources/mapper/CollectionMapper.xml`

**接口：**
- `Page<UserCollectionSubjectVO> selectCollectionPage(Page<?> page, @Param("userId") Long userId, @Param("type") Integer type)` — JOIN 分页查询
- `UserCollectionSubjectVO selectCollectionBySubject(@Param("userId") Long userId, @Param("subjectId") Long subjectId)` — 查单条

XML 中两个 SELECT：JOIN subject 表，取 name/name_cn/image/score/eps/air_date 字段，type 起别名 subject_type。

- [ ] **Step 1: Create CollectionMapper.java + CollectionMapper.xml**
- [ ] **Step 2: Commit**

---

### Task 3: CollectionConverter

**Files:**
- Create: `backend/business/subject/src/main/java/top/zhaizz/subject/converter/CollectionConverter.java`

静态方法 `toUserCollectionVO(UserCollectionSubjectVO)` 和 `toUserCollectionVOList(List)`，将扁平 JOIN 结果映射为 `UserCollectionVO`（嵌套 SubjectListVO）。

- [ ] **Step 1: Create CollectionConverter.java**
- [ ] **Step 2: Commit**

---

### Task 4: CollectionService

**Files:**
- Create: `backend/business/subject/src/main/java/top/zhaizz/subject/service/CollectionService.java`
- Create: `backend/business/subject/src/main/java/top/zhaizz/subject/service/impl/CollectionServiceImpl.java`

**接口方法：**
- `PageResult<UserCollectionVO> listCollections(Long userId, Integer type, int page, int size)`
- `UserCollectionVO getCollection(Long userId, Long subjectId)`
- `Map<Integer, Long> countByType(Long userId)` — 统计各状态数量，用于前端 tab 计数显示
- `void saveOrUpdate(Long userId, Long subjectId, CollectionUpdateDTO dto)` — @Transactional, 先校验 subject 存在
- `void deleteCollection(Long userId, Long subjectId)`
- `void updateEpStatus(Long userId, Long subjectId, int epStatus)` — @Transactional

服务实现注入 CollectionMapper 和 SubjectMapper。

- [ ] **Step 1: Create CollectionService interface + impl**
- [ ] **Step 2: Commit**

---

### Task 5: CollectionController

**Files:**
- Create: `backend/business/subject/src/main/java/top/zhaizz/subject/controller/CollectionController.java`

**端点：**
- GET `/api/user/collections` — 列表，?type=&page=&size=
- GET `/api/user/collections` — 列表，?type=&page=&size=
- GET `/api/user/collections/counts` — 各状态收藏数统计，返回 `{1: 5, 2: 3, 3: 8, 4: 1, 5: 2}`，用于 tab 计数
- GET `/api/user/collections/{subjectId}` — 查单条
- PUT `/api/user/collections/{subjectId}` — 添加/修改
- DELETE `/api/user/collections/{subjectId}` — 删除
- PATCH `/api/user/collections/{subjectId}/ep-status` — 更新进度

从 SecurityContextHolder 取当前用户 ID。

- [ ] **Step 1: Create CollectionController.java**
- [ ] **Step 2: Commit**

---

### Task 6: 前端类型定义与 API 模块

**Files:**
- Modify: `frontend/client/src/types/index.ts`
- Create: `frontend/client/src/api/collections.ts`

types/index.ts 追加 UserCollectionVO 和 CollectionUpdateDTO 接口。

api/collections.ts 导出 collectionsApi 对象，含 list/get/saveOrUpdate/remove/updateEpStatus 方法。

- [ ] **Step 1: 追加类型定义**
- [ ] **Step 2: 创建 api/collections.ts**
- [ ] **Step 3: Commit**

---

### Task 7: 前端路由 + 导航入口

**Files:**
- Modify: `frontend/client/src/router/index.ts`
- Modify: `frontend/client/src/layouts/Header.vue`

路由：`{ path: 'my-collections', name: 'MyCollections', component: () => import('@/pages/MyCollections.vue'), meta: { requiresAuth: true } }`

Header：添加 `<router-link to="/my-collections" class="nav-link">我的追番</router-link>`

- [ ] **Step 1: 更新路由配置**
- [ ] **Step 2: 添加导航链接**
- [ ] **Step 3: Commit**

---

### Task 8: MyCollections 页面

**Files:**
- Create: `frontend/client/src/pages/MyCollections.vue`

功能：
- 顶部 tab：全部/在看/想看/看过/搁置/抛弃
- 卡片网格布局，每张卡片显示番剧信息 + 状态标签 + 评分 + 进度
- 空状态提示 + 去发现按钮
- 分页

- [ ] **Step 1: 创建 MyCollections.vue**
- [ ] **Step 2: Commit**

---

### Task 9: SubjectDetail 追番操作区

**Files:**
- Modify: `frontend/client/src/pages/SubjectDetail.vue`

在封面图下方追加追番操作区：
- 未追番：显示"追番"按钮，点击弹出状态选择菜单
- 已追番：显示当前状态、评分、进度，提供修改状态下拉、评分编辑、进度 +1、删除

加载详情时同步获取收藏状态。

- [ ] **Step 1: 更新 SubjectDetail.vue**
- [ ] **Step 2: Commit**
