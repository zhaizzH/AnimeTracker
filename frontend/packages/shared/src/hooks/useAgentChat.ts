import { useCallback, useEffect, useRef, useState } from 'react';
import { useAuthStore } from '../store/auth';
import { SseAbortError, SseError, streamSse } from '../sse';

export interface ChatMsg { id: string; role: 'user' | 'assistant'; content: string; thinking?: string }
export interface ToolStep { name: string; status: 'running' | 'done' | 'error'; message?: string }
const nextId = () => `${Date.now()}-${Math.random().toString(36).slice(2)}`;

interface SsePayload {
  type?: string;
  is_end?: boolean;
  content?: { text?: string; name?: string; state?: string; message?: string; result?: string };
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
  /** 某会话当前 run 状态；无 run 时后端 404。 */
  sessionRun: (id: string) => Promise<{ run_id: string; status: string }>;
  /** 逻辑停止当前 run（不打断底层节点），幂等。 */
  stopRun: (runId: string) => Promise<void>;
  /** 重连订阅地址；after 是已收到的事件帧数。 */
  runStreamUrl: (runId: string, after: number) => string;
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
      // 删当前会话后优先选中列表里最接近的会话；仅当无会话可时才新建，
      // 避免删一个非末尾会话也凭空多出一个空会话。
      const list = await refreshSessions();
      if (list.length > 0) await select(String(list[0].id));
      else await create();
    } else {
      refreshSessions();
    }
  }, [activeId, refreshSessions, select, create]);

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
    // 结束锁用局部对象而非 state：state 置位有渲染延迟，脏帧会在空窗期漏进来。
    const ended = { current: false };
    try {
      await streamSse({ url: apiRef.current.streamUrl, body: apiRef.current.streamBody(text, sessionId || undefined), token, signal: ab.current.signal, onEvent: (data) => {
        if (ended.current) return;
        const ev = parseEvent(data);
        if (!ev) return;
        if (ev.is_end) { ended.current = true; return; }
        const c = ev.content ?? {};
        // 只认白名单四类事件；曾经用 `c.text` 兜底，导致 status/function_call 的 message 污染正文。
        switch (ev.type) {
          case 'thinking':
            // thinking 挂在对应 assistant 消息上，随消息一起渲染在其上方
            if (c.text) setMessages((m) => m.map((x) => (x.id === assistantId ? { ...x, thinking: (x.thinking ?? '') + c.text! } : x)));
            break;
          case 'answer':
            if (c.text) setMessages((m) => m.map((x) => (x.id === assistantId ? { ...x, content: x.content + c.text! } : x)));
            break;
          case 'function_call':
            if (!c.name) break;
            // 失败不以 state=error 表达：后端用 state=end + result=error（middleware.py emit_function_call）。
            // state=error 只出现在 status 事件上，别把两者混成一条判据。
            if (c.state === 'end') {
              const failed = c.result === 'error';
              setTools((ts) => ts.map((t) => (t.name === c.name ? { ...t, status: failed ? 'error' : 'done', message: c.message } : t)));
            }
            else if (c.state === 'start') setTools((ts) => (ts.some((t) => t.name === c.name) ? ts : [...ts, { name: c.name!, status: 'running', message: c.message }]));
            break;
          case 'status':
            // status 不写正文；但 state=error 的 message 是后端给用户看的持久化失败提示（回答/待确认动作
            // 保存失败），丢弃会让用户以为一切正常，因此非空时追加到当前 assistant 消息尾部。
            if (c.state === 'error' && c.message) {
              setMessages((m) => m.map((x) => (x.id === assistantId ? { ...x, content: `${x.content}${x.content ? '\n\n' : ''}${c.message}` } : x)));
            }
            break;
          default:
            // 其它未登记类型不渲染，避免误落正文。
            break;
        }
      } });
    } catch (err) {
      // 主动停止是正常路径，不写中断文案；鉴权失败单独提示，别混进通用故障。
      if (!(err instanceof SseAbortError)) {
        const unauthorized = err instanceof SseError && (err.status === 401 || err.status === 403);
        const notice = unauthorized ? '(未认证或无权限，请重新登录)' : '(流式中断，请重试)';
        setMessages((m) => m.map((x) => (x.id === assistantId && !x.content ? { ...x, content: notice } : x)));
      }
    }
    finally { setStreaming(false); void refreshSessions(); }
  }, [token, activeId, streaming, ready, refreshSessions]);

  const stop = useCallback(() => ab.current?.abort(), []);
  return { messages, sessions, activeId, health, streaming, ready, tools, send, stop, select, create, remove };
}
