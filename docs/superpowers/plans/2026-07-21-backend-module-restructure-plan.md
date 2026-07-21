# 后端模块重分层 Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 将 business 的 subject 和 user 模块按角色拆散重组为 admin 和 client 两个模块，消除模块内职责模糊。

**Architecture:** 按角色跨领域切分。admin 模块包含管理端 controller/service/mapper，client 模块包含用户端 controller/service/mapper。共享的 SubjectMapper 和 UserMapper 各模块持独立副本，零跨模块依赖。

**Tech Stack:** Maven multi-module, Spring Boot 3.2, MyBatis-Plus, Java 21

## Global Constraints

- 业务逻辑零改动，只挪位置不挪逻辑
- URL 路径不变：`/api/admin/**` 仍在 admin，`/api/user/**` 仍在 client
- AppApplication 的 `scanBasePackages = "top.zhaizz"` 和 `@MapperScan("top.zhaizz.**.mapper")` 不变
- pojo 和 common 模块完全不动
- admin 和 client 之间无 Maven 依赖
- XML namespace 必须从 `top.zhaizz.subject.mapper.*` 改为 `top.zhaizz.client.mapper.*`

---

### Task 1: 创建 Maven 模块结构

**Files:**
- Create: `backend/business/admin/pom.xml`
- Create: `backend/business/client/pom.xml`
- Modify: `backend/business/pom.xml` (modules + dependencyManagement)
- Modify: `backend/business/app/pom.xml` (dependencies)

- [ ] **Step 1: 创建 `admin/pom.xml`**

```xml
<?xml version="1.0" encoding="UTF-8"?>
<project xmlns="http://maven.apache.org/POM/4.0.0"
         xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance"
         xsi:schemaLocation="http://maven.apache.org/POM/4.0.0 https://maven.apache.org/xsd/maven-4.0.0.xsd">
    <modelVersion>4.0.0</modelVersion>

    <parent>
        <groupId>top.zhaizz</groupId>
        <artifactId>business</artifactId>
        <version>2.0.0</version>
        <relativePath>../pom.xml</relativePath>
    </parent>

    <artifactId>animetracker-admin</artifactId>
    <packaging>jar</packaging>
    <name>AnimeTracker Admin</name>
    <description>Admin module: admin subject CRUD, user management, import</description>

    <dependencies>
        <dependency>
            <groupId>top.zhaizz</groupId>
            <artifactId>animetracker-common</artifactId>
        </dependency>
        <dependency>
            <groupId>top.zhaizz</groupId>
            <artifactId>animetracker-pojo</artifactId>
            <version>2.0.0</version>
        </dependency>
        <dependency>
            <groupId>org.springframework.boot</groupId>
            <artifactId>spring-boot-starter-validation</artifactId>
        </dependency>
        <dependency>
            <groupId>com.baomidou</groupId>
            <artifactId>mybatis-plus-spring-boot3-starter</artifactId>
        </dependency>
        <dependency>
            <groupId>org.projectlombok</groupId>
            <artifactId>lombok</artifactId>
        </dependency>
        <dependency>
            <groupId>org.springframework.boot</groupId>
            <artifactId>spring-boot-starter-security</artifactId>
        </dependency>
    </dependencies>
</project>
```

- [ ] **Step 2: 创建 `client/pom.xml`**

