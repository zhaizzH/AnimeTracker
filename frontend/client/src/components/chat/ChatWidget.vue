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
