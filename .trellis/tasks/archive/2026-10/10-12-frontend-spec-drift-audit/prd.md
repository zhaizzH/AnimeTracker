# 前端 spec 漂移审计与文档更新

## Goal

对 `.trellis/spec/frontend/` 的五个文档做一次「文档 vs 代码」的**全量漂移审计**,修正所有与当前实现不符的陈述。起因是最近四个前端提交改动了结构却未同步文档:

- `62354fa4` refactor(auth):登录页改用 efferd/auth-5 面板并独占整屏
- `ca920141` feat(web):两端新增 404 页,admin 去掉 `/admin` 路由前缀并修复主题跟随
- `e432ece1` chore(admin):页面标题统一为 AnimeTracker
- `657f8ffe` chore(client):收录 efferd 页头组件簇(header/mobile-nav/portal/use-scroll)

同时执行一次**免登录真实运行验证**,并按严格标准最多新增 1 条 ADR。

## Requirements

### R1 范围(已定:全量审计)

- 审计范围是 `.trellis/spec/frontend/` 的**全部**五个文档,以及与其直接相关的 `GLOSSARY.md`、`adr/README.md`、frontend 相关 ADR(0017/0018)。
- 不限于上述四个提交;凡发现文档陈述与当前代码不符,一并列入。
- 后端(`spec/backend/`)、guides(`spec/guides/`)**不在本次范围**。

### R2 真实验证(已定:免登录优先)

- 执行**免登录可达到**的真实浏览器验证:匿名可达页面的路由落点、`/register` 行为、两端 404 整屏、外壳之外页面的主题跟随。
- 仓库内**无任何可用登录凭据**(已确认:无 seed、无默认管理员、无 docker-compose;管理员需手工 SQL 引导)。因此**不**做登录后验证,登录态部分以读代码为准。
- 验证结论必须可复现地记录;若某条声明无法在免登录下验证,明确标注「以源码为准」。

### R3 死代码登记策略(已定:按性质分类)

- 有意的未来脚手架(如 `657f8ffe` 的 `header/mobile-nav/portal/use-scroll` 簇)登记为**未接线脚手架 : 当前无引用、不进构建产物**。
- 无意图的遗留孤儿(如 `client/src/components/auth/auth-shell.tsx`、`admin/src/App.tsx`)不逐个点进目录规范,仅以一句总则覆盖。
- 只在**目录规范**内登记存在性;**质量规范**只负责「不得进构建产物」这类门禁表述。

### R4 新增 ADR(已定:最多 1 条)

- 新增 **1 条 ADR**:前端视觉件(client/admin)各端自持,shared 只承载跨应用契约与逻辑,不放视觉件。理由:`auth-divider.tsx`、`floating-paths.tsx` 在两端逐字节相同仍刻意各持一份。
- **不**为「admin 去 `/admin` 前缀」新增 ADR —— 该决策已被 ADR 0018(独立端口部署)覆盖,本次只是「代码对齐既有 ADR」,应写在 `directory-structure.md` 里而非新开 ADR。
- 若审计后**无**任何决策同时满足「难以反转 + 无上下文会困惑 + 真实权衡」三条,则接受**本轮 0 新增 ADR**,仍以 R4 的视觉件条目为候选中枢。

### R5 文本完整性(硬约束)

- `.trellis/spec/frontend/` 下文档为**混合 CRLF/LF** 行尾;编辑时必须保持各文件原有行尾,**禁止**因工具重写而把整文件刷成 LF、放大 diff。
- 中文文档措辞风格与既有 spec 保持一致(陈述式、带 `file:line` 佐证、显式标注「目标 / 现状 / 债务」状态)。

## Acceptance Criteria

### A. 已确认的陈旧点必须修正

- [ ] `directory-structure.md` 的 admin 页面清单:`AdminLogin` 已删除,改为 `components/auth/auth-page.tsx`(导出名仍为 `AdminLogin`,但**不是**路由页面)。
- [ ] `directory-structure.md` 与 `component-guidelines.md` 中「`AdminLogin` 静态导入例外」改写为指向现行文件与现行事实。
- [ ] `directory-structure.md` 补充 client 认证路由现行结构:`/login` 与 `/register` 渲染**同一个** `AuthPage`(注册为面板内切换,`/register` 直接 redirect 到 `/login`);`/verify-email`、`/forgot-password`、`/reset-password` 已提到 `ClientLayout` **之外**、整屏渲染。
- [ ] `directory-structure.md` 补充 client 的 404 现为**顶层** `path: '*'`(位于 `ClientLayout` 之外);文档当前只写了 admin 侧该约定。
- [ ] 登记 efferd `header` 簇为未接线脚手架(见 R3)。

### B. 全量审计项(已由审计确定的具体漂移)

