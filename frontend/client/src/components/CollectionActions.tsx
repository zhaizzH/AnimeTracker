import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';
import { toast } from 'sonner';
import { collectionsApi, useAuthStore } from '@shared';
import type { CollectionType } from '@shared';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import {
  AlertDialog, AlertDialogAction, AlertDialogCancel, AlertDialogContent, AlertDialogDescription,
  AlertDialogFooter, AlertDialogHeader, AlertDialogTitle, AlertDialogTrigger,
} from '@/components/ui/alert-dialog';
import { cn } from '@/lib/utils';

const TYPE_LABEL: Record<CollectionType, string> = { 1: '想看', 2: '看过', 3: '在看', 4: '搁置', 5: '抛弃' };
const TYPES = Object.keys(TYPE_LABEL).map(Number) as CollectionType[];

export function CollectionActions({ subjectId, eps }: { subjectId: string; eps: number }) {
  const status = useAuthStore((s) => s.status);
  const isLoggedIn = status === 'authenticated';
  const qc = useQueryClient();
  const { data: col, isLoading } = useQuery({
    queryKey: ['collection', subjectId],
    queryFn: () => collectionsApi.getCollection(subjectId),
    enabled: isLoggedIn,
  });
  const invalidate = () => {
    qc.invalidateQueries({ queryKey: ['collection', subjectId] });
    qc.invalidateQueries({ queryKey: ['collections'] });
  };
  const setType = useMutation({
    mutationFn: (t: CollectionType) =>
      col
        ? collectionsApi.save(subjectId, { type: t, ...(col.rate ? { rate: col.rate } : {}) })
        : collectionsApi.wishlist(subjectId).then(() => collectionsApi.save(subjectId, { type: t })),
    onSuccess: () => { invalidate(); toast.success('已更新追番状态'); },
    onError: (e) => toast.error((e as Error).message),
  });
  const setRate = useMutation({
    mutationFn: (rate: number) => collectionsApi.save(subjectId, { type: col!.type, rate }),
    onSuccess: invalidate,
  });
  const setEp = useMutation({
    mutationFn: (epStatus: number) => collectionsApi.updateEpStatus(subjectId, { epStatus }),
    onSuccess: invalidate,
  });
  const del = useMutation({
    mutationFn: () => collectionsApi.remove(subjectId),
    onSuccess: () => { invalidate(); toast.success('已取消收藏'); },
  });

  if (!isLoggedIn) return <p className="text-sm text-muted-foreground">登录后可追番</p>;
  if (isLoading) return null;

  if (!col) {
    return (
      <div className="grid gap-2">
        {TYPES.map((t) => (
          <Button key={t} variant="outline" onClick={() => setType.mutate(t)}>{TYPE_LABEL[t]}</Button>
        ))}
      </div>
    );
  }

  return (
    <div className="grid gap-4">
      <div className="grid gap-2">
        {TYPES.map((t) => (
          <Button
            key={t}
            variant={col.type === t ? 'default' : 'outline'}
            onClick={() => t !== col.type && setType.mutate(t)}
          >
            {TYPE_LABEL[t]}
          </Button>
        ))}
      </div>
      <div className="grid gap-3 text-sm">
        <div className="grid gap-1.5">
          <span className="text-muted-foreground">评分</span>
          <input
            type="range"
            min={0}
            max={10}
            step={1}
            aria-label="评分"
            value={col.rate || 0}
            onChange={(e) => setRate.mutate(Number(e.target.value))}
            className="w-full accent-[var(--primary)]"
          />
          <span className="text-xs text-muted-foreground">{col.rate || 0} 分</span>
        </div>
        <div className="grid gap-1.5">
          <span className="text-muted-foreground">进度</span>
          <div className="flex items-center gap-2">
            <Input
              type="number"
              min={0}
              max={eps}
              aria-label="进度集数"
              value={col.epStatus}
              onChange={(e) => {
                const v = Number(e.target.value);
                if (Number.isFinite(v) && v >= 0 && v <= eps) setEp.mutate(v);
              }}
              className="w-20"
            />
            <span className={cn('text-xs text-muted-foreground')}>{col.epStatus}/{eps} 集</span>
          </div>
        </div>
        <AlertDialog>
          <AlertDialogTrigger asChild>
            <Button variant="destructive">取消收藏</Button>
          </AlertDialogTrigger>
          <AlertDialogContent>
            <AlertDialogHeader>
              <AlertDialogTitle>确定取消收藏？</AlertDialogTitle>
              <AlertDialogDescription>取消后该条目的追番状态与进度将一并移除。</AlertDialogDescription>
            </AlertDialogHeader>
            <AlertDialogFooter>
              <AlertDialogCancel>保留</AlertDialogCancel>
              <AlertDialogAction onClick={() => del.mutate()}>确认取消</AlertDialogAction>
            </AlertDialogFooter>
          </AlertDialogContent>
        </AlertDialog>
      </div>
    </div>
  );
}
