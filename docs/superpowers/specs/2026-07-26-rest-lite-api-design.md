# REST-lite API 设计规范

## 背景

后端接口设计不再严格遵循 RESTful 风格，改为 "REST-lite" 方案——查询保留 GET，所有写操作统一使用 POST + URL 动词。目的是简化设计决策，不再纠结 PUT/PATCH/DELETE 的语义选择。

## 原则

| HTTP 方法 | 用途 | 说明 |
|-----------|------|------|
| GET | 纯查询 | 保留幂等、可缓存特性 |
| POST | 所有写操作 | 增/改/删统一 POST，URL 后缀标识动作 |

## 接口变更清单

### 认证模块 `/api/user/auth` — 零改动

全部已是 POST，保持现状：
- `POST /register` — 注册
- `POST /login` — 登录
- `POST /refresh` — 刷新 Token
- `POST /logout` — 退出
- `POST /verify-email` — 验证邮箱
- `POST /resend-code` — 重发验证码
- `POST /forgot-password` — 发送重置码
- `POST /reset-password` — 重置密码

### 番剧模块 `/api/user/subjects` — 零改动

全部是 GET 查询：
- `GET` — 分页列表
- `GET /search` — 搜索
- `GET /season` — 按季度
- `GET /schedule` — 每周放送
- `GET /{id}` — 详情
- `GET /{id}/episodes` — 剧集列表

### 收藏模块 `/api/user/collections`

| 原 | 改 |
|---|----|
| `GET` | 不动 |
| `GET /schedule` | 不动 |
| `GET /{subjectId}` | 不动 |
| **`PUT /{subjectId}`** | **`POST /{subjectId}/save`** |
| **`DELETE /{subjectId}`** | **`POST /{subjectId}/remove`** |
| **`PUT /{subjectId}/ep-status`** | **`POST /{subjectId}/ep-status`** |

### 用户模块 `/api/user/me`

| 原 | 改 |
|---|----|
| `GET` | 不动 |
| **`PUT`** | **`POST /update`** |
| **`PUT /password`** | **`POST /update-password`** |
| `POST /send-email-code` | 不动 |
| `POST /verify-email-code` | 不动 |

### 标签模块 `/api/user/tags` — 零改动

- `GET` — 标签列表
- `GET /{tag}/subjects` — 标签下番剧

### 管理番剧 `/api/admin/subjects`

| 原 | 改 |
|---|----|
| `POST` | 不动（创建） |
| **`PUT /{id}`** | **`POST /{id}/update`** |
| **`DELETE /{id}`** | **`POST /{id}/remove`** |

### 管理用户 `/api/admin/users`

| 原 | 改 |
|---|----|
| `GET` | 不动 |
| **`PUT /{id}/role`** | **`POST /{id}/update-role`** |

### 导入模块 `/api/admin/import` — 零改动

- `POST /run` — 触发导入
- `GET /status` — 查询状态

### 文件模块 `/api/common/files` — 零改动

- `POST /upload` — 上传

## 前端配合

1. 所有写请求改为 `POST`，`Content-Type: application/json`（或 `multipart/form-data` 用于上传）
2. URL 路径按上表更新
3. 查询请求保持 `GET` + Query Parameters

## 注意事项

- 保留的 GET 查询若参数复杂（多层嵌套/数组），保持使用 Query Parameters，不做 POST 化
- 后续新增接口一律遵循此规范
