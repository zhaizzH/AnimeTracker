# @animetracker/shared

> **一句话定位**：client 与 admin 共用的逻辑包（`@animetracker/shared`），集中放**双端共用**的 API 封装、鉴权协调、SSE 消费、类型、Zustand store 与公共组件。

> 上级文档：[前端总览](../../README.md) · [项目总览](../../../README.md)

## 适用场景

- 新增或修改双端共用的 REST/SSE 调用、类型与状态。
- 调整 token 刷新、跨标签页会话广播等鉴权时序。
- 维护 `SubjectCard`、`AuthGate` 这类契约性共享组件。

## 归属边界

- **下沉 shared**：双端确实共用的 API、鉴权、主题、SSE、类型与通用组件。
- **留在各自应用**：只属于单端的页面、布局壳、装饰件与 `components/ui` 原语（各端自持，允许逐字节重复）。判定见 [ADR 0021](../../../.trellis/spec/adr/0021-shared-contract-visuals-vs-app-local-decorations.md)。
- client/admin **不互相相对导入**；新共享导出先检查命名冲突。

## 目录结构

```text
packages/shared/src/
├── index.ts        # 唯一公共出口（命名空间导出 API）
├── api/            # http.ts(拦截器) + auth/subjects/collections/tags/files/agent
│   └── admin/      # agent/dashboard/import/logs/subjects/users（管理端）
├── auth/           # coordinator：refreshWithLock / 跨标签页会话广播
├── sse.ts          # streamSse（原生 fetch 流式消费）
├── hooks/          # useAgentChat / useAuthStatus / useBootstrapAuth
├── store/          # auth（内存 token）/ theme（persist）
├── components/     # AuthGate / SubjectCard
├── types/          # 跨端共享类型（ID 类型按领域核对）
└── format.ts
```

## 公共出口与 API 命名空间

`src/index.ts` 是唯一入口，API 以命名空间导出，避免 `list`/`remove`/`schedule` 等同名冲突：

```ts
import { subjectsApi, collectionsApi, adminLogsApi } from '@shared';
```

| 命名空间 | 来源 | 说明 |
|---|---|---|
| `authApi` / `subjectsApi` / `collectionsApi` / `tagsApi` / `filesApi` / `agentApi` | `api/*` | 用户端与通用接口 |
| `adminAgentApi` / `adminImportApi` / `adminLogsApi` / `adminUsersApi` / `adminSubjectsApi` / `adminDashboardApi` | `api/admin/*` | 管理端接口 |

应用统一从 `@shared` 导入（Vite alias + tsconfig paths 指向源码）；不穿透 shared 私有文件。

## HTTP 与鉴权时序（要点）

- `http`（Axios）：从内存 store 注入 `Authorization: Bearer`，解包 `ApiResult<T>.data`；401 最多刷新并重放原请求**一次**（`AUTH_ENDPOINT` 除外，见 `api/http.ts`）。
- `sessionHttp` 仅负责 refresh 等会话请求；`streamSse` 用原生 fetch，**不会**自动 401 刷新，消费方须自行「刷新一次 → 重开同一流一次」。
- Access Token 只存 `useAuthStore` 内存，禁止持久化到 localStorage（初始化时主动清除旧键）。

完整契约（含错误矩阵、Good/Base/Bad、测试点）见 [Hook 规范 · 前端 HTTP 与 SSE 认证/刷新契约](../../../.trellis/spec/frontend/hook-guidelines.md#scenario-前端-http-与-sse-认证刷新契约)。

## SSE 与 Agent 对话

- `streamSse` 发 POST JSON，携带可选 Bearer 与 `AbortSignal`；事件 `type` 只有 `answer / thinking / function_call / status`，**不存在 `type=end`**，结束由 `is_end=true` 表达。
- `useAgentChat` 负责会话、历史、流式、停止与工具状态；client/admin 只提供不同的 `AgentChatApi` 适配对象。

## 类型归属

- 跨应用/跨页面 API 类型集中在 `types/`；ID 类型按领域核对（`SubjectListItem`/`HotItemVO` 为 `string`，`User`/`Episode`/`Collection`/`Tag`/`Log` 仍为 `number`）。
- 当前无 Zod 等运行时 schema；字段变化靠端到端核对与测试补足。改字段时按 [跨层同步清单](../../../.trellis/spec/frontend/component-guidelines.md#跨层同步) 逐项检查。

## 质量检查

```bash
cd frontend
npm run typecheck
npm test          # shared 的 *.test.ts 随 workspace 一起跑
```

## 与相邻模块的关联

- 消费方：[client](../../client/README.md) 与 [admin](../../admin/README.md)。
- 规范：[组件与类型](../../../.trellis/spec/frontend/component-guidelines.md) · [Hook 与状态](../../../.trellis/spec/frontend/hook-guidelines.md) · [质量门禁](../../../.trellis/spec/frontend/quality-guidelines.md)。
