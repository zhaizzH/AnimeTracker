import { useState } from 'react';
import { useQuery } from '@tanstack/react-query';
import { useSearchParams } from 'react-router-dom';
import { collectionsApi } from '@shared';
import type { CollectionType } from '@shared';
import { SubjectGrid } from '@/components/SubjectGrid';
import { ProgressPreviewModal } from '@/components/ProgressPreviewModal';
import { Button } from '@/components/ui/button';
import { cn } from '@/lib/utils';

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
  const { data, isLoading } = useQuery({
    queryKey: ['collections', type, page],
    queryFn: () => collectionsApi.list({ type, page, size: 24 }),
  });

  return (
    <div className="mx-auto w-full max-w-[1400px] p-6">
      <div className="mb-4 flex flex-wrap items-center justify-between gap-3 border-b">
        <div role="tablist" aria-label="收藏分类" className="flex flex-wrap gap-1">
          {TABS.map((t) => (
            <button
              key={t.key}
              type="button"
              role="tab"
              aria-selected={tab === t.key}
              className={cn(
                '-mb-px border-b-2 px-4 py-2 text-sm',
                tab === t.key ? 'border-primary font-medium text-foreground' : 'border-transparent text-muted-foreground hover:text-foreground',
              )}
              onClick={() => setTab(t.key)}
            >
              {t.label}
              {t.key !== 'all' ? `(${cts.data?.[t.key] ?? 0})` : ''}
            </button>
          ))}
        </div>
        <Button onClick={() => setPreviewOpen(true)}>更新本周进度</Button>
      </div>

      <SubjectGrid
        items={(data?.content ?? []).map((c) => c.subject)}
        loading={isLoading}
        emptyText="还没有收藏，去番剧索引逛逛"
        total={data?.total}
        page={data?.page}
        size={data?.size}
        onPageChange={setPage}
      />

      <ProgressPreviewModal open={previewOpen} onClose={() => setPreviewOpen(false)} />
    </div>
  );
}
