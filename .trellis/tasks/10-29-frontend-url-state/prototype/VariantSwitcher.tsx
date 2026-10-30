// 底部变体切换条：同时显示「真实进 URL 的筛选状态」。
import { RotateCcwIcon, SmartphoneIcon } from 'lucide-react';
import { Button } from '@/components/ui/button';
import { cn } from '@/lib/utils';

export type Variant = 'v1' | 'v2' | 'v3';

const ITEMS: Array<{ key: Variant; label: string; hint: string }> = [
  { key: 'v1', label: 'V1', hint: '浮层内系统提示' },
  { key: 'v2', label: 'V2', hint: '页面顶部 toast' },
  { key: 'v3', label: 'V3', hint: '窄屏收起为气泡' },
];

export function VariantSwitcher({
  variant,
  url,
  busy,
  narrow,
  onVariant,
  onToggleNarrow,
  onReset,
}: {
  variant: Variant;
  url: string;
  busy: boolean;
  narrow: boolean;
  onVariant: (v: Variant) => void;
  onToggleNarrow: () => void;
  onReset: () => void;
}) {
  return (
    <div className="fixed bottom-4 left-1/2 z-50 w-[calc(100vw-1.5rem)] max-w-max -translate-x-1/2">
      <div className="flex flex-wrap items-center justify-center gap-2 rounded-2xl border bg-background/95 px-2 py-1.5 shadow-lg backdrop-blur sm:rounded-full">
        <span className="pl-2 text-[10px] font-semibold tracking-widest text-muted-foreground">PROTOTYPE</span>
        <div className="flex items-center gap-1">
          {ITEMS.map((item) => (
            <button
              key={item.key}
              type="button"
              onClick={() => onVariant(item.key)}
              className={cn(
                'rounded-full px-3 py-1 text-xs transition',
                variant === item.key
                  ? 'bg-primary font-medium text-primary-foreground shadow-sm'
                  : 'text-muted-foreground hover:bg-muted hover:text-foreground',
              )}
            >
              {item.label}
              <span className={cn('ml-1 hidden sm:inline', variant === item.key ? 'opacity-75' : 'opacity-60')}>
                {item.hint}
              </span>
            </button>
          ))}
        </div>
        <span className="max-w-full truncate rounded-md bg-muted px-2 py-1 font-mono text-[11px] text-muted-foreground">{url}</span>
        {busy && <span className="animate-pulse text-[11px] text-foreground">agent 正在操作…</span>}
        <Button type="button" size="xs" variant={narrow ? 'secondary' : 'ghost'} onClick={onToggleNarrow}>
          <SmartphoneIcon />
          模拟窄屏
        </Button>
        <Button type="button" size="xs" variant="ghost" onClick={onReset}>
          <RotateCcwIcon />
          重置
        </Button>
      </div>
    </div>
  );
}
