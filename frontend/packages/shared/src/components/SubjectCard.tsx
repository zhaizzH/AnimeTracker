import { theme } from 'antd';
import type { SubjectListItem } from '../types';
interface Props { subject: SubjectListItem; onClick?: () => void }
export function SubjectCard({ subject, onClick }: Props) {
  const { token } = theme.useToken();
  return (
    <div onClick={onClick} style={{ cursor: onClick ? 'pointer' : 'default' }}>
      <div style={{ aspectRatio: '3/4', background: token.colorBorderSecondary, overflow: 'hidden', borderRadius: token.borderRadius }}>
        {subject.image
          ? <img src={subject.image} alt={subject.nameCn ?? subject.name} style={{ width: '100%', height: '100%', objectFit: 'cover' }} loading="lazy" />
          : <div style={{ height: '100%', display: 'flex', alignItems: 'center', justifyContent: 'center', color: token.colorTextTertiary }}>暂无封面</div>}
      </div>
      <div style={{ fontSize: 14, lineHeight: '20px', marginTop: 6, overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap', color: token.colorText }}>{subject.nameCn ?? subject.name}</div>
      <div style={{ fontSize: 12, color: token.colorTextSecondary }}>{subject.score > 0 ? `${subject.score.toFixed(1)} 分` : '未评分'}</div>
    </div>
  );
}
