# 实施计划:前端 spec 漂移审计与文档更新

前置:`pwd` 应为 `C:/workspace/project/AnimeTracker`。本计划只改文档,不碰代码。

## 行尾处理(先做)

待改文件里只有 `hook-guidelines.md` 是混合行尾(27 CRLF / 89 裸 LF),其余均为纯 CRLF。策略:

- 对纯 CRLF 的四个文件:编辑时保持 CRLF,禁止整文件翻转。
- 对 `hook-guidelines.md`:按 Q9(a) **整体规范化为 CRLF**,并在提交信息说明。
- 每步改完用下面命令核验某文件不再出现裸 LF:

```bash
python -c "import sys;d=open(sys.argv[1],'rb').read();print(sys.argv[1],'CRLF',d.count(b'\r\n'),'bareLF',d.count(b'\n')-d.count(b'\r\n'))" .trellis/spec/frontend/<file>.md
```

对纯 CRLF 文件,期望 `bareLF 0`;对规范化后的 hook-guidelines,同样期望 `bareLF 0`。

## 步骤清单

### Step 1 — quality-guidelines.md(3 处定点)

- [ ] `:22` 测试计数:18 → **20**;分项 `shared 3 / client 6 / admin 11`;点名新增 `client/src/test/not-found.test.tsx`、`admin/src/components/auth/auth-page.test.tsx`。保留「79 例为带日期的历史基线」的措辞。
- [ ] `:24` shim 位置:`client/src/test/matchMedia.ts` → `client/src/test/setup.ts`(matchMedia shim 内联于此)。
- [ ] `:34` client `optimizeDeps.include`:补 `react-router-dom`、`react-markdown`、`remark-gfm`、`sonner`、`react-dom/client`;保留「不含 Ant Design」。
- [ ] 新增 D4 总则一句(未接线文件允许存在、不得进构建产物)。

### Step 2 — hook-guidelines.md

- [ ] `:116` followSystem 段:改写为已实现现状(两端 `theme-bridge.tsx` 订阅 `prefers-color-scheme` 变化,含 `addListener` 回退与清理);去掉「未订阅」的过时陈述。保留「浏览器不支持 matchMedia 的降级」注意点(以源码为准)。
- [ ] 全文件行尾规范化为 CRLF(Q9a)。

### Step 3 — component-guidelines.md

- [ ] `:41` forwardRef 清单:删 `badge.tsx`/`breadcrumb.tsx`,仅留 `button.tsx`(两端);说明 badge/breadcrumb 用 `asChild ? Slot.Root : span/a` 且当前无消费方传 ref。保留判据句。
- [ ] (可选)`:16` 若提到 `AdminLogin`,把文件指针更新为 `components/auth/auth-page.tsx`。

### Step 4 — directory-structure.md

- [ ] `:36` 页面清单:`AdminLogin` → `components/auth/auth-page.tsx`(默认导出 `AdminLogin`,非 `pages/` 路由页);页面清单不再把 `AdminLogin` 列进 `pages`。
- [ ] `:37`/`:38` 保留「仅静态导入/无外壳」语义,文件名更新。
- [ ] 新增 D2 段:client 认证路由结构(`/login`≡`/register` 同一 `AuthPage`;三个认证页提到外壳外;全部 `PublicOnly`)+ client 顶层 404。
- [ ] 新增 D3 段:efferd `header` 簇登记为未接线脚手架(含路径与「无引用、不进构建」)。
- [ ] `:23` 补 admin 测试就近约定。
- [ ] `:39` 显式写出「无 `/admin` 前缀 = ADR 0018 的落地」。

### Step 5 — 新 ADR

- [ ] 新建 `.trellis/spec/adr/0021-shared-contract-visuals-vs-app-local-decorations.md`,按既有模板(状态/记录日期/相关规范 + 背景/决策/备选方案/后果)。
- [ ] 在 `.trellis/spec/adr/README.md` 索引表追加一行(编号 0021)。
- [ ] 不改 README 末尾「关于取舍」清单。

### Step 6 — 全文自查

- [ ] `git diff --stat` 复核改动范围未越界(仅上述文件)。
- [ ] 对每个被改文档核验行尾。
- [ ] 回查文档中新增/改动的每个 `file:line` 指针确实指向所声称内容。
- [ ] 点击校对 spec 内部相对链接(新 ADR ←→ frontend spec,frontend index ←→ 子文档)无死链。

## 验证命令

```bash
cd C:/workspace/project/AnimeTracker
git diff --stat
git diff -- .trellis/spec/frontend/quality-guidelines.md
python -c "import sys;d=open(sys.argv[1],'rb').read();print(sys.argv[1],'bareLF',d.count(b'\n')-d.count(b'\r\n'))" .trellis/spec/frontend/hook-guidelines.md
```

## 审查门(review gate)

在 `task.py start` 前,请你 review `prd.md` / `design.md` / `implement.md` 与本任务 `research/` 两份记录。

## 回滚点

- Step 1–4 之间任一:仅文档,`git checkout -- .trellis/spec/frontend/<file>` 即回滚。
- Step 5:`git rm .trellis/spec/adr/0021-*.md` 并撤销 README 索引行。

## 提交

单一提交,信息形如:

```
docs(spec): 前端 spec 漂移审计修正 + 新增 ADR 0021

- quality-guidelines: 测试数 18→20、shim 位置纠错、optimizeDeps 补全
- hook-guidelines: followSystem 已订阅现状改写(并规范化 CRLF)
- component-guidelines: forwardRef 契约仅 button.tsx
- directory-structure: auth-page/认证路由/顶层 404/登记未接线 header 簇
- adr: 新增 0021(契约性视觉下沉 shared、装饰件各端自持)
```
