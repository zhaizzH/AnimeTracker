import type { ReactNode } from 'react';
import { Label } from '@/components/ui/label';

export function AuthShell({ title, children, footer }: { title: string; children: ReactNode; footer?: ReactNode }) {
  return (
    <div className="mx-auto flex min-h-screen w-full max-w-sm flex-col justify-center gap-4 py-8">
      <div className="text-center text-xl font-semibold tracking-tight">AnimeTracker</div>
      <div className="rounded-xl border bg-card p-6 shadow-sm">
        <h1 className="mb-4 text-lg font-medium">{title}</h1>
        {children}
      </div>
      {footer && <div className="flex justify-center gap-4 text-sm text-muted-foreground">{footer}</div>}
    </div>
  );
}

/** 表单字段：label + 控件 + 错误文本，统一间距与 a11y 关联。 */
export function Field({
  id,
  label,
  error,
  children,
}: {
  id: string;
  label: string;
  error?: string;
  children: ReactNode;
}) {
  return (
    <div className="grid gap-2">
      <Label htmlFor={id}>{label}</Label>
      {children}
      {error && (
        <p className="text-xs text-destructive" role="alert">
          {error}
        </p>
      )}
    </div>
  );
}
