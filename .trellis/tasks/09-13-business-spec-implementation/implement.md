# 实施清单

- [x] 1. 保存构建基线，激活任务和上下文。
- [x] 2. 迁移 infrastructure/auth/log；精简 common 并拆分常量。
- [x] 3. 调整 client/admin/agent/app 的公开调用、POM、配置与 Mapper 扫描。
- [x] 4. DTO/VO 统一 pojo，Converter 按模块迁移，补齐全 Java Javadoc。
- [x] 5. 运行针对性测试、Javadoc 检查与完整 mvn -B clean test，审查全部改动，更新规范状态与任务记录。

## 检查
- backend/business: mvn -B clean test。
- 架构测试：允许依赖矩阵，禁止 app 反向引用、业务内部 Mapper 跨模块访问、旧包残留。
- 静态：git diff --check、旧包名/重复类扫描、Javadoc 覆盖与语法校验。
- 本任务不修改前端/Python 功能，无对应代码变化时不重复全套前端/Python测试。

## 历史执行记录（以文末最终验收为准）
- 用户最终规范与本任务范围一致，授权已具备；未新增产品决策。

- 已完成九模块职责迁移：新增 infrastructure、auth、log，将 agent 收敛为 Python 网关与 HTTP 适配，common 仅保留结果、分页和错误基础定义；HTTP 异常适配位于 app.web。
- 已完成 client/admin 职责隔离、pojo DTO/VO/Entity 统一、模块内 Converter 迁移，并移除 ServiceImpl 中的纯字段映射；Redis、限流、图片存储和邮件实现已并入 infrastructure。
- 此前声称 Javadoc 缺失 0 的检查不充分；本次复核确认仍有缺失和机械模板，R5 尚未验收。
- 完整回归：在 backend/business 执行 mvn -B clean test，10 个模块全部成功；测试总数 65，失败 0，错误 0，跳过 0（common、pojo、admin 无测试；infrastructure 8、auth 8、log 6、agent 3、client 25、app 15）。
- 架构边界、旧包引用和重复实现扫描已通过；规范文档状态已更新为当前实现状态。
- 最终质量验收未通过：Javadoc、专项测试和架构门禁仍有缺口，详见 review.md；当前分支未提交。

## 2026-09-14 复核验证

修复 AgentServiceImpl 文件末尾异常字符后重新执行 mvn -B clean test：2026-09-14 14:35:10 完成，耗时 80 秒，父项目及九个子模块成功，65 个测试通过，失败/错误/跳过均为 0。该结果不覆盖 review.md 中缺失的验收用例和 Javadoc 检查；任务保持未完成。

## 2026-09-14 最终修复验收

- Javadoc 已按实际行为修正：补齐手写声明、参数/返回标签、枚举与 record 组件；替换机械模板，纠正 Converter 引用/空值、预览错误、会话和配置等语义。自动声明检查不替代人工语义审查。
- 新增导入网关、client/admin Converter、登录/刷新/注销编排测试；架构门禁覆盖九模块允许矩阵、内部 Mapper/服务实现/供应商适配器隔离、common 精简，并用故意违规夹具验证规则确实拒绝非法边。
- 导入网关成功/网络失败日志改为固定事件；捕获日志测试断言不含请求参数、URL、凭据或原始网络异常。修复标点批处理误插入 CorsConfig/SecurityConfig 代码的中文句号，保留原有路由与安全逻辑。
- 完整回归命令：mvn -B clean test -f backend/business/pom.xml；2026-09-14 21:28:04 完成，40.158 秒，父项目和九模块全部成功；95 tests，0 failures，0 errors，0 skipped。
- 文档命令：python backend/business/tools/check_javadoc.py；255 文件、1658 声明、0 违规，JDK doclint 退出 0。检查器命令：python backend/business/tools/test_check_javadoc.py；6 个正反例测试通过。输出在 backend/business/target/javadoc-check，任务内 txt 保存最终摘要。
- 真实外部服务联调不在上述单元/配置回归证明范围内。已满足本任务约定的修复验收，当前待提交剩余修复与工具；任务状态保留 in_progress，提交及归档按 Trellis 流程执行。