```xml
<?xml version="1.0" encoding="UTF-8"?>
<project xmlns="http://maven.apache.org/POM/4.0.0"
         xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance"
         xsi:schemaLocation="http://maven.apache.org/POM/4.0.0 https://maven.apache.org/xsd/maven-4.0.0.xsd">
    <modelVersion>4.0.0</modelVersion>

    <parent>
        <groupId>top.zhaizz</groupId>
        <artifactId>business</artifactId>
        <version>2.0.0</version>
        <relativePath>../pom.xml</relativePath>
    </parent>

    <artifactId>animetracker-client</artifactId>
    <packaging>jar</packaging>
    <name>AnimeTracker Client</name>
    <description>Client module: subject browse/search, auth, profile, tags</description>

    <dependencies>
        <dependency>
            <groupId>top.zhaizz</groupId>
            <artifactId>animetracker-common</artifactId>
        </dependency>
        <dependency>
            <groupId>top.zhaizz</groupId>
            <artifactId>animetracker-pojo</artifactId>
            <version>2.0.0</version>
        </dependency>
        <dependency>
            <groupId>org.springframework.boot</groupId>
            <artifactId>spring-boot-starter-validation</artifactId>
        </dependency>
        <dependency>
            <groupId>com.baomidou</groupId>
            <artifactId>mybatis-plus-spring-boot3-starter</artifactId>
        </dependency>
        <dependency>
            <groupId>org.projectlombok</groupId>
            <artifactId>lombok</artifactId>
        </dependency>
        <dependency>
            <groupId>org.springframework.boot</groupId>
            <artifactId>spring-boot-starter-security</artifactId>
        </dependency>
        <dependency>
            <groupId>com.resend</groupId>
            <artifactId>resend-java</artifactId>
        </dependency>
    </dependencies>
</project>
```

- [ ] **Step 3: 修改 `business/pom.xml`**

将 `<modules>` 中的 `subject` 和 `user` 替换为 `admin` 和 `client`：

```xml
<modules>
    <module>common</module>
    <module>pojo</module>
    <module>admin</module>
    <module>client</module>
    <module>app</module>
</modules>
```

在 `<dependencyManagement>` 中添加 `animetracker-admin` 和 `animetracker-client`，移除 `animetracker-subject` 和 `animetracker-user`：

```xml
<dependency>
    <groupId>top.zhaizz</groupId>
    <artifactId>animetracker-admin</artifactId>
    <version>${project.version}</version>
</dependency>
<dependency>
    <groupId>top.zhaizz</groupId>
    <artifactId>animetracker-client</artifactId>
    <version>${project.version}</version>
</dependency>
```

- [ ] **Step 4: 修改 `app/pom.xml`**

将 `animetracker-user` 和 `animetracker-subject` 替换为 `animetracker-admin` 和 `animetracker-client`：

```xml
<dependency>
    <groupId>top.zhaizz</groupId>
    <artifactId>animetracker-admin</artifactId>
</dependency>
<dependency>
    <groupId>top.zhaizz</groupId>
    <artifactId>animetracker-client</artifactId>
</dependency>
```

- [ ] **Step 5: 提交**

```bash
git add backend/business/admin/pom.xml backend/business/client/pom.xml backend/business/pom.xml backend/business/app/pom.xml
git commit -m "refactor: 创建 admin/client Maven 模块结构"
```

---

### Task 2: admin 模块 — mappers + converters

**Files:**
- Create: `backend/business/admin/src/main/java/top/zhaizz/admin/mapper/SubjectMapper.java`
- Create: `backend/business/admin/src/main/java/top/zhaizz/admin/mapper/SubjectTagMapper.java`
- Create: `backend/business/admin/src/main/java/top/zhaizz/admin/mapper/UserMapper.java`
- Create: `backend/business/admin/src/main/java/top/zhaizz/admin/mapper/ImportRecordMapper.java`
- Create: `backend/business/admin/src/main/java/top/zhaizz/admin/converter/SubjectConverter.java`
- Create: `backend/business/admin/src/main/java/top/zhaizz/admin/converter/UserConverter.java`

- [ ] **Step 1: 创建 `admin/mapper/SubjectMapper.java`**

仅需 `BaseMapper<Subject>`，无自定义方法：

```java
package top.zhaizz.admin.mapper;

import com.baomidou.mybatisplus.core.mapper.BaseMapper;
import top.zhaizz.pojo.entity.Subject;

public interface SubjectMapper extends BaseMapper<Subject> {
}
```

