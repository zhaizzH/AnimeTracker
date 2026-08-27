import { useState } from 'react';
import { useQuery } from '@tanstack/react-query';
import { useSearchParams } from 'react-router-dom';
import { Button, Tabs } from 'antd';
import { collectionsApi } from '@shared';
import type { CollectionType } from '@shared';
import { SubjectGrid } from '../components/SubjectGrid';
import { ProgressPreviewModal } from '../components/ProgressPreviewModal';

const TABS: Array<{ key: string; label: string; type?: CollectionType }> = [
  { key: 'all', label: '全部' }, { key: '1', label: '想看', type: 1 }, { key: '2', label: '看过', type: 2 },
  { key: '3', label: '在看', type: 3 }, { key: '4', label: '搁置', type: 4 }, { key: '5', label: '抛弃', type: 5 },
];
export default function MyCollections() {
  const [params, setParams] = useSearchParams();
  const tab = params.get('tab') ?? 'all';
  const page = Number(params.get('page') ?? 1);
  const setTab = (k: string) => setParams({ tab: k, page: '1' });
  const setPage = (p: number) => setParams({ tab, page: String(p) });
  const [previewOpen, setPreviewOpen] = useState(false);
  const type = TABS.find((t) => t.key === tab)?.type;
  const cts = useQuery({ queryKey: ['collections', 'counts'], queryFn: collectionsApi.counts });
  const { data, isLoading } = useQuery({ queryKey: ['collections', type, page], queryFn: () => collectionsApi.list({ type, page, size: 24 }) });
  return (
    <div style={{ maxWidth: 1400, margin: '0 auto', padding: 24 }}>
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
        <Tabs activeKey={tab} onChange={setTab} items={TABS.map((t) => ({ key: t.key, label: `${t.label}${t.key !== 'all' ? `(${cts.data?.[t.key] ?? 0})` : ''}` }))} />
        <Button onClick={() => setPreviewOpen(true)}>更新本周进度</Button>
      </div>
      <SubjectGrid items={(data?.content ?? []).map((c) => c.subject)} loading={isLoading} emptyText="还没有收藏，去番剧索引逛逛" total={data?.total} page={data?.page} size={data?.size} onPageChange={setPage} />
      <ProgressPreviewModal open={previewOpen} onClose={() => setPreviewOpen(false)} />
    </div>
  );
}
