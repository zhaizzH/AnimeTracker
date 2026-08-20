import { get, post } from './http';
export const health = () => get<string>('/client/agent/health');
export const listSessions = () => get<Record<string, unknown>[]>('/client/agent/sessions');
export const createSession = () => post<Record<string, unknown>>('/client/agent/sessions', {});
export const history = (sessionId: string) => get<Record<string, unknown>[]>(`/client/agent/sessions/${encodeURIComponent(sessionId)}/history`);
export const deleteSession = (sessionId: string) => post<void>(`/client/agent/sessions/${encodeURIComponent(sessionId)}/remove`);
// 流式 body 组装；字段与 Python ChatRequest(content/session_id) 对齐
export const streamBody = (message: string, sessionId?: string) => ({ content: message, ...(sessionId ? { session_id: sessionId } : {}) });