- [ ] **Step 2: 创建 `admin/mapper/UserMapper.java`**

仅需 `BaseMapper<User>`，无自定义方法：

```java
package top.zhaizz.admin.mapper;

import com.baomidou.mybatisplus.core.mapper.BaseMapper;
import top.zhaizz.pojo.entity.User;

public interface UserMapper extends BaseMapper<User> {
}
```

- [ ] **Step 3: 创建 `admin/mapper/ImportRecordMapper.java`**

从 `top.zhaizz.subject.mapper.ImportRecordMapper` 搬过来，改包名：

```java
package top.zhaizz.admin.mapper;

import com.baomidou.mybatisplus.core.mapper.BaseMapper;
import top.zhaizz.pojo.entity.ImportRecord;

public interface ImportRecordMapper extends BaseMapper<ImportRecord> {
}
```

- [ ] **Step 4: 创建 `admin/mapper/SubjectTagMapper.java`**

AdminSubjectServiceImpl.getSubjectDetail() 内部查询 `subjectTagMapper`，所以 admin 也需要：

```java
package top.zhaizz.admin.mapper;

import com.baomidou.mybatisplus.core.mapper.BaseMapper;
import top.zhaizz.pojo.entity.SubjectTag;

public interface SubjectTagMapper extends BaseMapper<SubjectTag> {
}
```

- [ ] **Step 5: 创建 `admin/converter/SubjectConverter.java`**

从 `top.zhaizz.subject.converter.SubjectConverter` 抽取 admin 侧需要的静态方法：`toSubjectDetailVO`, `toTagVO`, `toTagVOList`, `toEntityFromCreate`, `updateFromRequest`, `toImportRecordVO`, `toImportRecordVOList`。包名改为 `top.zhaizz.admin.converter`，代码内容与原 SubjectConverter 中对应方法完全一致。

- [ ] **Step 6: 创建 `admin/converter/UserConverter.java`**

```java
package top.zhaizz.admin.converter;

import top.zhaizz.pojo.entity.User;
import top.zhaizz.pojo.vo.UserVO;

public class UserConverter {
    private UserConverter() {}
    public static UserVO toUserVO(User entity) {
        if (entity == null) return null;
        UserVO vo = new UserVO();
        vo.setId(entity.getId());
        vo.setUsername(entity.getUsername());
        vo.setEmail(entity.getEmail());
        vo.setNickname(entity.getNickname());
        vo.setAvatar(entity.getAvatar());
        vo.setRole(entity.getRole());
        vo.setCreatedAt(entity.getCreatedAt());
        return vo;
    }
}
```

- [ ] **Step 7: 提交**

```bash
git add backend/business/admin/src/main/java/top/zhaizz/admin/mapper/ backend/business/admin/src/main/java/top/zhaizz/admin/converter/
git commit -m "refactor: admin 模块 mappers + converters"
```

---

### Task 3: admin 模块 — services

**Files:**
- Create: `backend/business/admin/src/main/java/top/zhaizz/admin/service/AdminSubjectService.java`
- Create: `backend/business/admin/src/main/java/top/zhaizz/admin/service/impl/AdminSubjectServiceImpl.java`
- Create: `backend/business/admin/src/main/java/top/zhaizz/admin/service/AdminUserService.java`
- Create: `backend/business/admin/src/main/java/top/zhaizz/admin/service/impl/AdminUserServiceImpl.java`
- Create: `backend/business/admin/src/main/java/top/zhaizz/admin/service/ImportService.java`
- Create: `backend/business/admin/src/main/java/top/zhaizz/admin/service/impl/ImportServiceImpl.java`

- [ ] **Step 1: 创建 `AdminSubjectService` + `AdminSubjectServiceImpl`**

