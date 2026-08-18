import { useCallback, useEffect, useRef, useState } from 'react';
import { agentApi, streamSse, useAuthStore } from '@shared';

export interface ChatMsg { id: string; role: 'user' | 'assistant'; content: string }
const nextId = () => `${Date.now()}-${Math.random().toString(36).slice(2)}`;

export function useAgentChat() {
  const token = useAuthStore((s) => s.token);
  const [sessions, setSessions] = useState<Record<string, unknown>[]>([]);
  const [activeId, setActiveId] = useState<string | null>(null);
  const [messages, setMessages] = useState<ChatMsg[]>([]);
  const [health, setHealth] = useState<string>('checking');
  const [streaming, setStreaming] = useState(false);
  const ab = useRef<AbortController | null>(null);

  const refreshSessions = useCallback(() => agentApi.listSessions().then(setSessions).catch(() => {}), []);
  useEffect(() => { agentApi.health().then(setHealth).catch(() => setHealth('unavailable')); refreshSessions(); }, [refreshSessions]);

  const loadHistory = useCallback(async (id: string) => {
    const h = await agentApi.history(id).catch(() => []);
    setMessages((h as Array<{ role?: string; content?: string }>).map((m) => ({ id: nextId(), role: m.role === 'user' ? 'user' : 'assistant', content: String(m.content ?? '') })));
  }, []);

  const select = useCallback(async (id: string) => { setActiveId(id); await loadHistory(id); }, [loadHistory]);
  const create = useCallback(async () => {
    const s = await agentApi.createSession();
    await refreshSessions(); await select(String((s as { id?: unknown })?.id));
  }, [refreshSessions, select]);
  const remove = useCallback(async (id: string) => {
    await agentApi.deleteSession(id).catch(() => {});
    if (id === activeId) { setActiveId(null); setMessages([]); }
    refreshSessions();
  }, [activeId, refreshSessions]);

  const send = useCallback(async (text: string) => {
    if (!text.trim() || streaming) return;
    const userMsg: ChatMsg = { id: nextId(), role: 'user', content: text };
    setMessages((m) => [...m, userMsg]);
    const assistantId = nextId();
    setMessages((m) => [...m, { id: assistantId, role: 'assistant', content: '' }]);
    setStreaming(true);
    ab.current = new AbortController();
    try {
      await streamSse({ url: '/api/client/agent/stream', body: agentApi.streamBody(text, activeId ?? undefined), token, signal: ab.current.signal, onEvent: (data) => {
        if (data === '[DONE]') return;
        setMessages((m) => m.map((x) => (x.id === assistantId ? { ...x, content: x.content + data } : x)));
      } });
    } catch { setMessages((m) => m.map((x) => (x.id === assistantId && !x.content ? { ...x, content: '(流式中断，请重试)' } : x))); }
    finally { setStreaming(false); }
  }, [token, activeId, streaming]);

  const stop = useCallback(() => ab.current?.abort(), []);
  return { messages, sessions, activeId, health, streaming, send, stop, select, create, remove };
}
