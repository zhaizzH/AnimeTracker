import { get, post } from '../http';
import type { ModelConfigVO, ModelConfigViewVO, PromptVO } from '../../types';
export const prompts = () => get<PromptVO[]>('/admin/agent/prompts');
export const promptDetail = (key: string) => get<PromptVO>(`/admin/agent/prompts/${encodeURIComponent(key)}`);
export const promptUpdate = (key: string, d: { promptContent: string }) => post<PromptVO>(`/admin/agent/prompts/${encodeURIComponent(key)}/update`, d);
export const promptReset = (key: string) => post<void>(`/admin/agent/prompts/${encodeURIComponent(key)}/reset`);
// GET 返回生效值 + 逐字段来源；POST 只提交被修改的字段（稀疏），故入参仍是 ModelConfigVO。
export const config = () => get<ModelConfigViewVO>('/admin/agent/config');
export const configUpdate = (d: ModelConfigVO) => post<void>('/admin/agent/config/update', d);
export const chatSessions = () => get<Record<string, unknown>[]>('/admin/agent/chat/sessions');
export const chatCreateSession = () => post<Record<string, unknown>>('/admin/agent/chat/sessions', {});
export const chatHistory = (sessionId: string) => get<Record<string, unknown>[]>(`/admin/agent/chat/sessions/${encodeURIComponent(sessionId)}/history`);
export const chatDeleteSession = (sessionId: string) => post<void>(`/admin/agent/chat/sessions/${encodeURIComponent(sessionId)}/remove`);
export const chatStreamBody = (message: string, sessionId?: string) => ({ content: message, ...(sessionId ? { session_id: sessionId } : {}) });

// ── chat run（重连/状态/停止）────────────────────────────────────────────
export const chatSessionRun = (sessionId: string) =>
  get<{ run_id: string; status: string }>(`/admin/agent/chat/sessions/${encodeURIComponent(sessionId)}/run`);
export const chatStopRun = (runId: string) => post<void>(`/admin/agent/chat/runs/${encodeURIComponent(runId)}/stop`);
export const chatRunStreamUrl = (runId: string, after: number) =>
  `/api/admin/agent/chat/runs/${encodeURIComponent(runId)}/stream?after=${after}`;
