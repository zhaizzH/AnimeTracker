import { useState } from 'react';
import { Input, Select, Table, Segmented, Pagination, Spin, Empty } from 'antd';
import { useSearchParams, useNavigate } from 'react-router-dom';
import { useQuery } from '@tanstack/react-query';
import { subjectsApi } from '@/api/subjects';
import { tagsApi } from '@/api/tags';
import SubjectCard from '@/components/SubjectCard';
import PageHeading from '@/components/PageHeading';
import type { SubjectListVO } from '@/types';

const sortOptions = [
  { value: 'score', label: '评分' },
  { value: 'airDate', label: '放送日' },
  { value: 'collectionTotal', label: '收藏数' },
];

const viewOptions = [
  { value: 'card', label: '卡片' },
  { value: 'table', label: '表格' },
];

export default function AnimeIndex() {
  const [searchParams, setSearchParams] = useSearchParams();
  const navigate = useNavigate();
  const q = searchParams.get('q') || '';
  const tag = searchParams.get('tag') || '';
  const year = searchParams.get('year') || '';
  const sort = searchParams.get('sort') || 'score';
  const order = searchParams.get('order') || 'desc';
  const page = parseInt(searchParams.get('page') || '1');
  const [view, setView] = useState<'card' | 'table'>('card');
  const [searchText, setSearchText] = useState(q);

  // 获取标签列表（用于筛选）
  const { data: allTags } = useQuery({
    queryKey: ['tags'],
    queryFn: () => tagsApi.list() as any,
  });

  // 查询番剧列表
  const { data, isLoading } = useQuery({
    queryKey: ['subjects', 'search', { q, tag, year, sort, order, page }],
    queryFn: () => subjectsApi.search({
      q: q || undefined,
      tag: tag ? [tag] : undefined,
      year: year ? parseInt(year) : undefined,
      sort, order, page, size: 20,
    }),
  });

  const updateParams = (updates: Record<string, string>) => {
    const params = new URLSearchParams(searchParams);
    Object.entries(updates).forEach(([k, v]) => {
      if (v) params.set(k, v);
      else params.delete(k);
    });
    if (updates.page === undefined) params.set('page', '1');
    setSearchParams(params);
  };

  const columns = [
    { title: '封面', dataIndex: 'image', key: 'image',
      render: (src: string, record: SubjectListVO) => (
        <img src={src} alt={record.name} style={{ width: 48, height: 64, objectFit: 'cover', cursor: 'pointer' }}
          onClick={() => navigate(`/subject/${record.id}`)} />
      ),
    },
    { title: '标题', key: 'name',
      render: (_: any, r: SubjectListVO) => (
        <a onClick={() => navigate(`/subject/${r.id}`)}>{r.nameCn || r.name}</a>
      ),
    },
    { title: '类型', dataIndex: 'type', key: 'type', width: 80 },
    { title: '集数', dataIndex: 'eps', key: 'eps', width: 60 },
    { title: '评分', dataIndex: 'score', key: 'score', width: 80, sorter: true },
    { title: '放送日', dataIndex: 'airDate', key: 'airDate', width: 120 },
  ];

  return (
    <div>
      <PageHeading
        index="03 / INDEX"
        title="番剧索引"
        subtitle="按标签、年份与评分翻查全部条目"
      />

      <div className="index-toolbar">
        <Input.Search
          placeholder="搜索番剧名称..."
          value={searchText}
          onChange={e => setSearchText(e.target.value)}
          onSearch={val => updateParams({ q: val, page: '' })}
          enterButton
          size="large"
        />

        <div className="index-toolbar-row">
          <Select
            placeholder="标签"
            allowClear
            style={{ width: 140 }}
            value={tag || undefined}
            onChange={val => updateParams({ tag: val || '', page: '' })}
            options={allTags?.map((t: any) => ({ value: t.name, label: `${t.name}(${t.count})` })) || []}
          />
          <Input
            placeholder="年份"
            type="number"
            style={{ width: 100 }}
            value={year}
            onChange={e => updateParams({ year: e.target.value, page: '' })}
          />
          <Select
            style={{ width: 120 }}
            value={sort}
            onChange={val => updateParams({ sort: val })}
            options={sortOptions}
          />
          <Select
            style={{ width: 100 }}
            value={order}
            onChange={val => updateParams({ order: val })}
            options={[{ value: 'desc', label: '降序' }, { value: 'asc', label: '升序' }]}
          />
        </div>
      </div>

      <div className="index-result-line">
        <span>共 <strong>{(data as any)?.total || 0}</strong> 条记录</span>
        <Segmented options={viewOptions} value={view} onChange={v => setView(v as 'card' | 'table')} />
      </div>

      {isLoading ? <Spin className="paper-loading" /> : (
        !data || (data as any).content?.length === 0 ? <Empty description="没有找到匹配的番剧" /> : (
          view === 'card' ? (
              <div className="poster-grid">
                {(data as any).content?.map((subject: SubjectListVO) => (
                  <SubjectCard subject={subject} key={subject.id} />
                ))}
              </div>
          ) : (
            <Table
              className="paper-table"
              dataSource={(data as any).content || []}
              columns={columns}
              rowKey="id"
              pagination={false}
            />
          )
        )
      )}

      <div style={{ marginTop: 20, textAlign: 'right' }}>
        <Pagination
          current={page}
          total={(data as any)?.total || 0}
          pageSize={20}
          onChange={p => updateParams({ page: String(p) })}
          showTotal={total => `共 ${total} 条`}
        />
      </div>
    </div>
  );
}
