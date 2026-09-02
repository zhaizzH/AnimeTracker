# 全量完善README.md

## Goal

全面完善项目根目录 `README.md`，使其成为结构严谨、内容准确完整、对齐当前工程现状、具备高质量中英文双语或纯正技术中文的高水准项目主文档。

## Requirements

1. **项目定位与核心价值阐述清晰**：
   - 介绍 AnimeTracker 的系统架构与核心定位（面向真实数据的 LangGraph Agent + Spring Boot + React 双端番剧追踪系统）。
   - 阐明核心亮点：「预览 → 用户确认 → 执行」的安全写机制、SSE 流式交互、Bangumi 数据管道、RAG 混合检索等。

2. **系统架构与交互时序图完备**：
   - 提供直观的端到端调用时序图与系统整体架构拓扑图（Mermaid 格式），准确反映 client/admin、Spring Boot 业务服务与 Agent 微服务之间的边界。

3. **技术栈与模块目录索引全覆盖**：
   - 完整列出前端（React 18 / Vite / Antd / TanStack Query / Zustand / React Router 7 / ECharts）、后端（Java 21 / Spring Boot 3.2 / MyBatis-Plus / JJWT）、AI Agent（Python 3.10+ / FastAPI / LangGraph / LangChain / uv）及数据设施（MySQL 8 / Redis / MinIO / Bangumi API）的技术选型。
   - 准确更新完整的目录结构树，覆盖 `frontend/`、`backend/`、`docs/` 及 CI 等核心位置。

4. **开箱即用的环境准备与本地快速启动指南**：
   - 详细列出前置环境要求（Node.js, JDK 21+, Maven 3.9+, Python 3.10+, uv, MySQL, Redis, MinIO, LLM API Key）。
   - 给出清晰、准确、按顺序执行的本地初始化步骤（创建数据库与初始化表、启动 Business、启动 Agent、启动用户端/管理端、导入初始数据）。
   - 提供核心 API / Agent 调用验证与自检命令。

5. **功能清单与运维常见问题（FAQ）全面细致**：
   - 分模块（用户端、管理端、业务后端、AI Agent、数据抓取与索引）罗列核心功能。
   - 补充常见的环境踩坑、配置项映射（如 JWT 密钥一致性、Cookie Secure 属性、LLM 报错、跨域等）与常见排错方案。
   - 提供统一的 Git 提交信息规范与文档导航链接。

## Acceptance Criteria

- [x] 根目录 `README.md` 包含：项目简介与定位、核心亮点、系统架构图与核心时序图、功能清单、技术栈、目录结构、前置依赖、分步快速启动、数据导入指南、API 验证方式、常见问题 FAQ、提交规范、子模块文档链接等完整板块。
- [x] 所有代码路径、端口号（5173/5174/8080/8090）、依赖版本（Java 21, Python 3.10+, Node 22, Spring Boot 3.2.0）与现有代码库完全保持一致，无死链与虚假配置。
- [x] 文档排版规范优雅，格式统一，层级分明。

## Notes

- 保持真实准确，不引入代码库中不存在的虚构文件（如不存在的 docker-compose.prod.yml 或空无一物的未存在目录）。
