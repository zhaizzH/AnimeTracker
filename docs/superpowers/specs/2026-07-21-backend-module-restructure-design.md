# 后端模块重分层设计：subject + user → admin + client

## 背景

后端 business 模块目前按**领域**组织：
- `subject` 模块 — 番剧相关（含 admin CRUD 和 client 查询）
- `user` 模块 — 用户相关（含 admin 管理和 client 认证/个人信息）

两个模块都同时包含管理端和用户端代码，职责边界模糊。目标是按**角色**重新分层，将 subject 和 user 拆散合并为 admin（管理端）和 client（用户端）两个模块。

## 目标模块结构

```
backend/business/
├── pom.xml                    (modules: common, pojo, admin, client, app)
├── common/                    (不变: 安全、配置、异常、工具)
├── pojo/                      (不变: 实体、DTO、VO)
├── admin/                     (NEW: 管理端 — controller + service + mapper)
├── client/                    (NEW: 用户端 — controller + service + mapper)
└── app/                       (依赖: admin + client 替代 subject + user)
```

依赖链：`app → {admin, client} → common, pojo`（admin 和 client 之间**无依赖**）

## 设计规则

1. **模块间零依赖**：admin 和 client 不互相引用，各自持有需要的 mapper 接口和 XML
2. **共享 mapper 各自复制**：SubjectMapper 和 UserMapper 被双方共用，各自模块持有一份自己的副本，包名不同（`top.zhaizz.admin.mapper` / `top.zhaizz.client.mapper`），MyBatis namespace 各自独立
3. **Service 按角色拆分**：原来 SubjectService → AdminSubjectService（admin）+ ClientSubjectService（client），UserService 同理
4. **XML namespace 同步更新**：迁移到 client 模块的 Mapper XML（EpisodeMapper.xml、SubjectTagMapper.xml、SubjectMapper.xml）必须将 namespace 从 `top.zhaizz.subject.mapper.*` 改为 `top.zhaizz.client.mapper.*`
5. **Controller 注入类型变更**：搬迁到 admin 的控制器原注入 `SubjectService` → `AdminSubjectService`，`UserService` → `AdminUserService`；搬迁到 client 的控制器原注入 `SubjectService` → `ClientSubjectService`，`UserService` → `ClientUserService`
6. **Converter 各取所需**：每个模块只保留自己需要的转换方法，少量重复（如 toSubjectDetailVO）可接受
7. **URL 路径不变**：admin 模块仍提供 `/api/admin/**`，client 模块仍提供 `/api/user/**`
8. **App 层零改动**：`@SpringBootApplication(scanBasePackages = "top.zhaizz")` 和 `@MapperScan("top.zhaizz.**.mapper")` 对新包结构开箱即用

## admin 模块

包路径：`top.zhaizz.admin`

### 文件清单（共 3 controller + 3 service + 3 mapper + 2 converter）

| 分类 | 文件 | 来源 | 说明 |
|---|---|---|---|
| controller | `AdminController` | subject 搬迁 | `/api/admin/subjects` CRUD，注入 `AdminSubjectService` |
| controller | `AdminUserController` | user 搬迁 | `/api/admin/users` 列表+改角色，注入 `AdminUserService` |
| controller | `ImportController` | subject 搬迁 | `/api/admin/import` 运行导入+查状态，注入 `ImportService` |
| service | `AdminSubjectService` / `Impl` | SubjectService 拆分 | `createSubject`, `updateSubject`, `deleteSubject` |
| service | `AdminUserService` / `Impl` | UserService 拆分 | `listUsers`, `updateUserRole` |
| service | `ImportService` / `Impl` | subject 搬迁 | 原代码不变 |
| mapper | `SubjectMapper` | **新建** | 仅 `extends BaseMapper<Subject>`，无 XML |
| mapper | `UserMapper` | **新建** | 仅 `extends BaseMapper<User>`，无 XML |
| mapper | `ImportRecordMapper` | subject 搬迁 | `extends BaseMapper<ImportRecord>`，无 XML |
| converter | `SubjectConverter` | 从原 SubjectConverter 抽取 | `toSubjectDetailVO`, `toTagVO`, `toTagVOList`, `toEntityFromCreate`, `updateFromRequest`, `toImportRecordVO(s)` |
| converter | `UserConverter` | 从原 UserConverter 抽取 | `toUserVO` |

## client 模块

包路径：`top.zhaizz.client`

### 文件清单（共 4 controller + 6 service + 4 mapper + 2 converter + 1 util）

