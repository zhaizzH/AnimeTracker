import { Link } from 'react-router-dom';
import type { SubjectListItem } from '../types';

// 本组件不依赖任何主题上下文，靠 CSS 变量跟随应用明暗切换。两端重建为 shadcn/Tailwind 后
// 统一使用 shadcn 令牌：foreground→正文、muted-foreground→次级/三级文字、border→占位底色；
// 字面量为兜底（与亮色主题一致）。CSS 变量在 React 内联样式里可正常求值并参与级联，
// 故 .dark 翻转时自动跟随。
const TOKEN = {
  border: 'var(--border, #E5E5E5)',
  textTertiary: 'var(--muted-foreground, #A3A3A3)',
  text: 'var(--foreground, #0A0A0A)',
  textSecondary: 'var(--muted-foreground, #737373)',
} as const;

interface Props { subject: SubjectListItem }
export function SubjectCard({ subject }: Props) {
  // ponytail: 二级降级（airDate→年份、eps→集数），两者皆空兜底"暂无收录"
  const meta = subject.score > 0
    ? `${subject.score.toFixed(1)} 分`
    : [subject.airDate && subject.airDate.slice(0, 4), subject.eps > 0 && `${subject.eps} 集`].filter(Boolean).join(' · ') || '暂无收录';
  return (
    <Link to={`/subject/${subject.id}`} style={{ display: 'block', color: 'inherit', textDecoration: 'none' }}>
      <div style={{ aspectRatio: '3/4', borderRadius: 8, background: TOKEN.border, overflow: 'hidden' }}>
        {subject.image
          ? <img src={subject.image} alt={subject.nameCn ?? subject.name} style={{ width: '100%', height: '100%', objectFit: 'cover' }} loading="lazy" />
          : <div style={{ height: '100%', display: 'flex', alignItems: 'center', justifyContent: 'center', color: TOKEN.textTertiary }}>暂无封面</div>}
      </div>
      <div style={{ fontSize: 14, lineHeight: '20px', marginTop: 6, overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap', color: TOKEN.text }}>{subject.nameCn ?? subject.name}</div>
      <div style={{ fontSize: 12, color: TOKEN.textSecondary }}>{meta}</div>
    </Link>
  );
}
