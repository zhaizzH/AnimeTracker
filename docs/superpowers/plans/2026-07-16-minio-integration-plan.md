# MinIO 对象存储集成 — 实施计划

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 集成 MinIO 用于用户头像上传/存储，并将现有第三方封面图迁移到 MinIO

**Architecture:** MinIO Docker 本地运行，Spring Boot 后端通过 MinIO Java SDK 上传/管理文件，前端 Profile 页面改为文件选择器上传头像。封面由一次性 Python 迁移脚本处理。

**Tech Stack:** `io.minio:minio:8.5.7`, Spring Boot 3.2, Vue 3, Python 3.10+

## Global Constraints

- MinIO endpoint/ak/sk/bucket 通过 `application.yml` 配置，不硬编码
- 仅允许 `image/jpeg`、`image/png`、`image/webp` 三种格式
- 文件大小上限 5MB（`spring.servlet.multipart.max-file-size=5MB`）
- 存储路径: `avatars/{uuid}.{ext}` / `covers/{uuid}.{ext}`
- DB 字段 `user.avatar` / `subject.image` 类型不变（`VARCHAR(512)`），存的仍是 URL
- 所有异常经 `GlobalExceptionHandler` 统一处理

---

### Task 1: Backend MinIO 依赖 + 配置类

**Files:**
- Modify: `backend/business/pom.xml:35-36`
- Modify: `backend/business/common/pom.xml:73-79`
- Create: `backend/business/common/src/main/java/top/zhaizz/common/config/MinioProperties.java`
- Create: `backend/business/common/src/main/java/top/zhaizz/common/config/MinioConfig.java`

**Interfaces:**
- Consumes: 无
- Produces: `MinioClient` Bean（全局可用）、`MinioProperties`（可从任何 Spring Bean 注入）

- [ ] **Step 1: 父 POM 添加 minio 版本属性**

编辑 `backend/business/pom.xml`，在 `<properties>` 中添加：

```xml
<minio.version>8.5.7</minio.version>
```

插入到 `jjwt.version` 后面。

- [ ] **Step 2: 父 POM 添加 minio 依赖管理**

编辑 `backend/business/pom.xml`，在 `<dependencyManagement>` 中添加：

```xml
<!-- MinIO -->
<dependency>
    <groupId>io.minio</groupId>
    <artifactId>minio</artifactId>
    <version>${minio.version}</version>
</dependency>
```

插入到 Lombok 依赖后面。

- [ ] **Step 3: common 模块添加 minio 依赖**

编辑 `backend/business/common/pom.xml`，在 `</dependencies>` 前添加：

```xml
<dependency>
    <groupId>io.minio</groupId>
    <artifactId>minio</artifactId>
</dependency>
```

- [ ] **Step 4: 创建 MinioProperties.java**

创建 `backend/business/common/src/main/java/top/zhaizz/common/config/MinioProperties.java`：

```java
package top.zhaizz.common.config;

import lombok.Data;
import org.springframework.boot.context.properties.ConfigurationProperties;

@Data
@ConfigurationProperties(prefix = "minio")
public class MinioProperties {
    private String endpoint = "http://localhost:9000";
    private String accessKey;
    private String secretKey;
    private String bucket = "anime-tracker";
}
```

- [ ] **Step 5: 创建 MinioConfig.java**

创建 `backend/business/common/src/main/java/top/zhaizz/common/config/MinioConfig.java`：

