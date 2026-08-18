import { useCallback, useEffect, useRef, useState } from 'react';
import { useAuthStore } from '../store/auth';
import { streamSse } from '../sse';

export interface ChatMsg { id: string; role: 'user' | 'assistant'; content: string }
const nextId = () => `${Date.now()}-${Math.random().toString(36).slice(2)}`;

export interface AgentChatApi {
  listSessions: () => Promise<Record<string, unknown>[]>;
  createSession: () => Promise<Record<string, unknown>>;
  history: (id: string) => Promise<Record<string, unknown>[]>;
  deleteSession: (id: string) => Promise<void>;
  streamBody: (message: string, sessionId?: string) => Record<string, unknown>;
  streamUrl: string;
  health?: () => Promise<string>;
}

export function useAgentChat(api: AgentChatApi) {
  const token = useAuthStore((s) => s.token);
  const [sessions, setSessions] = useState<Record<string, unknown>[]>([]);
  const [activeId, setActiveId] = useState<string | null>(null);
  const [messages, setMessages] = useState<ChatMsg[]>([]);
  const [health, setHealth] = useState<string>('n/a');
  const [streaming, setStreaming] = useState(false);
  const ab = useRef<AbortController | null>(null);
  // api 为调用方内联对象，引用不稳定；用 ref 保持挂载期只跑一次 effect，与旧 client 行为一致。
  // ponytail: 若日后需要响应 api 变化，可去掉 ref。
  const apiRef = useRef(api);
  apiRef.current = api;

  const refreshSessions = useCallback(() => apiRef.current.listSessions().then(setSessions).catch(() => {}), []);
  useEffect(() => {
    if (apiRef.current.health) apiRef.current.health().then(setHealth).catch(() => setHealth('unavailable'));
    refreshSessions();
  }, [refreshSessions]);

  const loadHistory = useCallback(async (id: string) => {
    const h = await apiRef.current.history(id).catch(() => []);
    setMessages((h as Array<{ role?: string; content?: string }>).map((m) => ({ id: nextId(), role: m.role === 'user' ? 'user' : 'assistant', content: String(m.content ?? '') })));
  }, []);

  const select = useCallback(async (id: string) => { setActiveId(id); await loadHistory(id); }, [loadHistory]);
  const create = useCallback(async () => {
    const s = await apiRef.current.createSession();
    await refreshSessions(); await select(String((s as { id?: unknown })?.id));
  }, [refreshSessions, select]);
  const remove = useCallback(async (id: string) => {
    await apiRef.current.deleteSession(id).catch(() => {});
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
      await streamSse({ url: apiRef.current.streamUrl, body: apiRef.current.streamBody(text, activeId ?? undefined), token, signal: ab.current.signal, onEvent: (data) => {
        if (data === '[DONE]') return;
        setMessages((m) => m.map((x) => (x.id === assistantId ? { ...x, content: x.content + data } : x)));
      } });
    } catch { setMessages((m) => m.map((x) => (x.id === assistantId && !x.content ? { ...x, content: '(流式中断，请重试)' } : x))); }
    finally { setStreaming(false); }
  }, [token, activeId, streaming]);

  const stop = useCallback(() => ab.current?.abort(), []);
  return { messages, sessions, activeId, health, streaming, send, stop, select, create, remove };
}
