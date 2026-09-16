# 执行计划

## Phase 1：事实核对

- [x] 阅读 Backend 索引、目录、异常、质量和跨层文档，列出旧表述
- [x] 对照业务模块 POM、`ArchitectureBoundaryTest`、源码目录、配置资源与 CI
- [x] 标记每个结论为当前实现、目标规则或历史证据

## Phase 2：文档合并与修正

- [x] 更新 Backend 索引的主题入口、当前范围和验证入口
- [x] 更新目录结构文档的九模块职责、依赖矩阵、Converter/POJO 归属、资源文件与边界测试说明
- [x] 更新异常文档的 `common` 基础定义与 `app` HTTP 适配边界
- [x] 更新质量文档的当前验证命令、Javadoc 注释规则与历史基线标记
- [x] 更新跨层指南中与当前实现、历史迁移和文档合并状态有关的表述

## Phase 3：验证与交付

- [x] 执行 Trellis 任务校验和规范索引/链接/占位文本检查
- [x] 执行必要的 Backend 质量命令，记录真实结果
- [x] 运行 `git diff --check`，复查历史内容是否仍被清楚标识
- [ ] 更新任务状态、提交文档变更并按 Trellis 流程归档

## 本轮验证记录（2026-09-16）

- `mvn -B test -f backend/business/pom.xml`：95 个测试通过，0 失败，0 错误
- `python backend/business/tools/check_javadoc.py`：255 个文件、1658 个声明、0 个违规
- `python backend/business/tools/test_check_javadoc.py`：7 项通过
- Trellis 上下文校验、Markdown 相对链接检查、占位文本扫描和 `git diff --check`：通过
