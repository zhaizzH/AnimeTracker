import { useEffect, useState } from 'react';
import { Tabs, Rate, InputNumber, Button, Popconfirm, Pagination, Skeleton } from 'antd';
import { useQuery } from '@tanstack/react-query';
import { useNavigate } from 'react-router-dom';
import { collectionsApi } from '@/api/collections';
import { useCollections } from '@/hooks/useCollections';
import PageHeading from '@/components/PageHeading';
import { COLLECTION_TYPE_LABELS } from '@/utils';
import type { UserCollectionVO } from '@/types';

const typeTabs = [
  { key: '', label: '全部' },
  ...Object.entries(COLLECTION_TYPE_LABELS).map(([key, label]) => ({ key, label })),
];

// 窄屏阈值：小于该宽度时用卡片列表布局（避免表格右侧操作列被遮挡）
const MOBILE_BREAKPOINT = 768;

function useIsMobile() {
  const [isMobile, setIsMobile] = useState(() =>
    typeof window !== 'undefined' && window.matchMedia(`(max-width: ${MOBILE_BREAKPOINT}px)`).matches,
  );
  useEffect(() => {
    const mql = window.matchMedia(`(max-width: ${MOBILE_BREAKPOINT}px)`);
    const onChange = (e: MediaQueryListEvent) => setIsMobile(e.matches);
    mql.addEventListener('change', onChange);
    return () => mql.removeEventListener('change', onChange);
  }, []);
  return isMobile;
}

function CollectionCard({ record, onNavigate, onRate, onProgress, onRemove }: {
  record: UserCollectionVO;
  onNavigate: () => void;
  onRate: (val: number) => void;
  onProgress: (val: number | null) => void;
  onRemove: () => void;
}) {
  const sub = record.subject || ({} as UserCollectionVO['subject']);
  return (
    <div className="collection-card">
      <img
        src={sub.image || '/placeholder.png'}
        alt={sub.name}
        className="collection-card-cover"
        onClick={onNavigate}
      />
      <div className="collection-card-main">
        <a className="collection-card-title" onClick={onNavigate}>
          {sub.nameCn || sub.name}
        </a>
        <div className="collection-card-row">
          <span className="collection-card-label">评分</span>
          <Rate count={10} value={record.rate} onChange={onRate} />
        </div>
        <div className="collection-card-row">
          <span className="collection-card-label">进度</span>
          <InputNumber
            min={0}
            size="small"
            value={record.epStatus}
            onChange={onProgress}
            style={{ width: 64 }}
          />
          <span className="collection-card-eps">/ {sub.eps || '?'}</span>
        </div>
        <div className="collection-card-actions">
          <Popconfirm title="确定取消收藏？" onConfirm={onRemove}>
            <Button size="small" danger>取消收藏</Button>
          </Popconfirm>
        </div>
      </div>
    </div>
  );
}

export default function MyCollections() {
  const [type, setType] = useState<string>('');
  const [page, setPage] = useState(1);
  const navigate = useNavigate();
  const isMobile = useIsMobile();
  const { saveMutation, removeMutation, epStatusMutation } = useCollections();

  const { data, isLoading } = useQuery({
    queryKey: ['collections', type, page],
    queryFn: () => collectionsApi.list({
      type: type ? parseInt(type) : undefined,
      page,
      size: 20,
    }),
  });

  const items: UserCollectionVO[] = (data as any)?.content || [];
  const total = (data as any)?.total || 0;

  const handleRate = (record: UserCollectionVO, val: number) =>
    saveMutation.mutate({ subjectId: record.subjectId, data: { type: record.type, rate: val, epStatus: record.epStatus } });

  const handleProgress = (record: UserCollectionVO, val: number | null) =>
    epStatusMutation.mutate({ subjectId: record.subjectId, epStatus: val || 0 });

  return (
    <div>
      <PageHeading
        index="04 / LIBRARY"
        title="我的收藏"
        subtitle="想看、在看、看过，都记在这一页"
      />

      <Tabs
        className="paper-tabs"
        activeKey={type}
        onChange={val => { setType(val); setPage(1); }}
        items={typeTabs.map(t => ({ key: t.key, label: t.label }))}
      />

      <div className="index-result-line">
        <span>共 <strong>{total}</strong> 条记录</span>
        <span style={{ color: 'var(--ink-faint)', fontFamily: 'var(--mono)', fontSize: 11 }}>
          EPISODE LOG
        </span>
      </div>

      {isLoading ? (
        <Skeleton active paragraph={{ rows: 4 }} />
      ) : isMobile ? (
        <div className="collection-cards">
          {items.map(record => (
            <CollectionCard
              key={record.id}
              record={record}
              onNavigate={() => navigate(`/subject/${record.subjectId}`)}
              onRate={val => handleRate(record, val)}
              onProgress={val => handleProgress(record, val)}
              onRemove={() => removeMutation.mutate(record.subjectId)}
            />
          ))}
          {items.length === 0 && (
            <div className="collection-empty">暂无收藏</div>
          )}
          <Pagination
            simple
            current={page}
            total={total}
            pageSize={20}
            onChange={setPage}
            style={{ marginTop: 16, textAlign: 'center' }}
          />
        </div>
      ) : (
        <table className="collection-table">
          <thead>
            <tr>
              <th style={{ width: 76 }}>封面</th>
              <th>标题</th>
              <th style={{ width: 210 }}>评分</th>
              <th style={{ width: 160 }}>进度</th>
              <th style={{ width: 110 }}>操作</th>
            </tr>
          </thead>
          <tbody>
            {items.map(record => (
              <tr key={record.id}>
                <td>
                  <img
                    src={record.subject.image || '/placeholder.png'}
                    alt={record.subject.name}
                    className="collection-cover"
                    onClick={() => navigate(`/subject/${record.subjectId}`)}
                  />
                </td>
                <td>
                  <a className="collection-title" onClick={() => navigate(`/subject/${record.subjectId}`)}>
                    {record.subject.nameCn || record.subject.name}
                  </a>
                </td>
                <td>
                  <Rate
                    count={10}
                    value={record.rate}
                    onChange={val => handleRate(record, val)}
                  />
                </td>
                <td>
                  <span className="collection-progress">
                    <InputNumber
                      min={0}
                      value={record.epStatus}
                      onChange={val => handleProgress(record, val)}
                      style={{ width: 70 }}
                    />
                    <span>/ {record.subject.eps || '?'}</span>
                  </span>
                </td>
                <td>
                  <Popconfirm title="确定取消收藏？" onConfirm={() => removeMutation.mutate(record.subjectId)}>
                    <Button size="small" danger>取消收藏</Button>
                  </Popconfirm>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      )}
    </div>
  );
}
