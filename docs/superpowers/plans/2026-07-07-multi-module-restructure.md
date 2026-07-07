# AnimeTracker 后端多模块重构实施计划

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 将 `backend/api` 单模块 Spring Boot 项目拆分为 `backend/business/` 下的 5 子模块 Maven 项目（common, security, user, subject, app）

**Architecture:** 按业务垂直切分，每个子模块有独立 POM，通过 `dependencyManagement` 统一版本。Java 包命名空间不变（`top.zhaizz.animetracker.*`），仅重新分配文件所属模块。

**Tech Stack:** Maven 3.9+, Java 21, Spring Boot 3.2.0

## Global Constraints

- Java 21, Spring Boot 3.2.0, Maven compiler source/target 21
- 所有原有包名保持不变（`top.zhaizz.animetracker.*`），不修改 Java import 语句
- 不改动任何业务逻辑、API 路径、数据库映射
- `@MapperScan` 保留在 AppApplication 中，扫描范围覆盖全部模块
- 最终交付产物：`app/target/animetracker-app-*.jar` 可独立运行

---

## File Structure

```
backend/business/                              # 新增：父 POM 目录
├── pom.xml                                     # packaging=pom
├── common/
│   ├── pom.xml
│   └── src/main/java/top/zhaizz/animetracker/common/
│       ├── result/Result.java, PageResult.java
│       ├── exception/BizException.java, GlobalExceptionHandler.java
│       ├── ErrorType.java
│       ├── util/RedisClient.java
│       ├── entity/User.java, Subject.java, Episode.java, SubjectTag.java, ImportRecord.java
│       ├── dto/LoginDTO.java, RegisterDTO.java, SubjectCreateDTO.java, SubjectUpdateDTO.java, ...
│       └── vo/LoginVO.java, UserVO.java, SubjectListVO.java, SubjectDetailVO.java, ...
├── security/
│   ├── pom.xml
│   ├── src/main/java/top/zhaizz/animetracker/security/
│   │   ├── JwtTokenProvider.java
│   │   ├── JwtAuthenticationFilter.java
│   │   ├── UserPrincipal.java
│   │   ├── config/SecurityConfig.java         # 从原 config/ 移入
│   │   └── config/CorsConfig.java             # 从原 config/ 移入
│   └── src/main/resources/                    # 无资源
├── user/
│   ├── pom.xml
│   └── src/main/java/top/zhaizz/animetracker/user/
│       ├── controller/AuthController.java, UserController.java, AdminUserController.java
│       ├── service/AuthService.java, UserService.java, impl/AuthServiceImpl.java, impl/UserServiceImpl.java
│       ├── mapper/UserMapper.java
│       └── converter/UserConverter.java
├── subject/
│   ├── pom.xml
│   └── src/main/java/top/zhaizz/animetracker/subject/
│       ├── controller/SubjectController.java, TagController.java, AdminController.java, ImportController.java
│       ├── service/SubjectService.java, EpisodeService.java, TagService.java, ImportService.java, impl/*
│       ├── mapper/SubjectMapper.java, EpisodeMapper.java, SubjectTagMapper.java, ImportRecordMapper.java
│       ├── converter/SubjectConverter.java
│       └── util/SeasonUtil.java
└── app/                                       # Spring Boot 启动器
    ├── pom.xml
    ├── src/main/java/top/zhaizz/animetracker/
    │   ├── AppApplication.java
    │   └── config/
    │       ├── MyBatisPlusConfig.java
    │       └── OpenApiConfig.java
    └── src/main/resources/
        ├── application.yml
        ├── application-local.yml
        └── mapper/
            ├── UserMapper.xml
            ├── SubjectMapper.xml
            ├── EpisodeMapper.xml
            └── SubjectTagMapper.xml
```

---

### Task 1: 创建父 POM

**Files:**
- Create: `backend/business/pom.xml`

**Interfaces:**
- Consumes: 无
- Produces: 父 POM，定义所有依赖版本、子模块列表、Maven Enforcer

- [ ] **Step 1: 创建父 POM 文件**

