import http from './client';

export const agentApi = {
  health: () => http.get('/agent/health'),
  sessions: () => http.get('/agent/sessions'),
  createSession: () => http.post('/agent/sessions'),
  history: (sessionId: string) => http.get(`/agent/sessions/${sessionId}/history`),
  removeSession: (sessionId: string) => http.post(`/agent/sessions/${sessionId}`),
};
