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
};