```xml
<?xml version="1.0" encoding="UTF-8"?>
<project xmlns="http://maven.apache.org/POM/4.0.0"
         xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance"
         xsi:schemaLocation="http://maven.apache.org/POM/4.0.0 https://maven.apache.org/xsd/maven-4.0.0.xsd">
    <modelVersion>4.0.0</modelVersion>

    <groupId>top.zhaizz</groupId>
    <artifactId>business</artifactId>
    <version>2.0.0</version>
    <packaging>pom</packaging>
    <name>AnimeTracker Business</name>
    <description>AnimeTracker - Personal Anime Tracking Platform Backend Parent</description>

    <parent>
        <groupId>org.springframework.boot</groupId>
        <artifactId>spring-boot-starter-parent</artifactId>
        <version>3.2.0</version>
        <relativePath/>
    </parent>

    <modules>
        <module>common</module>
        <module>security</module>
        <module>user</module>
        <module>subject</module>
        <module>app</module>
    </modules>

    <properties>
        <java.version>21</java.version>
        <maven.compiler.source>21</maven.compiler.source>
        <maven.compiler.target>21</maven.compiler.target>
        <project.build.sourceEncoding>UTF-8</project.build.sourceEncoding>

        <mybatis-plus.version>3.5.5</mybatis-plus.version>
        <jjwt.version>0.12.3</jjwt.version>
        <knife4j.version>4.5.0</knife4j.version>
        <lombok.version>1.18.30</lombok.version>
    </properties>

    <dependencyManagement>
        <dependencies>
            <!-- 子模块间依赖 -->
            <dependency>
                <groupId>top.zhaizz</groupId>
                <artifactId>animetracker-common</artifactId>
                <version>${project.version}</version>
            </dependency>
            <dependency>
                <groupId>top.zhaizz</groupId>
                <artifactId>animetracker-security</artifactId>
                <version>${project.version}</version>
            </dependency>
            <dependency>
                <groupId>top.zhaizz</groupId>
                <artifactId>animetracker-user</artifactId>
                <version>${project.version}</version>
            </dependency>
            <dependency>
                <groupId>top.zhaizz</groupId>
                <artifactId>animetracker-subject</artifactId>
                <version>${project.version}</version>
            </dependency>

            <!-- MyBatis-Plus -->
            <dependency>
                <groupId>com.baomidou</groupId>
                <artifactId>mybatis-plus-spring-boot3-starter</artifactId>
                <version>${mybatis-plus.version}</version>
            </dependency>

            <!-- JWT -->
            <dependency>
                <groupId>io.jsonwebtoken</groupId>
                <artifactId>jjwt-api</artifactId>
                <version>${jjwt.version}</version>
            </dependency>
            <dependency>
                <groupId>io.jsonwebtoken</groupId>
                <artifactId>jjwt-impl</artifactId>
                <version>${jjwt.version}</version>
                <scope>runtime</scope>
            </dependency>
            <dependency>
                <groupId>io.jsonwebtoken</groupId>
                <artifactId>jjwt-jackson</artifactId>
                <version>${jjwt.version}</version>
                <scope>runtime</scope>
            </dependency>

            <!-- Knife4j -->
            <dependency>
                <groupId>com.github.xiaoymin</groupId>
                <artifactId>knife4j-openapi3-jakarta-spring-boot-starter</artifactId>
                <version>${knife4j.version}</version>
            </dependency>

            <!-- Lombok -->
            <dependency>
                <groupId>org.projectlombok</groupId>
                <artifactId>lombok</artifactId>
                <version>${lombok.version}</version>
                <scope>provided</scope>
            </dependency>
        </dependencies>
    </dependencyManagement>

    <build>
        <pluginManagement>
            <plugins>
                <plugin>
                    <groupId>org.springframework.boot</groupId>
                    <artifactId>spring-boot-maven-plugin</artifactId>
                </plugin>
            </plugins>
        </pluginManagement>
        <plugins>
            <plugin>
                <groupId>org.apache.maven.plugins</groupId>
                <artifactId>maven-enforcer-plugin</artifactId>
                <version>3.4.1</version>
                <executions>
                    <execution>
                        <id>enforce-java</id>
                        <goals><goal>enforce</goal></goals>
                        <configuration>
                            <rules>
                                <requireJavaVersion><version>[21,)</version></requireJavaVersion>
                                <requireMavenVersion><version>[3.9,)</version></requireMavenVersion>
                            </rules>
                        </configuration>
                    </execution>
                </executions>
            </plugin>
        </plugins>
    </build>
</project>
```

