# 实施：client 页面重建

## 1. 前置确认
- [x] 外壳与路由骨架已就绪（子任务 3）；核对表 `research/page-api-deps.md` 在手
- [x] 确认 `sonner` 已装并挂 `Toaster`（替代 antd `message`）

## 2. 认证 5 页
- [x] Login / Register / VerifyEmail / ForgotPassword / ResetPassword 接 `authApi`
- [x] 保留 `setAuthenticated` + `publishSessionAvailable`
- [x] 表单校验与错误透出（对齐现状的「认证错误透出后端 message」行为）

## 3. 业务 7 页
- [x] Home：hero 轮播 + 统计 + 分类入口；**落定轮播的可测试锚点**
- [x] AnimeIndex：筛选 + 搜索，状态与 URL query 同步
- [x] Schedule：放送日历按星期分组 + 切换
- [x] SubjectDetail：详情 + 剧集表（表格横向滚动区域）+ 收藏
- [x] MyCollections：Tabs + 收藏/进度 CRUD，mutation 后失效 query
- [x] Profile：信息卡 + 改密/头像/资料弹窗；改密成功 → `publishSignedOut` 登出
- [x] Agent：会话 sider + 流式对话 + 停止按钮

## 4. Agent 浮窗
- [x] `AIAssistantFloat`：开合、Esc、焦点管理、`location.key` 路由切换关闭、`/agent` 下不显示
- [x] `AgentChat`：provider/context 契约不变；流式区 `aria-live="polite"`
- [x] **落定无障碍名与焦点 id 契约**（作测试锚点）

## 5. 测试
- [x] 重写 `home.hero` / `agent.float` / `agent.markdown` 三个用例到新锚点
- [x] 补认证守卫、登录登出用例
- [x] 确认 `matchMedia.ts` 是否仍需要

## 6. 验证
- [x] `npm run typecheck`
- [x] `npm test -w client`
- [x] 手工联调（business :8080）：筛选 / 收藏 / 进度 / 日历 / Profile / Agent

## 验证命令
```bash
cd frontend
npm run typecheck
npm test -w client
npm run dev:client
```

## 回滚点
- 按页粒度回滚；整体回滚至 `pre-frontend-rebuild`。
