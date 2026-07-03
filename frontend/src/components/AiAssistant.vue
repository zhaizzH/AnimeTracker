<script setup lang="ts">
import { ref } from 'vue'

const isOpen = ref(false)
const message = ref('')
const isStreaming = ref(false)

function toggle() {
  isOpen.value = !isOpen.value
}

function sendMessage() {
  if (!message.value.trim() || isStreaming.value) return
  // Phase 3 实现: 调用 chat store 发送消息
  isStreaming.value = true
  message.value = ''
}
</script>

<template>
  <!-- 浮动按钮 -->
  <button
    @click="toggle"
    class="fixed bottom-6 right-6 w-12 h-12 bg-indigo-600 text-white rounded-full shadow-lg hover:bg-indigo-700 flex items-center justify-center z-50"
  >
    <svg class="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
      <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M8 10h.01M12 10h.01M16 10h.01M9 16H5a2 2 0 01-2-2V6a2 2 0 012-2h14a2 2 0 012 2v8a2 2 0 01-2 2h-5l-5 5v-5z" />
    </svg>
  </button>

  <!-- 聊天窗口 -->
  <Transition name="slide">
    <div v-if="isOpen" class="fixed bottom-20 right-6 w-80 h-96 bg-white rounded-lg shadow-xl border flex flex-col z-50">
      <!-- 头部 -->
      <div class="flex items-center justify-between px-4 py-3 border-b bg-indigo-600 text-white rounded-t-lg">
        <span class="text-sm font-medium">AI 助手</span>
        <button @click="toggle" class="text-white/80 hover:text-white">
          <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12" />
          </svg>
        </button>
      </div>
      <!-- 消息区域 -->
      <div class="flex-1 overflow-y-auto p-3 space-y-3">
        <div class="text-xs text-center text-gray-400 py-4">
          AI 助手，帮你查询动漫信息
        </div>
      </div>
      <!-- 输入栏 -->
      <div class="border-t p-3 flex gap-2">
        <input
          v-model="message"
          placeholder="输入消息..."
          class="flex-1 text-sm border rounded px-2 py-1.5 focus:outline-none focus:border-indigo-400"
          @keyup.enter="sendMessage"
        />
        <button @click="sendMessage" class="text-sm bg-indigo-600 text-white px-3 py-1.5 rounded hover:bg-indigo-700 disabled:opacity-50" :disabled="isStreaming">
          发送
        </button>
      </div>
    </div>
  </Transition>
</template>

<style scoped>
.slide-enter-active, .slide-leave-active {
  transition: all 0.3s ease;
}
.slide-enter-from, .slide-leave-to {
  opacity: 0;
  transform: translateY(20px);
}
</style>
