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
