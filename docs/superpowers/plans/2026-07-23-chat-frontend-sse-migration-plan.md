# Chat 前端 SSE 迁移实施计划

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 将前端 Chat 模块从 WebSocket 通信迁移到 REST API + SSE 流

**Architecture:** 新建 `api/chat.ts` 封装 REST 调用，重写 `stores/chat.ts` 去掉 WebSocket 改用 `fetch` + `ReadableStream` 解析 SSE，各 chat 组件同步删除 WebSocket 状态依赖

**Tech Stack:** Vue 3 + Pinia + TypeScript + Fetch API (ReadableStream)

## Global Constraints

- Agent 服务 base URL 使用 `http://localhost:8090`（开发环境跨域）
- SSE 解析使用原生 `fetch` + `ReadableStream`，不引入额外依赖
- 所有 REST 调用自动带 `Authorization: Bearer <token>`
- 保留现有 store 对外接口（`sessions`, `messages`, `currentSessionId`, `currentMessages`, `sendMessage`, `newSession`, `fetchSessions`, `loadHistory`, `deleteSession`），上层组件只改 WebSocket 相关逻辑

---

### Task 1: 类型更新 + API 模块

**Files:**
- Modify: `frontend/client/src/types/index.ts` (lines 182-199)
- Create: `frontend/client/src/api/chat.ts`

**Interfaces:**
- Consumes: `ChatSession`, `ChatMessage` from types
- Produces: `chatApi` with `getSessions`, `createSession`, `getHistory`, `deleteSession`

- [ ] **Step 1: Update types/index.ts**

```typescript
// 替换 ChatMessage.tool_calls: string → string[] | null
export interface ChatMessage {
  id?: number
  role: 'user' | 'assistant'
  content: string
  tool_calls?: string[] | null  // changed from string
  created_at?: string
}

// 删除 WsConnectionState
// export type WsConnectionState = 'connecting' | 'connected' | 'disconnected' | 'error'  ← remove
```

- [ ] **Step 2: Create src/api/chat.ts**

```typescript
import type { ChatSession, ChatMessage } from '@/types'
import { useAuthStore } from '@/stores/auth'

const AGENT_BASE = 'http://localhost:8090'

async function authHeaders(): Promise<Record<string, string>> {
  const auth = useAuthStore()
  const headers: Record<string, string> = {}
  if (auth.token) headers['Authorization'] = `Bearer ${auth.token}`
  return headers
}

async function getSessions(): Promise<ChatSession[] | null> {
  try {
    const headers = await authHeaders()
    const res = await fetch(`${AGENT_BASE}/api/chat/sessions`, { headers })
    if (!res.ok) return null
    return await res.json()
  } catch { return null }
}

async function createSession(): Promise<{ session_id: string } | null> {
  try {
    const headers = await authHeaders()
    const res = await fetch(`${AGENT_BASE}/api/chat/sessions`, {
      method: 'POST',
      headers: { ...headers, 'Content-Type': 'application/json' },
      body: '{}',
    })
    if (!res.ok) return null
    return await res.json()
  } catch { return null }
}

async function getHistory(sessionId: string): Promise<ChatMessage[] | null> {
  try {
    const headers = await authHeaders()
    const res = await fetch(`${AGENT_BASE}/api/chat/sessions/${sessionId}/history`, { headers })
    if (!res.ok) return null
    return await res.json()
  } catch { return null }
}

async function deleteSession(sessionId: string): Promise<boolean> {
  try {
    const headers = await authHeaders()
    const res = await fetch(`${AGENT_BASE}/api/chat/sessions/${sessionId}`, {
      method: 'DELETE',
      headers,
    })
    return res.ok
  } catch { return false }
}

export const chatApi = { getSessions, createSession, getHistory, deleteSession }
```

- [ ] **Step 3: Commit**

```bash
git add frontend/client/src/types/index.ts frontend/client/src/api/chat.ts
git commit -m "feat(chat): 添加 chat API 模块，更新 ChatMessage 类型"
```

---

### Task 2: 重写 Chat Store（WebSocket → SSE）

**Files:**
- Rewrite: `frontend/client/src/stores/chat.ts`

**Interfaces:**
- Consumes: `chatApi` from `@/api/chat`, `ChatMessage`, `ChatSession` from `@/types`
- Produces: same store interface (`sessions`, `messages`, `currentSessionId`, `currentMessages`, `sendMessage`, `newSession`, `fetchSessions`, `loadHistory`, `deleteSession`, `init` + new `loading`, `error`)

