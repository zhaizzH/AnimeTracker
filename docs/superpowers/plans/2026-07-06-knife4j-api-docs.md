# Knife4j API 文档注解完善 Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 在所有 Controller、DTO、VO 上添加 Knife4j/Swagger 注解，使 Knife4j 文档页面呈现完整、可读的 API 文档。

**Architecture:** 项目已集成 Knife4j 依赖和基础配置（OpenApiConfig、Spring Security 白名单、application.yml 配置），但所有 Controller 方法和请求/响应模型缺少 `@Tag`、`@Operation`、`@Schema` 注解。本计划逐个文件添加注解，最终构建验证。

**Tech Stack:** Spring Boot 3.2 + Knife4j 4.5.0 (OpenAPI 3 / Jakarta) + Spring Security + MyBatis-Plus

## Global Constraints

- 使用 `io.swagger.v3.oas.annotations` 包（OpenAPI 3 标准注解），而非 `io.swagger.annotations`（Swagger 2）
- 保持现有代码风格：Lombok `@Data`、`@RequiredArgsConstructor`
- 不修改业务逻辑，仅添加注解
- Knife4j UI 路径 `/doc.html` 已在 SecurityConfig 中放行，无需修改

---

### Task 1: DTO 模型添加 @Schema 注解

**Files:**
- Modify: `backend/api/src/main/java/top/zhaizz/animetracker/common/dto/LoginDTO.java`
- Modify: `backend/api/src/main/java/top/zhaizz/animetracker/common/dto/RegisterDTO.java`
- Modify: `backend/api/src/main/java/top/zhaizz/animetracker/common/dto/UpdateUserDTO.java`
- Modify: `backend/api/src/main/java/top/zhaizz/animetracker/common/dto/UpdateRoleDTO.java`
- Modify: `backend/api/src/main/java/top/zhaizz/animetracker/common/dto/SubjectCreateDTO.java`
- Modify: `backend/api/src/main/java/top/zhaizz/animetracker/common/dto/SubjectUpdateDTO.java`
- Modify: `backend/api/src/main/java/top/zhaizz/animetracker/common/dto/SubjectSearchCriteriaDTO.java`
- Modify: `backend/api/src/main/java/top/zhaizz/animetracker/common/dto/SeasonQueryDTO.java`

**Interfaces:**
- Consumes: (none — pure annotation addition)
- Produces: 8 DTO classes with `@Schema` annotations, improving Knife4j request body documentation

- [ ] **Step 1: LoginDTO 添加 @Schema**

```java
package top.zhaizz.animetracker.common.dto;

import io.swagger.v3.oas.annotations.media.Schema;
import jakarta.validation.constraints.NotBlank;
import lombok.AllArgsConstructor;
import lombok.Data;
import lombok.NoArgsConstructor;

@Data
@NoArgsConstructor
@AllArgsConstructor
@Schema(description = "登录请求")
public class LoginDTO {

    @NotBlank(message = "用户名不能为空")
    @Schema(description = "用户名", requiredMode = Schema.RequiredMode.REQUIRED, example = "alice")
    private String username;

    @NotBlank(message = "密码不能为空")
    @Schema(description = "密码", requiredMode = Schema.RequiredMode.REQUIRED, example = "password123")
    private String password;
}
```

- [ ] **Step 2: RegisterDTO 添加 @Schema**

```java
package top.zhaizz.animetracker.common.dto;

import io.swagger.v3.oas.annotations.media.Schema;
import jakarta.validation.constraints.Email;
import jakarta.validation.constraints.NotBlank;
import jakarta.validation.constraints.Size;
import lombok.Data;

@Data
@Schema(description = "注册请求")
public class RegisterDTO {

    @NotBlank(message = "用户名不能为空")
    @Size(min = 1, max = 32, message = "用户名长度需在1~32之间")
    @Schema(description = "用户名", requiredMode = Schema.RequiredMode.REQUIRED, example = "alice")
    private String username;

    @NotBlank(message = "密码不能为空")
    @Size(min = 6, max = 128, message = "密码长度需在6~128之间")
    @Schema(description = "密码", requiredMode = Schema.RequiredMode.REQUIRED, example = "password123")
    private String password;

    @Email(message = "邮箱格式不正确")
    @Size(max = 128, message = "邮箱长度不能超过128")
    @Schema(description = "邮箱", example = "alice@example.com")
    private String email;
}
```

- [ ] **Step 3: UpdateUserDTO 添加 @Schema**

```java
package top.zhaizz.animetracker.common.dto;

import io.swagger.v3.oas.annotations.media.Schema;
import jakarta.validation.constraints.Email;
import jakarta.validation.constraints.Size;
import lombok.Data;

@Data
@Schema(description = "修改个人信息请求（所有字段可选）")
public class UpdateUserDTO {

    @Size(max = 64, message = "昵称长度不能超过64")
    @Schema(description = "昵称", example = "爱丽丝")
    private String nickname;

    @Size(max = 512, message = "头像URL长度不能超过512")
    @Schema(description = "头像URL", example = "https://example.com/avatar.png")
    private String avatar;

    @Email(message = "邮箱格式不正确")
    @Size(max = 128, message = "邮箱长度不能超过128")
    @Schema(description = "邮箱", example = "alice@example.com")
    private String email;
}
```

- [ ] **Step 4: UpdateRoleDTO 添加 @Schema**