接口：
```java
package top.zhaizz.admin.service;

import top.zhaizz.pojo.dto.SubjectCreateDTO;
import top.zhaizz.pojo.dto.SubjectUpdateDTO;
import top.zhaizz.pojo.vo.SubjectDetailVO;

public interface AdminSubjectService {
    SubjectDetailVO createSubject(SubjectCreateDTO request);
    SubjectDetailVO updateSubject(Long id, SubjectUpdateDTO request);
    void deleteSubject(Long id);
}
```

实现：从 `SubjectServiceImpl` 抽取 `createSubject`, `updateSubject`, `deleteSubject` 三个方法。注入 `SubjectMapper`, `SubjectTagMapper`（均为 admin 包）和 `SubjectConverter`（admin 包）。方法体与原实现一致。

- [ ] **Step 2: 创建 `AdminUserService` + `AdminUserServiceImpl`**

接口：
```java
package top.zhaizz.admin.service;

import top.zhaizz.common.result.PageResult;
import top.zhaizz.pojo.vo.UserVO;

public interface AdminUserService {
    PageResult<UserVO> listUsers(int page, int size);
    UserVO updateUserRole(Long userId, String role);
}
```

实现：从 `UserServiceImpl` 抽取 `listUsers`, `updateUserRole`。注入 `UserMapper`（admin 包）和 `UserConverter`（admin 包）。方法体与原实现一致（注意 `updateUserRole` 中 super admin 保护逻辑：`if(user.getId()==1)` 需保留）。

- [ ] **Step 3: 创建 `ImportService` + `ImportServiceImpl`**

从 `top.zhaizz.subject.service.ImportService` 和 `top.zhaizz.subject.service.impl.ImportServiceImpl` 搬迁。包名改为 `top.zhaizz.admin.service` 和 `top.zhaizz.admin.service.impl`，代码内容不变。

- [ ] **Step 4: 提交**

```bash
git add backend/business/admin/src/main/java/top/zhaizz/admin/service/
git commit -m "refactor: admin 模块 services"
```

---

### Task 4: admin 模块 — controllers

**Files:**
- Create: `backend/business/admin/src/main/java/top/zhaizz/admin/controller/AdminController.java`
- Create: `backend/business/admin/src/main/java/top/zhaizz/admin/controller/AdminUserController.java`
- Create: `backend/business/admin/src/main/java/top/zhaizz/admin/controller/ImportController.java`

- [ ] **Step 1: 创建 `AdminController.java`**

从 `top.zhaizz.subject.controller.AdminController` 搬迁。变更：
- 包名 `top.zhaizz.admin.controller`
- `import top.zhaizz.subject.service.SubjectService` → `import top.zhaizz.admin.service.AdminSubjectService`
- 注入字段 `SubjectService` → `AdminSubjectService`
- `SubjectService` 引用改为 `adminSubjectService`
- 移除不再需要的 import（如 `SubjectUpdateDTO` 的 import 路径不变）

- [ ] **Step 2: 创建 `AdminUserController.java`**

从 `top.zhaizz.user.controller.AdminUserController` 搬迁。变更：
- 包名 `top.zhaizz.admin.controller`
- `import top.zhaizz.user.service.UserService` → `import top.zhaizz.admin.service.AdminUserService`
- 注入字段 `UserService` → `AdminUserService`
- 引用改为 `adminUserService`

- [ ] **Step 3: 创建 `ImportController.java`**

从 `top.zhaizz.subject.controller.ImportController` 搬迁。变更：
- 包名 `top.zhaizz.admin.controller`
- `import top.zhaizz.subject.service.ImportService` → `import top.zhaizz.admin.service.ImportService`

- [ ] **Step 4: 验证 admin 模块编译**

```bash
cd backend/business
mvn compile -pl admin -am -q
```

预期：BUILD SUCCESS

- [ ] **Step 5: 提交**

```bash
git add backend/business/admin/src/main/java/top/zhaizz/admin/controller/
git commit -m "refactor: admin 模块 controllers"
```

