# 全量完善 README.md 技术设计

## 1. 整体目标与结构规划

将根目录 `README.md` 打造为一份工业级、清晰详实且与当前代码库 100% 真实对齐的项目主说明文档。

目录结构规划：
1. **项目标题与定位 (Header & Positioning)**
   - 项目名称与徽标/简介
   - 一句话定位与解决的核心痛点
2. **核心特性与设计亮点 (Key Features & Highlights)**
   - 真实数据驱动的 LangGraph 多 Agent 协同与领域路由
   - 「预览 → 确认 → 执行」安全写入机制（Redis 暂存态）
   - SSE 全链路流式响应（含思考过程、工具调用状态）
   - 完备的 Bangumi 数据同步与断点续传机制 + RAG 语义索引
   - 生产级安全鉴权（短 AccessToken + HttpOnly Cookie 轮换刷新）
3. **系统架构与交互设计 (Architecture & Workflows)**
   - 端到端交互时序图 (Mermaid Sequence)
   - 系统组件拓扑图 (Mermaid Flowchart)
4. **功能矩阵 (Feature Matrix)**
   - 用户端 (Client Web)
   - 管理端 (Admin Web)
   - 业务后端 (Business Service)
   - 智能体服务 (Agent Service)
   - 离线任务 (Data Importer / Indexer / Scheduler)
5. **技术栈一览 (Tech Stack)**
   - 前端、管理端图表、业务后端、AI Agent、数据存储、工程交付
6. **目录结构 (Directory Structure)**
   - 根目录、`frontend/`、`backend/`、`docs/`
7. **环境要求与前置依赖 (Prerequisites)**
   - 各种运行环境及最低版本
8. **快速开始与启动步骤 (Getting Started)**
   - 1. 数据库初始化 (MySQL 8 + db-schema.sql)
   - 2. 启动业务后端 (Spring Boot :8080)
   - 3. 启动 AI Agent (FastAPI :8090)
   - 4. 启动前端应用 (Client :5173 / Admin :5174)
   - 5. 导入首批数据 (CLI / Season / Sample)
9. **接口与连通性验证 (Verification & Health Check)**
   - Health Check
   - 示例 API 请求
10. **常见问题与排障指南 (Troubleshooting & FAQ)**
    - 认证与 Cookie 问题
    - LLM Provider 配置与 Extra Inputs 报错
    - MinIO 桶名约束
    - 数据导入单实例锁与 PID 问题
11. **项目规范与参与指南 (Conventions & Submodules)**
    - Git 提交规范
    - 子模块文档导航
