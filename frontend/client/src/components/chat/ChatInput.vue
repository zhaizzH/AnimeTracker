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
  if (!text || store.isStreaming || store.connectionState !== 'connected') return
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
        v-for="q in quickQuestions"
        :key="q"
        class="text-[11px] px-2.5 py-1.5 rounded-full transition-colors"
        style="background: var(--color-hover); color: var(--color-text-secondary);"
        @click="sendQuick(q)"
        :disabled="store.connectionState !== 'connected'"
      >
        {{ q }}
      </button>
    </div>

    <!-- Input row -->
    <div class="flex items-center gap-2">
      <input
        v-model="input"
        type="text"
        placeholder="输入你想问的..."
        class="flex-1 px-4 py-2.5 rounded-xl text-sm outline-none transition-all"
        :style="{
          background: 'var(--color-bg)',
          color: 'var(--color-text)',
          border: '1px solid var(--color-border)',
        }"
        @keyup.enter="send"
        :disabled="store.connectionState !== 'connected'"
      />
      <button
        class="shrink-0 w-9 h-9 rounded-full flex items-center justify-center transition-colors"
        :style="{
          background: store.isStreaming ? 'var(--color-hover)' : 'var(--color-primary)',
          color: store.isStreaming ? 'var(--color-text-secondary)' : '#fff',
        }"
        @click="send"
        :disabled="!input.trim() || store.connectionState !== 'connected'"
      >
        <span class="text-sm">{{ store.isStreaming ? '···' : '➤' }}</span>
      </button>
    </div>
  </div>
</template>
