# 设计：client 页面重建

总体设计见父任务 `design.md`；此处写页面级接线与测试契约。

## 数据流（不变）

```
页面 → shared 命名空间 API（get/post/postForm）→ http.ts 拦截器解包为 T → 组件
Agent 页 → useAgentChat → streamSse(fetch 流) → 事件 JSON.parse
登录态 → useAuthStore(status) ← coordinator（token 内存 + BroadcastChannel）
```

## 页面接线对照（旧实现的语义须保留）

| 页 | 关键行为（现状） | 重建要点 |
|---|---|---|
| Home | 轮播 hero（5s 自动切换） | 轮播改纯 CSS/React，**新测试锚点须落定**（旧锚点 `.od-hero__slide.is-active .od-hero__title` 随样式删除） |
| AnimeIndex | 多条件筛选（5 个 Select + 搜索） | 筛选状态与 URL query 同步；`subjectsApi` |
| Schedule | 放送日历（按星期分组 + 切换） | 分组查询参数；空日显示空态 |
| SubjectDetail | 详情 + 剧集表 + 收藏入口 | `subjectsApi` + `collectionsApi` |
| MyCollections | Tabs + 收藏/进度 CRUD | mutation 后失效权威 query（`hook-guidelines.md`） |
| Profile | 信息卡 + 改密/头像/资料三弹窗 | 改密成功 → `publishSignedOut` 登出 |
| Agent | 会话 sider + 流式对话 | `useAgentChat` + 停止；`aria-live="polite"` |
| 认证 5 页 | 表单 + `message` 提示 | antd `message` → `sonner`；保留 `publishSessionAvailable` |

## 测试契约（覆盖不许减少）

| 原用例 | 断言对象 | 重建后 |
|---|---|---|
| `home.hero.test.tsx` | hero 轮播自动切换 | 保持「按 5s 自动推进」语义，锚点改为新 markup（**实施时确定并记录**） |
| `agent.float.test.tsx` | 浮窗开合、Esc、无障碍名、provider 重挂载、流式停止 | 保持全部断言；无障碍名与 id 按新实现落定并作为契约 |
| `agent.markdown.test.tsx` | 表格横向滚动 `role="region"` | 保持；锚点由 `od-agent-table-scroll` 改为新类名 |
| `client/src/test/matchMedia.ts` | antd 响应式桩 | Tailwind 外壳可能不再需要；保留除非确认无用户 |

## 风险

- 无障碍名/焦点 id 是测试契约，实施时须**先落定再写测试**，避免测试追着实现跑。
- 轮播是真实计时器测试（旧用例 20s 超时），重建时保持真实计时，不用 fake timer 掩盖。

## 回滚

- 页面文件独立，可按页回滚；整体回滚至 `pre-frontend-rebuild`。