- [ ] **Step 2: 验证目录结构**

确保 `backend/business/` 目录存在：
```bash
mkdir -p backend/business
```

---

### Task 2: 创建 common 模块

**Files:**
- Create: `backend/business/common/pom.xml`
- Copy: 全部 `backend/api/src/main/java/top/zhaizz/animetracker/common/` → `backend/business/common/src/main/java/top/zhaizz/animetracker/common/`

**Interfaces:**
- Consumes: Task 1 父 POM
- Produces: `animetracker-common` 模块，被 security/user/subject/app 依赖

- [ ] **Step 1: 创建 common 模块 POM**

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

    <artifactId>animetracker-common</artifactId>
    <packaging>jar</packaging>
    <name>AnimeTracker Common</name>
    <description>Shared base classes, exceptions, utilities</description>

    <dependencies>
        <dependency>
            <groupId>org.springframework.boot</groupId>
            <artifactId>spring-boot-starter-web</artifactId>
        </dependency>
        <dependency>
            <groupId>org.springframework.boot</groupId>
            <artifactId>spring-boot-starter-data-redis</artifactId>
        </dependency>
        <dependency>
            <groupId>commons-codec</groupId>
            <artifactId>commons-codec</artifactId>
        </dependency>
        <dependency>
            <groupId>com.fasterxml.jackson.core</groupId>
            <artifactId>jackson-databind</artifactId>
        </dependency>
        <dependency>
            <groupId>com.fasterxml.jackson.datatype</groupId>
            <artifactId>jackson-datatype-jsr310</artifactId>
        </dependency>
        <dependency>
            <groupId>org.projectlombok</groupId>
            <artifactId>lombok</artifactId>
        </dependency>
    </dependencies>
</project>
```

- [ ] **Step 2: 复制 common 包源码**

```bash
SRC="backend/api/src/main/java/top/zhaizz/animetracker/common"
DST="backend/business/common/src/main/java/top/zhaizz/animetracker/common"
mkdir -p "$DST/result" "$DST/exception" "$DST/util" "$DST/entity" "$DST/dto" "$DST/vo"
cp -r "$SRC/result/" "$DST/result/"
cp -r "$SRC/exception/" "$DST/exception/"
cp -r "$SRC/util/" "$DST/util/"
cp -r "$SRC/entity/" "$DST/entity/"
cp -r "$SRC/dto/" "$DST/dto/"
cp -r "$SRC/vo/" "$DST/vo/"
cp "$SRC/ErrorType.java" "$DST/ErrorType.java"
```

---

### Task 3: 创建 security 模块

**Files:**
- Create: `backend/business/security/pom.xml`
- Copy: `backend/api/src/main/java/top/zhaizz/animetracker/security/` → `backend/business/security/src/main/java/top/zhaizz/animetracker/security/`
- Move & repackage: `backend/api/src/main/java/top/zhaizz/animetracker/config/SecurityConfig.java` → `backend/business/security/src/main/java/top/zhaizz/animetracker/security/config/SecurityConfig.java`
- Move & repackage: `backend/api/src/main/java/top/zhaizz/animetracker/config/CorsConfig.java` → `backend/business/security/src/main/java/top/zhaizz/animetracker/security/config/CorsConfig.java`

**Interfaces:**
- Consumes: Task 1 (父 POM), Task 2 (common)
- Produces: `animetracker-security` 模块，被 user/subject/app 依赖

- [ ] **Step 1: 创建 security 模块 POM**

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

    <artifactId>animetracker-security</artifactId>
    <packaging>jar</packaging>
    <name>AnimeTracker Security</name>
    <description>JWT authentication, security filters, CORS config</description>

    <dependencies>
        <dependency>
            <groupId>top.zhaizz</groupId>
            <artifactId>animetracker-common</artifactId>
        </dependency>
        <dependency>
            <groupId>org.springframework.boot</groupId>
            <artifactId>spring-boot-starter-security</artifactId>
        </dependency>
        <dependency>
            <groupId>io.jsonwebtoken</groupId>
            <artifactId>jjwt-api</artifactId>
        </dependency>
        <dependency>
            <groupId>io.jsonwebtoken</groupId>
            <artifactId>jjwt-impl</artifactId>
        </dependency>
        <dependency>
            <groupId>io.jsonwebtoken</groupId>
            <artifactId>jjwt-jackson</artifactId>
        </dependency>
    </dependencies>
</project>
```

