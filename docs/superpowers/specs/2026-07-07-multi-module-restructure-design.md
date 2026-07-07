# AnimeTracker 后端多模块重构设计

> **版本:** 1.0
> **日期:** 2026-07-07
> **状态:** 设计稿

## 1. 动机

当前项目为单模块 Spring Boot 应用（`backend/api`），所有代码集中在同一 Maven 模块中。随着业务增长，单模块导致：

- 编译时间长，每次改任意代码都要重编整个项目
- 模块边界不清晰，`common` 包和业务包混杂
- 无法独立构建/测试某个业务模块
- 新人（或 AI 代理）理解项目需要加载全部上下文

多模块重构旨在**从组织上隔离职责**，不改动现有业务逻辑和 API 签名。

## 2. 模块划分

```
backend/
├── business/                              # 父 POM
│   ├── pom.xml                            # packaging=pom, 聚合所有子模块
│   ├── common/                            # 共享基类、异常、工具
│   ├── security/                          # JWT 安全层
│   ├── user/                              # 用户模块（完整垂直栈）
│   ├── subject/                           # 条目模块（完整垂直栈）
│   └── app/                               # Spring Boot 启动器
```

### 2.1 business (父 POM)

- **artifactId:** `business`
- **packaging:** `pom`
- **作用:** 统一管理依赖版本（`dependencyManagement`），聚合子模块，定义 Maven Enforcer 插件
- **groupId:** `top.zhaizz`
- **version:** `2.0.0`
- **父 POM:** `spring-boot-starter-parent:3.2.0`

### 2.2 common

- **artifactId:** `animetracker-common`
- **包基路径:** `top.zhaizz.animetracker.common`
- **包含内容:**
  - `result/` — `Result<T>`, `PageResult<T>`
  - `exception/` — `BizException`, `GlobalExceptionHandler`
  - `ErrorType.java`
  - `util/` — `RedisClient`
- **依赖:** `spring-boot-starter-web`, `spring-boot-starter-data-redis`, `commons-codec`, `jackson`, `lombok`

### 2.3 security

- **artifactId:** `animetracker-security`
- **包基路径:** `top.zhaizz.animetracker.security`
- **包含内容:**
  - `JwtTokenProvider`
  - `JwtAuthenticationFilter`
  - `UserPrincipal`
  - `SecurityConfig` — 安全过滤链、密码编码器
  - `CorsConfig`
- **依赖:** `common`, `spring-boot-starter-security`, `jjwt` (api+impl+jackson)

> `SecurityConfig` 和 `CorsConfig` 当前放在 `config/` 包下，但它们是安全基础设施。重构后移入 security 模块。

### 2.4 user

- **artifactId:** `animetracker-user`
- **包基路径:** `top.zhaizz.animetracker.user`
- **包含内容（完整垂直栈，不自带启动/配置）:**
  - `entity/` — `User`
  - `mapper/` — `UserMapper`
  - `service/` — `AuthService`, `UserService` + impl
  - `controller/` — `AuthController`, `UserController`, `AdminUserController`
  - `converter/` — `UserConverter`
- **DTO/VO 归属说明:** `LoginDTO`, `RegisterDTO`, `UpdateUserDTO`, `UpdateRoleDTO`, `LoginVO`, `UserVO` 保留在 common 模块（被 subject 模块的 `AdminController` 引用）

### 2.5 subject

- **artifactId:** `animetracker-subject`
- **包基路径:** `top.zhaizz.animetracker.subject`
- **包含内容（完整垂直栈）:**
  - `entity/` — `Subject`, `Episode`, `SubjectTag`, `ImportRecord`
  - `mapper/` — 4 个 Mapper
  - `service/` — 4 个 Service + impl
  - `controller/` — `SubjectController`, `TagController`, `AdminController`, `ImportController`
  - `converter/` — `SubjectConverter`
  - `util/` — `SeasonUtil`
- **MyBatis XML:** 保留在 app 模块的 resources 下（MyBatis-Plus 扫描时读取）

### 2.6 app

- **artifactId:** `animetracker-app`
- **包基路径:** `top.zhaizz.animetracker`
- **作用:** 可运行入口，聚合所有模块
- **包含内容:**
  - `AppApplication.java` — `@SpringBootApplication` + `@MapperScan`
  - `config/` — `MyBatisPlusConfig`, `OpenApiConfig`（应用级配置，非安全）
  - `src/main/resources/` — `application.yml`, `application-local.yml`, mapper XML
- **依赖:** `user`, `subject`, `mysql-connector-j` (runtime), `knife4j`, `spring-boot-starter-cache`, test 依赖

## 3. 依赖关系

```
common  ←  security  ←  user  ←  app
                    ←  subject ←  app
```

具体传递路径：

| 模块 | 直接依赖 | 传递依赖 |
|------|---------|---------|
| common | web, data-redis, commons-codec, jackson, lombok | — |
| security | common, spring-security, jjwt | web (通过 common) |
| user | common, security, mybatis-plus, validation | spring-security (通过 security) |
| subject | common, security, mybatis-plus, validation | spring-security (通过 security) |
| app | user, subject, mysql-connector, knife4j, cache, h2, test-starter | 全部 |

## 4. 依赖版本管理

父 POM `dependencyManagement` 锁定以下版本，子模块不再重复写 version：

| 依赖 | 版本 |
|------|------|
| mybatis-plus-spring-boot3-starter | 3.5.5 |
| jjwt-api / jjwt-impl / jjwt-jackson | 0.12.3 |
| knife4j-openapi3-jakarta-spring-boot-starter | 4.5.0 |
| lombok | 1.18.30 |

`spring-boot-starter-*` 系列由 `spring-boot-starter-parent` 管理版本，不在父 POM 中重复声明。

## 5. 不变项

重构不改变以下内容：

- **API 路径和签名** — 所有 URL、请求参数、响应体格式不变
- **数据库表结构** — entity 字段映射不变
- **业务逻辑** — service impl 代码不修改
- **配置文件结构** — `application.yml` key 不变
- **`@MapperScan` 扫描范围** — 仍扫描所有 mapper 包
- **`@SpringBootApplication` 启动类位置** — 仍在 `top.zhaizz.animetracker` 包

## 6. 构建命令

```bash
# 编译全部
cd backend/business
mvn clean compile

# 打包（跳过测试）
mvn clean package -DskipTests

# 运行
java -jar app/target/animetracker-app-*.jar

# 单独编译某模块
mvn -pl user compile
mvn -pl app compile
```