```java
package top.zhaizz.animetracker.common.dto;

import io.swagger.v3.oas.annotations.media.Schema;
import jakarta.validation.constraints.NotBlank;
import jakarta.validation.constraints.Pattern;
import lombok.Data;

@Data
@Schema(description = "修改角色请求")
public class UpdateRoleDTO {

    @NotBlank(message = "角色不能为空")
    @Pattern(regexp = "USER|ADMIN", message = "角色值必须是 USER 或 ADMIN")
    @Schema(description = "角色", allowableValues = {"USER", "ADMIN"}, example = "ADMIN")
    private String role;
}
```

- [ ] **Step 5: SubjectCreateDTO 添加 @Schema**

```java
package top.zhaizz.animetracker.common.dto;

import io.swagger.v3.oas.annotations.media.Schema;
import jakarta.validation.constraints.NotBlank;
import lombok.Data;

import java.time.LocalDate;

@Data
@Schema(description = "创建番剧条目请求")
public class SubjectCreateDTO {

    @Schema(description = "Bangumi 条目ID", example = "123456")
    private Integer bangumiId;

    @NotBlank(message = "条目名称不能为空")
    @Schema(description = "条目名称（日文/英文）", requiredMode = Schema.RequiredMode.REQUIRED, example = "進撃の巨人")
    private String name;

    @Schema(description = "中文名称", example = "进击的巨人")
    private String nameCn;

    @Schema(description = "简介")
    private String summary;

    @Schema(description = "类型（2=动画）", example = "2")
    private Integer type;

    @Schema(description = "总集数", example = "25")
    private Integer eps;

    @Schema(description = "首播日期", example = "2013-04-07")
    private LocalDate airDate;

    @Schema(description = "封面图URL", example = "https://example.com/cover.jpg")
    private String image;
}
```

- [ ] **Step 6: SubjectUpdateDTO 添加 @Schema**

```java
package top.zhaizz.animetracker.common.dto;

import io.swagger.v3.oas.annotations.media.Schema;
import lombok.Data;

import java.time.LocalDate;

@Data
@Schema(description = "更新番剧条目请求（所有字段可选，仅传入需要修改的字段）")
public class SubjectUpdateDTO {

    @Schema(description = "条目名称（日文/英文）", example = "進撃の巨人 The Final Season")
    private String name;

    @Schema(description = "中文名称", example = "进击的巨人 最终季")
    private String nameCn;

    @Schema(description = "简介")
    private String summary;

    @Schema(description = "类型（2=动画）", example = "2")
    private Integer type;

    @Schema(description = "总集数", example = "16")
    private Integer eps;

    @Schema(description = "首播日期", example = "2020-12-07")
    private LocalDate airDate;

    @Schema(description = "封面图URL", example = "https://example.com/cover.jpg")
    private String image;
}
```

- [ ] **Step 7: SubjectSearchCriteriaDTO 添加 @Schema**

```java
package top.zhaizz.animetracker.common.dto;

import io.swagger.v3.oas.annotations.media.Schema;
import jakarta.validation.constraints.NotEmpty;
import lombok.Data;

@Data
@Schema(description = "番剧搜索参数")
public class SubjectSearchCriteriaDTO {

    @NotEmpty(message = "搜索关键词不能为空")
    @Schema(description = "搜索关键词", requiredMode = Schema.RequiredMode.REQUIRED, example = "巨人")
    private String q;

    @Schema(description = "页码", example = "1")
    private int page = 1;

    @Schema(description = "每页条数", example = "20")
    private int size = 20;
}
```

- [ ] **Step 8: SeasonQueryDTO 添加 @Schema**

```java
package top.zhaizz.animetracker.common.dto;

import io.swagger.v3.oas.annotations.media.Schema;
import jakarta.validation.constraints.Max;
import jakarta.validation.constraints.Min;
import jakarta.validation.constraints.Pattern;
import lombok.Data;

@Data
@Schema(description = "季度查询参数")
public class SeasonQueryDTO {

    @Min(value = 1970, message = "年份不能早于1970")
    @Max(value = 2100, message = "年份不能晚于2100")
    @Schema(description = "年份", requiredMode = Schema.RequiredMode.REQUIRED, example = "2026")
    private int year;

    @Pattern(regexp = "spring|summer|autumn|winter", message = "季度仅允许: spring/summer/autumn/winter")
    @Schema(description = "季度", allowableValues = {"spring", "summer", "autumn", "winter"}, example = "spring")
    private String quarter;
}
```

- [ ] **Step 9: Commit**

```bash
git add backend/api/src/main/java/top/zhaizz/animetracker/common/dto/*.java
git commit -m "docs: 为 DTO 添加 @Schema 注解以完善 Knife4j API 文档"
```

---

### Task 2: VO 与 Result 模型添加 @Schema 注解