- [ ] **Step 2: 复制 security 包源码（无 package 变更）**

```bash
cp -r "backend/api/src/main/java/top/zhaizz/animetracker/security" \
      "backend/business/security/src/main/java/top/zhaizz/animetracker/"
```

- [ ] **Step 3: 移动 SecurityConfig.java 并更新包声明**

创建目标目录并复制：
```bash
mkdir -p "backend/business/security/src/main/java/top/zhaizz/animetracker/security/config"
cp "backend/api/src/main/java/top/zhaizz/animetracker/config/SecurityConfig.java" \
   "backend/business/security/src/main/java/top/zhaizz/animetracker/security/config/SecurityConfig.java"
```

读目标文件确认内容：
```bash
head -5 backend/business/security/src/main/java/top/zhaizz/animetracker/security/config/SecurityConfig.java
```
当前第一行 package `top.zhaizz.animetracker.config`。将文件顶部 `package top.zhaizz.animetracker.config;` 改为 `package top.zhaizz.animetracker.security.config;`

- [ ] **Step 4: 移动 CorsConfig.java 并更新包声明**

```bash
cp "backend/api/src/main/java/top/zhaizz/animetracker/config/CorsConfig.java" \
   "backend/business/security/src/main/java/top/zhaizz/animetracker/security/config/CorsConfig.java"
```

同样将 package 从 `top.zhaizz.animetracker.config` 改为 `top.zhaizz.animetracker.security.config`

---

### Task 4: 创建 user 模块

**Files:**
- Create: `backend/business/user/pom.xml`
- Copy: `backend/api/src/main/java/top/zhaizz/animetracker/user/` → `backend/business/user/src/main/java/top/zhaizz/animetracker/user/`

**Interfaces:**
- Consumes: Task 1 (父 POM), Task 2 (common), Task 3 (security)
- Produces: `animetracker-user` 模块，被 app 依赖

- [ ] **Step 1: 创建 user 模块 POM**

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

    <artifactId>animetracker-user</artifactId>
    <packaging>jar</packaging>
    <name>AnimeTracker User</name>
    <description>User module: auth, registration, profile, admin user management</description>

    <dependencies>
        <dependency>
            <groupId>top.zhaizz</groupId>
            <artifactId>animetracker-common</artifactId>
        </dependency>
        <dependency>
            <groupId>top.zhaizz</groupId>
            <artifactId>animetracker-security</artifactId>
        </dependency>
        <dependency>
            <groupId>org.springframework.boot</groupId>
            <artifactId>spring-boot-starter-validation</artifactId>
        </dependency>
        <dependency>
            <groupId>com.baomidou</groupId>
            <artifactId>mybatis-plus-spring-boot3-starter</artifactId>
        </dependency>
    </dependencies>
</project>
```

- [ ] **Step 2: 复制 user 包源码（无 package 变更）**

```bash
cp -r "backend/api/src/main/java/top/zhaizz/animetracker/user" \
      "backend/business/user/src/main/java/top/zhaizz/animetracker/"
```

---

### Task 5: 创建 subject 模块

**Files:**
- Create: `backend/business/subject/pom.xml`
- Copy: `backend/api/src/main/java/top/zhaizz/animetracker/subject/` → `backend/business/subject/src/main/java/top/zhaizz/animetracker/subject/`

**Interfaces:**
- Consumes: Task 1 (父 POM), Task 2 (common), Task 3 (security)
- Produces: `animetracker-subject` 模块，被 app 依赖

- [ ] **Step 1: 创建 subject 模块 POM**

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

    <artifactId>animetracker-subject</artifactId>
    <packaging>jar</packaging>
    <name>AnimeTracker Subject</name>
    <description>Subject module: anime entries, episodes, tags, import</description>

    <dependencies>
        <dependency>
            <groupId>top.zhaizz</groupId>
            <artifactId>animetracker-common</artifactId>
        </dependency>
        <dependency>
            <groupId>top.zhaizz</groupId>
            <artifactId>animetracker-security</artifactId>
        </dependency>
        <dependency>
            <groupId>org.springframework.boot</groupId>
            <artifactId>spring-boot-starter-validation</artifactId>
        </dependency>
        <dependency>
            <groupId>com.baomidou</groupId>
            <artifactId>mybatis-plus-spring-boot3-starter</artifactId>
        </dependency>
    </dependencies>
</project>
```

