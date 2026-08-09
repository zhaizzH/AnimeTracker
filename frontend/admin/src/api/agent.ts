import http from './client';
import type {
  AgentHealthVO,
  AgentModelConfig,
  AgentPrompt,
  PromptUpdateDTO,
} from '../types/api';

export const agentApi = {
  health: () => http.get<AgentHealthVO>('/client/agent/health'),
  prompts: () => http.get<AgentPrompt[]>('/admin/agent/prompts'),
  prompt: (key: string) => http.get<AgentPrompt>(`/admin/agent/prompts/${key}`),
  updatePrompt: (key: string, data: PromptUpdateDTO) =>
    http.post<AgentPrompt>(`/admin/agent/prompts/${key}/update`, data),
  resetPrompt: (key: string) => http.post<AgentPrompt>(`/admin/agent/prompts/${key}/reset`),
  config: () => http.get<AgentModelConfig>('/admin/agent/config'),
  updateConfig: (data: AgentModelConfig) =>
    http.post<AgentModelConfig>('/admin/agent/config/update', data),
  adminSessions: () => http.get('/admin/agent/chat/sessions'),
  adminCreateSession: () => http.post('/admin/agent/chat/sessions'),
  adminHistory: (sessionId: string) =>
    http.get(`/admin/agent/chat/sessions/${sessionId}/history`),
  adminRemoveSession: (sessionId: string) =>
    http.post(`/admin/agent/chat/sessions/${sessionId}/remove`),
  /** SSE 流式对话：不走 axios（拦截器解包且无法流式），直接 fetch 返回原生 Response */
  adminStream: (sessionId: string, content: string, accessToken: string) =>
    fetch('/api/admin/agent/chat/stream', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'Authorization': `Bearer ${accessToken}`,
      },
      body: JSON.stringify({ session_id: sessionId, content }),
    }),
};
