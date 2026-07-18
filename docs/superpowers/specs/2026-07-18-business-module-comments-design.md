---
title: Business 模块类级注释补全
date: 2026-07-18
status: draft
---

## 范围

为 `backend/business/` 中缺少类级 Javadoc 的 7 个文件补充 1-3 行中文类注释，说明类的职责。已有注释的文件不动。

## 文件清单

| 文件 | 拟补充注释 |
|------|-----------|
| `MinioProperties.java` | MinIO 对象存储配置属性 |
| `MinioConfig.java` | MinIO 客户端 Bean 配置与自动初始化 |
| `UserService.java` | 用户服务接口 |
| `SubjectService.java` | 番剧服务接口 |
| `TagService.java` | 标签服务接口 |
| `EpisodeService.java` | 剧集服务接口 |
| `ImportService.java` | 数据导入服务接口 |

## 风格

- `/** 一行说明 */` 或 `/** <p>多行</p> */`
- 中文
- 纯职责说明，不含参数/返回值细节（类级注释不需要）
