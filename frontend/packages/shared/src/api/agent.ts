import { get, post } from './http';
export const health = () => get<string>('/client/agent/health');
export const listSessions = () => get<Record<string, unknown>[]>('/client/agent/sessions');
export const createSession = () => post<Record<string, unknown>>('/client/agent/sessions', {});
export const history = (sessionId: string) => get<Record<string, unknown>[]>(`/client/agent/sessions/${encodeURIComponent(sessionId)}/history`);
export const deleteSession = (sessionId: string) => post<void>(`/client/agent/sessions/${encodeURIComponent(sessionId)}/remove`);
// 流式 body 组装；字段与 Python ChatRequest(content/session_id) 对齐
export const streamBody = (message: string, sessionId?: string) => ({ content: message, ...(sessionId ? { session_id: sessionId } : {}) });

// ── chat run（重连/状态/停止）────────────────────────────────────────────
/** 某会话当前是否有 run 在跑；无 run → 404（调用方按异常处理）。 */
export const sessionRun = (sessionId: string) =>
  get<{ run_id: string; status: string }>(`/client/agent/sessions/${encodeURIComponent(sessionId)}/run`);
/** 逻辑停止：只标 cancelled + 封存，不打断底层节点。幂等。 */
export const stopRun = (runId: string) => post<void>(`/client/agent/runs/${encodeURIComponent(runId)}/stop`);
/** 重连同一 run；`after` 是已收到的事件帧数，不是 token 数。 */
export const runStreamUrl = (runId: string, after: number) =>
  `/api/client/agent/runs/${encodeURIComponent(runId)}/stream?after=${after}`;
