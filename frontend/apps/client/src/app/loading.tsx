import { copy } from '@/content/zh-CN';
import { SubjectGridSkeleton } from '@/components/feedback/subject-grid-skeleton';

/** 首页流式渲染期间的占位：保留三个板块标题，正文用骨架占位。 */
export default function Loading() {
  const sections = [copy.home.seasonal, copy.home.popular, copy.home.todaySchedule];
  return (
    <main
      style={{ display: 'flex', flexDirection: 'column', gap: 'var(--space-10)', padding: 'var(--space-6) var(--space-4) var(--space-12)' }}
    >
      {sections.map((heading) => (
        <section key={heading} style={{ display: 'flex', flexDirection: 'column', gap: 'var(--space-4)' }}>
          <header>
            <h2 style={{ margin: 0, fontSize: 'var(--text-xl)' }}>{heading}</h2>
          </header>
          <SubjectGridSkeleton count={6} />
        </section>
      ))}
    </main>
  );
}