- [ ] **Step 1: Rewrite stores/chat.ts**

```typescript
import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import type { ChatSession, ChatMessage } from '@/types'
import { chatApi } from '@/api/chat'
import { useAuthStore } from '@/stores/auth'

const AGENT_BASE = 'http://localhost:8090'

export const useChatStore = defineStore('chat', () => {
  const sessions = ref<ChatSession[]>([])
  const messages = ref<ChatMessage[]>([])
  const currentSessionId = ref<string | null>(null)
  const streamingContent = ref('')
  const isStreaming = ref(false)
  const loading = ref(false)
  const error = ref<string | null>(null)
  const initialized = ref(false)

  const currentMessages = computed(() => {
    if (streamingContent.value) {
      return [...messages.value, { role: 'assistant' as const, content: streamingContent.value }]
    }
    return messages.value
  })

  function init() {
    if (initialized.value) return
    initialized.value = true
    fetchSessions()
  }

  async function fetchSessions() {
    const result = await chatApi.getSessions()
    if (result) {
      sessions.value = result
    }
  }

  async function newSession(): Promise<string | null> {
    loading.value = true
    const result = await chatApi.createSession()
    loading.value = false
    if (!result) {
      error.value = '创建会话失败'
      return null
    }
    currentSessionId.value = result.session_id
    messages.value = []
    streamingContent.value = ''
    await fetchSessions()
    return result.session_id
  }

  async function loadHistory(sessionId: string) {
    currentSessionId.value = sessionId
    messages.value = []
    streamingContent.value = ''
    loading.value = true
    const result = await chatApi.getHistory(sessionId)
    loading.value = false
    if (result) {
      messages.value = result
    } else {
      error.value = '加载历史消息失败'
    }
  }

  async function deleteSession(sessionId: string) {
    loading.value = true
    const ok = await chatApi.deleteSession(sessionId)
    loading.value = false
    if (!ok) {
      error.value = '删除会话失败'
      return
    }
    if (currentSessionId.value === sessionId) {
      currentSessionId.value = null
      messages.value = []
      streamingContent.value = ''
    }
    await fetchSessions()
  }

  async function sendMessage(content: string) {
    if (isStreaming.value) return

    // Ensure session
    if (!currentSessionId.value) {
      const sid = await newSession()
      if (!sid) return
    }

    const auth = useAuthStore()
    if (!auth.token || !currentSessionId.value) return

    messages.value.push({ role: 'user', content })
    isStreaming.value = true
    streamingContent.value = ''
    error.value = null

    try {
      const response = await fetch(`${AGENT_BASE}/api/chat/stream`, {
        method: 'POST',
        headers: {
          'Authorization': `Bearer ${auth.token}`,
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          session_id: currentSessionId.value,
          content,
        }),
      })

      if (!response.ok) {
        const errMsg = response.status === 401 ? '登录已过期，请重新登录'
          : response.status === 404 ? '会话不存在'
          : '请求失败，请重试'
        messages.value.push({ role: 'assistant', content: `❌ ${errMsg}` })
        isStreaming.value = false
        streamingContent.value = ''
        return
      }

      const reader = response.body!.getReader()
      const decoder = new TextDecoder()
      let buffer = ''

      while (true) {
        const { done, value } = await reader.read()
        if (done) break

        buffer += decoder.decode(value, { stream: true })
        const lines = buffer.split('\n')
        buffer = lines.pop() || ''

        let eventType = ''
        for (const line of lines) {
          if (line.startsWith('event: ')) {
            eventType = line.slice(7).trim()
          } else if (line.startsWith('data: ')) {
            const dataStr = line.slice(6)
            try {
              if (eventType === 'token') {
                const data = JSON.parse(dataStr)
                streamingContent.value += data.content || ''
              } else if (eventType === 'error') {
                const data = JSON.parse(dataStr)
                messages.value.push({ role: 'assistant', content: `❌ ${data.message}` })
                isStreaming.value = false
                streamingContent.value = ''
              } else if (eventType === 'done') {
                messages.value.push({ role: 'assistant', content: streamingContent.value })
                streamingContent.value = ''
                isStreaming.value = false
                fetchSessions()
              }
              // event: metadata → ignored
            } catch { /* skip malformed JSON */ }
          }
        }
      }
      // Guard: 流结束但没收到 done event
      if (isStreaming.value) {
        messages.value.push({ role: 'assistant', content: streamingContent.value })
        streamingContent.value = ''
        isStreaming.value = false
        fetchSessions()
      }
    } catch (e) {
      console.error('sendMessage error:', e)
      if (!isStreaming.value) {
        messages.value.push({ role: 'assistant', content: '❌ 网络错误，请检查连接后重试' })
      } else {
        isStreaming.value = false
        streamingContent.value = ''
      }
    }
  }

  return {
    sessions, messages, currentSessionId,
    streamingContent, isStreaming, loading, error, currentMessages,
    init, fetchSessions, newSession, loadHistory, deleteSession, sendMessage,
  }
})
```

