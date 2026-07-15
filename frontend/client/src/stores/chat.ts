import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import type { ChatSession, ChatMessage, WsConnectionState } from '@/types'
import { useAuthStore } from '@/stores/auth'

const WS_URL = 'ws://localhost:8090/ws/chat'

export const useChatStore = defineStore('chat', () => {
  const connectionState = ref<WsConnectionState>('disconnected')
  const sessions = ref<ChatSession[]>([])
  const messages = ref<ChatMessage[]>([])
  const currentSessionId = ref<string | null>(null)
  const streamingContent = ref('')
  const isStreaming = ref(false)

  let ws: WebSocket | null = null
  let reconnectTimer: ReturnType<typeof setTimeout> | null = null

  const currentMessages = computed(() => {
    if (streamingContent.value) {
      // 追加一条临时的 assistant 消息展示流式内容，不覆盖用户消息
      return [...messages.value, { role: 'assistant' as const, content: streamingContent.value }]
    }
    return messages.value
  })

  function connect() {
    const auth = useAuthStore()
    if (!auth.token) return

    connectionState.value = 'connecting'
    const token = encodeURIComponent(auth.token)
    ws = new WebSocket(`${WS_URL}?token=${token}`)

    ws.onopen = () => {
      connectionState.value = 'connected'
      fetchSessions()
    }

    ws.onmessage = (event) => {
      const data = JSON.parse(event.data)
      handleMessage(data)
    }

    ws.onclose = () => {
      connectionState.value = 'disconnected'
      scheduleReconnect()
    }

    ws.onerror = () => {
      connectionState.value = 'error'
      ws?.close()
    }
  }

  function scheduleReconnect() {
    if (reconnectTimer) clearTimeout(reconnectTimer)
    reconnectTimer = setTimeout(() => {
      if (connectionState.value === 'disconnected') {
        connect()
      }
    }, 3000)
  }

  function disconnect() {
    if (reconnectTimer) clearTimeout(reconnectTimer)
    ws?.close()
    ws = null
    connectionState.value = 'disconnected'
    sessions.value = []
    messages.value = []
    currentSessionId.value = null
    streamingContent.value = ''
    isStreaming.value = false
  }

  function handleMessage(data: any) {
    switch (data.type) {
      case 'token':
        isStreaming.value = true
        streamingContent.value += data.content || ''
        break

      case 'done':
        if (isStreaming.value) {
          // 流式完成，追加完整消息
          messages.value.push({
            role: 'assistant',
            content: data.full_content || streamingContent.value,
            tool_calls: data.tool_calls?.join(', '),
          })
          streamingContent.value = ''
          isStreaming.value = false
        }
        // 如果是 new_session 或 delete_session 的响应，刷新列表
        fetchSessions()
        break

      case 'error':
        messages.value.push({
          role: 'assistant',
          content: `❌ ${data.message}`,
        })
        isStreaming.value = false
        streamingContent.value = ''
        break

      case 'session_list':
        sessions.value = data.sessions || []
        break

      case 'history':
        messages.value = (data.messages || []).map((m: any) => ({
          role: m.role,
          content: m.content,
          tool_calls: m.tool_calls,
        }))
        break

      case 'ping':
        send({ type: 'pong' })
        break
    }
  }

  function send(data: any) {
    if (ws?.readyState === WebSocket.OPEN) {
      ws.send(JSON.stringify(data))
    }
  }

  function sendMessage(content: string) {
    if (!currentSessionId.value) {
      newSession()
    }
    messages.value.push({ role: 'user', content })
    send({ type: 'message', session_id: currentSessionId.value, content })
  }

  function newSession() {
    send({ type: 'new_session' })
  }

  function fetchSessions() {
    send({ type: 'list_sessions' })
  }

  function loadHistory(sessionId: string) {
    currentSessionId.value = sessionId
    messages.value = []
    streamingContent.value = ''
    send({ type: 'load_history', session_id: sessionId })
  }

  function deleteSession(sessionId: string) {
    if (currentSessionId.value === sessionId) {
      currentSessionId.value = null
      messages.value = []
    }
    send({ type: 'delete_session', session_id: sessionId })
  }

  // 处理 new_session 响应中的 session_id
  function onSessionCreated(sessionId: string) {
    currentSessionId.value = sessionId
    messages.value = []
    streamingContent.value = ''
  }

  return {
    connectionState, sessions, messages, currentSessionId,
    streamingContent, isStreaming, currentMessages,
    connect, disconnect, sendMessage, newSession,
    fetchSessions, loadHistory, deleteSession, onSessionCreated,
  }
})
