import { useEffect, useRef, useState } from 'react';
import { useLocation, useNavigate } from 'react-router-dom';
import { BotIcon, MaximizeIcon, XIcon } from 'lucide-react';
import { Button } from '@/components/ui/button';
import { Tooltip, TooltipContent, TooltipTrigger } from '@/components/ui/tooltip';
import { cn } from '@/lib/utils';
import { AgentConversation } from './AgentChat';
import { clearNavHint, consumeAgentNavigation, useNavHint } from './agentNavigation';

export default function AIAssistantFloat() {
  const [open, setOpen] = useState(false);
  const location = useLocation();
  const navigate = useNavigate();
  const wasOpen = useRef(false);
  // 最近一条导航提示（本地瞬时状态，不进会话历史）；面板关闭时也保留，下次打开补显示
  const navHint = useNavHint();

  useEffect(() => {
    // agent 发起的导航保留面板与提示；标记一次性消费，用户后续手动导航仍照旧关闭
    if (consumeAgentNavigation()) return;
    setOpen(false);
    // 用户手动跳走后，上一条「已跳转到」已不成立，留着就是过期假信息
    clearNavHint();
  }, [location.key]);
  useEffect(() => {
    if (!open) return;
    const closeOnEscape = (event: KeyboardEvent) => {
      if (event.key === 'Escape') setOpen(false);
    };
    window.addEventListener('keydown', closeOnEscape);
    return () => window.removeEventListener('keydown', closeOnEscape);
  }, [open]);
  useEffect(() => {
    if (open) document.getElementById('agent-float-close')?.focus();
    else if (wasOpen.current) document.getElementById('agent-float-trigger')?.focus();
    wasOpen.current = open;
  }, [open]);

  // 冗余尾斜杠视为同一路径（`/agent/` 与 `/agent`）。
  if (location.pathname.replace(/\/+$/, '') === '/agent') return null;

  const toggle = () => setOpen((current) => !current);
  const openFullAgent = () => {
    setOpen(false);
    navigate('/agent');
  };

  return (
    <>
      <Tooltip>
        <TooltipTrigger asChild>
          <Button
            id="agent-float-trigger"
            type="button"
            size="icon"
            className={cn('fixed right-6 bottom-6 z-40 size-12 rounded-full shadow-lg', open && 'ring-2 ring-ring')}
            aria-label={open ? '关闭 AI 助手' : '打开 AI 助手'}
            aria-expanded={open}
            onClick={toggle}
          >
            <BotIcon />
          </Button>
        </TooltipTrigger>
        <TooltipContent side="left">AI 助手</TooltipContent>
      </Tooltip>
      {open && (
        <section
          id="agent-float-panel"
          role="dialog"
          aria-modal="false"
          aria-label="AI 助手"
          className="fixed right-6 bottom-24 z-40 flex h-[28rem] w-[22rem] max-w-[calc(100vw-3rem)] flex-col rounded-xl border bg-background shadow-2xl"
        >
          <header className="flex items-center gap-2 border-b p-3">
            <h2 className="text-sm font-medium">AI 助手</h2>
            <div className="ml-auto flex items-center gap-1">
              <Tooltip>
                <TooltipTrigger asChild>
                  <Button type="button" variant="ghost" size="icon-sm" aria-label="打开完整助手" onClick={openFullAgent}>
                    <MaximizeIcon />
                  </Button>
                </TooltipTrigger>
                <TooltipContent>打开完整助手</TooltipContent>
              </Tooltip>
              <Button
                id="agent-float-close"
                type="button"
                variant="ghost"
                size="icon-sm"
                aria-label="关闭 AI 助手对话框"
                onClick={() => setOpen(false)}
              >
                <XIcon />
              </Button>
            </div>
          </header>
          <div className="flex min-h-0 flex-1 flex-col">
            {navHint && (
              <p
                role="status"
                className="border-b px-3 py-2 text-xs text-muted-foreground"
              >
                ⚡ 已跳转到「{navHint}」
              </p>
            )}
            <AgentConversation />
          </div>
        </section>
      )}
    </>
  );
}
