import { useCallback, useEffect, useRef, useState } from 'react';
import { useAuthStore } from '../store/auth';
import { SseAbortError, SseError, streamSse } from '../sse';
import { asRunConflict, type RunConflict } from '../api/conflict';

export interface ChatMsg { id: string; role: 'user' | 'assistant'; content: string; thinking?: string }
export interface ToolStep { name: string; status: 'running' | 'done' | 'error'; message?: string }

/** 发送被 409 拒绝时的选择态：`text` 是未发出的原文，任选项都不会丢。 `error` 是停止失败的内联原因。 */
export interface SendConflict extends RunConflict { text: string; error?: string }
/** 停不掉活跃 run 就不能重发：重发必然再 409，面板会连环弹。 */
const STOP_FAILED = '无法打断当前回答，请稍后重试';
export type ConflictChoice = 'interrupt' | 'wait' | 'cancel';
const nextId = () => `${Date.now()}-${Math.random().toString(36).slice(2)}`;

interface SsePayload {
  type?: string;
  is_end?: boolean;
  meta?: { run_id?: string };
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
  const [conflict, setConflict] = useState<SendConflict | null>(null);
  const ab = useRef<AbortController | null>(null);
  // 当前 run 的身份，来自首帧 meta.run_id；用 ref 而非 state（首帧高频，无需重渲染）。
  const runId = useRef<string | null>(null);
  const historyRequest = useRef(0);
  // 冲突选择的同步锁：`setConflict(null)` 是异步 state，双击会两次读到旧 conflict。
  const resolving = useRef(false);
  // 在途回放订阅的世代号：切会话时递增，旧订阅的迟到帧一律丢弃。
  const replaySeq = useRef(0);
  useEffect(() => () => ab.current?.abort(), []);
  // api 为调用方内联对象，引用不稳定；用 ref 保持挂载期只跑一次 effect，与旧 client 行为一致。
  // ponytail: 若日后需要响应 api 变化，可去掉 ref。
  const apiRef = useRef(api);
  apiRef.current = api;
  const tokenRef = useRef(token);
  tokenRef.current = token;

  // 一次性提示（流中断、内容过期、状态未知）走 notice，由两端各自转成 toast：
  // 写成 assistant 消息会污染会话历史，而且刷新后消失得莫名其妙。
  const [notice, setNotice] = useState<{ text: string } | null>(null);
  const addNotice = useCallback((text: string) => {
    // 每次都是新对象：同一条文案连续出现两次也要各弹一次 toast。
    setNotice({ text });
  }, []);
  // 「上次回答未完成」是会话级状态而非一次性事件：它来自 run 的 failed 懒收敛，
  // 用户刷新后仍应看到，所以留在页面里而不是 toast。
  const [runFailed, setRunFailed] = useState(false);