**Files:**
- Modify: `backend/api/src/main/java/top/zhaizz/animetracker/common/vo/LoginVO.java`
- Modify: `backend/api/src/main/java/top/zhaizz/animetracker/common/vo/UserVO.java`
- Modify: `backend/api/src/main/java/top/zhaizz/animetracker/common/vo/SubjectListVO.java`
- Modify: `backend/api/src/main/java/top/zhaizz/animetracker/common/vo/SubjectDetailVO.java`
- Modify: `backend/api/src/main/java/top/zhaizz/animetracker/common/vo/EpisodeVO.java`
- Modify: `backend/api/src/main/java/top/zhaizz/animetracker/common/vo/TagVO.java`
- Modify: `backend/api/src/main/java/top/zhaizz/animetracker/common/vo/ImportStatusVO.java`
- Modify: `backend/api/src/main/java/top/zhaizz/animetracker/common/vo/ImportRecordVO.java`
- Modify: `backend/api/src/main/java/top/zhaizz/animetracker/common/result/Result.java`
- Modify: `backend/api/src/main/java/top/zhaizz/animetracker/common/result/PageResult.java`

**Interfaces:**
- Consumes: Task 1 (same layer, no dependency)
- Produces: 10 model classes with `@Schema` annotations

- [ ] **Step 1: LoginVO**

```java
package top.zhaizz.animetracker.common.vo;

import io.swagger.v3.oas.annotations.media.Schema;
import lombok.AllArgsConstructor;
import lombok.Data;

@Data
@AllArgsConstructor
@Schema(description = "登录/注册结果（JWT Token + 用户信息）")
public class LoginVO {

    @Schema(description = "JWT Token，后续请求需在 Authorization 头携带 Bearer {token}", example = "eyJhbGciOiJIUzI1NiJ9...")
    private String token;

    @Schema(description = "用户信息")
    private UserVO user;
}
```

- [ ] **Step 2: UserVO**

```java
package top.zhaizz.animetracker.common.vo;

import io.swagger.v3.oas.annotations.media.Schema;
import lombok.Data;

import java.time.LocalDateTime;

@Data
@Schema(description = "用户信息（不含密码）")
public class UserVO {

    @Schema(description = "用户ID", example = "1")
    private Long id;

    @Schema(description = "用户名", example = "alice")
    private String username;

    @Schema(description = "邮箱", example = "alice@example.com")
    private String email;

    @Schema(description = "昵称", example = "爱丽丝")
    private String nickname;

    @Schema(description = "头像URL", example = "https://example.com/avatar.png")
    private String avatar;

    @Schema(description = "角色", allowableValues = {"USER", "ADMIN"}, example = "USER")
    private String role;

    @Schema(description = "创建时间", example = "2026-01-01 12:00:00")
    private LocalDateTime createdAt;
}
```

- [ ] **Step 3: SubjectListVO**

```java
package top.zhaizz.animetracker.common.vo;

import io.swagger.v3.oas.annotations.media.Schema;
import lombok.Data;

import java.math.BigDecimal;
import java.time.LocalDate;

@Data
@Schema(description = "番剧列表项（摘要信息）")
public class SubjectListVO {

    @Schema(description = "条目ID", example = "1")
    private Long id;

    @Schema(description = "条目名称（日文/英文）", example = "進撃の巨人")
    private String name;

    @Schema(description = "中文名称", example = "进击的巨人")
    private String nameCn;

    @Schema(description = "封面图URL", example = "https://example.com/cover.jpg")
    private String image;

    @Schema(description = "评分", example = "9.1")
    private BigDecimal score;

    @Schema(description = "排名", example = "1")
    private Integer rank;

    @Schema(description = "总集数", example = "25")
    private Integer eps;

    @Schema(description = "首播日期", example = "2013-04-07")
    private LocalDate airDate;

    @Schema(description = "类型（2=动画）", example = "2")
    private Integer type;
}
```

- [ ] **Step 4: SubjectDetailVO**

```java
package top.zhaizz.animetracker.common.vo;

import io.swagger.v3.oas.annotations.media.Schema;
import lombok.Data;
import lombok.EqualsAndHashCode;

import java.time.LocalDateTime;
import java.util.List;

@Data
@EqualsAndHashCode(callSuper = true)
@Schema(description = "番剧详情（含标签等完整信息）")
public class SubjectDetailVO extends SubjectListVO {

    @Schema(description = "Bangumi 条目ID", example = "123456")
    private Integer bangumiId;

    @Schema(description = "简介", example = "人类与巨人的战斗...")
    private String summary;

    @Schema(description = "卷数", example = "32")
    private Integer volumes;

    @Schema(description = "放送星期（0=周日 1=周一 ...）", example = "6")
    private Integer airWeekday;

    @Schema(description = "收藏数", example = "10000")
    private Integer collectionTotal;

    @Schema(description = "是否 NSFW", example = "false")
    private Boolean nsfw;

    @Schema(description = "标签列表")
    private List<TagVO> tags;

    @Schema(description = "创建时间", example = "2026-01-01 12:00:00")
    private LocalDateTime createdAt;

    @Schema(description = "更新时间", example = "2026-06-15 12:00:00")
    private LocalDateTime updatedAt;
}
```

- [ ] **Step 5: EpisodeVO**

```java
package top.zhaizz.animetracker.common.vo;

import io.swagger.v3.oas.annotations.media.Schema;
import lombok.Data;

import java.math.BigDecimal;
import java.time.LocalDate;

@Data
@Schema(description = "剧集信息")
public class EpisodeVO {

    @Schema(description = "剧集ID", example = "1")
    private Long id;

    @Schema(description = "所属条目ID", example = "1")
    private Long subjectId;

    @Schema(description = "类型（0=本篇 1=SP 2=OP 3=ED 4=预告）", example = "0")
    private Integer type;

    @Schema(description = "集数排序", example = "1.0")
    private BigDecimal sort;

    @Schema(description = "名称（日文/英文）", example = "Episode 1")
    private String name;

    @Schema(description = "中文名称", example = "第一集")
    private String nameCn;

    @Schema(description = "时长", example = "24:00")
    private String duration;

    @Schema(description = "播出日期", example = "2013-04-07")
    private LocalDate airdate;

    @Schema(description = "简介")
    private String description;

    @Schema(description = "放送状态（Air / Today / NA）", example = "NA")
    private String status;
}
```

