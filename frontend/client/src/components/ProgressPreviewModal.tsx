import { useEffect, useState } from 'react';
import { toast } from 'sonner';
import { collectionsApi } from '@shared';
import type { ExecuteResultVO, ProgressPreviewVO } from '@shared';
import { Button } from '@/components/ui/button';
import {
  Dialog, DialogContent, DialogFooter, DialogHeader, DialogTitle,
} from '@/components/ui/dialog';

interface Props { open: boolean; onClose: () => void }

export function ProgressPreviewModal({ open, onClose }: Props) {
  const [preview, setPreview] = useState<ProgressPreviewVO | null>(null);
  const [result, setResult] = useState<ExecuteResultVO | null>(null);
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    if (!open) return;
    setPreview(null);
    setResult(null);
    collectionsApi.progressPreview().then(setPreview).catch((e) => toast.error((e as Error).message));
  }, [open]);

  const confirm = async () => {
    if (!preview) return;
    setLoading(true);
    try {
      const r = await collectionsApi.executePreview(preview.previewId);
      if (r.state === 'PREVIEW_CHANGED' && r.preview) {
        setPreview(r.preview);
        setResult(null);
        toast.warning('数据有变化，请再次确认');
      } else {
        setResult(r);
        toast.success('已更新本周进度');
      }
    } catch (e) {
      toast.error((e as Error).message);
    } finally {
      setLoading(false);
    }
  };

  return (
    <Dialog open={open} onOpenChange={(next) => { if (!next) onClose(); }}>
      <DialogContent>
        <DialogHeader>
          <DialogTitle>更新本周追番进度</DialogTitle>
        </DialogHeader>

        {preview && (
          <>
            <p className="rounded-md border bg-muted px-3 py-2 text-sm text-muted-foreground">
              周起始 {preview.weekStart} · 截止 {preview.cutoffDate}
            </p>
            <ul className="max-h-64 overflow-y-auto text-sm">
              {preview.items.map((it) => (
                <li key={it.subjectId} className="border-b py-1.5 last:border-b-0">
                  {it.subjectName}：{it.currentEpStatus} → {it.targetEpStatus} 集
                  {it.suggestMarkAsWatched ? '（建议标记看过）' : ''}
                </li>
              ))}
            </ul>
          </>
        )}

        {result && (
          <p className="rounded-md border bg-muted px-3 py-2 text-sm">
            成功 {result.succeeded.length} · 跳过 {result.skipped.length} · 失败 {result.failed.length}
          </p>
        )}

        <DialogFooter>
          {result ? (
            <Button onClick={onClose}>完成</Button>
          ) : (
            <Button disabled={!preview || loading} onClick={confirm}>
              {loading ? '更新中…' : '确认更新'}
            </Button>
          )}
        </DialogFooter>
      </DialogContent>
    </Dialog>
  );
}
