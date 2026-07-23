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