- [ ] **Step 6: TagVO**

```java
package top.zhaizz.animetracker.common.vo;

import io.swagger.v3.oas.annotations.media.Schema;
import lombok.Data;

@Data
@Schema(description = "标签信息")
public class TagVO {

    @Schema(description = "标签ID", example = "1")
    private Long id;

    @Schema(description = "标签名称", example = "热血")
    private String name;

    @Schema(description = "该标签下的条目数", example = "42")
    private Integer count;
}
```

- [ ] **Step 7: ImportStatusVO**

```java
package top.zhaizz.animetracker.common.vo;

import io.swagger.v3.oas.annotations.media.Schema;
import lombok.Data;

import java.time.LocalDateTime;
import java.util.List;

@Data
@Schema(description = "导入状态信息")
public class ImportStatusVO {

    @Schema(description = "最近导入时间（从未导入=null）", example = "2026-06-15 12:00:00")
    private LocalDateTime lastImportedAt;

    @Schema(description = "当前 subject 表总条目数", example = "1200")
    private Integer totalSubjects;

    @Schema(description = "最近导入记录")
    private List<ImportRecordVO> recentRecords;
}
```

- [ ] **Step 8: ImportRecordVO**

```java
package top.zhaizz.animetracker.common.vo;

import io.swagger.v3.oas.annotations.media.Schema;
import lombok.Data;

import java.time.LocalDateTime;

@Data
@Schema(description = "导入记录")
public class ImportRecordVO {

    @Schema(description = "记录ID", example = "1")
    private Long id;

    @Schema(description = "季度标识", example = "2026-spring")
    private String season;

    @Schema(description = "开始时间", example = "2026-06-15 10:00:00")
    private LocalDateTime startedAt;

    @Schema(description = "完成时间（可空）", example = "2026-06-15 10:05:00")
    private LocalDateTime completedAt;

    @Schema(description = "状态（RUNNING / COMPLETED / FAILED）", allowableValues = {"RUNNING", "COMPLETED", "FAILED"}, example = "COMPLETED")
    private String status;

    @Schema(description = "导入条目数", example = "50")
    private Integer subjectCount;

    @Schema(description = "错误信息（可空）", example = "连接超时")
    private String errorMessage;
}
```

- [ ] **Step 9: Result<T> 添加 @Schema**

```java
package top.zhaizz.animetracker.common.result;

import com.fasterxml.jackson.annotation.JsonInclude;
import io.swagger.v3.oas.annotations.media.Schema;
import lombok.Getter;

@Getter
@JsonInclude(JsonInclude.Include.NON_NULL)
@Schema(description = "统一响应体")
public class Result<T> {

    @Schema(description = "状态码", example = "200")
    private int code;

    @Schema(description = "提示信息", example = "success")
    private String message;

    @Schema(description = "响应数据")
    private T data;

    public Result() {}

    public Result(int code, String message, T data) {
        this.code = code;
        this.message = message;
        this.data = data;
    }

    public static <T> Result<T> success(T data) {
        return new Result<>(200, "success", data);
    }

    public static <T> Result<T> success() {
        return new Result<>(200, "success", null);
    }

    public static <T> Result<T> error(int code, String message) {
        return new Result<>(code, message, null);
    }

    public static <T> Result<T> error(int code, String message, T data) {
        return new Result<>(code, message, data);
    }

    public static <T> Result<T> fail(String message) {
        return new Result<>(400, message, null);
    }
}
```

- [ ] **Step 10: PageResult<T> 添加 @Schema**

```java
package top.zhaizz.animetracker.common.result;

import io.swagger.v3.oas.annotations.media.Schema;
import lombok.Getter;
import lombok.Setter;

import java.util.List;

@Getter
@Setter
@Schema(description = "统一分页结果")
public class PageResult<T> {

    @Schema(description = "数据列表")
    private List<T> content;

    @Schema(description = "总记录数", example = "100")
    private long total;

    @Schema(description = "当前页码", example = "1")
    private int page;

    @Schema(description = "每页条数", example = "20")
    private int size;

    public PageResult() {}

    public PageResult(List<T> content, long total, int page, int size) {
        this.content = content;
        this.total = total;
        this.page = page;
        this.size = size;
    }

    public static <T> PageResult<T> of(List<T> content, long total, int page, int size) {
        return new PageResult<>(content, total, page, size);
    }

    public static <T> PageResult<T> empty(int page, int size) {
        return new PageResult<>(List.of(), 0, page, size);
    }
}
```

- [ ] **Step 11: Commit**

```bash
git add backend/api/src/main/java/top/zhaizz/animetracker/common/vo/*.java backend/api/src/main/java/top/zhaizz/animetracker/common/result/*.java
git commit -m "docs: 为 VO 和 Result 类添加 @Schema 注解以完善 Knife4j API 文档"
```

---

