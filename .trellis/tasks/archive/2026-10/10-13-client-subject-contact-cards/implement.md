# Implement — 条目详情页信息栏改用 efferd contact-1 卡片

## 前置检查

- [ ] 确认无其他任务正在改 `SubjectDetail.tsx` / `client/src/components`（`python ./.trellis/scripts/task.py list`，看 `10-13-client-footer` 状态——它改的是外壳挂载点，与本任务无文件重叠）。
- [ ] 基线：`npm run typecheck -w client` 当前通过。

## 步骤

1. **新增 `frontend/client/src/components/full-width-divider.tsx`**
   - 逐字移植 `https://efferd.com/r/new-york/full-width-divider.json` 的组件内容（`React.ComponentProps<"div">`、`contained`、`position`、`aria-hidden`）。
   - 校验：`cn` 来自 `@/lib/utils`（本项目别名正确）。

2. **新增 `frontend/client/src/components/subject-info-cards.tsx`**
   - 按 design「组件契约」实现：接收 5 个标量 props；内部常量 `SUBJECT_TYPE_LABEL` + 图标/字段数组；根 `<div className={cn('relative', className)}>`；`<dl>` 网格 + `<dt>/<dd>` 卡片 + `aria-hidden` 图标；上下 `FullWidthDivider contained position="top|bottom"`。
   - 兜底：`放送 → formatDate(airDate)`、`类型未登记 → 未知(n)`、**`排名 → rank > 0 ? rank : '—'`**（不用 truthiness）、`集数/收藏` 原样（`0` 保持 `0`）。
   - 响应式：文本列 `min-w-0`、值 `break-words`、图标框 `shrink-0`（见 design「响应式加固」）。

3. **改 `frontend/client/src/pages/SubjectDetail.tsx`**
   - 62–75 行 `<dl>…</dl>` → `<SubjectInfoCards className="mt-4" … />`。
   - 删除页面内 `SUBJECT_TYPE_LABEL` 常量；清理随之不再使用的导入（按 `typecheck` 提示）。

4. **新增 `frontend/client/src/test/subject.info-cards.test.tsx`**
   - 3 个用例（见 design「测试」）。参考 `home.hero.test.tsx` 的 render 风格，但本组件无需 QueryClient/MemoryRouter。
5. **spec 登记（保持行尾）**
   - `python -I` 按字节替换 `.trellis/spec/frontend/directory-structure.md` 中 client 组件登记子串，补上 `components/full-width-divider.tsx` 与 `components/subject-info-cards.tsx`（efferd contact-1 骨架落地）。
   - 完成后 `git diff --stat` 确认该文件只有 1–2 行变动；若整文件重写则回退重做。

## 验证命令

```bash
cd frontend/client
npm run typecheck
npm test -- --run
npm run build        # 交付型变更
```

- 浏览器免登录验证：`npm run dev:client` → `http://localhost:5173/subject/115`
  - 卡片网格 3 列呈现，窄屏（DevTools ≤640px）为单列；
  - **横向无滚动条**（重点复核 D5 的 `contained` 结论）；
  - 上下分隔线与卡片网格同宽；
  - `排名/集数/放送/类型/收藏` 5 项值与改动前一致；无数据条目验证 `—` 与 `未知(n)`。

## 评审门 / 回滚点

- **门 1（步骤 1–2 后）**：两个组件通过 `typecheck`，`SubjectDetail.tsx` 尚未改 → 此时回滚只需删文件。
- **门 2（步骤 3 后）**：页面渲染正确且无横向溢出 → 未过则 `git checkout -- src/pages/SubjectDetail.tsx` 单独回退页面。
- **门 3（步骤 4–5 后）**：测试绿、spec diff 最小 → 提交。

## 提交

- 建议信息：`feat(client): 条目详情信息栏改用 efferd contact-1 卡片网格`
- 提交前确认未误改 spec 行尾、未引入 `@efferd/*` 依赖、`packages/shared` 未动。