- [ ] **Step 2: 复制 subject 包源码（无 package 变更）**

```bash
cp -r "backend/api/src/main/java/top/zhaizz/animetracker/subject" \
      "backend/business/subject/src/main/java/top/zhaizz/animetracker/"
```

---

### Task 6: 创建 app 模块（启动器）

**Files:**
- Create: `backend/business/app/pom.xml`
- Copy: `AppApplication.java` 到 `backend/business/app/src/main/java/top/zhaizz/animetracker/AppApplication.java`
- Copy: `MyBatisPlusConfig.java`、`OpenApiConfig.java` 到 `backend/business/app/src/main/java/top/zhaizz/animetracker/config/`
- Copy: `application.yml`、`application-local.yml`、`mapper/*.xml` 到 `backend/business/app/src/main/resources/`

**Interfaces:**
- Consumes: Task 1 (父 POM), Task 2 (common), Task 3 (security), Task 4 (user), Task 5 (subject)
- Produces: 最终可运行 JAR

- [ ] **Step 1: 创建 app 模块 POM**

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

    <artifactId>animetracker-app</artifactId>
    <packaging>jar</packaging>
    <name>AnimeTracker App</name>
    <description>AnimeTracker Spring Boot application entry point</description>

    <dependencies>
        <!-- 聚合业务模块 -->
        <dependency>
            <groupId>top.zhaizz</groupId>
            <artifactId>animetracker-user</artifactId>
        </dependency>
        <dependency>
            <groupId>top.zhaizz</groupId>
            <artifactId>animetracker-subject</artifactId>
        </dependency>

        <!-- MySQL 驱动 -->
        <dependency>
            <groupId>com.mysql</groupId>
            <artifactId>mysql-connector-j</artifactId>
            <scope>runtime</scope>
        </dependency>

        <!-- Knife4j API 文档 -->
        <dependency>
            <groupId>com.github.xiaoymin</groupId>
            <artifactId>knife4j-openapi3-jakarta-spring-boot-starter</artifactId>
        </dependency>

        <!-- Spring Cache（Redis 缓存注解支持） -->
        <dependency>
            <groupId>org.springframework.boot</groupId>
            <artifactId>spring-boot-starter-cache</artifactId>
        </dependency>

        <!-- Lombok -->
        <dependency>
            <groupId>org.projectlombok</groupId>
            <artifactId>lombok</artifactId>
        </dependency>

        <!-- Test -->
        <dependency>
            <groupId>org.springframework.boot</groupId>
            <artifactId>spring-boot-starter-test</artifactId>
            <scope>test</scope>
        </dependency>
        <dependency>
            <groupId>org.springframework.security</groupId>
            <artifactId>spring-security-test</artifactId>
            <scope>test</scope>
        </dependency>
        <dependency>
            <groupId>com.h2database</groupId>
            <artifactId>h2</artifactId>
            <scope>test</scope>
        </dependency>
    </dependencies>

    <build>
        <plugins>
            <plugin>
                <groupId>org.springframework.boot</groupId>
                <artifactId>spring-boot-maven-plugin</artifactId>
                <configuration>
                    <mainClass>top.zhaizz.animetracker.AppApplication</mainClass>
                </configuration>
            </plugin>
        </plugins>
    </build>
</project>
```

- [ ] **Step 2: 复制 AppApplication.java 和 config 类**

```bash
mkdir -p "backend/business/app/src/main/java/top/zhaizz/animetracker/config"
cp "backend/api/src/main/java/top/zhaizz/animetracker/AppApplication.java" \
   "backend/business/app/src/main/java/top/zhaizz/animetracker/AppApplication.java"
