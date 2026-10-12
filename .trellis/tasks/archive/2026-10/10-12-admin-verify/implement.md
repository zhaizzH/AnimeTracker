# 实施：admin 核验

## 1. 基线
- [x] `npm run typecheck -w admin`、`npm test -w admin` 记录基线（不改代码）

## 2. 外壳与导航
- [x] 读 `layouts/AdminLayout.tsx`：判定是否 `app-shell-5` 形态
- [x] 读 `components/app-sidebar.tsx`：7 条路由是否真实、有无 demo 分组/changelog 卡

## 3. 卡片
- [x] 逐卡片读 props：确认数据源为真实后端类型
- [x] `grep -rn "vercel.app\|https://" frontend/admin/src` 逐条判定
- [x] 确认 `delta.tsx` 图标仅 lucide

## 4. 六页与契约
- [x] 六页各查 loading/empty/error
- [x] 查确认弹窗的 `asChild` + `forwardRef` 契约

## 5. 产出
- [x] 写 `research/admin-diff.md`（已对齐 / 有差异 / 建议动作 + 证据 file:line）
- [x] 结论：admin 是否需进一步改动

## 验证命令
```bash
cd frontend
npm run typecheck -w admin
npm test -w admin
grep -rn "vercel.app\|https://" admin/src
```

## 回滚点
- 本任务只读，无回滚需要。
