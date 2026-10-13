import { useState } from 'react';
import { TrashIcon, PanelLeftCloseIcon, PanelLeftOpenIcon } from 'lucide-react';
import { AgentConversation, useClientAgentChat } from '@/components/AgentChat';
import { Button } from '@/components/ui/button';
import { cn } from '@/lib/utils';

export default function Agent() {
  const { chat } = useClientAgentChat();
  const { sessions, activeId, streaming, ready, select, create, remove } = chat;
  const [collapsed, setCollapsed] = useState(false);

  return (
    <div className="mx-auto h-[calc(100vh-5.5rem)] w-full max-w-[1400px] p-4 md:h-[calc(100vh-6.5rem)] md:p-6">
      <div className="flex h-full overflow-hidden rounded-xl border">
        <aside
          className={cn('shrink-0 border-r bg-card transition-all', collapsed ? 'w-0 overflow-hidden' : 'w-60')}
          aria-label="会话列表"
        >
          <div className="p-3">
            <Button className="w-full" disabled={!ready || streaming} onClick={create}>新建会话</Button>
          </div>
          <ul className="max-h-full overflow-y-auto px-2 pb-2">
            {sessions.map((s) => {
              const id = String((s as { id?: unknown }).id);
              const title = String((s as { title?: unknown }).title ?? id);
              return (
                <li key={id}>
                  <div
                    className={cn(
                      'flex items-center gap-1 rounded-md px-2 py-1.5 text-sm',
                      id === activeId && 'bg-accent text-accent-foreground',
                    )}
                  >
                    <button
                      type="button"
                      className="min-w-0 flex-1 truncate text-left disabled:cursor-default"
                      disabled={!ready || streaming}
                      onClick={() => { if (ready && !streaming) void select(id); }}
                    >
                      {title}
                    </button>
                    <Button
                      type="button"
                      variant="ghost"
                      size="icon-sm"
                      aria-label="删除会话"
                      disabled={!ready || streaming}
                      onClick={() => void remove(id)}
                    >
                      <TrashIcon />
                    </Button>
                  </div>
                </li>
              );
            })}
          </ul>
        </aside>

        <div className="flex min-w-0 flex-1 flex-col p-4">
          <Button
            type="button"
            variant="ghost"
            size="icon-sm"
            className="mb-2 self-start"
            aria-label={collapsed ? '展开会话列表' : '收起会话列表'}
            onClick={() => setCollapsed((c) => !c)}
          >
            {collapsed ? <PanelLeftOpenIcon /> : <PanelLeftCloseIcon />}
          </Button>
          <AgentConversation />
        </div>
      </div>
    </div>
  );
}
