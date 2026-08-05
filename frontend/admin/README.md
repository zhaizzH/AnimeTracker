# AnimeTracker 管理端前端（admin）

> **预览版已就绪**：基于「极光白昼」浅色运营后台主题，已完成登录页与仪表盘的可交互预览。

管理端前端将用于番剧条目管理、用户管理与数据导入等运营操作，对应后端已在 `backend/business/admin`（Maven 模块 `animetracker-admin`）中提供完整 API。

## 后端能力（已就绪）

管理端 API 路径前缀为 `/api/admin/*`，主要包括：

- **用户管理**：查看 / 禁用 / 启用用户，管理用户角色。
- **番剧管理**：条目 CRUD（创建、编辑、下架），剧集与标签维护。
- **数据导入**：触发 / 查看 Bangumi 数据导入任务（详见 [`../../backend/data/importer/README.md`](../../backend/data/importer/README.md)）。

后端接口定义见 [`../../docs/backend.md`](../../docs/backend.md) 的「管理接口」章节；业务后端总览见 [`../../backend/business/README.md`](../../backend/business/README.md)。

## 建议技术栈

与用户端 `../client` 保持一致，推荐：

- React 18 + TypeScript + Vite
- Ant Design 5 + ProComponents（表格 / 表单 / 权限）
- React Router 7 + Zustand + React Query

## 待办

- [x] 初始化 Vite + React + TS 工程
- [x] 登录与权限（当前为演示模式，待接入 `/api/user/auth`）
- [ ] 番剧管理页（CRUD + 剧集 / 标签）
- [ ] 用户管理页
- [ ] 数据导入任务面板
