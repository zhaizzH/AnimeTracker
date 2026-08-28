import { theme } from 'antd';
import { Link } from 'react-router-dom';
import type { SubjectListItem } from '../types';
interface Props { subject: SubjectListItem }
export function SubjectCard({ subject }: Props) {
  const { token } = theme.useToken();
  // ponytail: 二级降级（airDate→年份、eps→集数），两者皆空兜底"暂无收录"
  const meta = subject.score > 0
    ? `${subject.score.toFixed(1)} 分`
    : [subject.airDate && subject.airDate.slice(0, 4), subject.eps > 0 && `${subject.eps} 集`].filter(Boolean).join(' · ') || '暂无收录';
  return (
    <Link to={`/subject/${subject.id}`} style={{ display: 'block', color: 'inherit', textDecoration: 'none' }}>
      <div className="od-card-img" style={{ aspectRatio: '3/4', background: token.colorBorderSecondary, overflow: 'hidden' }}>
        {subject.image
          ? <img src={subject.image} alt={subject.nameCn ?? subject.name} style={{ width: '100%', height: '100%', objectFit: 'cover' }} loading="lazy" />
          : <div style={{ height: '100%', display: 'flex', alignItems: 'center', justifyContent: 'center', color: token.colorTextTertiary }}>暂无封面</div>}
      </div>
      <div style={{ fontSize: 14, lineHeight: '20px', marginTop: 6, overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap', color: token.colorText }}>{subject.nameCn ?? subject.name}</div>
      <div style={{ fontSize: 12, color: token.colorTextSecondary }}>{meta}</div>
    </Link>
  );
}