- [ ] **Step 2: Commit**

```bash
git add frontend/client/src/stores/chat.ts
git commit -m "feat(chat): 重写 Chat Store，WebSocket 迁移到 SSE+REST"
```

---

### Task 3: 更新 Chat 组件

**Files:**
- Modify: `frontend/client/src/components/chat/ChatWidget.vue`
- Modify: `frontend/client/src/components/chat/ChatInput.vue`
- Modify: `frontend/client/src/components/chat/ChatMessageList.vue`
- Modify: `frontend/client/src/components/chat/ChatSessionList.vue`

**Interfaces:**
- Consumes: store from `useChatStore()` with new `init()`, removed `connect()/disconnect()`, removed `connectionState`

- [ ] **Step 1: Update ChatWidget.vue**

```vue
<script setup lang="ts">
import { ref } from 'vue'
import { useChatStore } from '@/stores/chat'
import ChatSessionList from './ChatSessionList.vue'
import ChatMessageList from './ChatMessageList.vue'
import ChatInput from './ChatInput.vue'

const store = useChatStore()
const open = ref(false)
const showSessions = ref(true)

function toggle() {
  open.value = !open.value
  if (open.value) store.init()
}
</script>

<template>
  <!-- FAB -->
  <button
    class="fixed bottom-6 right-6 z-50 w-14 h-14 rounded-full shadow-xl flex items-center justify-center text-2xl transition-transform duration-200 hover:scale-105 active:scale-95"
    style="background: var(--color-primary); color: #fff; box-shadow: 0 4px 20px rgba(0,0,0,0.15);"
    @click="toggle"
  >
    {{ open ? '✕' : '💬' }}
  </button>

  <!-- Panel -->
  <Transition
    enter-active-class="transition duration-200 ease-out"
    enter-from-class="opacity-0 scale-95"
    enter-to-class="opacity-100 scale-100"
    leave-active-class="transition duration-150 ease-in"
    leave-from-class="opacity-100 scale-100"
    leave-to-class="opacity-0 scale-95"
  >
    <div
      v-if="open"
      class="fixed bottom-24 right-6 z-50 w-[720px] max-w-[calc(100vw-2rem)] h-[600px] max-h-[calc(100vh-8rem)] rounded-2xl shadow-2xl flex overflow-hidden"
      style="background: var(--color-card); border: 1px solid var(--color-border);"
    >
      <!-- Session sidebar -->
      <div v-if="showSessions" class="w-52 shrink-0 hidden md:block">
        <ChatSessionList />
      </div>

      <!-- Main chat area -->
      <div class="flex-1 flex flex-col min-w-0">
        <!-- Top bar -->
        <div class="flex items-center justify-between px-4 py-2.5 border-b shrink-0" style="border-color: var(--color-border);">
          <button
            v-if="store.currentSessionId"
            class="text-xs px-2 py-1 rounded-md transition-colors md:hidden"
            style="background: var(--color-hover); color: var(--color-text-secondary);"
            @click="showSessions = !showSessions"
          >
            ☰
          </button>
          <span class="text-sm font-semibold" style="color: var(--color-text);">
            AI 追番助手
          </span>
        </div>

        <!-- Messages -->
        <ChatMessageList />

        <!-- Input -->
        <ChatInput />
      </div>
    </div>
  </Transition>
</template>
```

- [ ] **Step 2: Update ChatInput.vue** — 将 `store.connectionState !== 'connected'` 替换为 `store.isStreaming`

