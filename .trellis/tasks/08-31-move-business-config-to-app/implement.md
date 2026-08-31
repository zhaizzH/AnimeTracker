# 实施计划：Business 配置集中到 App

## 1. 建立迁移前行为护栏

- [x] 在 app 测试目录新增 `AppConfigurationBindingTest`，锁定配置绑定、Bean 唯一性和 CORS 内容。
- [x] 新增 `SecurityConfigAuthorizationTest`，锁定匿名、USER、ADMIN、默认拒绝和 401/403 JSON。
- [x] 新增 `CookieOriginFilterTest`，锁定 refresh/logout Origin fail-closed 行为。
- [x] 新增 `AgentConfigTest`，锁定普通超时、Trace Header 与 SSE 无读超时。
- [x] 新增 `ArchitectureBoundaryTest`，锁定下层包不得依赖 app。
- [x] 运行 `mvn -B clean test`，确保测试能保护迁移前行为。

建议第一批提交：`test(app): 锁定配置迁移前行为`。

## 2. 迁移配置与显式装配

- [x] 将六个配置类移动到 `app/src/main/java/top/zhaizz/app/config` 并更新 package/import。
- [x] 将 `RestTemplateConfig` 重命名为 `AgentConfig`。
- [x] 在 `AgentConfig` 显式创建 `AgentService`；保持普通与 SSE 超时、Trace Header 行为。
- [x] 修改 `AgentServiceImpl`：移除组件注解和 Properties 依赖，增加显式构造器及普通字段。
- [x] 在 `CorsConfig` 显式创建 `CookieOriginFilter`。
- [x] 修改 `CookieOriginFilter`：移除组件注解和 Properties 依赖，显式接收白名单集合。
- [x] 更新 `HttpImportAgentGateway` 等所有配置 import。
- [x] 在 `app/pom.xml` 显式声明 Web 与 Security 直接依赖。
- [x] 更新第一阶段测试的 import/装配入口，保持断言语义不变。
- [x] 搜索并确认不存在 `top.zhaizz.common.config` 和下层 `top.zhaizz.app` 引用。

建议第二批提交：`refactor(app): 集中 Business 配置装配`。

## 3. 验证与规范同步

- [x] 运行定向 app 测试，定位配置、授权、Origin、Agent HTTP/SSE 或架构边界失败。
- [x] 从 `backend/business` 运行 `mvn -B clean test`，验证整个 reactor。
- [x] 检查测试未访问真实 MySQL、Redis、MinIO 或 Python Agent。
- [x] 更新 `.trellis/spec/backend/directory-structure.md`：配置绑定和装配归 app。
- [x] 更新 `.trellis/spec/backend/quality-guidelines.md`：移动配置必须 clean test，并列出五类保护。
- [x] 如安全、日志或超时契约出现新发现，同步对应 spec，不扩大产品行为。
- [x] 运行 `git diff --check` 并确认 diff 仅覆盖本任务。

## 4. 回滚点

- 第一批测试失败：修正测试环境或暴露的既有行为，不开始迁移。
- 迁移后编译/上下文失败：整体回退第二批迁移，不保留新旧配置并存。
- SSE 黑盒测试不稳定：先校准延迟与总超时；不得改成反射私有字段或删除该保护。
- 出现仓库外兼容需求：停止实施并回到 Plan，不自行添加旧包 shim。

## 5. 启动前检查

- [ ] 用户已批准最终规划摘要。
- [ ] `prd.md`、`design.md`、`implement.md` 与用户决定一致。
- [ ] `implement.jsonl`、`check.jsonl` 含真实 spec 上下文。
- [ ] 从最新 `main` 创建独立 `codex/` 分支后再执行 `task.py start`。
