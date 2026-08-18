import { useEffect, useState } from 'react';
import { Alert, Button, List, Modal, message } from 'antd';
import { collectionsApi } from '@shared';
import type { ExecuteResultVO, ProgressPreviewVO } from '@shared';

interface Props { open: boolean; onClose: () => void }
export function ProgressPreviewModal({ open, onClose }: Props) {
  const [preview, setPreview] = useState<ProgressPreviewVO | null>(null);
  const [result, setResult] = useState<ExecuteResultVO | null>(null);
  const [loading, setLoading] = useState(false);
  useEffect(() => {
    if (!open) return;
    setPreview(null); setResult(null);
    collectionsApi.progressPreview().then(setPreview).catch((e) => message.error((e as Error).message));
  }, [open]);
  const confirm = async () => {
    if (!preview) return;
    setLoading(true);
    try {
      const r = await collectionsApi.executePreview(preview.previewId);
      if (r.state === 'PREVIEW_CHANGED' && r.preview) { setPreview(r.preview); setResult(null); message.warning('数据有变化，请再次确认'); }
      else { setResult(r); message.success('已更新本周进度'); }
    } catch (e) { message.error((e as Error).message); } finally { setLoading(false); }
  };
  return (
    <Modal open={open} title="更新本周追番进度" onCancel={onClose} footer={result ? <Button onClick={onClose}>完成</Button> : <Button type="primary" loading={loading} onClick={confirm}>确认更新</Button>}>
      {preview && <>
        <Alert message={`周起始 ${preview.weekStart} · 截止 ${preview.cutoffDate}`} type="info" style={{ marginBottom: 12 }} />
        <List size="small" dataSource={preview.items} renderItem={(it) => (
          <List.Item>{it.subjectName}：{it.currentEpStatus} → {it.targetEpStatus} 集{it.suggestMarkAsWatched ? '（建议标记看过）' : ''}</List.Item>
        )} />
      </>}
      {result && <Alert type={result.failed.length ? 'warning' : 'success'} message={`成功 ${result.succeeded.length} · 跳过 ${result.skipped.length} · 失败 ${result.failed.length}`} />}
    </Modal>
  );
}
