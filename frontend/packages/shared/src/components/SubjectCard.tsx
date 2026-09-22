import { Link } from 'react-router-dom';
import type { SubjectListItem } from '../types';

// 本组件不再依赖 antd 主题上下文，但仍需跟随 client 的明暗切换：原 theme.useToken() 会随
// ConfigProvider 解析出对应主题的色值。这里改用 client 已定义的 --od-* 变量（其亮/暗取值与
// antdTheme / antdThemeDark 逐一对齐）：colorText→--od-ink、colorTextSecondary→--od-ink-2、
// colorTextTertiary→--od-ink-3、colorBorderSecondary→--od-line；字面量为兜底（与亮色主题一致）。
// CSS 变量在 React 内联样式里可正常求值并参与级联，故 .dark 翻转时自动跟随。
const TOKEN = {
  border: 'var(--od-line, #ECE9E1)',
  textTertiary: 'var(--od-ink-3, #A2A69A)',
  text: 'var(--od-ink, #23261F)',
  textSecondary: 'var(--od-ink-2, #6E7266)',
} as const;

interface Props { subject: SubjectListItem }
export function SubjectCard({ subject }: Props) {
  // ponytail: 二级降级（airDate→年份、eps→集数），两者皆空兜底"暂无收录"
  const meta = subject.score > 0
    ? `${subject.score.toFixed(1)} 分`
    : [subject.airDate && subject.airDate.slice(0, 4), subject.eps > 0 && `${subject.eps} 集`].filter(Boolean).join(' · ') || '暂无收录';
  return (
    <Link to={`/subject/${subject.id}`} style={{ display: 'block', color: 'inherit', textDecoration: 'none' }}>
      <div className="od-card-img" style={{ aspectRatio: '3/4', background: TOKEN.border, overflow: 'hidden' }}>
        {subject.image
          ? <img src={subject.image} alt={subject.nameCn ?? subject.name} style={{ width: '100%', height: '100%', objectFit: 'cover' }} loading="lazy" />
          : <div style={{ height: '100%', display: 'flex', alignItems: 'center', justifyContent: 'center', color: TOKEN.textTertiary }}>暂无封面</div>}
      </div>
      <div style={{ fontSize: 14, lineHeight: '20px', marginTop: 6, overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap', color: TOKEN.text }}>{subject.nameCn ?? subject.name}</div>
      <div style={{ fontSize: 12, color: TOKEN.textSecondary }}>{meta}</div>
    </Link>
  );
}