  /** 单条订阅的帧分发：实时与回放共用同一套事件白名单和同一把 is_end 锁。 */
  const makeOnEvent = useCallback((targetId: string) => {
    // 结束锁用局部对象而非 state：state 置位有渲染延迟，脏帧会在空窗期漏进来。
    const ended = { current: false };
    const dispatch = (ev: SsePayload) => {
      if (ended.current) return;
      if (ev.meta?.run_id) runId.current = ev.meta.run_id;
      if (ev.is_end) { ended.current = true; runId.current = null; return; }
      const c = ev.content ?? {};
      // 只认白名单四类事件；曾经用 `c.text` 兜底，导致 status/function_call 的 message 污染正文。
      switch (ev.type) {
        case 'thinking':
          // thinking 挂在对应 assistant 消息上，随消息一起渲染在其上方
          if (c.text) setMessages((m) => m.map((x) => (x.id === targetId ? { ...x, thinking: (x.thinking ?? '') + c.text! } : x)));
          break;
        case 'answer':
          if (c.text) setMessages((m) => m.map((x) => (x.id === targetId ? { ...x, content: x.content + c.text! } : x)));
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
            setMessages((m) => m.map((x) => (x.id === targetId ? { ...x, content: `${x.content}${x.content ? '\n\n' : ''}${c.message}` } : x)));
          } else if (c.state === 'warning') {
            // 回放缓存的游标已被缓冲上限截断：后端先发 warning 再跳过旧帧，静默丢弃会让人以为内容完整。
            addNotice(c.message || '(部分实时内容已过期，完整回答见历史)');
          }
          break;
        default:
          // 其它未登记类型不渲染，避免误落正文。
          break;
      }
    };
    // 每帧只解析一次：回放包装器需要看 warn 帧，若自己再 parse 一遍就是双重 JSON.parse。
    const onEvent = (data: string) => {
      const ev = parseEvent(data);
      if (ev) dispatch(ev);
    };
    return { ended, onEvent, dispatch };
  }, [addNotice]);

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

  /** 订阅某 run 并从头回放；不阻塞 select（订阅可能活到 run 结束）。 */
  const replayRun = useCallback(async (runIdNow: string, seq: number) => {
    // 回放会重推全量事件：必须新开空气泡，复用 loadHistory 写的历史气泡会把正文拼两遍。
    const assistantId = nextId();
    setMessages((m) => [...m, { id: assistantId, role: 'assistant', content: '' }]);
    runId.current = runIdNow;
    setStreaming(true);
    const ac = new AbortController();
    ab.current = ac;
    // 游标是「已收到的事件帧数」，与文本长度、token 数无关。
    let frames = 0;
    const { ended, dispatch } = makeOnEvent(assistantId);
    // 收到截断降级帧后 after 已经无法与后端 buffer_start 对齐，续订只会重放已收帧 → 不再续订。
    let truncated = false;
    try {
      // 最多续订一次：流正常结束却没收到 is_end，说明中间层掐断了回放。
      for (let attempt = 0; attempt < 2; attempt += 1) {
        try {
          await streamSse({ url: apiRef.current.runStreamUrl(runIdNow, frames), method: 'GET', token: tokenRef.current, signal: ac.signal, onEvent: (data) => {
            if (seq !== replaySeq.current) return;
            const ev = parseEvent(data);
            if (!ev) return;
            frames += 1;
            // 截断降级帧意味着后端缓冲已丢过头，after 不再能对齐 buffer_start：放弃续订，别再重放已收帧。
            if (ev.type === 'status' && ev.content?.state === 'warning') truncated = true;
            dispatch(ev);
          } });
        } catch (err) {
          if (err instanceof SseAbortError) {
            // 只收掉还没写进任何内容的空气泡；已有正文若被删，用户点停止会把答案抹掉。
            if (seq === replaySeq.current) setMessages((m) => m.filter((x) => !(x.id === assistantId && !x.content)));
            return;
          }
          const unauthorized = err instanceof SseError && (err.status === 401 || err.status === 403);
          if (seq === replaySeq.current) addNotice(unauthorized ? '(未认证或无权限，请重新登录)' : '(流式中断，请重试)');
          return;
        }
        if (ac.signal.aborted || ended.current || truncated) return;
      }
    } finally {
      // 世代号变了说明已经在别的会话里，别把它的 streaming 状态清掉。
      if (seq === replaySeq.current) { runId.current = null; setStreaming(false); }
      // 回放结束后该 run 已落库，会话列表的排序/标题要跟着更新（切走会话就不必再刷）。
      if (seq === replaySeq.current) void refreshSessions();
    }
  }, [makeOnEvent, addNotice, refreshSessions]);

  const select = useCallback(async (id: string) => {
    setActiveId(id);
    setRunFailed(false);
    // 冲突面板属于上一个会话的发送尝试，切会话就作废。
    setConflict(null);
    // 切会话先掐掉在途订阅：否则旧 run 的迟到帧会写进新会话的气泡。
    replaySeq.current += 1;
    const seq = replaySeq.current;
    ab.current?.abort();
    ab.current = null;
    runId.current = null;
    // 旧订阅已掐掉；它的 finally 因世代号变化不会再清 streaming，这里负责收尾。
    setStreaming(false);
    // 工具步骤属于上一条 run，跟着切会话一起清，否则会残留在新会话的工具栏。
    setTools([]);
    if (!(await loadHistory(id))) return;
    setReady(true);
    // 无 run 时后端 404，按「没有进行中的 run」处理；其它失败（401/500/网络）不能装作没有 run，
    // 否则用户会以为回答还在、其实回放根本没接上。
    const state = await apiRef.current.sessionRun(id).catch((err: unknown) => {
      if ((err as { status?: number } | null)?.status !== 404 && seq === replaySeq.current) {
        addNotice('(无法确认回答状态，请刷新)');
      }
      return null;
    });
    if (seq !== replaySeq.current || !state) return;
    if (state.status === 'failed') {
      // 进程重启后 running 会被懒收敛成 failed，后端不补写消息：历史里没有这条回答，只能靠提示告知。
      setRunFailed(true);
      return;
    }
    if (state.status !== 'running' || !state.run_id) return;

    void replayRun(state.run_id, seq);
  }, [loadHistory, replayRun]);
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
    setConflict(null);
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
    // 新回答开始，上一条 failed run 不再是「最近一条」，横幅要收起来（文案否则是假的）。
    setRunFailed(false);
    setStreaming(true);
    runId.current = null;
    const myAb = new AbortController();
    ab.current = myAb;
    const { onEvent } = makeOnEvent(assistantId);
    try {
      await streamSse({ url: apiRef.current.streamUrl, body: apiRef.current.streamBody(text, sessionId || undefined), token, signal: ab.current.signal, onEvent });
    } catch (err) {
      const rejected = asRunConflict(err);
      if (rejected) {
        // 后端拒绝并发：收起两条气泡（含空气泡），把原文交还调用方让用户选。
        setMessages((m) => m.filter((x) => x.id !== userMsg.id && x.id !== assistantId));
        setConflict({ ...rejected, text });
      }
      // 主动停止是正常路径，不写中断文案；鉴权失败单独提示，别混进通用故障。
      else if (!(err instanceof SseAbortError)) {
        const unauthorized = err instanceof SseError && (err.status === 401 || err.status === 403);
        const notice = unauthorized ? '(未认证或无权限，请重新登录)' : '(流式中断，请重试)';
        setMessages((m) => m.map((x) => (x.id === assistantId && !x.content ? { ...x, content: notice } : x)));
      }
    }
    // 只有当前请求仍是拥有者时才收尾：切到另一个有 running run 的会话时，回放已经接管
    // ab.current / streaming / run_id，旧 send 的 finally 不能把它们清掉。
    finally {
      if (ab.current === myAb) { runId.current = null; setStreaming(false); }
      void refreshSessions();
    }
  }, [token, activeId, streaming, ready, refreshSessions, makeOnEvent]);

  // 顺序不能反：先 abort 会让后端把断连当掉线，run 继续烧 token。
  // run_id 未到达时只 abort——此时后端还没有 run 可停，排队/重试都没有意义。
  const stop = useCallback(async () => {
    const id = runId.current;
    if (id) {
      try { await apiRef.current.stopRun(id); }
      catch (err) { console.warn('[useAgentChat] 停 run 失败，仍断开本地连接', id, err); }
    }
    ab.current?.abort();
  }, []);
  /**
   * 处理 409 选择：interrupt = 先停活跃 run，停成功才重发同一段文本；
   * wait / cancel 都不发请求。缺 active_run_id 时没有可停的 run，按取消处理。
   * 同一次尝试只跑一遍（同步锁）；stop 失败时保留面板与原文，只写回内联错误。
   */
  const resolveConflict = useCallback(async (choice: ConflictChoice) => {
    if (resolving.current) return;
    const current = conflict;
    if (!current) return;
    resolving.current = true;
    try {
      if (choice !== 'interrupt' || !current.activeRunId) { setConflict(null); return; }
      // 用户原地重试：先清掉上一次的内联错误，否则按钮看着像没反应。
      if (current.error) setConflict({ ...current, error: undefined });
      try { await apiRef.current.stopRun(current.activeRunId); }
      catch (err) {
        // 活跃 run 还在：重发必然再 409 → 面板重开成循环。原位保留，让用户重试。
        console.warn('[useAgentChat] 停活跃 run 失败，保留冲突面板', current.activeRunId, err);
        setConflict({ ...current, error: STOP_FAILED });
        return;
      }
      setConflict(null);
      // 不 await：重发会一直跑到 run 结束，面板点击不能被它挂住。
      void send(current.text);
    } finally {
      resolving.current = false;
    }
  }, [conflict, send]);

  return { messages, sessions, activeId, health, streaming, ready, tools, conflict, notice, runFailed, send, stop, select, create, remove, resolveConflict };
}