```vue
<script setup lang="ts">
import { ref } from 'vue'
import { useChatStore } from '@/stores/chat'

const store = useChatStore()
const input = ref('')
const quickQuestions = [
  '推荐这季度热门番',
  '今晚有什么更新',
  '评分最高的番是哪些',
  '推荐几部热血战斗番',
]

function send() {
  const text = input.value.trim()
  if (!text || store.isStreaming) return
  store.sendMessage(text)
  input.value = ''
}

function sendQuick(q: string) {
  if (store.isStreaming) return
  store.sendMessage(q)
}
</script>

<template>
  <div class="border-t px-4 py-3 shrink-0" style="border-color: var(--color-border); background: var(--color-card);">
    <!-- Quick questions -->
    <div v-if="store.messages.length === 0 && !store.isStreaming" class="flex flex-wrap gap-1.5 mb-3">
      <button
        v-for="q in quickQuestions" :key="q"
        class="text-[11px] px-2.5 py-1.5 rounded-full transition-colors"
        style="background: var(--color-hover); color: var(--color-text-secondary);"
        @click="sendQuick(q)"
      >
        {{ q }}
      </button>
    </div>

    <!-- Input row -->
    <div class="flex items-center gap-2">
      <input
        v-model="input" type="text" placeholder="输入你想问的..."
        class="flex-1 px-4 py-2.5 rounded-xl text-sm outline-none transition-all"
        :style="{ background: 'var(--color-bg)', color: 'var(--color-text)', border: '1px solid var(--color-border)' }"
        @keyup.enter="send"
        :disabled="store.isStreaming"
      />
      <button
        class="shrink-0 w-9 h-9 rounded-full flex items-center justify-center transition-colors"
        :style="{ background: store.isStreaming ? 'var(--color-hover)' : 'var(--color-primary)', color: store.isStreaming ? 'var(--color-text-secondary)' : '#fff' }"
        @click="send"
        :disabled="!input.trim() || store.isStreaming"
      >
        <span class="text-sm">{{ store.isStreaming ? '···' : '➤' }}</span>
      </button>
    </div>
  </div>
</template>
```

- [ ] **Step 3: Update ChatMessageList.vue** — 删除连接状态相关代码

```vue
<script setup lang="ts">
import { ref, watch, nextTick, computed } from 'vue'
import { useChatStore } from '@/stores/chat'
import { marked } from 'marked'

marked.setOptions({ breaks: true })

const store = useChatStore()
const container = ref<HTMLElement | null>(null)

watch(
  () => store.currentMessages.length + store.streamingContent.length,
  async () => {
    await nextTick()
    if (container.value) {
      container.value.scrollTop = container.value.scrollHeight
    }
  },
  { flush: 'post' }
)

const isEmpty = computed(() => store.currentMessages.length === 0 && !store.isStreaming)

function formatRole(role: string) {
  return role === 'assistant' ? '🤖 AI' : '👤 我'
}

function isStreamingLast(idx: number) {
  return idx === store.currentMessages.length - 1 && store.isStreaming
}
</script>

<template>
  <div ref="container" class="flex-1 overflow-y-auto p-4 space-y-4 scroll-smooth" style="min-height: 0;">
    <!-- Empty state -->
    <div v-if="isEmpty" class="flex flex-col items-center justify-center h-full text-center py-8">
      <div class="text-4xl mb-3">🎌</div>
      <h3 class="text-lg font-semibold mb-2" style="color: var(--color-text);">AI 追番助手</h3>
      <p class="text-sm mb-4" style="color: var(--color-text-secondary);">问我关于番剧的任何问题</p>
    </div>

    <!-- Messages -->
    <div
      v-for="(msg, idx) in store.currentMessages" :key="idx"
      class="flex" :class="msg.role === 'user' ? 'justify-end' : 'justify-start'"
    >
      <div
        class="max-w-[85%] rounded-2xl px-4 py-2.5"
        :style="{
          background: msg.role === 'user' ? 'var(--color-primary)' : 'var(--color-card)',
          color: msg.role === 'user' ? '#fff' : 'var(--color-text)',
          border: msg.role === 'user' ? 'none' : '1px solid var(--color-border)',
        }"
      >
        <div class="text-[11px] opacity-60 mb-1">{{ formatRole(msg.role) }}</div>
        <div v-if="isStreamingLast(idx)" class="text-sm whitespace-pre-wrap break-words leading-relaxed">
          {{ msg.content }}<span class="inline-block w-1.5 h-4 ml-0.5 animate-pulse rounded-sm" style="background: var(--color-text);" />
        </div>
        <div v-else class="text-sm break-words leading-relaxed prose prose-sm max-w-none" v-html="marked.parse(msg.content)" />
      </div>
    </div>
  </div>
</template>
```