- [ ] `quality-guidelines.md:24`:浏览器 shim 位置错,`client/src/test/matchMedia.ts` **不存在**,shim 内联在 `client/src/test/setup.ts` → 改为正确位置。
- [ ] `quality-guidelines.md:22`:测试文件数 18 → **20**(client 5→6 补 `not-found.test.tsx`;admin 10→11 补 `components/auth/auth-page.test.tsx`),并更新分项描述。
- [ ] `quality-guidelines.md:34`:client `optimizeDeps.include` 描述不全 → 补 `react-router-dom`、`react-markdown`、`remark-gfm`、`sonner`、`react-dom/client`;「不含 Ant Design」的结论保留。
- [ ] `component-guidelines.md:41`:forwardRef 清单纠错 —— 仅 `button.tsx` 前向 ref;`badge.tsx`/`breadcrumb.tsx` 只支持 `asChild`、不前向 ref,且无消费方传 ref。移除后两者,保留「判据是消费方是否真的传 ref」。
- [ ] `hook-guidelines.md:116`:`followSystem` 陈述已被证伪 —— 两端 `theme-bridge.tsx` 已 `media.addEventListener('change', …)` 订阅(含 `addListener` 回退与清理),改写为已实现现状。
- [ ] `directory-structure.md:23`:补记 admin 测试同目录约定(`src/**/*.test.tsx` 就近)。
- [ ] 审计报告落入任务 `research/`,逐条含 `file:line` 与反证。
- [ ] 全部 `STALE` 项已修入对应文档;`PARTIALLY-STALE` 项已按「目标 / 现状」拆分保留;仍属目标的(SSE 401/403 自愈、ProgressPreviewModal/Profile 缓存失效、SubjectCard 依赖、URL 筛选)保持标注不变。

### C. 新增 ADR

- [ ] 新增 ADR:**前端「契约性视觉」下沉 shared,「装饰件与原语层」各端自持**。判据按性质划界 ——
  - shared 承载跨应用共享的**领域契约展示**(如 `SubjectCard` 渲染两端共用的 Subject 呈现);
  - **纯装饰件与 shadcn 原语层**(`ui/*`、`auth-divider`、`floating-paths`、`empty`、`input-group`)各端自持,允许逐字节重复,不上提。
- [ ] 按既有编号与模板落盘,并登记进 `adr/README.md` 索引表。
- [ ] **不**为「admin 去 `/admin` 前缀」新增 ADR —— 该决策已被 ADR 0018 覆盖,本次仅「代码对齐既有 ADR」,写在 `directory-structure.md` 里。
- [ ] 若最终判定无够格决策,则明确记录「本轮不新增 ADR」及理由(可接受达成)。

### D. 真实验证(已执行)

免登录真实浏览器验证已于 2026-10-12 执行,实际观测:

- [x] client `http://localhost:5173/login`:整屏认证面板(左品牌面板 + 右表单),**无侧边栏/外壳**。
- [x] client `http://localhost:5173/register`:URL 落定为 `/login`(redirect 生效);点击「创建新账号」后**面板内**切换为注册表单,URL 不变。
- [x] client `http://localhost:5173/forgot-password`:外壳之外的独立页面(link 回到 `/login`)。
- [x] client 未知路径 `/this-path-does-not-exist-xyz`:整屏 404,**未**重定向到 `/login`;链接为「返回首页 `/`」「浏览番剧 `/anime`」。
- [x] admin `http://localhost:5174/nope-not-here`:整屏 404,无 AdminLayout 外壳;链接「返回面板 `/dashboard`」「番剧管理 `/subjects`」。
- [x] admin 旧前缀 `http://localhost:5174/admin/dashboard`:落到 404(证明 `/admin` 前缀确已移除)。
- [x] admin `http://localhost:5174/login`:整屏登录面板(仅登录,无注册/找回)。
- [x] 主题跟随(外壳之外):client 登录页与两端 404 在 `followSystem=true` + 系统 dark 下,`html.dark` 生效、`color-scheme:dark`、`meta theme-color` 随之变暗。
- [x] 无法免登录验证的声明(登录后跳转、`location.state.from` 回退、角色门)标注为**以源码为准**。
- [x] 各服务在线:client 5173 / admin 5174 / business 8080 `/actuator/health` UP / agent 8090 health ok。

### E. 文本与门禁

- [ ] 除 `hook-guidelines.md` 外,所有被改文档的行尾保持原状(CRLF);`hook-guidelines.md` **按 Q9(a) 规范化为 CRLF**(它是唯一混合文件,27 CRLF / 89 裸 LF),并在提交信息中说明该行尾规范化。
- [ ] `git diff` 中除 `hook-guidelines.md` 的行尾规范化外,无其他无关改写(空白、重排、无关段落)。
- [ ] 文档引用的路径与命名与当前代码一致(抽样回查)。
- [ ] frontend spec 引用的所有 `file:line` 指针在改动后仍指向正确目标。

## Notes

- 本任务为**纯文档更新**,不含代码实现;不产生构建/测试产物变更。
- 顺带发现(超出本任务范围,仅记录不处理):`backend/agent/.env`、`application-local.yml` 含已提交的真实密钥。
