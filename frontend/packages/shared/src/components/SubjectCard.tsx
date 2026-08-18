import type { SubjectListItem } from '../types';
interface Props { subject: SubjectListItem; onClick?: () => void }
export function SubjectCard({ subject, onClick }: Props) {
  return (
    <div onClick={onClick} style={{ cursor: onClick ? 'pointer' : 'default' }}>
      <div style={{ aspectRatio: '3/4', background: '#F0F0F0', overflow: 'hidden', borderRadius: 6 }}>
        {subject.image
          ? <img src={subject.image} alt={subject.nameCn ?? subject.name} style={{ width: '100%', height: '100%', objectFit: 'cover' }} loading="lazy" />
          : <div style={{ height: '100%', display: 'flex', alignItems: 'center', justifyContent: 'center', color: '#999' }}>暂无封面</div>}
      </div>
      <div style={{ fontSize: 14, lineHeight: '20px', marginTop: 6, overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }}>{subject.nameCn ?? subject.name}</div>
      <div style={{ fontSize: 12, color: '#888' }}>{subject.score > 0 ? `${subject.score.toFixed(1)} 分` : '未评分'}</div>
    </div>
  );
}