```java
package top.zhaizz.common.config;

import io.minio.BucketExistsArgs;
import io.minio.MakeBucketArgs;
import io.minio.MinioClient;
import io.minio.SetBucketPolicyArgs;
import lombok.RequiredArgsConstructor;
import lombok.extern.slf4j.Slf4j;
import org.springframework.boot.context.properties.EnableConfigurationProperties;
import org.springframework.context.annotation.Bean;
import org.springframework.context.annotation.Configuration;

@Slf4j
@Configuration
@RequiredArgsConstructor
@EnableConfigurationProperties(MinioProperties.class)
public class MinioConfig {

    private final MinioProperties properties;

    @Bean
    public MinioClient minioClient() {
        return MinioClient.builder()
                .endpoint(properties.getEndpoint())
                .credentials(properties.getAccessKey(), properties.getSecretKey())
                .build();
    }

    @Bean
    public boolean initMinioBucket(MinioClient minioClient) {
        try {
            boolean exists = minioClient.bucketExists(
                    BucketExistsArgs.builder().bucket(properties.getBucket()).build());
            if (!exists) {
                minioClient.makeBucket(
                        MakeBucketArgs.builder().bucket(properties.getBucket()).build());

                // 设置公开读策略
                String policy = """
                {
                  "Version": "2012-10-17",
                  "Statement": [{
                    "Effect": "Allow",
                    "Principal": {"AWS": ["*"]},
                    "Action": ["s3:GetObject"],
                    "Resource": ["arn:aws:s3:::%s/*"]
                  }]
                }
                """.formatted(properties.getBucket());

                minioClient.setBucketPolicy(
                        SetBucketPolicyArgs.builder()
                                .bucket(properties.getBucket())
                                .config(policy)
                                .build());

                log.info("MinIO bucket '{}' created with public-read policy", properties.getBucket());
            } else {
                log.info("MinIO bucket '{}' already exists", properties.getBucket());
            }
            return true;
        } catch (Exception e) {
            log.warn("MinIO bucket init skipped (MinIO may not be running yet): {}", e.getMessage());
            return false;
        }
    }
}
```

- [ ] **Step 6: Commit**

```bash
git add backend/business/pom.xml backend/business/common/pom.xml \
  backend/business/common/src/main/java/top/zhaizz/common/config/MinioProperties.java \
  backend/business/common/src/main/java/top/zhaizz/common/config/MinioConfig.java
git commit -m "feat: add MinIO dependency and configuration"
```

---

### Task 2: Backend FileController + 安全配置 + 应用配置

**Files:**
- Create: `backend/business/common/src/main/java/top/zhaizz/common/controller/FileController.java`
- Modify: `backend/business/common/src/main/java/top/zhaizz/common/config/SecurityConfig.java:44-47`
- Modify: `backend/business/app/src/main/resources/application.yml:56-59`
- Modify: `backend/business/app/src/main/resources/application-local.yml:30-34`

**Interfaces:**
- Consumes: `MinioClient`, `MinioProperties` (from Task 1)
- Produces: `POST /api/common/files/upload?type=avatar|cover` 上传端点
- Response: `{"code":200,"message":"success","data":"http://localhost:9000/anime-tracker/avatars/uuid.jpg"}`

- [ ] **Step 1: 创建 FileController.java**

创建 `backend/business/common/src/main/java/top/zhaizz/common/controller/FileController.java`：

