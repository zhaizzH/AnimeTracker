// 原型 AI 浮层：尺寸/结构照生产 AIAssistantFloat.tsx，消息全在内存。
import { useEffect, useRef } from 'react';
import {
  BotIcon,
  CheckIcon,
  LoaderCircleIcon,
  MaximizeIcon,
  SendIcon,
  XIcon,
  ZapIcon,
} from 'lucide-react';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Tooltip, TooltipContent, TooltipTrigger } from '@/components/ui/tooltip';
import { cn } from '@/lib/utils';

export type Msg =
  | { id: number; kind: 'user'; text: string }
  | { id: number; kind: 'assistant'; text: string }
  | { id: number; kind: 'system'; text: string }
  | { id: number; kind: 'tool'; text: string; running: boolean }
  | { id: number; kind: 'preview'; title: string; body: string; resolved?: 'confirmed' | 'cancelled' };

function ToolRow({ msg }: { msg: Extract<Msg, { kind: 'tool' }> }) {
  return (
    <div className="flex items-start gap-1.5 px-1 py-0.5 text-xs text-muted-foreground">
      {msg.running ? (
        <LoaderCircleIcon className="mt-px size-3.5 shrink-0 animate-spin" />
      ) : (
        <CheckIcon className="mt-px size-3.5 shrink-0" />
      )}
      <span>{msg.text}</span>
    </div>
  );
}

function SystemRow({ text }: { text: string }) {
  return (
    <div className="flex items-start gap-1.5 rounded-md bg-muted/50 px-2 py-1.5 text-xs text-muted-foreground">
      <ZapIcon className="mt-px size-3.5 shrink-0" />
      <span>{text}</span>
    </div>
  );
}

export function AgentFloat({
  open,
  narrow,
  messages,
  input,
  onInputChange,
  onSubmit,
  onToggle,
  onClose,
  onConfirm,
  onCancel,
  onDemo,
  badge,
  pending,
}: {
  open: boolean;
  narrow: boolean;
  messages: Msg[];
  input: string;
  onInputChange: (v: string) => void;
  onSubmit: () => void;
  onToggle: () => void;
  onClose: () => void;
  onConfirm: (id: number) => void;
  onCancel: (id: number) => void;
  onDemo: (text: string) => void;
  badge: number;
  pending: boolean;
}) {
  const scrollRef = useRef<HTMLDivElement>(null);
  useEffect(() => {
    const el = scrollRef.current;
    if (el) el.scrollTop = el.scrollHeight;
  }, [messages]);

  return (
    <>
      <Tooltip>
        <TooltipTrigger asChild>
          <Button
            type="button"
            size="icon"
            className={cn('fixed right-6 bottom-6 z-40 size-12 rounded-full shadow-lg', open && 'ring-2 ring-ring')}
            aria-label={open ? '关闭 AI 助手' : '打开 AI 助手'}
            aria-expanded={open}
            onClick={onToggle}
          >
            <BotIcon />
            {badge > 0 && !open && (
              <span className="absolute -top-1 -right-1 flex size-5 items-center justify-center rounded-full bg-destructive text-[11px] font-medium text-white">
                {badge}
              </span>
            )}
          </Button>
        </TooltipTrigger>
        <TooltipContent side="left">AI 助手</TooltipContent>
      </Tooltip>

      {open && (
        <section
          role="dialog"
          aria-modal="false"
          aria-label="AI 助手"
          className={cn(
            'fixed right-6 bottom-24 z-40 flex h-[28rem] flex-col rounded-xl border bg-background shadow-2xl',
            // 手机外框里的 fixed 容器是外框本身，100vw 会取到真实视口，故窄屏改用 100%。
            narrow ? 'w-[calc(100%-3rem)] max-w-[327px]' : 'w-[22rem] max-w-[calc(100vw-3rem)]',
          )}
        >
          <header className="flex items-center gap-2 border-b p-3">
            <h2 className="text-sm font-medium">AI 助手</h2>
            <div className="ml-auto flex items-center gap-1">
              <Tooltip>
                <TooltipTrigger asChild>
                  <Button type="button" variant="ghost" size="icon-sm" aria-label="打开完整助手">
                    <MaximizeIcon />
                  </Button>
                </TooltipTrigger>
                <TooltipContent>打开完整助手</TooltipContent>
              </Tooltip>
              <Button type="button" variant="ghost" size="icon-sm" aria-label="关闭 AI 助手对话框" onClick={onClose}>
                <XIcon />
              </Button>
            </div>
          </header>

          <div ref={scrollRef} className="flex min-h-0 flex-1 flex-col gap-2 overflow-y-auto p-3" aria-live="polite">
            {messages.length === 0 && (
              <div className="m-auto flex w-full max-w-[16rem] flex-col gap-2 text-xs">
                <p className="text-center leading-relaxed text-muted-foreground">一键演示，也可直接在下框手打</p>
                <button
                  type="button"
                  className="rounded-md border bg-card px-2 py-1.5 text-left hover:bg-muted"
                  onClick={() => onDemo('给我看 2022 年的番')}
                >
                  给我看 2022 年的番
                </button>
                <button
                  type="button"
                  className="rounded-md border bg-card px-2 py-1.5 text-left hover:bg-muted"
                  onClick={() => onDemo('把《孤独摇滚》加入想看，然后打开我的收藏')}
                >
                  把《孤独摇滚》加入想看，然后打开我的收藏
                </button>
              </div>
            )}
            {messages.map((m) => {
              if (m.kind === 'user')
                return (
                  <div key={m.id} className="ml-auto max-w-[85%] rounded-lg bg-primary px-3 py-2 text-sm text-primary-foreground">
                    {m.text}
                  </div>
                );
              if (m.kind === 'assistant')
                return (
                  <div key={m.id} className="mr-auto max-w-[95%] rounded-lg bg-muted px-3 py-2 text-sm">
                    {m.text}
                  </div>
                );
              if (m.kind === 'system') return <SystemRow key={m.id} text={m.text} />;
              if (m.kind === 'tool') return <ToolRow key={m.id} msg={m} />;
              return (
                <div key={m.id} className="rounded-lg border bg-card p-2.5 text-sm">
                  <div className="font-medium">{m.title}</div>
                  {!m.resolved && (
                    <>
                      <div className="mt-0.5 text-xs text-muted-foreground">{m.body}</div>
                      <div className="mt-2 flex gap-2">
                        <Button type="button" size="sm" onClick={() => onConfirm(m.id)}>
                          确认
                        </Button>
                        <Button type="button" size="sm" variant="outline" onClick={() => onCancel(m.id)}>
                          取消
                        </Button>
                      </div>
                    </>
                  )}
                  {m.resolved === 'confirmed' && <div className="mt-1 text-xs text-muted-foreground">已确认执行</div>}
                  {m.resolved === 'cancelled' && <div className="mt-1 text-xs text-muted-foreground">已取消，未做任何改动</div>}
                </div>
              );
            })}
          </div>

          <div className="flex items-center gap-2 border-t p-2">
            <Input
              aria-label="发送给 AI 助手的消息"
              placeholder="输入消息…"
              value={input}
              disabled={pending}
              onChange={(e) => onInputChange(e.target.value)}
              onKeyDown={(e) => {
                if (e.key === 'Enter' && !e.nativeEvent.isComposing) onSubmit();
              }}
            />
            <Button type="button" size="icon" aria-label="发送" disabled={pending} onClick={onSubmit}>
              <SendIcon />
            </Button>
          </div>
        </section>
      )}
    </>
  );
}
