import { copy } from '@/content/zh-CN';
import { SubjectCard } from '@/features/subjects/subject-card';
import { EmptyState } from '@/components/feedback/empty-state';
import type { SubjectCardModel } from '@/features/subjects/model';
import styles from './public-home.module.css';

export type PublicHomeProps = {
  season: SubjectCardModel[];
  popular: SubjectCardModel[];
  today: SubjectCardModel[];
};

type Section = {
  heading: string;
  href: string;
  cards: SubjectCardModel[];
};

/**
 * 公开首页三个板块：本季新番 / 热门作品 / 今日放送。
 * 标题始终渲染（SSR 后在 JS 执行前即可见），数据缺失时以空态兜底。
 */
function SectionBlock({ heading, href, cards }: Section) {
  return (
    <section className={styles.section}>
      <header className={styles.header}>
        <h2>{heading}</h2>
        <a className={styles.more} href={href}>
          {copy.home.viewAll}
        </a>
      </header>
      {cards.length > 0 ? (
        <div className={styles.grid}>
          {cards.map((card) => (
            <SubjectCard key={card.id} subject={card} />
          ))}
        </div>
      ) : (
        <EmptyState message={copy.common.notAvailable} />
      )}
    </section>
  );
}

export function PublicHome({ season, popular, today }: PublicHomeProps) {
  const sections: Section[] = [
    { heading: copy.home.seasonal, href: '/discovery', cards: season },
    { heading: copy.home.popular, href: '/discovery?sort=score&order=desc', cards: popular },
    { heading: copy.home.todaySchedule, href: '/schedule', cards: today },
  ];

  return (
    <main className={styles.home}>
      {sections.map((section) => (
        <SectionBlock key={section.heading} {...section} />
      ))}
    </main>
  );
}

/** 当前年月季度与 ISO 星期（纯函数，便于测试与 SSR 无时区副作用）。 */
export type SeasonContext = {
  year: number;
  quarter: 'spring' | 'summer' | 'autumn' | 'winter';
  /** ISO 8601 星期：1=周一 … 7=周日 */
  isoWeekday: number;
};

export function getSeasonContext(now: Date = new Date()): SeasonContext {
  const month = now.getMonth() + 1;
  const quarter =
    month >= 3 && month <= 5
      ? 'spring'
      : month >= 6 && month <= 8
        ? 'summer'
        : month >= 9 && month <= 11
          ? 'autumn'
          : 'winter';
  // getDay(): 0=周日 … 6=周六 → ISO: 1=周一 … 7=周日
  const isoWeekday = ((now.getDay() + 6) % 7) + 1;
  return { year: now.getFullYear(), quarter, isoWeekday };
}

/** 后端星期列 0=周日 … 6=周六，与 ISO 星期（1=周一…7=周日）的换算。 */
export function isoWeekdayToBackend(isoWeekday: number): number {
  return isoWeekday % 7;
}