```java
package top.zhaizz.common.controller;

import io.minio.MinioClient;
import io.minio.PutObjectArgs;
import lombok.RequiredArgsConstructor;
import lombok.extern.slf4j.Slf4j;
import org.springframework.web.bind.annotation.*;
import org.springframework.web.multipart.MultipartFile;
import top.zhaizz.common.config.MinioProperties;
import top.zhaizz.common.result.Result;

import java.util.List;
import java.util.UUID;

@Slf4j
@RestController
@RequestMapping("/api/common/files")
@RequiredArgsConstructor
public class FileController {

    private final MinioClient minioClient;
    private final MinioProperties minioProperties;

    private static final List<String> ALLOWED_CONTENT_TYPES = List.of("image/jpeg", "image/png", "image/webp");
    private static final List<String> ALLOWED_CATEGORIES = List.of("avatar", "cover");

    @PostMapping("/upload")
    public Result<String> upload(
            @RequestParam("file") MultipartFile file,
            @RequestParam(defaultValue = "avatar") String type) {

        // 校验分类
        if (!ALLOWED_CATEGORIES.contains(type)) {
            return Result.error(400, "无效的上传分类: " + type);
        }

        // 校验文件类型
        String contentType = file.getContentType();
        if (contentType == null || !ALLOWED_CONTENT_TYPES.contains(contentType)) {
            return Result.error(400, "仅支持 JPG/PNG/WebP 格式的图片");
        }

        // 推断扩展名
        String ext = switch (contentType) {
            case "image/jpeg" -> "jpg";
            case "image/png" -> "png";
            case "image/webp" -> "webp";
            default -> throw new IllegalStateException("Unexpected content type: " + contentType);
        };

        // 生成对象路径
        String dir = type + "s"; // avatar → avatars, cover → covers
        String objectName = dir + "/" + UUID.randomUUID() + "." + ext;

        try {
            minioClient.putObject(PutObjectArgs.builder()
                    .bucket(minioProperties.getBucket())
                    .object(objectName)
                    .stream(file.getInputStream(), file.getSize(), -1)
                    .contentType(contentType)
                    .build());

            String url = minioProperties.getEndpoint() + "/"
                    + minioProperties.getBucket() + "/"
                    + objectName;

            log.info("File uploaded: {}", url);
            return Result.success(url);
        } catch (Exception e) {
            log.error("MinIO upload failed", e);
            return Result.error(500, "文件上传失败: " + e.getMessage());
        }
    }
}
```

- [ ] **Step 2: SecurityConfig 添加上传接口白名单**

编辑 `backend/business/common/src/main/java/top/zhaizz/common/config/SecurityConfig.java`，在 `.requestMatchers("/api/user/**").authenticated()` **之后**添加一行：

```java
// 文件上传：需认证
.requestMatchers("/api/common/files/**").authenticated()
```

- [ ] **Step 3: application.yml 添加 multipart 和 minio 配置**

编辑 `backend/business/app/src/main/resources/application.yml`，在 `# JWT 配置` 块之前添加：

```yaml
# 文件上传
spring:
  servlet:
    multipart:
      max-file-size: 5MB
      max-request-size: 10MB

# MinIO 对象存储
minio:
  endpoint: ${minio.endpoint:http://localhost:9000}
  access-key: ${minio.access-key}
  secret-key: ${minio.secret-key}
  bucket: ${minio.bucket:anime-tracker}
```

- [ ] **Step 4: application-local.yml 添加本地 MinIO 配置**

编辑 `backend/business/app/src/main/resources/application-local.yml`，在文件末尾添加：

```yaml
# MinIO 对象存储
minio:
  endpoint: http://localhost:9000
  access-key: minioadmin
  secret-key: minioadmin
  bucket: anime-tracker
```

- [ ] **Step 5: Commit**

```bash
git add -A
git commit -m "feat: add file upload endpoint and MinIO config"
```

---

### Task 3: 启动 MinIO Docker 并验证后端编译

**Files:** 无代码改动

- [ ] **Step 1: 启动 MinIO Docker 容器**

```bash
docker run -d --name minio \
  -p 9000:9000 -p 9001:9001 \
  -e MINIO_ROOT_USER=minioadmin \
  -e MINIO_ROOT_PASSWORD=minioadmin \
  -v minio-data:/data \
  minio/minio server /data --console-address ":9001"
```

- [ ] **Step 2: 编译后端验证依赖正确**

```bash
cd backend/business
mvn compile -q
```

预期输出: `BUILD SUCCESS`，无错误。

- [ ] **Step 3: Commit**

```bash
git commit --allow-empty -m "chore: start MinIO Docker for local development"
```

---

### Task 4: 前端上传 API + 类型定义

**Files:**
- Create: `frontend/client/src/api/upload.ts`
- Modify: `frontend/client/src/types/index.ts:155-160`

**Interfaces:**
- Consumes: 后端 `POST /api/common/files/upload` (from Task 2)
- Produces: `uploadFile(file, type): Promise<string>` — 上传文件并返回 MinIO URL

