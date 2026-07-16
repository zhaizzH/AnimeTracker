# MinIO 对象存储集成设计

> 为 AnimeTracker 引入 MinIO 对象存储，用于用户头像存储及番剧封面迁移。

## 背景

- 用户头像 (`user.avatar`): 当前为空字段，无数据
- 番剧封面 (`subject.image`): 由 Bangumi API 导入产生，现存约 1200 条记录，指向第三方 CDN（lain.bgm.tv 等）
- 项目当前无文件上传能力，无对象存储依赖

## 架构

```
用户/迁移脚本 → POST /api/common/files/upload → 后端 → MinIO (Docker)
                                                    ↓
                                               返回 MinIO URL
                                                    ↓
                                              存入 DB (avatar/image 字段)
```

- DB 字段类型保持 `VARCHAR(512)` 不变，存的仍是 URL，只是来源变成 MinIO
- 现存第三方 CDN 链接继续可访问，不删除

## 改动范围

### 后端

| # | 文件 | 类型 | 说明 |
|---|------|------|------|
| 1 | `backend/business/pom.xml` | 修改 | `io.minio:minio:8.5.7` 版本属性 |
| 2 | `backend/business/common/pom.xml` | 修改 | 添加 minio 依赖 |
| 3 | `common/.../config/MinioProperties.java` | 新增 | `@ConfigurationProperties(prefix="minio")` |
| 4 | `common/.../config/MinioConfig.java` | 新增 | `MinioClient` Bean + bucket 启动自检（不存在则创建） |
| 5 | `common/.../controller/FileController.java` | 新增 | `POST /api/common/files/upload?type=avatar\|cover` |
| 6 | `common/.../config/SecurityConfig.java` | 修改 | `requestMatchers("/api/common/files/**").authenticated()` |
| 7 | `app/.../resources/application.yml` | 修改 | 添加 minio 配置占位符 |
| 8 | `app/.../resources/application-local.yml` | 修改 | 添加本地 minio 具体值 |

### 前端

| # | 文件 | 类型 | 说明 |
|---|------|------|------|
| 9 | `frontend/client/src/api/upload.ts` | 新增 | 封装文件上传函数 |
| 10 | `frontend/client/src/pages/Profile.vue` | 修改 | 文件选择器替换 URL 输入框 |
| 11 | `frontend/client/src/types/index.ts` | 修改 | 添加 `UploadResult` 类型 |

### 数据迁移

| # | 文件 | 类型 | 说明 |
|---|------|------|------|
| 12 | `backend/data/migration/migrate_covers.py` | 新增 | Python 脚本：下载现有封面 → 上传 MinIO → 更新 DB |

## 详细设计

### MinioProperties

```java
@ConfigurationProperties(prefix = "minio")
public class MinioProperties {
    private String endpoint = "http://localhost:9000";
    private String accessKey;
    private String secretKey;
    private String bucket = "anime-tracker";
}
```

### MinioConfig

- 创建 `MinioClient` Bean
- `@PostConstruct` 方法检查 bucket 是否存在，不存在则创建（`MakeBucketArgs`）
- bucket 设置 `READ_ONLY` 策略（通过 `SetBucketPolicyArgs`）

### FileController

```java
@RestController
@RequestMapping("/api/common/files")
@RequiredArgsConstructor
public class FileController {

    @PostMapping("/upload")
    public Result<UploadVO> upload(
            @RequestParam("file") MultipartFile file,
            @RequestParam(value = "type", defaultValue = "avatar") String type) {

        // 1. 校验文件类型: jpg/png/webp only
        // 2. 校验文件大小: max 5MB
        // 3. 生成路径: {type}/{uuid}.{ext}
        // 4. 上传到 MinIO (PutObjectArgs)
        // 5. 返回 URL: {endpoint}/{bucket}/{path}
    }
}
```

路径规则:
- 头像: `avatars/{uuid}.{ext}`
- 封面: `covers/{uuid}.{ext}`

### SecurityConfig

```java
.requestMatchers(HttpMethod.POST, "/api/common/files/**").authenticated()
```

上传接口需要登录即可，前端页面靠路由守卫控制管理权限。

### 前端上传 (Profile.vue)

- `<input type="file" accept="image/jpeg,image/png,image/webp">`
- 用户选文件后自动上传到 `/api/common/files/upload?type=avatar`
- 上传完成后返回的 URL 自动填到表单中
- 增加上传中进度反馈

### 封面迁移脚本 (migrate_covers.py)

独立 Python 脚本，不依赖于 Spring 启动：

```
1. 连接 MySQL（通过环境变量或 .env 配置）
2. SELECT id, image FROM subject WHERE image IS NOT NULL AND image != ''
3. 对每条记录:
   a. 请求下载 image URL (requests.get, timeout=15s, stream)
   b. 从 Content-Type 或 URL 后缀推断扩展名
   c. 上传到 MinIO: covers/{subjectId}.{ext}（用 MinIO Python SDK）
   d. UPDATE subject SET image = {minio_url} WHERE id = {id}
4. 打印统计: 总数 / 成功 / 失败
```

依赖: `pip install minio requests sqlalchemy pymysql`

迁移可重复执行：脚本先检查 `image` 字段是否已指向 MinIO endpoint，是则跳过。

## 配置示例

```yaml
# application-local.yml
minio:
  endpoint: http://localhost:9000
  access-key: minioadmin
  secret-key: minioadmin
  bucket: anime-tracker
```

```yaml
# application.yml (占位符)
minio:
  endpoint: ${minio.endpoint:http://localhost:9000}
  access-key: ${minio.access-key}
  secret-key: ${minio.secret-key}
  bucket: ${minio.bucket:anime-tracker}
```

## 安全 & 边界

- 文件类型白名单：`image/jpeg`, `image/png`, `image/webp`
- 文件大小上限：5MB（`spring.servlet.multipart.max-file-size=5MB`）
- 文件名使用 UUID 防止冲突/遍历
- MinIO endpoint/ak/sk 通过配置注入，不硬编码

## 不做的事

- ❌ SubjectManage.vue 封面 URL 输入改为上传（封面来自导入，不需要）
- ❌ 删除现有第三方封面链接（保持向前兼容）
- ❌ 头像迁移（当前无数据）
- ❌ MinIO 管理界面配置
