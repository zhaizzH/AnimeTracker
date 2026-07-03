import { defineStore } from 'pinia'
import { ref } from 'vue'
import type { ChatSession, ChatMessage } from '@/types'

export const useChatStore = defineStore('chat', () => {
  const sessions = ref<ChatSession[]>([])
  const currentSessionId = ref<string | null>(null)
  const messages = ref<ChatMessage[]>([])
  const isStreaming = ref(false)

  async function sendMessage(message: string) {
    // Phase 3 实现: SSE 流式发送
  }

  async function createSession() {
    // Phase 3 实现
  }

  async function listSessions() {
    // Phase 3 实现
  }

  async function deleteSession(sessionId: string) {
    // Phase 3 实现
  }

  return {
    sessions, currentSessionId, messages, isStreaming,
    sendMessage, createSession, listSessions, deleteSession,
  }
})