### Task 3: AuthController 添加 @Tag / @Operation / @Parameter

**Files:**
- Modify: `backend/api/src/main/java/top/zhaizz/animetracker/user/controller/AuthController.java`

**Interfaces:**
- Consumes: `LoginDTO`, `RegisterDTO`, `LoginVO`, `UserVO` (from Tasks 1-2, already annotated)
- Produces: Documented authentication API group in Knife4j

- [ ] **Step 1: AuthController 添加注解**

```java
package top.zhaizz.animetracker.user.controller;

import io.swagger.v3.oas.annotations.Operation;
import io.swagger.v3.oas.annotations.Parameter;
import io.swagger.v3.oas.annotations.tags.Tag;
import jakarta.servlet.http.HttpServletRequest;
import jakarta.validation.Valid;
import lombok.RequiredArgsConstructor;
import org.springframework.web.bind.annotation.*;
import top.zhaizz.animetracker.common.result.Result;
import top.zhaizz.animetracker.common.dto.LoginDTO;
import top.zhaizz.animetracker.common.dto.RegisterDTO;
import top.zhaizz.animetracker.user.service.AuthService;
import top.zhaizz.animetracker.common.vo.LoginVO;
import top.zhaizz.animetracker.common.vo.UserVO;

@RestController
@RequestMapping("/api/user/auth")
@RequiredArgsConstructor
@Tag(name = "认证管理", description = "用户注册、登录、注销接口")
public class AuthController {

    private final AuthService authService;

    @PostMapping("/register")
    @Operation(summary = "用户注册", description = "注册新用户，成功后自动登录并返回 JWT Token 和用户信息")
    public Result<LoginVO> register(@Valid @RequestBody RegisterDTO request) {
        UserVO userVO = authService.register(request);
        LoginVO loginVO = authService.login(
                new LoginDTO(request.getUsername(), request.getPassword()));
        return Result.success(loginVO);
    }

    @PostMapping("/login")
    @Operation(summary = "用户登录", description = "使用用户名和密码登录，返回 JWT Token 和用户信息")
    public Result<LoginVO> login(@Valid @RequestBody LoginDTO request) {
        LoginVO loginVO = authService.login(request);
        return Result.success(loginVO);
    }

    @GetMapping("/logout")
    @Operation(summary = "用户注销", description = "使当前 JWT Token 失效（需在请求头携带 Bearer token）")
    public Result<Void> logout(HttpServletRequest request) {
        String authHeader = request.getHeader("Authorization");
        if (authHeader != null && authHeader.startsWith("Bearer ")) {
            String token = authHeader.substring(7);
            authService.logout(token);
        }
        return Result.success(null);
    }
}
```

- [ ] **Step 2: Commit**

```bash
git add backend/api/src/main/java/top/zhaizz/animetracker/user/controller/AuthController.java
git commit -m "docs: AuthController 添加 @Tag/@Operation 注解"
```

---

### Task 4: UserController + AdminUserController 添加注解

**Files:**
- Modify: `backend/api/src/main/java/top/zhaizz/animetracker/user/controller/UserController.java`
- Modify: `backend/api/src/main/java/top/zhaizz/animetracker/user/controller/AdminUserController.java`

**Interfaces:**
- Consumes: `UpdateUserDTO`, `UpdateRoleDTO`, `UserVO`, `PageResult` (from Tasks 1-2)
- Produces: Documented user management and admin user management API groups

- [ ] **Step 1: UserController 添加注解**

```java
package top.zhaizz.animetracker.user.controller;

import io.swagger.v3.oas.annotations.Operation;
import io.swagger.v3.oas.annotations.tags.Tag;
import jakarta.validation.Valid;
import lombok.RequiredArgsConstructor;
import org.springframework.security.core.Authentication;
import org.springframework.security.core.context.SecurityContextHolder;
import org.springframework.web.bind.annotation.*;
import top.zhaizz.animetracker.common.result.Result;
import top.zhaizz.animetracker.common.dto.UpdateUserDTO;
import top.zhaizz.animetracker.user.service.UserService;
import top.zhaizz.animetracker.common.vo.UserVO;

@RestController
@RequestMapping("/api/user")
@RequiredArgsConstructor
@Tag(name = "个人信息管理", description = "查看和修改当前登录用户个人信息")
public class UserController {

    private final UserService userService;

    @GetMapping("/me")
    @Operation(summary = "获取当前用户信息", description = "返回当前登录用户的详细信息（不含密码）")
    public Result<UserVO> getMyProfile() {
        Long userId = getCurrentUserId();
        return Result.success(userService.getUserById(userId));
    }

    @PutMapping("/me")
    @Operation(summary = "修改当前用户信息", description = "修改当前登录用户的昵称、头像、邮箱等信息（仅传入需要修改的字段）")
    public Result<UserVO> updateMyProfile(@Valid @RequestBody UpdateUserDTO request) {
        Long userId = getCurrentUserId();
        return Result.success(userService.updateUser(userId, request));
    }

    private Long getCurrentUserId() {
        Authentication auth = SecurityContextHolder.getContext().getAuthentication();
        return (Long) auth.getPrincipal();
    }
}
```

- [ ] **Step 2: AdminUserController 添加注解**