cp "backend/api/src/main/java/top/zhaizz/animetracker/config/MyBatisPlusConfig.java" \
   "backend/business/app/src/main/java/top/zhaizz/animetracker/config/MyBatisPlusConfig.java"
cp "backend/api/src/main/java/top/zhaizz/animetracker/config/OpenApiConfig.java" \
   "backend/business/app/src/main/java/top/zhaizz/animetracker/config/OpenApiConfig.java"
```

- [ ] **Step 3: 复制资源配置文件**

```bash
mkdir -p "backend/business/app/src/main/resources/mapper"
cp "backend/api/src/main/resources/application.yml" \
   "backend/business/app/src/main/resources/application.yml"
cp "backend/api/src/main/resources/application-local.yml" \
   "backend/business/app/src/main/resources/application-local.yml"
cp "backend/api/src/main/resources/mapper/"*.xml \
   "backend/business/app/src/main/resources/mapper/"
```

---

### Task 7: 验证多模块编译

- [ ] **Step 1: 编译全部模块**

```bash
cd backend/business
mvn clean compile -q
```
Expected: `BUILD SUCCESS`。如果失败，检查：

- 所有子模块 POM 中的 parent relativePath 是否正确
- `@MapperScan` 是否能扫描到所有模块的 mapper
- `SecurityConfig` 和 `CorsConfig` 的 package 变更后，`@ComponentScan` 是否能发现（位于 `top.zhaizz.animetracker.security` 下，在 `@SpringBootApplication` 扫描范围内）

- [ ] **Step 2: 打包验证**

```bash
mvn clean package -DskipTests -q
```
Expected: `BUILD SUCCESS`，产出 `app/target/animetracker-app-*.jar`

---

### Task 8: 清理旧目录

- [ ] **Step 1: 删除旧 api 目录**

```bash
rm -rf backend/api
```

- [ ] **Step 2: 检查是否有其他地方引用旧路径**

```bash
cd ../..
grep -rn "backend/api" README.md docs/ --include="*.md" || echo "no references found"
```
如果找到引用，记录到 Task 9 中更新。

---

### Task 9: 更新文档

**Files:**
- Modify: `README.md`
- Modify: `docs/tech-spec.md`（更新目录结构章节）

- [ ] **Step 1: 更新 README.md**

将项目结构树中的 `backend/api/` 路径更新为 `backend/business/`，并反映多模块结构：

```
backend/business/                   # 后端多模块工程
├── common/                         # 共享模块
├── security/                       # 安全模块
├── user/                           # 用户模块
├── subject/                        # 条目模块
└── app/                            # 启动器
```

更新构建命令：
```diff
- cd backend/api
+ cd backend/business
```

更新目录说明：
```diff
- backend/api/     # Spring Boot REST API (端口 8080)
+ backend/business/ # Spring Boot 多模块工程 (端口 8080)
```

- [ ] **Step 2: 更新 docs/tech-spec.md**

将第 3 节「项目目录结构」中的 `backend/api/` 路径和描述更新为新的多模块结构。

- [ ] **Step 3: 提交**

```bash
cd backend/business
git add -A
git commit -m "refactor: restructure backend into multi-module Maven project

- Create business parent POM with dependencyManagement
- Split into 5 modules: common, security, user, subject, app
- Move SecurityConfig/CorsConfig from config/ to security module
- Remove old backend/api single-module directory
- Add Maven Enforcer plugin for version consistency
- Update documentation"
```

---

## Spec Coverage Check

| Spec Requirement | Task |
|:---|---:|
| 父 POM `business` 聚合所有子模块 | Task 1 |
| common 模块：共享基类、异常、工具 | Task 2 |
| security 模块：JWT、安全过滤链、CORS | Task 3 |
| user 模块：用户完整垂直栈 | Task 4 |
| subject 模块：条目完整垂直栈 | Task 5 |
| app 模块：Spring Boot 启动器 | Task 6 |
| Maven Enforcer 保证版本一致 | Task 1 (父 POM plugins) |
| MyBatis XML 保留在 app 模块资源目录 | Task 6 |
| 移除旧 backend/api 目录 | Task 8 |
| 更新文档 | Task 9 |
