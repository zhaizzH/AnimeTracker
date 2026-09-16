# 技术设计

## 现状判断

当前 Backend 已形成 `common`、`pojo`、`infrastructure`、`auth`、`log`、`agent`、`client`、`admin`、`app` 九个业务模块。`ArchitectureBoundaryTest` 同时约束模块依赖矩阵、内部实现包可见性和 `common` 的基础定义范围。现有规范已经记录过模块拆分和注释约定，但部分章节仍把迁移前结构、目标设计或旧资源列表写成当前事实

本次以以下顺序判断事实：实现代码与测试 > 模块 POM 与运行配置 > CI 配置 > 现有规范中的历史记录。无法由当前实现证明的内容保留为历史或待验证说明，不写成现行强制规则

## 文档调整策略

1. 在现有同主题文档内修正当前总览、依赖矩阵、职责边界、异常适配、配置资源和质量门禁
2. 在每个仍有价值的迁移记录前加历史/迁移前标记，并补充当前实现指向
3. 用源码路径、测试类、POM 或配置文件作为证据链接或路径引用
4. 不拆出新的模块文档；只有当既有主题无法容纳事实时才保留独立文件
5. 用 Backend 索引维护主题入口，跨层规则继续放在 `guides/cross-layer-thinking-guide.md`

## 预期文件

- `.trellis/spec/backend/index.md`
- `.trellis/spec/backend/directory-structure.md`
- `.trellis/spec/backend/error-handling.md`
- `.trellis/spec/backend/quality-guidelines.md`
- `.trellis/spec/guides/cross-layer-thinking-guide.md`

如核对发现其他 Backend 文档存在同一类明确过时事实，仅做最小修正，不扩展为业务代码重构

## 验证策略

- 重新核对模块 POM、`ArchitectureBoundaryTest`、资源目录、CI 和规范内路径
- 运行 Trellis 任务校验、Markdown 相对链接检查、占位文本扫描和 `git diff --check`
- 若更新了当前测试基线，再运行 Backend Java/Python 质量命令并记录日期与结果；不凭历史数字推断当前结果
