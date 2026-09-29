'use client';

import * as React from 'react';
import { Minus, TrendingDown, TrendingUp } from 'lucide-react';
import { cn } from '@/lib/utils';
import { Badge } from '@/components/ui/badge';

type DeltaVariant = 'default' | 'badge';

const DeltaContext = React.createContext<number | null>(null);

function useDeltaValue() {
  const value = React.useContext(DeltaContext);
  if (value === null) {
    throw new Error('DeltaIcon and DeltaValue must be used inside a `Delta` component.');
  }
  return value;
}

function Delta({
  className,
  value,
  variant = 'default',
  ...props
}: React.ComponentProps<'div'> & { value: number; variant?: DeltaVariant }) {
  const tone = value > 0 ? 'up' : value < 0 ? 'down' : 'flat';
  return (
    <DeltaContext.Provider value={value}>
      {variant === 'badge' ? (
        <Badge
          className={cn(
            'gap-1 border-none tabular-nums [&_svg]:size-4 [&_svg]:shrink-0',
            tone === 'up' && 'bg-emerald-500/10 text-emerald-500',
            tone === 'down' && 'bg-red-500/10 text-red-500',
            tone === 'flat' && 'bg-muted text-muted-foreground',
            className,
          )}
          data-slot="delta"
          data-tone={tone}
          variant="secondary"
          {...(props as React.ComponentProps<typeof Badge>)}
        />
      ) : (
        <div
          className={cn(
            'inline-flex items-center gap-1 text-muted-foreground tabular-nums',
            '[&_svg]:size-3 [&_svg]:shrink-0',
            tone === 'up' && 'text-emerald-600 dark:text-emerald-400',
            tone === 'down' && 'text-rose-600 dark:text-rose-400',
            className,
          )}
          data-slot="delta"
          data-tone={tone}
          {...props}
        />
      )}
    </DeltaContext.Provider>
  );
}

function DeltaIcon({ className, ...props }: React.ComponentProps<'svg'>) {
  const value = useDeltaValue();
  const Icon = !value ? Minus : value > 0 ? TrendingUp : TrendingDown;
  return <Icon aria-hidden="true" className={cn(className)} data-slot="delta-icon" {...props} />;
}

function DeltaValue({
  className,
  precision = 1,
  suffix = '%',
  absolute = true,
  ...props
}: React.ComponentProps<'span'> & {
  precision?: number;
  suffix?: string;
  absolute?: boolean;
}) {
  const value = useDeltaValue();
  const shown = (absolute ? Math.abs(value) : value).toFixed(precision);
  return (
    <span className={cn('tabular-nums', className)} data-slot="delta-value" {...props}>
      {shown}
      {suffix}
    </span>
  );
}

export { Delta, DeltaIcon, DeltaValue };
