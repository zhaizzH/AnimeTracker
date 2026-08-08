# AnimeTracker 文档目录

本目录存放项目级文档、数据库脚本与 API 规范。

---

## 文件清单

| 文件 | 说明 |
|------|------|
| [`db-schema.sql`](db-schema.sql) | 数据库建表脚本（含 `operation_log` 等操作审计表） |
| [`openapi.yaml`](openapi.yaml) | OpenAPI 3.0 规范（完整接口定义） |

---

## 子目录

| 目录 | 说明 |
|------|------|
| `api/` | 第三方 API 文档工具（独立 Git 仓库，已被 `.gitignore` 忽略，不属于本项目源码） |
| `superpowers/` | 项目规划与设计文档（`plans/`、`specs/`） |

---

## 数据库

数据库名统一为 `anime_tracker`，建表脚本位于 `db-schema.sql`。核心表：

| 表 | 说明 |
|----|------|
| `user` | 用户信息、认证、角色与邮箱状态 |
| `subject` | 番剧条目（Bangumi ID、标题、封面、季度、评分等） |
| `episode` | 番剧剧集（集数、类型、播出状态、时长） |
| `subject_tag` | 番剧—标签关联 |
| `user_collection` | 用户收藏与观看进度 |
| `subject_relation` | 番剧间关联关系 |
| `import_record` | 数据导入批次记录 |
| `operation_log` | 操作审计日志（登录、条目增删改、角色变更、导入等） |

初始化：

```bash
mysql -u root -p
CREATE DATABASE anime_tracker DEFAULT CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
mysql -u root -p anime_tracker < docs/db-schema.sql
```

---

## 相关文档

- 项目总览：[`../README.md`](../README.md)
- 后端详解：[`../backend/README.md`](../backend/README.md)
- 前端总览：[`../frontend/README.md`](../frontend/README.md)
