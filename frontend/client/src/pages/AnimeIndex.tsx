import { useState } from 'react';
import { useQuery } from '@tanstack/react-query';
import { useSearchParams } from 'react-router-dom';
import { Button, Input, Select, Space } from 'antd';
import { subjectsApi, tagsApi } from '@shared';
import { SubjectGrid } from '../components/SubjectGrid';

const SORTS = [
  { value: 'score', label: '评分' },
  { value: 'air_date', label: '播出日期' },
  { value: 'rank', label: '排名' },
  { value: 'collection_total', label: '收藏数' },
];

export default function AnimeIndex() {
  const [params, setParams] = useSearchParams();
  const q = params.get('q') ?? '';
  const [keyword, setKeyword] = useState(q);
  const [filters, setFilters] = useState<{ sort?: string; order?: 'asc' | 'desc' } & Record<string, unknown>>({ sort: 'score', order: 'desc' });
  const page = Number(params.get('page') ?? 1);
  const { data: tags } = useQuery({ queryKey: ['tags'], queryFn: tagsApi.list });
  const { data: years } = useQuery({ queryKey: ['subjects', 'years'], queryFn: subjectsApi.years });
  const { data, isLoading } = useQuery({
    queryKey: ['subjects', 'search', q, filters, page],
    queryFn: () => subjectsApi.search({ q, page, size: 24, sort: 'score', order: 'desc', ...filters }),
  });
  const applyFilters = (patch: Record<string, unknown>) => {
    setFilters((f) => ({ ...f, ...patch }));
    setParams(q ? { q } : {});
  };
  const reset = () => { setFilters({ sort: 'score', order: 'desc' }); setKeyword(''); setParams({}); };
  return (
    <div style={{ maxWidth: 1400, margin: '0 auto', padding: 24 }}>
      <h1 style={{ fontSize: 28, textWrap: 'balance', marginBottom: 16 }}>番剧索引</h1>
      <div className="od-index-filter" style={{ marginBottom: 20 }}>
        <Space style={{ flexWrap: 'wrap' }}>
          <Input.Search defaultValue={keyword} placeholder="关键词" onSearch={(v) => { setKeyword(v); setParams(v ? { q: v, page: '1' } : { page: '1' }); }} style={{ width: 200 }} />
          <Select
            allowClear showSearch placeholder="年份" style={{ width: 110 }} virtual={false}
            onChange={(v) => applyFilters({ year: v })}
            options={(years ?? []).map((y) => ({ value: y, label: `${y}` }))}
          />
          <Select allowClear placeholder="播出星期" style={{ width: 110 }} onChange={(v) => applyFilters({ weekday: v })} options={['周日', '周一', '周二', '周三', '周四', '周五', '周六'].map((label, i) => ({ value: i, label }))} />
          <Select
            allowClear mode="multiple" maxTagCount="responsive" placeholder="标签" style={{ minWidth: 200 }} virtual={false}
            onChange={(v) => applyFilters({ tag: v?.length ? v : undefined })}
            options={(tags ?? []).map((t) => ({ value: t.name, label: `${t.name} (${t.count})` }))}
          />
          <Select placeholder="排序" style={{ width: 110 }} value={filters.sort} onChange={(v) => applyFilters({ sort: v })} options={SORTS} />
          <Select placeholder="方向" style={{ width: 90 }} value={filters.order} onChange={(v) => applyFilters({ order: v })} options={[{ value: 'desc', label: '降序' }, { value: 'asc', label: '升序' }]} />
          <Button onClick={reset}>重置</Button>
        </Space>
      </div>
      <SubjectGrid
        items={data?.content ?? []} loading={isLoading}
        total={data?.total} page={data?.page} size={data?.size}
        onPageChange={(p) => setParams({ q, page: String(p) })}
      />
    </div>
  );
}