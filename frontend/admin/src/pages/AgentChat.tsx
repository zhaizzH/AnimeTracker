import { useEffect, useRef, useState } from 'react';
import ReactMarkdown from 'react-markdown';
import { adminAgentApi, useAgentChat, type ChatMsg } from '@shared';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';

function ThinkingCollapse({ text, streaming }: { text: string; streaming: boolean }) {
  const [open, setOpen] = useState(true);
  // 回答完成后自动收起；流式期间保持展开（保留 antd Collapse 版行为）
  useEffect(() => { if (!streaming) setOpen(false); }, [streaming]);
  return (
    <div className="mb-2">
      <button
        type="button"
        aria-expanded={open}
        className="text-xs text-muted-foreground underline-offset-2 hover:underline"
        onClick={() => setOpen((o) => !o)}
      >
        思考过程
      </button>
      {open && (
        <p className="mt-1 whitespace-pre-wrap text-xs text-muted-foreground">{text}</p>
      )}
    </div>
  );
}

export default function AgentChat() {
  const api = {
    listSessions: adminAgentApi.chatSessions,
    createSession: adminAgentApi.chatCreateSession,
    history: adminAgentApi.chatHistory,
    deleteSession: adminAgentApi.chatDeleteSession,
    streamBody: adminAgentApi.chatStreamBody,
    streamUrl: '/api/admin/agent/chat/stream',
  };
  const { messages, sessions, activeId, streaming, send, stop, select, create, remove } = useAgentChat(api);
  const [input, setInput] = useState('');
  const scrollRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    const el = scrollRef.current;
    if (el) el.scrollTop = el.scrollHeight;
  }, [messages]);

  const submit = () => {
    if (!input.trim() || streaming) return;
    send(input);
    setInput('');
  };

  const renderItem = (m: ChatMsg) => (
    <div key={m.id} className={m.role === 'user' ? 'mb-3 text-right' : 'mb-3 text-left'}>
      {m.thinking && <ThinkingCollapse text={m.thinking} streaming={streaming} />}
      <div
        className={`inline-block max-w-[80%] rounded-lg px-3 py-2 text-left ${
          m.role === 'user' ? 'bg-primary/10' : 'bg-muted'
        }`}
      >
        <ReactMarkdown>{m.content}</ReactMarkdown>
      </div>
    </div>
  );

  return (
    <div className="flex h-[calc(100vh-120px)]">
      <aside className="flex w-[240px] shrink-0 flex-col border-r">
        <Button className="m-3" onClick={create}>新建会话</Button>
        <ul className="flex-1 overflow-auto">
          {sessions.map((s: Record<string, unknown>) => {
            const id = String(s.id);
            return (
              <li
                key={id}
                className={`flex cursor-pointer items-center gap-2 px-3 py-2 text-sm ${id === activeId ? 'bg-muted' : ''}`}
                onClick={() => select(id)}
              >
                <span className="flex-1 truncate">
                  {String((s as { title?: unknown }).title ?? (s as { id?: unknown }).id)}
                </span>
                {activeId === id && (
                  // 阻止冒泡，避免触发外层会话选择
                  <Button
                    size="sm"
                    variant="destructive"
                    onClick={(e) => { e.stopPropagation(); remove(id); }}
                  >
                    删
                  </Button>
                )}
              </li>
            );
          })}
        </ul>
      </aside>

      <section className="flex min-w-0 flex-1 flex-col p-4">
        <div ref={scrollRef} className="mb-3 flex-1 overflow-auto" aria-live="polite">
          {messages.map(renderItem)}
        </div>
        <div className="flex w-full gap-2">
          <Input
            placeholder="输入消息…"
            aria-label="输入消息"
            value={input}
            onChange={(e) => setInput(e.target.value)}
            onKeyDown={(e) => { if (e.key === 'Enter') { e.preventDefault(); submit(); } }}
            disabled={streaming}
          />
          <Button
            variant={streaming ? 'destructive' : 'default'}
            disabled={!streaming && !input.trim()}
            onClick={streaming ? stop : submit}
          >
            {streaming ? '停止' : '发送'}
          </Button>
        </div>
      </section>
    </div>
  );
}
