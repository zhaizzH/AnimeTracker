# 设计:前端 spec 漂移审计与文档更新

## 边界

**改这些(仅文档,无代码):**

- `.trellis/spec/frontend/index.md`(预计不改,审计结论为干净)
- `.trellis/spec/frontend/directory-structure.md`
- `.trellis/spec/frontend/component-guidelines.md`
- `.trellis/spec/frontend/hook-guidelines.md`
- `.trellis/spec/frontend/quality-guidelines.md`
- `.trellis/spec/adr/0021-*.md`(新增)
- `.trellis/spec/adr/README.md`(登记新 ADR)

**不改:** `GLOSSARY.md`(审计无 frontend 域漂移)、`spec/backend/**`、`spec/guides/**`、任何代码、任何 ADR 正文(0017/0018 均 HOLDS)。

## 契约与事实来源

本次改动的唯一权威是**代码现状**,已由 `research/spec-drift-audit.md`(逐条 `file:line` + 反证)与 `research/runtime-verification.md`(免登录实测)固定。文档措辞不得超出这两份记录的范围。

## 关键设计决策

### D1 admin 页面清单的措辞(命名歧义)

`directory-structure.md:36` 的 `AdminLogin` 是**陈旧命名**。现状:文件是 `admin/src/components/auth/auth-page.tsx`,默认导出函数仍叫 `AdminLogin`,但它**不是** `pages/` 下的路由页面,而是 `components/auth/` 下的认证页组件。

处理:
- 页面清单中删去 `AdminLogin`,认证页改为按**文件路径**描述:`components/auth/auth-page.tsx`(默认导出 `AdminLogin`)。
- 明确它**仍是** admin 侧唯一静态导入的路由页(router 里直接 `import AdminLogin from './components/auth/auth-page'`),因此 `:37`/`:38`/`component-guidelines.md:16` 的「AdminLogin 静态导入例外」在**语义上仍成立**——只需把指向的文件名更新,不必推翻这条例外。

### D2 client 认证路由结构补记

新增一段描述(现状):

- `/login` 与 `/register` 渲染**同一个** `AuthPage`;注册不是独立路由,而是面板内 `switchMode`;`/register` 仅 `Navigate` 到 `/login`。
- `/verify-email`、`/forgot-password`、`/reset-password` 各自独立页面,但已**提到 `ClientLayout` 之外**(整屏,无外壳)。
- 全部认证路由由 `PublicOnly` 包裹。
- client 的 404 是**顶层** `path:'*'`(在 `ClientLayout` 外),旧实现(外壳内 `Navigate to="/"`)已删除。

### D3 死代码脚手架的登记口径(按性质分类)

- `client/src/components/{header,mobile-nav,portal}.tsx` + `hooks/use-scroll.ts`(efferd 页头簇):在 `directory-structure.md` 记为**已收录的未接线脚手架 : 当前无引用、不参与构建产物、来自 efferd registry 的营销页头**。要点是防止后来者误认作活页头。
- `client/src/components/auth/auth-shell.tsx`、`admin/src/App.tsx` 等**无意图孤儿**:不进目录规范点名,改由**一句总则**覆盖(见 D4)。

### D4 一条总则(放 quality-guidelines.md)

> 允许仓库内存在未被引用的文件;目录规范只登记被引用的活代码。未接线文件不得进入构建产物。

### D5 followSystem 段改写(Q10a)

`hook-guidelines.md:116` 整段替换为现状:两端 `theme-bridge.tsx` 在 effect 内 `media.addEventListener('change', apply)` 订阅(`addListener` 回退)并清理。保留的唯一注意点是「浏览器不支持 `matchMedia` 时的降级」由哪一端承担(以源码为准)。

### D6 forwardRef 契约纠错(Q11/Q9 无关)

`component-guidelines.md:41` 收敛为:仅 `button.tsx`(两端)必须前向 ref;`badge.tsx`/`breadcrumb.tsx` 以 `asChild ? Slot.Root : span/a` 渲染、**不前向 ref**,且当前无消费方传 ref。保留原文的**判据句**(「不是是否导出了 ref 类型,而是消费方是否真的传 ref」),因为判据本身正确。

### D7 新 ADR 的划界(Q11a)

标题:**前端「契约性视觉」下沉 shared,装饰件与 `ui` 原语层各端自持。**

- shared 承载**跨应用共享的领域契约展示**(`SubjectCard` 渲染两端共用的 Subject 呈现)——这是既有事实,ADR 为其**提供边界定义**而非新引入。
- `ui/*`(shadcn 原语派生)、`auth-divider`、`floating-paths`、`empty`、`input-group` 等**装饰件/原语层各端自持**,允许逐字节重复,不上提 shared。
- **依据**:`auth-divider.tsx`、`floating-paths.tsx` 两端逐字节相同仍刻意各持;`ui/empty.tsx`、`ui/input-group.tsx` 两端各自一份副本。上提的收益(省 ~94 行)小于引入的共享依赖面与版本耦合成本。
- **不**为「admin 去 `/admin` 前缀」开 ADR —— 已被 ADR 0018 覆盖,只把对齐关系写进 `directory-structure.md:39`。
- 编号顺延既有最大值(0020)→ 新文件 `0021-*.md`,并加入 `adr/README.md` 表。README 末尾「关于取舍」一段的例外清单不需改动。

## 数据流 / 无运行时影响

纯静态文档改动。不涉及构建、测试、运行时。`research/` 记录是审计证据,留在任务目录内,不进入 `.trellis/spec`。

## 兼容性与回滚

- 回滚 = `git checkout -- .trellis/spec/` 加删除新 ADR 文件;无迁移、无数据。
- 行尾:除 `hook-guidelines.md` 按 Q9(a) 规范化为 CRLF 外,其余文件保持原 CRLF。

## 验证方式

见 `implement.md` 的验证清单(diff 审查、行尾核验、`file:line` 指针回查、内部链接可点)。
