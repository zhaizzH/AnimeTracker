---
name: chat-frontend-sse-migration
description: 前端 Chat 模块从 WebSocket 迁移到 SSE+REST 的设计
---

# Chat 前端 SSE 迁移设计

> 配合 Agent 后端重构（2026-07-22-agent-module-refactor-design.md），前端 Chat 从 WebSocket 切换到 REST API + SSE 流

## 改动清单

| 文件 | 操作 |
|------|------|
| `src/api/chat.ts` | 新建 |
| `src/stores/chat.ts` | 重写 |
| `src/types/index.ts` | 微调 |
| `src/components/chat/ChatWidget.vue` | 更新 |
| `src/components/chat/ChatInput.vue` | 更新 |
| `src/components/chat/ChatMessageList.vue` | 更新 |
| `src/components/chat/ChatSessionList.vue` | 更新 |

## API 模块 (`src/api/chat.ts`)

封装 REST 调用，base URL `http://localhost:8090`（跨域），自动带 Bearer token：

- `getSessions()` → `GET /api/chat/sessions`，返回 `ChatSession[]`
- `createSession()` → `POST /api/chat/sessions`，返回 `{session_id: string}`
- `getHistory(sessionId)` → `GET /api/chat/sessions/{id}/history`，返回 `ChatMessage[]`
- `deleteSession(sessionId)` → `DELETE /api/chat/sessions/{id}`

所有 REST 调用失败时返回 `null`，由 store 统一处理错误状态（设置 `error` 字段）。

`POST /api/chat/stream` 不在 API 模块中，由 store 直接 `fetch('http://localhost:8090/api/chat/stream', ...)` + `ReadableStream` 解析 SSE。

## Store (`src/stores/chat.ts`)

**移除**：`ws`, `connectionState`, `connect()`, `disconnect()`, `send()`, `scheduleReconnect()`, `WsConnectionState`, `onSessionCreated()`

**保留**：`sessions`, `messages`, `currentSessionId`, `streamingContent`, `isStreaming`, `currentMessages`

**新增**：
- `loading: boolean` — 任何 REST 请求进行中为 true
- `error: string | null` — 最近的错误消息，消费后清空
- `initialized: boolean` — 防止重复初始化
- `init()` — 首次打开面板时调用，调用 `fetchSessions()` 并设 `initialized = true`

**`currentSessionId` 流转**：
- 用户点击"新对话" → `newSession()` → `POST /api/chat/sessions` 返回 `{session_id}` → 立即赋值 `currentSessionId`
- 用户选择历史会话 → `loadHistory(sessionId)` → 赋值 `currentSessionId`
- `sendMessage()` 时无 `currentSessionId` → 内部调用 `newSession()` 拿到 session_id 再发消息
- 删除当前会话 → `deleteSession(sessionId)` → 置空 `currentSessionId`

**核心变更 — SSE 流式调用**：

```
sendMessage(content)
  → 无 session → newSession() 自动创建并等待 session_id
  → messages 追加 user message
  → fetch('http://localhost:8090/api/chat/stream', POST, JSON body {session_id, content})
  → reader = response.body.getReader()
  → 逐 chunk 解码，按 \n 分割行
  → event: token  → streamingContent += data.content
  → event: metadata → 忽略（仅含 session_id + used_tools，当前不显示工具调用信息）
  → event: done   → messages 追加完整 assistant message，fetchSessions() 刷新标题
  → event: error  → messages 追加错误消息
  → catch 异常   → messages 追加网络错误消息
```

**错误处理**：
- REST 调用失败 → `error = '操作失败，请重试'`，组件展示 toast 或内联提示
- SSE `event: error` → 推入 `messages` 展示给用户
- fetch 网络异常 → 推入 `messages` 展示给用户
- 401 → 提示"登录已过期"（SSE error event 由后端发出）

## 组件更新

| 组件 | 改动 |
|------|------|
| `ChatWidget` | toggle 不再 connect/disconnect；连接指示器简化或移除；去掉 `onUnmounted` 清理 |
| `ChatInput` | 禁用条件从 `connectionState !== 'connected'` 改为 `isStreaming` |
| `ChatMessageList` | 删除"连接已断开"提示块 |
| `ChatSessionList` | 去掉 `connectionState` 相关的 disabled 条件 |

## 类型调整

- `ChatMessage.tool_calls`: `string` → `string[] | null`
- 移除 `WsConnectionState`
