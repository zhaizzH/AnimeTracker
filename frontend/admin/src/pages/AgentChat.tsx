import { useEffect, useRef, useState } from 'react';
import ReactMarkdown from 'react-markdown';
import { adminAgentApi, useAgentChat, type ChatMsg } from '@shared';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { toastWarning } from '@/lib/toast';

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
    sessionRun: adminAgentApi.chatSessionRun,
    stopRun: adminAgentApi.chatStopRun,
    runStreamUrl: adminAgentApi.chatRunStreamUrl,
  };
  const { messages, sessions, activeId, streaming, send, stop, select, create, remove, conflict, notice, runFailed, resolveConflict } = useAgentChat(api);
  const [input, setInput] = useState('');
  const scrollRef = useRef<HTMLDivElement>(null);
  // 一次性提示（流中断 / 内容过期 / 状态未知）弹 toast：它们是事件，不该写进会话历史。
  useEffect(() => {
    if (notice) toastWarning(notice.text);
  }, [notice]);

  // 409 时后端没接受这条消息（气泡已收回）：原文放回输入框，用户不会丢字。
  // error 更新（停 run 失败/重试）不是新一次尝试，不能再回填，否则会覆盖用户正在编辑的内容。
  useEffect(() => {
    if (conflict && !conflict.error) setInput(conflict.text);
  }, [conflict]);

  useEffect(() => {
    const el = scrollRef.current;
    if (el) el.scrollTop = el.scrollHeight;
  }, [messages]);

  // capabilities 缺失（null）是「不知道」，只有显式不含 interrupt 才禁用。
  const interruptBlocked = conflict?.capabilities?.includes('interrupt') === false;

  const submit = () => {
    if (!input.trim() || streaming || conflict) return;
    send(input);
    setInput('');
  };

  // 停止并发送=原文已重发，清空输入框；等待/取消都保留原文（已由冲突 effect 回填）。
  // 没有 activeRunId 或 capabilities 不含 interrupt 时该按钮是 disabled 的，所以这里不需要再判空。
  const choose = (choice: 'interrupt' | 'wait' | 'cancel') => {
    if (choice === 'interrupt') setInput('');
    void resolveConflict(choice);
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
        {runFailed && (
          <p role="status" className="mb-2 rounded-lg border bg-muted/60 px-3 py-2 text-xs text-muted-foreground">
            上次回答未完成，完整回答见历史
          </p>
        )}
        <div ref={scrollRef} className="mb-3 flex-1 overflow-auto" aria-live="polite">
          {messages.map(renderItem)}
        </div>
        {conflict && (
          <div role="group" aria-label="会话已有回答在生成" className="mb-3 flex flex-wrap items-center gap-2 rounded-lg border bg-muted/50 p-2 text-sm">
            <span className="text-muted-foreground">这个会话还有一条回答正在生成</span>
            {/* title 必须挂在外层 span：disabled 的 button 在 Chrome/Safari 不派发 hover，提示看不到。 */}
            <span title={interruptBlocked ? '当前无法打断' : undefined}>
              <Button
                type="button"
                size="sm"
                disabled={!conflict.activeRunId || interruptBlocked}
                onClick={() => choose('interrupt')}
              >
                停止并发送
              </Button>
            </span>
            <Button type="button" size="sm" variant="outline" onClick={() => choose('wait')}>等待</Button>
            <Button type="button" size="sm" variant="ghost" onClick={() => choose('cancel')}>取消</Button>
            {conflict.error && <p role="alert" className="basis-full text-destructive">{conflict.error}</p>}
          </div>
        )}
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