- [ ] **Step 4: Update ChatSessionList.vue** — 去掉 `connectionState` 相关的 disabled

```vue
<script setup lang="ts">
import { useChatStore } from '@/stores/chat'

const store = useChatStore()

function selectSession(sessionId: string) {
  store.loadHistory(sessionId)
}

function confirmDelete(sessionId: string, event: MouseEvent) {
  event.stopPropagation()
  if (confirm('确定删除该会话？')) {
    store.deleteSession(sessionId)
  }
}

function formatDate(dateStr: string): string {
  if (!dateStr) return ''
  const d = new Date(dateStr.replace(' ', 'T') + 'Z')
  const now = new Date()
  const diff = now.getTime() - d.getTime()
  if (diff < 86400000) return d.toLocaleTimeString('zh-CN', { hour: '2-digit', minute: '2-digit' })
  if (diff < 604800000) return `${Math.floor(diff / 86400000)}天前`
  return d.toLocaleDateString('zh-CN', { month: 'short', day: 'numeric' })
}
</script>

<template>
  <div class="flex flex-col h-full" style="background: var(--color-card); border-right: 1px solid var(--color-border);">
    <!-- Header -->
    <div class="flex items-center justify-between px-4 py-3 border-b shrink-0" style="border-color: var(--color-border);">
      <h3 class="text-sm font-semibold" style="color: var(--color-text);">会话</h3>
      <button
        class="text-xs px-3 py-1.5 rounded-full font-medium transition-colors"
        style="background: var(--color-primary); color: #fff;"
        @click="store.newSession()"
      >
        + 新对话
      </button>
    </div>

    <!-- Session list -->
    <div class="flex-1 overflow-y-auto py-2 px-2 space-y-0.5">
      <div v-if="store.sessions.length === 0" class="text-center py-8 text-xs" style="color: var(--color-text-secondary);">
        暂无会话记录
      </div>
      <button
        v-for="s in store.sessions" :key="s.session_id"
        class="flex items-center gap-2 w-full px-3 py-2.5 rounded-xl text-left text-sm transition-colors duration-150"
        :style="{
          background: s.session_id === store.currentSessionId ? 'var(--color-hover)' : 'transparent',
          color: 'var(--color-text)',
        }"
        @click="selectSession(s.session_id)"
      >
        <span class="text-base shrink-0">💬</span>
        <div class="flex-1 min-w-0">
          <div class="text-sm truncate">{{ s.title || '新对话' }}</div>
          <div class="text-[11px] mt-0.5" style="color: var(--color-text-secondary);">
            {{ s.message_count }} 条消息 · {{ formatDate(s.updated_at || s.created_at) }}
          </div>
        </div>
        <span
          class="shrink-0 w-6 h-6 flex items-center justify-center rounded-full text-xs cursor-pointer opacity-0 group-hover:opacity-100 hover:bg-red-100 hover:text-red-500 transition-all"
          style="color: var(--color-text-secondary);"
          @click.stop="confirmDelete(s.session_id, $event)"
        >
          ✕
        </span>
      </button>
    </div>
  </div>
</template>
```

- [ ] **Step 5: Commit**

```bash
git add frontend/client/src/components/chat/ChatWidget.vue frontend/client/src/components/chat/ChatInput.vue frontend/client/src/components/chat/ChatMessageList.vue frontend/client/src/components/chat/ChatSessionList.vue
git commit -m "feat(chat): 更新 Chat 组件，移除 WebSocket 状态依赖"
```

---

## Self-Review Checklist

1. **Spec coverage:** All spec items covered:
   - API 模块 → Task 1
   - Store 重写（SSE 流式调用、currentSessionId 流转、错误处理）→ Task 2
   - 类型调整、WsConnectionState 移除 → Task 1
   - ChatWidget/ChatInput/ChatMessageList/ChatSessionList 组件更新 → Task 3

2. **Placeholder scan:** No TODOs, TBDs, or "implement later" patterns. All code blocks are complete.

3. **Type consistency:** `tool_calls` changed everywhere: type definition (`string[] | null`) → store (uses from API response) → components (no rendering change needed). `init()` defined in store, called in ChatWidget. No `connectionState` references remain in any component.
