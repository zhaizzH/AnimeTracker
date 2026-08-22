import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';
import { Button, InputNumber, message, Popconfirm, Rate } from 'antd';
import { collectionsApi, useAuthStore } from '@shared';
import type { CollectionType } from '@shared';

const TYPE_LABEL: Record<CollectionType, string> = { 1: '想看', 2: '看过', 3: '在看', 4: '搁置', 5: '抛弃' };
export function CollectionActions({ subjectId, eps }: { subjectId: string; eps: number }) {
  const isLoggedIn = useAuthStore((s) => s.isLoggedIn);
  const qc = useQueryClient();
  const { data: col, isLoading } = useQuery({ queryKey: ['collection', subjectId], queryFn: () => collectionsApi.getCollection(subjectId), enabled: isLoggedIn });
  const invalidate = () => { qc.invalidateQueries({ queryKey: ['collection', subjectId] }); qc.invalidateQueries({ queryKey: ['collections'] }); };
  const setType = useMutation({ mutationFn: (t: CollectionType) => col ? collectionsApi.save(subjectId, { type: t, ...(col.rate ? { rate: col.rate } : {}) }) : collectionsApi.wishlist(subjectId).then(() => collectionsApi.save(subjectId, { type: t })), onSuccess: () => { invalidate(); message.success('已更新追番状态'); } });
  const setRate = useMutation({ mutationFn: (rate: number) => collectionsApi.save(subjectId, { type: col!.type, rate }), onSuccess: invalidate });
  const setEp = useMutation({ mutationFn: (epStatus: number) => collectionsApi.updateEpStatus(subjectId, { epStatus }), onSuccess: invalidate });
  const del = useMutation({ mutationFn: () => collectionsApi.remove(subjectId), onSuccess: () => { invalidate(); message.success('已取消收藏'); } });

  if (!isLoggedIn) return <div>登录后可追番</div>;
  if (isLoading) return null;
  if (!col) return (
    <div className="od-col-btns">
      {(Object.keys(TYPE_LABEL) as unknown as CollectionType[]).map((t) => <Button key={t} block onClick={() => setType.mutate(t)}>{TYPE_LABEL[t]}</Button>)}
    </div>
  );
  return (
    <div className="od-col-actions">
      <div className="od-col-btns">
        {Object.keys(TYPE_LABEL).map((k) => { const t = Number(k) as CollectionType; return <Button key={t} block type={col.type === t ? 'primary' : 'default'} onClick={() => t !== col.type && setType.mutate(t)}>{TYPE_LABEL[t]}</Button>; })}
      </div>
      <div className="od-col-meta">
        <div className="od-col-row"><span>评分</span><Rate count={10} value={col.rate || 0} onChange={(r) => setRate.mutate(r)} /></div>
        <div className="od-col-row">
          <span>进度</span>
          <InputNumber min={0} max={eps} value={col.epStatus} onChange={(v) => v != null && setEp.mutate(v)} />
          <span className="od-col-ep-count">{col.epStatus}/{eps} 集</span>
        </div>
        <Popconfirm title="确定取消收藏？" onConfirm={() => del.mutate()}><Button danger>取消收藏</Button></Popconfirm>
      </div>
    </div>
  );
}