```java
package top.zhaizz.animetracker.user.controller;

import io.swagger.v3.oas.annotations.Operation;
import io.swagger.v3.oas.annotations.Parameter;
import io.swagger.v3.oas.annotations.tags.Tag;
import jakarta.validation.Valid;
import lombok.RequiredArgsConstructor;
import org.springframework.web.bind.annotation.*;
import top.zhaizz.animetracker.common.result.Result;
import top.zhaizz.animetracker.common.result.PageResult;
import top.zhaizz.animetracker.common.dto.UpdateRoleDTO;
import top.zhaizz.animetracker.user.service.UserService;
import top.zhaizz.animetracker.common.vo.UserVO;

@RestController
@RequestMapping("/api/admin/users")
@RequiredArgsConstructor
@Tag(name = "用户管理（管理员）", description = "管理员查看用户列表、修改用户角色")
public class AdminUserController {

    private final UserService userService;

    @GetMapping
    @Operation(summary = "查看用户列表", description = "分页查看所有注册用户（不返回密码字段）")
    public Result<PageResult<UserVO>> listUsers(
            @Parameter(description = "页码", example = "1") @RequestParam(defaultValue = "1") int page,
            @Parameter(description = "每页条数", example = "20") @RequestParam(defaultValue = "20") int size) {
        return Result.success(userService.listUsers(page, size));
    }

    @PutMapping("/{id}/role")
    @Operation(summary = "修改用户角色", description = "修改指定用户的角色（USER / ADMIN）")
    public Result<UserVO> updateUserRole(
            @Parameter(description = "用户ID", example = "1") @PathVariable Long id,
            @Valid @RequestBody UpdateRoleDTO request) {
        return Result.success(userService.updateUserRole(id, request.getRole()));
    }
}
```

- [ ] **Step 3: Commit**

```bash
git add backend/api/src/main/java/top/zhaizz/animetracker/user/controller/UserController.java backend/api/src/main/java/top/zhaizz/animetracker/user/controller/AdminUserController.java
git commit -m "docs: UserController 和 AdminUserController 添加 @Tag/@Operation 注解"
```

---

### Task 5: SubjectController + AdminController 添加注解

**Files:**
- Modify: `backend/api/src/main/java/top/zhaizz/animetracker/subject/controller/SubjectController.java`
- Modify: `backend/api/src/main/java/top/zhaizz/animetracker/subject/controller/AdminController.java`

**Interfaces:**
- Consumes: `SubjectCreateDTO`, `SubjectUpdateDTO`, `SubjectDetailVO`, `SubjectListVO`, `EpisodeVO`, `PageResult` (from Tasks 1-2)
- Produces: Documented subject browsing and admin subject management API groups

- [ ] **Step 1: SubjectController 添加注解**

```java
package top.zhaizz.animetracker.subject.controller;

import io.swagger.v3.oas.annotations.Operation;
import io.swagger.v3.oas.annotations.Parameter;
import io.swagger.v3.oas.annotations.tags.Tag;
import jakarta.validation.constraints.Max;
import jakarta.validation.constraints.Min;
import jakarta.validation.constraints.Pattern;
import lombok.RequiredArgsConstructor;
import org.springframework.validation.annotation.Validated;
import org.springframework.web.bind.annotation.*;
import top.zhaizz.animetracker.common.result.Result;
import top.zhaizz.animetracker.common.exception.BizException;
import top.zhaizz.animetracker.common.ErrorType;
import top.zhaizz.animetracker.common.result.PageResult;
import top.zhaizz.animetracker.subject.service.EpisodeService;
import top.zhaizz.animetracker.subject.service.SubjectService;
import top.zhaizz.animetracker.common.vo.EpisodeVO;
import top.zhaizz.animetracker.common.vo.SubjectDetailVO;
import top.zhaizz.animetracker.common.vo.SubjectListVO;

import java.util.List;

@RestController
@RequestMapping("/api/user/subjects")
@RequiredArgsConstructor
@Validated
@Tag(name = "番剧浏览", description = "用户浏览、搜索番剧列表和详情")
public class SubjectController {

    private final SubjectService subjectService;
    private final EpisodeService episodeService;

    @GetMapping
    @Operation(summary = "获取番剧列表", description = "分页获取用户收藏/记录的番剧列表，支持排序")
    public Result<PageResult<SubjectListVO>> listSubjects(
            @Parameter(description = "页码", example = "1") @RequestParam(defaultValue = "1") @Min(1) int page,
            @Parameter(description = "每页条数", example = "20") @RequestParam(defaultValue = "20") @Min(1) @Max(100) int size,
            @Parameter(description = "排序字段（score / name / airDate 等）", example = "score") @RequestParam(defaultValue = "score") String sort,
            @Parameter(description = "排序方向（asc / desc）", example = "desc") @RequestParam(defaultValue = "desc") String order) {
        return Result.success(subjectService.listSubjects(page, size, sort, order));
    }

    @GetMapping("/search")
    @Operation(summary = "搜索番剧", description = "按关键词搜索番剧（模糊匹配名称）")
    public Result<PageResult<SubjectListVO>> searchSubjects(
            @Parameter(description = "搜索关键词", required = true, example = "巨人") @RequestParam String q,
            @Parameter(description = "页码", example = "1") @RequestParam(defaultValue = "1") @Min(1) int page,
            @Parameter(description = "每页条数", example = "20") @RequestParam(defaultValue = "20") @Min(1) @Max(100) int size) {
        if (q == null || q.trim().isEmpty()) {
            throw new BizException(ErrorType.BAD_REQUEST, "搜索关键词不能为空");
        }
        return Result.success(subjectService.searchSubjects(q.trim(), page, size));
    }

    @GetMapping("/season")
    @Operation(summary = "按季度筛选番剧", description = "按年份和季度筛选番剧，如 2026 年春季")
    public Result<PageResult<SubjectListVO>> listBySeason(
            @Parameter(description = "年份", required = true, example = "2026") @RequestParam @Min(1970) @Max(2100) int year,
            @Parameter(description = "季度（spring/summer/autumn/winter）", required = true, example = "spring") @RequestParam @Pattern(regexp = "spring|summer|autumn|winter", message = "季度仅允许: spring/summer/autumn/winter") String quarter,
            @Parameter(description = "页码", example = "1") @RequestParam(defaultValue = "1") @Min(1) int page,
            @Parameter(description = "每页条数", example = "20") @RequestParam(defaultValue = "20") @Min(1) @Max(100) int size) {
        return Result.success(subjectService.listBySeason(year, quarter, page, size));
    }

    @GetMapping("/{id}")
    @Operation(summary = "获取番剧详情", description = "根据条目ID获取番剧完整信息（含标签）")
    public Result<SubjectDetailVO> getSubjectDetail(
            @Parameter(description = "条目ID", required = true, example = "1") @PathVariable Long id) {
        return Result.success(subjectService.getSubjectDetail(id));
    }

    @GetMapping("/{id}/episodes")
    @Operation(summary = "获取番剧剧集列表", description = "根据条目ID获取该番剧的所有剧集")
    public Result<List<EpisodeVO>> getEpisodes(
            @Parameter(description = "条目ID", required = true, example = "1") @PathVariable Long id) {
        return Result.success(episodeService.getEpisodesBySubjectId(id));
    }
}
```

