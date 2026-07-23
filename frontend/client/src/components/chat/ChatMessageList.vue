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
