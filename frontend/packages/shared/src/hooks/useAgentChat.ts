import { useCallback, useEffect, useRef, useState } from 'react';
import { useAuthStore } from '../store/auth';
import { streamSse } from '../sse';

export interface ChatMsg { id: string; role: 'user' | 'assistant'; content: string; thinking?: string }
export interface ToolStep { name: string; status: 'running' | 'done'; message?: string }
const nextId = () => `${Date.now()}-${Math.random().toString(36).slice(2)}`;

interface SsePayload {
  type?: string;
  is_end?: boolean;
  content?: { text?: string; name?: string; state?: string; message?: string };
}

function parseEvent(data: string): SsePayload | null {
  try { return JSON.parse(data) as SsePayload; } catch { return null; }
}

export interface AgentChatApi {
  listSessions: () => Promise<Record<string, unknown>[]>;
  createSession: () => Promise<Record<string, unknown>>;
  history: (id: string) => Promise<Record<string, unknown>[]>;
  deleteSession: (id: string) => Promise<void>;
  streamBody: (message: string, sessionId?: string) => Record<string, unknown>;
  streamUrl: string;
  health?: () => Promise<string>;
}

export function useAgentChat(api: AgentChatApi, { enabled = true }: { enabled?: boolean } = {}) {
  const token = useAuthStore((s) => s.token);
  const [sessions, setSessions] = useState<Record<string, unknown>[]>([]);
  const [activeId, setActiveId] = useState<string | null>(null);
  const [messages, setMessages] = useState<ChatMsg[]>([]);
  const [tools, setTools] = useState<ToolStep[]>([]);
  const [health, setHealth] = useState<string>('n/a');
  const [streaming, setStreaming] = useState(false);
  const [ready, setReady] = useState(false);
  const ab = useRef<AbortController | null>(null);
  const historyRequest = useRef(0);
  useEffect(() => () => ab.current?.abort(), []);
  // api 为调用方内联对象，引用不稳定；用 ref 保持挂载期只跑一次 effect，与旧 client 行为一致。
  // ponytail: 若日后需要响应 api 变化，可去掉 ref。
  const apiRef = useRef(api);
  apiRef.current = api;

  const refreshSessions = useCallback(() => apiRef.current.listSessions()
    .then((list) => {
      const normalized = list.map((s) => ({ ...s, id: (s as { session_id?: unknown }).session_id ?? (s as { id?: unknown }).id }));
      setSessions(normalized);
      return normalized;
    })
    .catch(() => []), []);

  const loadHistory = useCallback(async (id: string) => {
    const request = ++historyRequest.current;
    setReady(false);
    const h = await apiRef.current.history(id).catch(() => []);
    if (request !== historyRequest.current) return false;
    setMessages((h as Array<{ role?: string; content?: string }>).map((m) => ({ id: nextId(), role: m.role === 'user' ? 'user' : 'assistant', content: String(m.content ?? '') })));
    return true;
  }, []);

  const select = useCallback(async (id: string) => {
    setActiveId(id);
    if (await loadHistory(id)) setReady(true);
  }, [loadHistory]);
  const create = useCallback(async () => {
    setReady(false);
    const s = await apiRef.current.createSession();
    await refreshSessions();
    const id = String((s as { session_id?: unknown })?.session_id ?? (s as { id?: unknown })?.id ?? '');
    await select(id);
  }, [refreshSessions, select]);

  useEffect(() => {
    if (!enabled) return;
    if (apiRef.current.health) apiRef.current.health().then((h) => setHealth(typeof h === 'string' ? h : String((h as { status?: unknown })?.status ?? 'n/a'))).catch(() => setHealth('unavailable'));
    // 后端已按 updated_at 倒序返回；默认选中最近会话，没有则自动新建
    void (async () => {
      const list = await refreshSessions();
      if (list.length > 0) await select(String(list[0].id));
      else await create();
    })().catch(() => {});
  }, [enabled, refreshSessions, select, create]);
  const remove = useCallback(async (id: string) => {
    await apiRef.current.deleteSession(id).catch(() => {});
    if (id === activeId) {
      historyRequest.current += 1;
      setActiveId(null);
      setMessages([]);
      // 删除当前会话后自动新建，避免"已连接但无会话"时 UI 悬挂在连接提示
      await create();
    } else {
      refreshSessions();
    }
  }, [activeId, refreshSessions, create]);

  const send = useCallback(async (text: string) => {
    if (!ready || !text.trim() || streaming) return;
    let sessionId = activeId;
    // 未选中会话时自动新建, 否则 /stream 会因缺 session_id 返回 404
    if (!sessionId) {
      const s = await apiRef.current.createSession();
      sessionId = String((s as { session_id?: unknown })?.session_id ?? (s as { id?: unknown })?.id ?? '');
      if (sessionId) { setActiveId(sessionId); refreshSessions(); }
    }
    const userMsg: ChatMsg = { id: nextId(), role: 'user', content: text };
    setMessages((m) => [...m, userMsg]);
    const assistantId = nextId();
    setMessages((m) => [...m, { id: assistantId, role: 'assistant', content: '' }]);
    setTools([]);
    setStreaming(true);
    ab.current = new AbortController();
    try {
      await streamSse({ url: apiRef.current.streamUrl, body: apiRef.current.streamBody(text, sessionId || undefined), token, signal: ab.current.signal, onEvent: (data) => {
        const ev = parseEvent(data);
        if (!ev) return;
        if (ev.is_end) return;
        const c = ev.content ?? {};
        if (ev.type === 'thinking' && c.text) {
          // thinking 挂在对应 assistant 消息上，随消息一起渲染在其上方
          setMessages((m) => m.map((x) => (x.id === assistantId ? { ...x, thinking: (x.thinking ?? '') + c.text! } : x)));
        }
        else if (ev.type === 'function_call' && c.name) {
          if (c.state === 'end') setTools((ts) => ts.map((t) => (t.name === c.name ? { ...t, status: 'done', message: c.message } : t)));
          else if (c.state === 'start') setTools((ts) => (ts.some((t) => t.name === c.name) ? ts : [...ts, { name: c.name!, status: 'running', message: c.message }]));
        }
        else if (c.text) setMessages((m) => m.map((x) => (x.id === assistantId ? { ...x, content: x.content + c.text! } : x)));
      } });
    } catch { setMessages((m) => m.map((x) => (x.id === assistantId && !x.content ? { ...x, content: '(流式中断，请重试)' } : x))); }
    finally { setStreaming(false); void refreshSessions(); }
  }, [token, activeId, streaming, ready, refreshSessions]);

  const stop = useCallback(() => ab.current?.abort(), []);
  return { messages, sessions, activeId, health, streaming, ready, tools, send, stop, select, create, remove };
}