- [ ] **Step 2: AdminController 添加注解**

```java
package top.zhaizz.animetracker.subject.controller;

import io.swagger.v3.oas.annotations.Operation;
import io.swagger.v3.oas.annotations.Parameter;
import io.swagger.v3.oas.annotations.tags.Tag;
import jakarta.validation.Valid;
import lombok.RequiredArgsConstructor;
import org.springframework.validation.annotation.Validated;
import org.springframework.web.bind.annotation.*;
import top.zhaizz.animetracker.common.result.Result;
import top.zhaizz.animetracker.common.dto.SubjectCreateDTO;
import top.zhaizz.animetracker.common.dto.SubjectUpdateDTO;
import top.zhaizz.animetracker.subject.service.SubjectService;
import top.zhaizz.animetracker.common.vo.SubjectDetailVO;

@RestController
@RequestMapping("/api/admin/subjects")
@RequiredArgsConstructor
@Validated
@Tag(name = "番剧管理（管理员）", description = "管理员创建、更新、删除番剧条目")
public class AdminController {

    private final SubjectService subjectService;

    @PostMapping
    @Operation(summary = "创建番剧", description = "创建新的番剧条目")
    public Result<SubjectDetailVO> createSubject(@Valid @RequestBody SubjectCreateDTO request) {
        return Result.success(subjectService.createSubject(request));
    }

    @PutMapping("/{id}")
    @Operation(summary = "更新番剧", description = "更新指定番剧条目的信息（仅传入需要修改的字段）")
    public Result<SubjectDetailVO> updateSubject(
            @Parameter(description = "条目ID", required = true, example = "1") @PathVariable Long id,
            @Valid @RequestBody SubjectUpdateDTO request) {
        return Result.success(subjectService.updateSubject(id, request));
    }

    @DeleteMapping("/{id}")
    @Operation(summary = "删除番剧", description = "删除指定番剧条目")
    public Result<Void> deleteSubject(
            @Parameter(description = "条目ID", required = true, example = "1") @PathVariable Long id) {
        subjectService.deleteSubject(id);
        return Result.success();
    }
}
```

- [ ] **Step 3: Commit**

```bash
git add backend/api/src/main/java/top/zhaizz/animetracker/subject/controller/SubjectController.java backend/api/src/main/java/top/zhaizz/animetracker/subject/controller/AdminController.java
git commit -m "docs: SubjectController 和 AdminController 添加 @Tag/@Operation 注解"
```

---

### Task 6: TagController + ImportController 添加注解

**Files:**
- Modify: `backend/api/src/main/java/top/zhaizz/animetracker/subject/controller/TagController.java`
- Modify: `backend/api/src/main/java/top/zhaizz/animetracker/subject/controller/ImportController.java`

**Interfaces:**
- Consumes: `TagVO`, `SubjectListVO`, `ImportStatusVO`, `PageResult` (from Tasks 1-2)
- Produces: Documented tag and import API groups

- [ ] **Step 1: TagController 添加注解**

