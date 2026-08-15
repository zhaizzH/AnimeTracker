import http from './client';

export const agentApi = {
  sessions: () => http.get('/client/agent/sessions'),
  createSession: () => http.post('/client/agent/sessions'),
  history: (sessionId: string) => http.get(`/client/agent/sessions/${sessionId}/history`),
  removeSession: (sessionId: string) => http.post(`/client/agent/sessions/${sessionId}/remove`),
  /** SSE 流式对话：不走 axios（拦截器解包且无法流式），直接 fetch 返回原生 Response */
  stream: (sessionId: string, content: string, accessToken: string) =>
    fetch('/api/client/agent/stream', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'Authorization': `Bearer ${accessToken}`,
      },
      body: JSON.stringify({ session_id: sessionId, content }),
    }),
};