- [ ] **Step 1: types/index.ts 添加 UploadResult**

编辑 `frontend/client/src/types/index.ts`，在 `WEEKDAYS` 定义之前添加：

```typescript
/** MinIO 上传返回结果 */
export interface UploadResult {
  url: string
}
```

- [ ] **Step 2: 创建 api/upload.ts**

创建 `frontend/client/src/api/upload.ts`：

```typescript
import http from './http'
import type { ApiResponse } from '@/types'

/**
 * 上传文件到 MinIO
 * @param file 图片文件 (jpg/png/webp)
 * @param type 上传分类: avatar | cover
 * @returns MinIO 可访问 URL
 */
export async function uploadFile(file: File, type: 'avatar' | 'cover' = 'avatar'): Promise<string> {
  const formData = new FormData()
  formData.append('file', file)
  formData.append('type', type)

  const res = await http.post<ApiResponse<string>>('/api/common/files/upload', formData, {
    headers: { 'Content-Type': 'multipart/form-data' },
  })

  return res.data.data
}
```

- [ ] **Step 3: Commit**

```bash
git add frontend/client/src/api/upload.ts frontend/client/src/types/index.ts
git commit -m "feat: add file upload API and types"
```

---

### Task 5: Profile.vue 头像上传

**Files:**
- Modify: `frontend/client/src/pages/Profile.vue` (多处改动)

**Interfaces:**
- Consumes: `uploadFile(file, type)` (from Task 4)
- Produces: 可用的头像上传 UI

- [ ] **Step 1: 改写 Profile.vue script 部分**

编辑 `frontend/client/src/pages/Profile.vue`，完整替换 `<script setup>` 部分：

```vue
<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
import { User, Mail, Image, Save, Shield, Calendar, CheckCircle, XCircle, Upload } from '@lucide/vue'
import { useAuthStore } from '@/stores/auth'
import { uploadFile } from '@/api/upload'

const authStore = useAuthStore()

const nickname = ref('')
const email = ref('')
const avatar = ref('')
const loading = ref(false)
const uploading = ref(false)
const success = ref('')
const error = ref('')

function initForm() {
  if (authStore.user) {
    nickname.value = authStore.user.nickname || ''
    email.value = authStore.user.email || ''
    avatar.value = authStore.user.avatar || ''
  }
}

async function handleFileSelected(event: Event) {
  const input = event.target as HTMLInputElement
  const file = input.files?.[0]
  if (!file) return

  // 校验文件类型
  const allowed = ['image/jpeg', 'image/png', 'image/webp']
  if (!allowed.includes(file.type)) {
    error.value = '仅支持 JPG、PNG、WebP 格式'
    setTimeout(() => { error.value = '' }, 5000)
    return
  }

  // 校验文件大小 (5MB)
  if (file.size > 5 * 1024 * 1024) {
    error.value = '图片大小不能超过 5MB'
    setTimeout(() => { error.value = '' }, 5000)
    return
  }

  uploading.value = true
  error.value = ''
  try {
    const url = await uploadFile(file, 'avatar')
    avatar.value = url
  } catch (e: any) {
    error.value = e?.response?.data?.message || '上传失败，请重试'
    setTimeout(() => { error.value = '' }, 5000)
  } finally {
    uploading.value = false
    // 清空 input 以便再次选择相同文件
    input.value = ''
  }
}

async function handleSave() {
  success.value = ''
  error.value = ''
  loading.value = true
  try {
    await authStore.updateProfile({
      nickname: nickname.value.trim() || undefined,
      email: email.value.trim() || undefined,
      avatar: avatar.value.trim() || undefined,
    })
    success.value = '个人资料已更新'
    setTimeout(() => { success.value = '' }, 3000)
  } catch (e: any) {
    error.value = e?.response?.data?.message || '更新失败，请稍后重试'
    setTimeout(() => { error.value = '' }, 5000)
  } finally {
    loading.value = false
  }
}

onMounted(async () => {
  if (!authStore.user) {
    await authStore.fetchMe()
  }
  initForm()
})

const memberSince = computed(() => {
  if (!authStore.user?.createdAt) return ''
  try {
    return new Date(authStore.user.createdAt).toLocaleDateString('zh-CN', {
      year: 'numeric',
      month: 'long',
      day: 'numeric',
    })
  } catch {
    return authStore.user.createdAt
  }
})
</script>
```

