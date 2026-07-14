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
  const d = new Date(dateStr.replace(' ', 'T'))
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
        :disabled="store.connectionState !== 'connected'"
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
        v-for="s in store.sessions"
        :key="s.session_id"
        class="flex items-center gap-2 w-full px-3 py-2.5 rounded-xl text-left text-sm transition-colors duration-150"
        :class="s.session_id === store.currentSessionId ? '' : ''"
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
