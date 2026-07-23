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

封装 REST 调用，base URL `http://localhost:8090`（跨域），所有请求自动带 Bearer token：

- `getSessions()` → `GET /api/chat/sessions`
- `createSession()` → `POST /api/chat/sessions`
- `getHistory(sessionId)` → `GET /api/chat/sessions/{id}/history`
- `deleteSession(sessionId)` → `DELETE /api/chat/sessions/{id}`

`POST /api/chat/stream` 不在 API 模块中，由 store 直接 `fetch` + `ReadableStream` 解析 SSE。

## Store (`src/stores/chat.ts`)

**移除**：`ws`, `connectionState`, `connect()`, `disconnect()`, `send()`, `scheduleReconnect()`, `WsConnectionState`, `onSessionCreated()`

**保留**：`sessions`, `messages`, `currentSessionId`, `streamingContent`, `isStreaming`, `currentMessages`

**新增**：`loading`, `error`, `init()`

**核心变更 — SSE 流式调用**：

```
sendMessage(content)
  → 无 session → newSession() 自动创建
  → messages 追加 user message
  → fetch POST /api/chat/stream
  → reader = response.body.getReader()
  → 逐 chunk 解码，按 \n 分割行
  → event: token  → streamingContent += data.content
  → event: done   → messages 追加完整 assistant message，fetchSessions()
  → event: error  → messages 追加错误消息
  → catch 异常   → messages 追加网络错误消息
```

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
