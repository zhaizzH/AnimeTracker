import { Empty, Pagination, Spin } from 'antd';
import { SubjectCard } from '@shared';
import type { SubjectListItem } from '@shared';

interface Props {
  items: SubjectListItem[]; loading?: boolean; emptyText?: string;
  total?: number; page?: number; size?: number;
  onPageChange?: (page: number) => void; onItemClick?: (s: SubjectListItem) => void;
}
export function SubjectGrid({ items, loading, emptyText = '暂无数据', total, page, size, onPageChange, onItemClick }: Props) {
  if (loading) return <div style={{ textAlign: 'center', padding: 40 }}><Spin /></div>;
  if (!items.length) return <Empty description={emptyText} />;
  return (
    <div>
      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fill, minmax(150px, 1fr))', gap: 20 }}>
        {items.map((s) => <div key={s.id} className="od-card-cell"><SubjectCard subject={s} onClick={onItemClick ? () => onItemClick(s) : undefined} /></div>)}
      </div>
      {onPageChange && <Pagination current={page} total={total} pageSize={size} onChange={onPageChange} style={{ marginTop: 24, textAlign: 'center' }} />}
    </div>
  );
}
