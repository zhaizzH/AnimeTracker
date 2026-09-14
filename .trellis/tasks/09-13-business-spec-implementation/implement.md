# 实施清单

- [x] 1. 保存构建基线，激活任务和上下文。
- [x] 2. 迁移 infrastructure/auth/log；精简 common 并拆分常量。
- [x] 3. 调整 client/admin/agent/app 的公开调用、POM、配置与 Mapper 扫描。
- [ ] 4. DTO/VO 统一 pojo，Converter 按模块迁移，补齐全 Java Javadoc。
- [ ] 5. 运行针对性测试、Javadoc 检查与完整 mvn -B clean test，审查全部改动，更新规范状态与任务记录。

## 检查
- backend/business: mvn -B clean test。
- 架构测试：允许依赖矩阵，禁止 app 反向引用、业务内部 Mapper 跨模块访问、旧包残留。
- 静态：git diff --check、旧包名/重复类扫描、Javadoc 覆盖与语法校验。
- 本任务不修改前端/Python 功能，无对应代码变化时不重复全套前端/Python测试。

## 执行记录
- 用户最终规范与本任务范围一致，授权已具备；未新增产品决策。

- 已完成九模块职责迁移：新增 infrastructure、auth、log，将 agent 收敛为 Python 网关与 HTTP 适配，common 仅保留结果、分页和错误基础定义；HTTP 异常适配位于 app.web。
- 已完成 client/admin 职责隔离、pojo DTO/VO/Entity 统一、模块内 Converter 迁移，并移除 ServiceImpl 中的纯字段映射；Redis、限流、图片存储和邮件实现已并入 infrastructure。
- 此前声称 Javadoc 缺失 0 的检查不充分；本次复核确认仍有缺失和机械模板，R5 尚未验收。
- 完整回归：在 backend/business 执行 mvn -B clean test，10 个模块全部成功；测试总数 65，失败 0，错误 0，跳过 0（common、pojo、admin 无测试；infrastructure 8、auth 8、log 6、agent 3、client 25、app 15）。
- 架构边界、旧包引用和重复实现扫描已通过；规范文档状态已更新为当前实现状态。
- 最终质量验收未通过：Javadoc、专项测试和架构门禁仍有缺口，详见 review.md；当前分支未提交。

## 2026-09-14 复核验证

修复 AgentServiceImpl 文件末尾异常字符后重新执行 mvn -B clean test：2026-09-14 14:35:10 完成，耗时 80 秒，父项目及九个子模块成功，65 个测试通过，失败/错误/跳过均为 0。该结果不覆盖 review.md 中缺失的验收用例和 Javadoc 检查；任务保持未完成。