| 分类 | 文件 | 来源 | 说明 |
|---|---|---|---|
| controller | `SubjectController` | subject 搬迁 | `/api/user/subjects/**`，注入 `ClientSubjectService` + `EpisodeService` |
| controller | `TagController` | subject 搬迁 | `/api/user/tags`，注入 `TagService` |
| controller | `AuthController` | user 搬迁 | `/api/user/auth`，注入 `AuthService` |
| controller | `UserController` | user 搬迁 | `/api/user/me`，注入 `ClientUserService` + `VerificationService` |
| service | `ClientSubjectService` / `Impl` | SubjectService 拆分 | `listSubjects`, `searchSubjects`, `listBySeason`, `listSchedule`, `getSubjectDetail` |
| service | `ClientUserService` / `Impl` | UserService 拆分 | `getUserById`, `updateUser` |
| service | `AuthService` / `Impl` | user 搬迁 | 原代码不变 |
| service | `EpisodeService` / `Impl` | subject 搬迁 | 原代码不变 |
| service | `TagService` / `Impl` | subject 搬迁 | 原代码不变 |
| service | `VerificationService` / `Impl` | user 搬迁 | 原代码不变 |
| mapper | `SubjectMapper` | **新建** | 含 `searchByKeyword`, `findByAirDateRange`, `findSubjectIdsByTag`, `findByAirDateRangeAndWeekday` + XML |
| mapper | `EpisodeMapper` | subject 搬迁 | `findBySubjectIdOrderBySort` + XML |
| mapper | `SubjectTagMapper` | subject 搬迁 | `selectTagCountList` + XML |
| mapper | `UserMapper` | **新建** | 含 `existsByUsername`, `existsByEmail`（default 方法），无 XML |
| converter | `SubjectConverter` | 从原 SubjectConverter 抽取 | `toSubjectListVO`, `toSubjectDetailVO`, `toEpisodeVO(s)`, `toTagVO(s)` |
| converter | `UserConverter` | 从原 UserConverter 抽取 | `toUserVO`, `updateFromRequest` |
| util | `SeasonUtil` | subject 搬迁 | 原代码不变 |

## Service 拆分方案

### SubjectService 拆分

```
原 SubjectService                     → AdminSubjectService   ClientSubjectService
  listSubjects(page, size, sort, order) →                   ✓
  getSubjectDetail(id)                → ✓                   ✓      ← 两边都需要
  getEpisodes(subjectId)              →                     ✓
  searchSubjects(keyword, page)       →                     ✓
  listBySeason(year, quarter, page)   →                     ✓
  listSchedule(y, q, wd, page)        →                     ✓
  createSubject(request)              → ✓
  updateSubject(id, request)          → ✓
  deleteSubject(id)                   → ✓
```

`getSubjectDetail` 是唯一两边共用的方法，各保留一份实现，代码量约 15 行。

### UserService 拆分

```
原 UserService                        → AdminUserService      ClientUserService
  getUserById(userId)                 →                       ✓
  updateUser(userId, request)         →                       ✓
  listUsers(page, size)               → ✓
  updateUserRole(userId, role)        → ✓
```

无重叠方法，拆分干净。

## Maven 变更

### business/pom.xml
- modules: `common, pojo, admin, client, app`（替换 `subject, user`）
- dependencyManagement: `animetracker-admin`, `animetracker-client` 替代 `animetracker-subject`, `animetracker-user`

### app/pom.xml
- 移除 `animetracker-user`, `animetracker-subject`
- 新增 `animetracker-admin`, `animetracker-client`

### 删除
- `subject/pom.xml`, `user/pom.xml`
- `subject/` 和 `user/` 整个目录

### 新建
- `admin/pom.xml`：依赖 `common`, `pojo`，以及 validation、mybatis-plus、lombok、security
- `client/pom.xml`：依赖 `common`, `pojo`，以及 validation、mybatis-plus、lombok、security、resend-email

两个模块的 pom.xml 从原有的 subject/pom.xml 和 user/pom.xml 合并各端所需的依赖项：admin 取 subject 的 validation+mybatis-plus+lombok + user 的 security；client 取两者的全部依赖。

### 不变
- `common/pom.xml`, `pojo/pom.xml` 完全不动

## 不变的内容（边界确认）

- **URL 路径**：全部不变
- **SecurityConfig**：规则不变
- **AppApplication**：scanBasePackages + MapperScan 不变
- **pojo**：实体、DTO、VO 一个文件不动
- **common**：安全、配置、异常处理、工具类不动
- **前端**：无影响，API 路径没变

## 不涉及的范围

- 数据库表结构
- 前端代码
- 业务逻辑（只挪位置，不改逻辑）
- API 协议（请求/响应格式不变）