- [ ] **Step 2: 替换 Avatar URL 输入为文件上传**

编辑 `frontend/client/src/pages/Profile.vue`，找到“头像 URL”部分（约第155-174行），替换为：

```vue
        <!-- 头像上传 -->
        <div>
          <label class="block text-sm font-medium mb-1.5" style="color: var(--color-text)">头像</label>
          <div class="flex items-center gap-4">
            <div
              class="w-16 h-16 rounded-2xl overflow-hidden flex items-center justify-center shrink-0 border-2 border-dashed"
              :style="{ borderColor: 'var(--color-border)', background: 'var(--color-hover)' }"
            >
              <img
                v-if="avatar"
                :src="avatar"
                alt="Avatar Preview"
                class="w-full h-full object-cover"
              />
              <User v-else class="h-6 w-6 opacity-30" style="color: var(--color-text-secondary)" />
            </div>
            <div class="flex-1">
              <label class="btn-secondary cursor-pointer inline-flex items-center gap-2" :class="{ 'opacity-50 pointer-events-none': uploading }">
                <Upload v-if="!uploading" class="h-4 w-4" />
                <svg v-else class="animate-spin h-4 w-4" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24">
                  <circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4" />
                  <path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4z" />
                </svg>
                {{ uploading ? '上传中...' : '选择图片' }}
                <input
                  type="file"
                  accept="image/jpeg,image/png,image/webp"
                  class="hidden"
                  @change="handleFileSelected"
                />
              </label>
              <p class="text-xs mt-1.5" style="color: var(--color-text-secondary)">支持 JPG/PNG/WebP，最大 5MB</p>
            </div>
          </div>
        </div>
```

- [ ] **Step 3: 验证编译**

```bash
cd frontend/client && npx vue-tsc --noEmit
```

预期输出: 无类型错误。

- [ ] **Step 4: Commit**

```bash
git add frontend/client/src/pages/Profile.vue
git commit -m "feat: replace avatar URL input with file upload"
```

---

### Task 6: 封面图片迁移脚本

**Files:**
- Create: `backend/data/migration/migrate_covers.py`

**Interfaces:**
- 独立 Python 脚本，不依赖 Spring，通过配置连接 MySQL 和 MinIO

- [ ] **Step 1: 创建迁移脚本**

创建 `backend/data/migration/migrate_covers.py`：