---

### Task 5: client 模块 — mappers + converters + util

**Files:**
- Create: `backend/business/client/src/main/java/top/zhaizz/client/mapper/SubjectMapper.java`
- Create: `backend/business/client/src/main/resources/mapper/SubjectMapper.xml`
- Create: `backend/business/client/src/main/java/top/zhaizz/client/mapper/EpisodeMapper.java`
- Create: `backend/business/client/src/main/resources/mapper/EpisodeMapper.xml`
- Create: `backend/business/client/src/main/java/top/zhaizz/client/mapper/SubjectTagMapper.java`
- Create: `backend/business/client/src/main/resources/mapper/SubjectTagMapper.xml`
- Create: `backend/business/client/src/main/java/top/zhaizz/client/mapper/UserMapper.java`
- Create: `backend/business/client/src/main/java/top/zhaizz/client/converter/SubjectConverter.java`
- Create: `backend/business/client/src/main/java/top/zhaizz/client/converter/UserConverter.java`
- Create: `backend/business/client/src/main/java/top/zhaizz/client/util/SeasonUtil.java`

- [ ] **Step 1: 创建 `client/mapper/SubjectMapper.java`**

从原 `top.zhaizz.subject.mapper.SubjectMapper` 搬迁，包名改为 `top.zhaizz.client.mapper`，保留所有自定义方法（`searchByKeyword`, `findByAirDateRange`, `findSubjectIdsByTag`, `findByAirDateRangeAndWeekday`）。

- [ ] **Step 2: 创建 `client/mapper/SubjectMapper.xml`**

从原 `subject/src/main/resources/mapper/SubjectMapper.xml` 搬迁，namespace 改为 `top.zhaizz.client.mapper.SubjectMapper`，SQL 内容不变。

- [ ] **Step 3: 创建 `client/mapper/EpisodeMapper.java` + `EpisodeMapper.xml`**

从原搬迁，包名改为 `top.zhaizz.client.mapper`，XML namespace 改为 `top.zhaizz.client.mapper.EpisodeMapper`。

- [ ] **Step 4: 创建 `client/mapper/SubjectTagMapper.java` + `SubjectTagMapper.xml`**

从原搬迁，包名改为 `top.zhaizz.client.mapper`，XML namespace 改为 `top.zhaizz.client.mapper.SubjectTagMapper`。

- [ ] **Step 5: 创建 `client/mapper/UserMapper.java`**

从 `top.zhaizz.user.mapper.UserMapper` 搬迁，包名改为 `top.zhaizz.client.mapper`，保留两个 default 方法（`existsByUsername`, `existsByEmail`）。

- [ ] **Step 6: 创建 `client/converter/SubjectConverter.java`**

从原 `SubjectConverter` 抽取 client 侧需要的静态方法：`toSubjectListVO`, `toSubjectDetailVO`, `toEpisodeVO`, `toEpisodeVOList`, `toTagVO`, `toTagVOList`。包名改为 `top.zhaizz.client.converter`。`toSubjectDetailVO` 与 admin 版完全一致（代码重复约 20 行，可接受）。

- [ ] **Step 7: 创建 `client/converter/UserConverter.java`**

从原 `UserConverter` 抽取 client 侧需要的静态方法：`toUserVO`, `updateFromRequest`。包名改为 `top.zhaizz.client.converter`。`toUserVO` 与 admin 版完全一致（代码重复约 10 行，可接受）。

- [ ] **Step 8: 创建 `client/util/SeasonUtil.java`**

从 `top.zhaizz.subject.util.SeasonUtil` 搬迁，包名改为 `top.zhaizz.client.util`，代码不变。

- [ ] **Step 9: 提交**

```bash
git add backend/business/client/src/main/java/top/zhaizz/client/mapper/ backend/business/client/src/main/resources/ backend/business/client/src/main/java/top/zhaizz/client/converter/ backend/business/client/src/main/java/top/zhaizz/client/util/
git commit -m "refactor: client 模块 mappers + converters + util"
```