```java
package top.zhaizz.animetracker.subject.controller;

import io.swagger.v3.oas.annotations.Operation;
import io.swagger.v3.oas.annotations.Parameter;
import io.swagger.v3.oas.annotations.tags.Tag;
import jakarta.validation.constraints.Max;
import jakarta.validation.constraints.Min;
import lombok.RequiredArgsConstructor;
import org.springframework.validation.annotation.Validated;
import org.springframework.web.bind.annotation.*;
import top.zhaizz.animetracker.common.result.Result;
import top.zhaizz.animetracker.common.result.PageResult;
import top.zhaizz.animetracker.subject.service.TagService;
import top.zhaizz.animetracker.common.vo.SubjectListVO;
import top.zhaizz.animetracker.common.vo.TagVO;

import java.util.List;

@RestController
@RequestMapping("/api/user/tags")
@RequiredArgsConstructor
@Validated
@Tag(name = "标签管理", description = "查看标签和按标签筛选番剧")
public class TagController {

    private final TagService tagService;

    @GetMapping
    @Operation(summary = "获取标签列表", description = "获取所有标签及其对应的番剧数量")
    public Result<List<TagVO>> listTags() {
        return Result.success(tagService.listTags());
    }

    @GetMapping("/{tag}/subjects")
    @Operation(summary = "按标签获取番剧", description = "获取指定标签下的番剧列表（分页）")
    public Result<PageResult<SubjectListVO>> listSubjectsByTag(
            @Parameter(description = "标签名称", required = true, example = "热血") @PathVariable String tag,
            @Parameter(description = "页码", example = "1") @RequestParam(defaultValue = "1") @Min(1) int page,
            @Parameter(description = "每页条数", example = "20") @RequestParam(defaultValue = "20") @Min(1) @Max(100) int size) {
        return Result.success(tagService.listSubjectsByTag(tag, page, size));
    }
}
```

- [ ] **Step 2: ImportController 添加注解**

```java
package top.zhaizz.animetracker.subject.controller;

import io.swagger.v3.oas.annotations.Operation;
import io.swagger.v3.oas.annotations.tags.Tag;
import lombok.RequiredArgsConstructor;
import org.springframework.web.bind.annotation.*;
import top.zhaizz.animetracker.common.result.Result;
import top.zhaizz.animetracker.subject.service.ImportService;
import top.zhaizz.animetracker.common.vo.ImportStatusVO;

@RestController
@RequestMapping("/api/admin/import")
@RequiredArgsConstructor
@Tag(name = "番剧导入（管理员）", description = "从 Bangumi 等来源导入番剧数据")
public class ImportController {

    private final ImportService importService;

    @PostMapping("/run")
    @Operation(summary = "运行导入", description = "触发番剧数据导入任务")
    public Result<Void> runImport() {
        importService.runImport();
        return Result.success();
    }

    @GetMapping("/status")
    @Operation(summary = "获取导入状态", description = "查询最近导入状态和导入记录")
    public Result<ImportStatusVO> getImportStatus() {
        return Result.success(importService.getImportStatus());
    }
}
```

- [ ] **Step 3: Commit**

```bash
git add backend/api/src/main/java/top/zhaizz/animetracker/subject/controller/TagController.java backend/api/src/main/java/top/zhaizz/animetracker/subject/controller/ImportController.java
git commit -m "docs: TagController 和 ImportController 添加 @Tag/@Operation 注解"
```

---

### Task 7: 构建验证

**Files:**
- Test: build project and verify Knife4j UI accessible

**Interfaces:**
- Consumes: All previous tasks
- Produces: Verified working Knife4j API documentation

- [ ] **Step 1: Maven 编译验证**

Run:
```bash
cd backend/api
mvn compile -q
```

Expected: BUILD SUCCESS (无编译错误)

- [ ] **Step 2: 启动应用（如本地环境支持）**

Run:
```bash
cd backend/api
mvn spring-boot:run
```

Expected: 应用启动成功，访问 http://localhost:8080/doc.html 可看到 Knife4j 文档页面

- [ ] **Step 3: 验证 API 文档内容**

确认 Knife4j 界面包含以下分组：
- 认证管理（注册/登录/注销）
- 个人信息管理（获取/修改个人信息）
- 番剧浏览（列表/搜索/季度筛选/详情/剧集）
- 标签管理（标签列表/按标签筛选）
- 用户管理-管理员（用户列表/修改角色）
- 番剧管理-管理员（CRUD）
- 番剧导入-管理员（导入/状态）

每个接口应有完整的参数说明、示例值和响应模型描述。

- [ ] **Step 4: 关闭应用（如已启动）**

按 Ctrl+C 停止应用

- [ ] **Step 5: 提交最终 commit（如果构建中修改了任何问题）**

```bash
git add -A
git commit -m "fix: 修复构建问题"
```

---

## Self-Review

**1. Spec coverage:**
- ✅ Knife4j 依赖检查 — 已在 pom.xml 中存在，无需修改
- ✅ Knife4j 配置检查 — 已在 application.yml 中存在，无需修改
- ✅ OpenAPI 配置检查 — OpenApiConfig.java 已配置标题、版本、JWT 安全方案
- ✅ Security 白名单检查 — `/doc.html`、`/v3/api-docs/**`、`/swagger-ui/**` 已在 SecurityConfig 中放行
- ✅ Controller `@Tag` / `@Operation` — 6 个 Controller 全部覆盖
- ✅ DTO `@Schema` — 8 个 DTO 全部覆盖
- ✅ VO `@Schema` — 8 个 VO 全部覆盖
- ✅ Result/PageResult `@Schema` — 统一响应体已覆盖
- ✅ 构建验证 — Task 7 覆盖

**2. Placeholder scan:** 无占位符，所有代码块包含完整实现。

**3. Type consistency:** 所有 `@Schema(description=...)` 的字段名、示例值与相应 DTO/VO 类定义一致。