```python
"""
封面图片迁移脚本

从第三方 CDN 下载现有番剧封面，上传到 MinIO，更新 DB。
可重复执行：已指向 MinIO 的链接自动跳过。

用法:
    pip install minio requests sqlalchemy pymysql python-dotenv
    cp .env.example .env  # 编辑配置
    python migrate_covers.py
"""

import os
import uuid
import logging
from urllib.parse import urlparse

import requests
from dotenv import load_dotenv
from minio import Minio
from sqlalchemy import create_engine, text

load_dotenv()

# ---------- 配置 ----------
DB_URL = os.getenv("DB_URL", "mysql+pymysql://root:password@localhost:3306/anime_tracker")
MINIO_ENDPOINT = os.getenv("MINIO_ENDPOINT", "localhost:9000")
MINIO_ACCESS_KEY = os.getenv("MINIO_ACCESS_KEY", "minioadmin")
MINIO_SECRET_KEY = os.getenv("MINIO_SECRET_KEY", "minioadmin")
MINIO_BUCKET = os.getenv("MINIO_BUCKET", "anime-tracker")
MINIO_PUBLIC_URL = os.getenv("MINIO_PUBLIC_URL", "http://localhost:9000")
DOWNLOAD_TIMEOUT = 15
# -------------------------

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
log = logging.getLogger(__name__)

# content-type → 扩展名映射
EXT_MAP = {
    "image/jpeg": "jpg",
    "image/png": "png",
    "image/webp": "webp",
}


def get_ext_from_url(url: str) -> str | None:
    """从 URL 路径推断扩展名"""
    path = urlparse(url).path.lower()
    for ext in [".jpg", ".jpeg", ".png", ".webp"]:
        if path.endswith(ext):
            return ext.lstrip(".")
    return None


def main():
    # 连接 MinIO
    minio_client = Minio(
        MINIO_ENDPOINT,
        access_key=MINIO_ACCESS_KEY,
        secret_key=MINIO_SECRET_KEY,
        secure=False,
    )
    if not minio_client.bucket_exists(MINIO_BUCKET):
        minio_client.make_bucket(MINIO_BUCKET)
        log.info("Bucket '%s' created", MINIO_BUCKET)

    # 连接 MySQL
    engine = create_engine(DB_URL, pool_pre_ping=True)
    minio_prefix = MINIO_PUBLIC_URL.rstrip("/")

    with engine.connect() as conn:
        # 找出所有非 MinIO 的封面
        rows = conn.execute(
            text("SELECT id, image FROM subject WHERE image IS NOT NULL AND image != ''")
        ).fetchall()

    total = len(rows)
    success = 0
    skipped = 0
    failed = 0

    log.info("Found %d subjects with cover images", total)

    for row in rows:
        subject_id, image_url = row

        # 跳过已迁移的
        if image_url.startswith(minio_prefix):
            skipped += 1
            continue

        try:
            # 下载
            resp = requests.get(image_url, timeout=DOWNLOAD_TIMEOUT, stream=True)
            resp.raise_for_status()

            content_type = resp.headers.get("Content-Type", "")
            ext = EXT_MAP.get(content_type) or get_ext_from_url(image_url) or "jpg"

            object_name = f"covers/{subject_id}.{ext}"

            # 上传到 MinIO
            result = minio_client.put_object(
                MINIO_BUCKET,
                object_name,
                resp.raw,
                length=int(resp.headers.get("Content-Length", 0)),
                content_type=content_type or "image/jpeg",
            )

            minio_url = f"{minio_prefix}/{MINIO_BUCKET}/{object_name}"

            # 更新 DB
            with engine.begin() as conn:
                conn.execute(
                    text("UPDATE subject SET image = :url WHERE id = :id"),
                    {"url": minio_url, "id": subject_id},
                )

            success += 1
            if success % 100 == 0:
                log.info("Progress: %d/%d", success, total)

        except Exception as e:
            log.warning("Failed to migrate subject %d (%s): %s", subject_id, image_url[:60], e)
            failed += 1

    log.info("Done! total=%d, success=%d, skipped=%d, failed=%d", total, success, skipped, failed)


if __name__ == "__main__":
    main()
```

- [ ] **Step 2: 创建 .env.example**

创建 `backend/data/migration/.env.example`：

```bash
DB_URL=mysql+pymysql://root:password@localhost:3306/anime_tracker
MINIO_ENDPOINT=localhost:9000
MINIO_ACCESS_KEY=minioadmin
MINIO_SECRET_KEY=minioadmin
MINIO_BUCKET=anime-tracker
MINIO_PUBLIC_URL=http://localhost:9000
```

- [ ] **Step 3: 创建 requirements.txt**

创建 `backend/data/migration/requirements.txt`：

```
minio>=7.2.0
requests>=2.31.0
sqlalchemy>=2.0.0
pymysql>=1.1.0
python-dotenv>=1.0.0
```

- [ ] **Step 4: Commit**

```bash
git add backend/data/migration/
git commit -m "feat: add cover image migration script to MinIO"
```