---

### Task 6: client 模块 — services

**Files:**
- Create: `backend/business/client/src/main/java/top/zhaizz/client/service/ClientSubjectService.java`
- Create: `backend/business/client/src/main/java/top/zhaizz/client/service/impl/ClientSubjectServiceImpl.java`
- Create: `backend/business/client/src/main/java/top/zhaizz/client/service/ClientUserService.java`
- Create: `backend/business/client/src/main/java/top/zhaizz/client/service/impl/ClientUserServiceImpl.java`
- Create: `backend/business/client/src/main/java/top/zhaizz/client/service/AuthService.java`
- Create: `backend/business/client/src/main/java/top/zhaizz/client/service/impl/AuthServiceImpl.java`
- Create: `backend/business/client/src/main/java/top/zhaizz/client/service/EpisodeService.java`
- Create: `backend/business/client/src/main/java/top/zhaizz/client/service/impl/EpisodeServiceImpl.java`
- Create: `backend/business/client/src/main/java/top/zhaizz/client/service/TagService.java`
- Create: `backend/business/client/src/main/java/top/zhaizz/client/service/impl/TagServiceImpl.java`
- Create: `backend/business/client/src/main/java/top/zhaizz/client/service/VerificationService.java`
- Create: `backend/business/client/src/main/java/top/zhaizz/client/service/impl/VerificationServiceImpl.java`

- [ ] **Step 1: 创建 `ClientSubjectService` + `ClientSubjectServiceImpl`**

接口：
```java
package top.zhaizz.client.service;

import top.zhaizz.common.result.PageResult;
import top.zhaizz.pojo.vo.EpisodeVO;
import top.zhaizz.pojo.vo.SubjectDetailVO;
import top.zhaizz.pojo.vo.SubjectListVO;
import java.util.List;

public interface ClientSubjectService {
    PageResult<SubjectListVO> listSubjects(int page, int size, String sort, String order);
    SubjectDetailVO getSubjectDetail(Long id);
    List<EpisodeVO> getEpisodes(Long subjectId);
    PageResult<SubjectListVO> searchSubjects(String keyword, int page, int size);
    PageResult<SubjectListVO> listBySeason(int year, String quarter, int page, int size);
    PageResult<SubjectListVO> listSchedule(int year, String quarter, Integer weekday, int page, int size);
}
```

实现：从 `SubjectServiceImpl` 抽取 `listSubjects`, `searchSubjects`, `listBySeason`, `listSchedule`, `getSubjectDetail`, `getEpisodes`。注入 `SubjectMapper`, `EpisodeMapper`, `SubjectTagMapper`（均为 client 包），使用 `SubjectConverter`（client 包）、`SeasonUtil`（client 包）。方法体与原实现一致。

- [ ] **Step 2: 创建 `ClientUserService` + `ClientUserServiceImpl`**

接口：
```java
package top.zhaizz.client.service;

import top.zhaizz.pojo.dto.UpdateUserDTO;
import top.zhaizz.pojo.vo.UserVO;

public interface ClientUserService {
    UserVO getUserById(Long userId);
    UserVO updateUser(Long userId, UpdateUserDTO request);
}
```

实现：从 `UserServiceImpl` 抽取 `getUserById`, `updateUser`。注入 `UserMapper`（client 包）、`UserConverter`（client 包）。方法体与原实现一致。

- [ ] **Step 3: 创建 `AuthService` + `AuthServiceImpl`**

从 `top.zhaizz.user.service.AuthService` 和 `top.zhaizz.user.service.impl.AuthServiceImpl` 搬迁。包名改为 `top.zhaizz.client.service` / `top.zhaizz.client.service.impl`。注意 `AuthServiceImpl` 引用了 `UserMapper`（client 包），需更新 import。

