import { get, post } from './http';
export const health = () => get<string>('/client/agent/health');
export const listSessions = () => get<Record<string, unknown>[]>('/client/agent/sessions');
export const createSession = () => post<Record<string, unknown>>('/client/agent/sessions', {});
export const history = (sessionId: string) => get<Record<string, unknown>[]>(`/client/agent/sessions/${encodeURIComponent(sessionId)}/history`);
export const deleteSession = (sessionId: string) => post<void>(`/client/agent/sessions/${encodeURIComponent(sessionId)}/remove`);
// 流式 body 组装；Python 期望字段以 backend/agent 实现为准
export const streamBody = (message: string, sessionId?: string) => ({ message, ...(sessionId ? { sessionId } : {}) });
