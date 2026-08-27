import { Empty, Pagination } from 'antd';
import { SubjectCard } from '@shared';
import type { SubjectListItem } from '@shared';

interface Props {
  items: SubjectListItem[]; loading?: boolean; emptyText?: string;
  total?: number; page?: number; size?: number;
  onPageChange?: (page: number) => void;
}
export function SubjectGrid({ items, loading, emptyText = '暂无数据', total, page, size, onPageChange }: Props) {
  if (loading) {
    // 卡片形状骨架：与加载后布局一致，消除「窄→宽」跳动
    const count = size && size > 0 ? Math.min(size, 12) : 12;
    return (
      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fill, minmax(200px, 1fr))', gap: 20 }}>
        {Array.from({ length: count }, (_, i) => (
          <div key={i} className="od-skeleton" aria-hidden="true">
            <div className="od-skeleton__img" />
            <div className="od-skeleton__line" style={{ width: '80%' }} />
            <div className="od-skeleton__line" style={{ width: '50%' }} />
          </div>
        ))}
      </div>
    );
  }
  if (!items.length) return <Empty description={emptyText} />;
  return (
    <div>
      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fill, minmax(200px, 1fr))', gap: 20 }}>
        {items.map((s) => <div key={s.id} className="od-card-cell"><SubjectCard subject={s} /></div>)}
      </div>
      {onPageChange && <Pagination current={page} total={total} pageSize={size} showSizeChanger={false} onChange={onPageChange} style={{ marginTop: 24, display: 'flex', justifyContent: 'center' }} />}
    </div>
  );
}