- [ ] **Step 4: 创建 `EpisodeService` + `EpisodeServiceImpl`**

从 subject 搬迁，包名改为 `top.zhaizz.client.service`。`EpisodeServiceImpl` 注入 `EpisodeMapper`（client 包）。

- [ ] **Step 5: 创建 `TagService` + `TagServiceImpl`**

从 subject 搬迁，包名改为 `top.zhaizz.client.service`。`TagServiceImpl` 注入 `SubjectMapper` 和 `SubjectTagMapper`（均为 client 包）。

- [ ] **Step 6: 创建 `VerificationService` + `VerificationServiceImpl`**

从 user 搬迁，包名改为 `top.zhaizz.client.service`。`VerificationServiceImpl` 引用了 `UserMapper`（client 包）、`RedisClient`（common 包）等，需更新 import。

- [ ] **Step 7: 提交**

```bash
git add backend/business/client/src/main/java/top/zhaizz/client/service/
git commit -m "refactor: client 模块 services"
```

---

### Task 7: client 模块 — controllers

**Files:**
- Create: `backend/business/client/src/main/java/top/zhaizz/client/controller/SubjectController.java`
- Create: `backend/business/client/src/main/java/top/zhaizz/client/controller/TagController.java`
- Create: `backend/business/client/src/main/java/top/zhaizz/client/controller/AuthController.java`
- Create: `backend/business/client/src/main/java/top/zhaizz/client/controller/UserController.java`

- [ ] **Step 1: 创建 `SubjectController.java`**

从 `top.zhaizz.subject.controller.SubjectController` 搬迁。变更：
- 包名 `top.zhaizz.client.controller`
- `import SubjectService` → `import top.zhaizz.client.service.ClientSubjectService`
- `import EpisodeService` → `import top.zhaizz.client.service.EpisodeService`
- `import top.zhaizz.subject.util.SeasonUtil` → `import top.zhaizz.client.util.SeasonUtil`
- 注入字段 `SubjectService` → `ClientSubjectService`

- [ ] **Step 2: 创建 `TagController.java`**

从 `top.zhaizz.subject.controller.TagController` 搬迁。变更：
- 包名 `top.zhaizz.client.controller`
- `import TagService` → `import top.zhaizz.client.service.TagService`

- [ ] **Step 3: 创建 `AuthController.java`**

从 `top.zhaizz.user.controller.AuthController` 搬迁。变更：
- 包名 `top.zhaizz.client.controller`
- `import AuthService` → `import top.zhaizz.client.service.AuthService`

- [ ] **Step 4: 创建 `UserController.java`**

从 `top.zhaizz.user.controller.UserController` 搬迁。变更：
- 包名 `top.zhaizz.client.controller`
- `import UserService` → `import top.zhaizz.client.service.ClientUserService`
- `import VerificationService` → `import top.zhaizz.client.service.VerificationService`
- 注入字段 `UserService` → `clientUserService`

- [ ] **Step 5: 验证 client 模块编译**

```bash
cd backend/business
mvn compile -pl client -am -q
```

预期：BUILD SUCCESS

- [ ] **Step 6: 提交**

```bash
git add backend/business/client/src/main/java/top/zhaizz/client/controller/
git commit -m "refactor: client 模块 controllers"
```

---

### Task 8: 删除旧模块 + 全量构建验证

**Files:**
- Delete: `backend/business/subject/`
- Delete: `backend/business/user/`

- [ ] **Step 1: 删除旧模块目录**

```bash
rm -rf backend/business/subject
rm -rf backend/business/user
```

- [ ] **Step 2: 全量构建**

```bash
cd backend/business
mvn clean compile -q
```

预期：BUILD SUCCESS

- [ ] **Step 3: 提交**

```bash
git add -A
git commit -m "refactor: 删除旧 subject/user 模块，完成 admin/client 重组"
```
