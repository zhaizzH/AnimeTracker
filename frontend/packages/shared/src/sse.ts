export interface StreamOptions {
  url: string;
  body: unknown;
  token: string | null;
  signal?: AbortSignal;
  onEvent: (data: string) => void;
}
export async function streamSse({ url, body, token, signal, onEvent }: StreamOptions): Promise<void> {
  const res = await fetch(url, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json', ...(token ? { Authorization: `Bearer ${token}` } : {}) },
    body: JSON.stringify(body),
    signal,
  });
  if (!res.ok || !res.body) throw new Error(`Agent 流式请求失败（${res.status}）`);
  const reader = res.body.getReader();
  const decoder = new TextDecoder();
  let buf = '';
  while (true) {
    const { done, value } = await reader.read();
    if (done) break;
    buf += decoder.decode(value, { stream: true });
    let idx: number;
    while ((idx = buf.indexOf('\n')) >= 0) {
      const line = buf.slice(0, idx).trim();
      buf = buf.slice(idx + 1);
      if (!line) continue;
      onEvent(line.startsWith('data:') ? line.slice(5).trim() : line);
    }
  }
}
