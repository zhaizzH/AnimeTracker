<script setup lang="ts">
import { ref, watch, onUnmounted } from 'vue'
import { useChatStore } from '@/stores/chat'
import ChatSessionList from './ChatSessionList.vue'
import ChatMessageList from './ChatMessageList.vue'
import ChatInput from './ChatInput.vue'

const store = useChatStore()
const open = ref(false)
const showSessions = ref(true)

function toggle() {
  open.value = !open.value
  if (open.value) {
    store.connect()
  } else {
    store.disconnect()
  }
}

// 监听 new_session 响应，设置 currentSessionId
watch(
  () => store.sessions.length,
  (_, old) => {
    if (old === 0 && store.sessions.length > 0) {
      // 新建会话后自动选中最新的
      const latest = store.sessions[0]
      store.loadHistory(latest.session_id)
    }
  }
)

// 当收到 done 且没有 currentSessionId 时（new_session 响应）
watch(
  () => store.messages.length,
  (n, prev) => {
    // 如果消息从 0 变为 1 且是 new_session 响应，检查 session_id
    if (n === 1 && prev === 0 && store.currentSessionId === null) {
      store.fetchSessions()
    }
  }
)

function confirmDelete() {
  if (!store.currentSessionId) return
  if (confirm('确定删除当前对话？')) {
    store.deleteSession(store.currentSessionId)
  }
}

onUnmounted(() => {
  store.disconnect()
})
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

  <!-- Panel overlay -->
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
          <div class="flex items-center gap-2">
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
            <span
              class="w-2 h-2 rounded-full"
              :style="{
                background: store.connectionState === 'connected' ? '#22c55e'
                  : store.connectionState === 'connecting' ? '#f59e0b'
                  : '#ef4444'
              }"
            />
          </div>
          <span class="text-[11px]" style="color: var(--color-text-secondary);">
            {{ store.connectionState === 'connected' ? '已连接' : store.connectionState === 'connecting' ? '连接中...' : '已断开' }}
          </span>
          <button
            v-if="store.currentSessionId"
            class="text-xs px-2 py-1 rounded-md transition-colors hover:bg-red-100 hover:text-red-500"
            style="color: var(--color-text-secondary);"
            title="删除当前对话"
            @click="confirmDelete()"
          >
            🗑
          </button>
        </div>

        <!-- Messages -->
        <ChatMessageList />

        <!-- Input -->
        <ChatInput />
      </div>
    </div>
  </Transition>
</template>
