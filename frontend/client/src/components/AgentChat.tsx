import { createContext, type ReactNode, useCallback, useContext, useEffect, useRef, useState } from 'react';
import { toast } from 'sonner';
import { ChevronRightIcon } from 'lucide-react';
import { agentApi, type ChatMsg, useAgentChat } from '@shared';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Collapsible, CollapsibleContent, CollapsibleTrigger } from '@/components/ui/collapsible';
import { cn } from '@/lib/utils';
import AgentMarkdown from './AgentMarkdown';

const clientAgentApi = {
  listSessions: agentApi.listSessions,
  createSession: agentApi.createSession,
  history: agentApi.history,
  deleteSession: agentApi.deleteSession,
  streamBody: agentApi.streamBody,
  streamUrl: '/api/client/agent/stream',
  sessionRun: agentApi.sessionRun,
  stopRun: agentApi.stopRun,
  runStreamUrl: agentApi.runStreamUrl,
  health: agentApi.health,
};

type AgentChatState = ReturnType<typeof useAgentChat>;
interface AgentChatContextValue {
  activate: () => void;
  chat: AgentChatState;
}

const AgentChatContext = createContext<AgentChatContextValue | null>(null);

export function AgentChatProvider({ children }: { children: ReactNode }) {
  const [enabled, setEnabled] = useState(false);
  const chat = useAgentChat(clientAgentApi, { enabled });
  const activate = useCallback(() => setEnabled(true), []);
  // 一次性提示在这里消费：provider 随布局常驻，而对话面板会随路由重挂载——
  // 把 effect 放在面板里，离开再回来会把同一条旧提示再弹一次。
  useEffect(() => {
    if (chat.notice) toast.warning(chat.notice.text);
  }, [chat.notice]);
  return <AgentChatContext.Provider value={{ activate, chat }}>{children}</AgentChatContext.Provider>;
}

export function useClientAgentChat() {
  const value = useContext(AgentChatContext);
  if (!value) throw new Error('useClientAgentChat must be used inside AgentChatProvider');
  return value;
}

function ThinkingCollapse({ text, streaming }: { text: string; streaming: boolean }) {
  const [open, setOpen] = useState(true);
  useEffect(() => {
    if (!streaming) setOpen(false);
  }, [streaming]);
  return (
    <Collapsible open={open} onOpenChange={setOpen} className="mb-1">
      <CollapsibleTrigger className="flex items-center gap-1 text-xs text-muted-foreground hover:text-foreground">
        <ChevronRightIcon className={cn('size-3.5 transition-transform', open && 'rotate-90')} />
        思考过程
      </CollapsibleTrigger>
      <CollapsibleContent className="pt-1 text-xs whitespace-pre-wrap text-muted-foreground">{text}</CollapsibleContent>
    </Collapsible>
  );
}

export function AgentConversation() {
  const { activate, chat } = useClientAgentChat();
  const { messages, activeId, health, streaming, ready, send, stop, conflict, runFailed, resolveConflict } = chat;
  const [input, setInput] = useState('');
  const scrollRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    activate();
  }, [activate]);
  // 409 时后端没接受这条消息（气泡已收回）：原文放回输入框，用户不会丢字。
  // error 更新（停 run 失败/重试）不是新一次尝试，不能再回填，否则会覆盖用户正在编辑的内容。
  useEffect(() => {
    if (conflict && !conflict.error) setInput(conflict.text);
  }, [conflict]);
  useEffect(() => {
    const el = scrollRef.current;
    if (el) el.scrollTop = el.scrollHeight;
  }, [messages]);

  const prevHealth = useRef(health);
  useEffect(() => {
    if (health === 'unavailable' && prevHealth.current !== 'unavailable') {
      toast.warning('AI 助手连接失败，请检查服务');
    }
    prevHealth.current = health;
  }, [health]);

  const interruptBlocked = conflict?.capabilities?.includes('interrupt') === false;

  const submit = () => {
    if (!ready || !input.trim() || streaming || !activeId || conflict) return;
    void send(input);
    setInput('');
  };

  // 停止并发送=原文已重发，清空输入框；等待/取消都保留原文（已由冲突 effect 回填）。
  // 没有 activeRunId 或 capabilities 不含 interrupt 时该按钮是 disabled 的，所以这里不需要再判空。
  const choose = (choice: 'interrupt' | 'wait' | 'cancel') => {
    if (choice === 'interrupt') setInput('');
    void resolveConflict(choice);
  };

  const renderMessage = (message: ChatMsg) => (
    <div
      key={message.id}
      className={cn(
        'rounded-lg px-3 py-2 text-sm',
        message.role === 'user' ? 'ml-auto max-w-[85%] bg-primary text-primary-foreground' : 'mr-auto max-w-[95%] bg-muted',
      )}
    >
      {message.thinking && <ThinkingCollapse text={message.thinking} streaming={streaming} />}
      {message.role === 'assistant' && !message.content ? (
        <span className="text-muted-foreground">思考中…</span>
      ) : (
        <AgentMarkdown>{message.content}</AgentMarkdown>
      )}
    </div>
  );

  return (
    <section className="flex min-h-0 flex-1 flex-col" aria-label="AI 对话">
      {runFailed && (
        <p role="status" className="border-b bg-muted/60 px-3 py-2 text-xs text-muted-foreground">
          上次回答未完成，完整回答见历史
        </p>
      )}
      <div ref={scrollRef} className="flex min-h-0 flex-1 flex-col gap-2 overflow-y-auto p-3" aria-live="polite">
        {messages.length > 0 ? (
          messages.map(renderMessage)
        ) : (
          <p className="m-auto text-sm text-muted-foreground">{activeId ? '开始一段对话吧' : '正在连接 AI 助手…'}</p>
        )}
      </div>
      {conflict && (
        <div role="group" aria-label="会话已有回答在生成" className="flex flex-wrap items-center gap-2 border-t p-2 text-sm">
          <span className="text-muted-foreground">这个会话还有一条回答正在生成</span>
          {/* capabilities 缺失（null）是「不知道」，只有显式不含 interrupt 才禁用。 */}
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
      <div className="flex items-center gap-2 border-t p-2">
        <Input
          aria-label="发送给 AI 助手的消息"
          placeholder="输入消息…"
          value={input}
          disabled={!ready || !activeId}
          onChange={(event) => setInput(event.target.value)}
          onKeyDown={(event) => {
            if (event.key === 'Enter' && !event.nativeEvent.isComposing) submit();
          }}
        />
        <Button
          type="button"
          variant={streaming ? 'destructive' : 'default'}
          disabled={!ready || !activeId}
          onClick={streaming ? stop : submit}
        >
          {streaming ? '停止' : '发送'}
        </Button>
      </div>
    </section>
  );
}
