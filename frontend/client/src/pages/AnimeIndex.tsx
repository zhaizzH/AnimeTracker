import { useState } from 'react';
import { useQuery } from '@tanstack/react-query';
import { useNavigate, useSearchParams } from 'react-router-dom';
import { Button, Input, Select, Space } from 'antd';
import { subjectsApi } from '@shared';
import { SubjectGrid } from '../components/SubjectGrid';
import type { SubjectListItem } from '@shared';

export default function AnimeIndex() {
  const navigate = useNavigate();
  const [params, setParams] = useSearchParams();
  const q = params.get('q') ?? '';
  const [keyword, setKeyword] = useState(q);
  const [filters, setFilters] = useState<Record<string, unknown>>({});
  const page = Number(params.get('page') ?? 1);
  const { data, isLoading } = useQuery({
    queryKey: ['subjects', 'search', q, filters, page],
    queryFn: () => subjectsApi.search({ q, page, size: 20, sort: 'score', order: 'desc', ...filters }),
  });
  const applyFilters = (patch: Record<string, unknown>) => { setFilters((f) => ({ ...f, ...patch })); setParams({}); };
  return (
    <div style={{ maxWidth: 1100, margin: '0 auto', padding: 24 }}>
      <div className="od-index-filter" style={{ marginBottom: 20 }}>
        <Space style={{ flexWrap: 'wrap' }}>
          <Input.Search defaultValue={keyword} placeholder="关键词" onSearch={(v) => { setKeyword(v); setParams({ q: v }); }} style={{ width: 200 }} />
          <Select allowClear placeholder="年份" style={{ width: 110 }} onChange={(v) => applyFilters({ year: v })} options={Array.from({ length: 16 }, (_, i) => ({ value: 2026 - i, label: `${2026 - i}` }))} />
          <Select allowClear placeholder="播出星期" style={{ width: 110 }} onChange={(v) => applyFilters({ weekday: v })} options={['周日', '周一', '周二', '周三', '周四', '周五', '周六'].map((label, i) => ({ value: i, label }))} />
          <Button onClick={() => { setFilters({}); setParams({}); }}>重置</Button>
        </Space>
      </div>
      <SubjectGrid
        items={data?.content ?? []} loading={isLoading}
        total={data?.total} page={data?.page} size={data?.size}
        onPageChange={(p) => setParams({ q, page: String(p) })}
        onItemClick={(s: SubjectListItem) => navigate(`/subject/${s.id}`)}
      />
    </div>
  );
}
