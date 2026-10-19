export interface StreamOptions {
  url: string;
  body: unknown;
  token: string | null;
  signal?: AbortSignal;
  onEvent: (data: string) => void;
}

/** 传输/协议层故障：非 2xx、Content-Type 不符、读流失败。 */
export class SseError extends Error {
  status?: number;
  contentType?: string | null;

  constructor(message: string, options: { status?: number; contentType?: string | null } = {}) {
    super(message);
    this.name = 'SseError';
    this.status = options.status;
    this.contentType = options.contentType;
  }
}

/** 调用方主动 abort（用户点停止 / 组件卸载），不是故障。 */
export class SseAbortError extends Error {
  constructor() {
    super('SSE 流已取消');
    this.name = 'SseAbortError';
  }
}

/** 从一帧原始文本里取出 data 负载：多行 `data:` 按 SSE 规范以换行拼接，无前缀则整帧即负载。 */
function frameToData(frame: string): string {
  const lines = frame.split(/\r?\n/);
  const dataLines = lines.filter((line) => line.startsWith('data:'));
  if (dataLines.length === 0) return frame.trim();
  return dataLines.map((line) => line.slice(5).replace(/^ /, '')).join('\n');
}

export async function streamSse({ url, body, token, signal, onEvent }: StreamOptions): Promise<void> {
  try {
    const res = await fetch(url, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json', ...(token ? { Authorization: `Bearer ${token}` } : {}) },
      body: JSON.stringify(body),
      signal,
    });

    if (!res.ok) {
      // 响应提交前的错误是普通 JSON 体，读出来便于定位；不把整段 body 塞进 message。
      const detail = await res.text().catch(() => '');
      throw new SseError(`Agent 流式请求失败（${res.status}）${detail ? `：${detail.slice(0, 200)}` : ''}`, {
        status: res.status,
        contentType: res.headers.get('content-type'),
      });
    }

    const contentType = res.headers.get('content-type');
    if (!contentType?.includes('text/event-stream')) {
      // 2xx 但不是流：多为反向代理/网关返回的错误页，按协议故障处理。
      throw new SseError(`Agent 流式响应不是 event-stream（Content-Type: ${contentType ?? '缺失'}）`, {
        status: res.status,
        contentType,
      });
    }

    if (!res.body) throw new SseError('Agent 流式响应缺少响应体', { status: res.status, contentType });

    const reader = res.body.getReader();
    const decoder = new TextDecoder();
    let buf = '';

    // SSE 以空行分帧，不按单换行切分——单换行只是帧内的行分隔。
    const drain = (flushTail: boolean) => {
      let idx: number;
      while ((idx = buf.search(/\r?\n\r?\n/)) >= 0) {
        const frame = buf.slice(0, idx);
        buf = buf.slice(idx + buf.slice(idx).match(/^\r?\n\r?\n/)![0].length);
        const data = frameToData(frame);
        if (data) onEvent(data);
      }
      if (flushTail && buf.trim()) {
        // 上游未按空行收尾时兜住最后一帧，避免 tail 帧丢失。
        const data = frameToData(buf);
        buf = '';
        if (data) onEvent(data);
      }
    };

    while (true) {
      const { done, value } = await reader.read();
      if (done) break;
      buf += decoder.decode(value, { stream: true });
      drain(false);
    }
    buf += decoder.decode();
    drain(true);
  } catch (err) {
    // abort 判据只用 signal 状态：AbortError 的 name 在各环境不一致。
    if (signal?.aborted) throw new SseAbortError();
    if (err instanceof SseError) throw err;
    throw new SseError(err instanceof Error ? err.message : String(err));
  }
}
