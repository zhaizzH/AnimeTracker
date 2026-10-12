# 实施：重建准备

## 0. 回滚锚点
- [x] 确认 `git status` 干净；`git tag pre-frontend-rebuild`
- [x] `git tag --list pre-frontend-rebuild` 确认已创建

## 1. 核对表（落盘 `research/`）
- [x] `grep -rn "@shared" frontend/client/src frontend/admin/src > research/shared-refs.txt`
- [x] 逐页整理 client 12 页 / admin 8 页的 API 依赖 → `research/page-api-deps.md`

## 2. dashboard-5 字段核对
- [x] 逐卡片核对（visitors / online-now / top-pages / top-countries / top-referrers / traffic-sources / audience-mix / browser-share / web-vitals）
- [x] 对照 `docs/spec/openapi.yaml` 与 `packages/shared/src/types/index.ts` 与 `api/admin/dashboard.ts`
- [x] 缺口写入 `research/dashboard5-gaps.md` 并回报父任务

## 3. shared 清理
- [x] 删除 `packages/shared/src/theme.ts`
- [x] 移除 `packages/shared/src/index.ts:11` 的 `antdTheme`/`antdThemeDark` 导出
- [x] 移除 `packages/shared/package.json` 的 `antd` 依赖
- [x] 改写 `packages/shared/src/components/SubjectCard.tsx` 的 `--od-*` 注释与样式依赖
- [x] 校验：`npm run typecheck -w @animetracker/shared && npm test -w @animetracker/shared`

## 4. 删除旧实现（仅 client）
- [x] `git rm -r frontend/client/src`（**admin 不删**：已是 dashboard-5 终态，见 `research/dashboard5-gaps.md`）
- [x] 校验：`grep -rn "from 'antd'\|@ant-design/icons" frontend --include=*.ts --include=*.tsx --exclude-dir=node_modules` 无结果

## 验证命令
```bash
cd frontend
npm run typecheck -w @animetracker/shared
npm test -w @animetracker/shared
```

## 回滚点
- `git checkout pre-frontend-rebuild -- frontend/`（整体还原本子任务）
