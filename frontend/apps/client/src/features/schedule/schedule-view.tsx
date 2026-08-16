import { copy } from '@/content/zh-CN';
import { SubjectCard } from '@/features/subjects/subject-card';
import { EmptyState } from '@/components/feedback/empty-state';
import { ErrorState } from '@/components/feedback/error-state';
import type { SubjectCardModel } from '@/features/subjects/model';
import { ALL_WEEKDAYS, quarterLabel, weekdayHref, type SeasonParams, type Weekday } from './season';
import styles from './schedule-view.module.css';

export type ScheduleViewProps = {
  /** 归一化后的季度参数（决定标题年份/季度与选择器链接） */
  params: SeasonParams;
  /** 当前强调的星期（URL 或今天），移动端只显示这一列 */
  selectedWeekday: Weekday;
  /** 星期 → 卡片列表 */
  grouped: Map<Weekday, SubjectCardModel[]>;
  /** 取数失败时的安全错误信息（布局仍渲染，只是列内不显示误导性空态） */
  errorMessage?: string;
};

/**
 * 放送时间表：桌面七列、移动端单选强调。
 * 全部星期始终在服务端 HTML 中渲染；CSS 在桌面展示七列、在移动端只显示
 * 选中星期所在列。移动端选择器是链接，切换星期即更新 URL，无需 JS。
 */
export function ScheduleView({ params, selectedWeekday, grouped, errorMessage }: ScheduleViewProps) {
  const seasonText = `${params.year} ${quarterLabel(params.quarter)}`;

  return (
    <main id="main" className={styles.page}>
      <h1 className={styles.title}>{copy.schedule.title}</h1>
      <p className={styles.season}>{seasonText}</p>

      {errorMessage ? (
        <ErrorState message={errorMessage} retryHref={weekdayHref(params, selectedWeekday)} />
      ) : null}

      <nav className={styles.selector} aria-label={copy.schedule.title}>
        {ALL_WEEKDAYS.map((weekday) => (
          <a
            key={weekday}
            className={weekday === selectedWeekday ? `${styles.dayLink} ${styles.dayLinkActive}` : styles.dayLink}
            aria-current={weekday === selectedWeekday ? 'page' : undefined}
            href={weekdayHref(params, weekday)}
          >
            {copy.schedule.weekdays[weekday - 1]}
          </a>
        ))}
      </nav>

      <div className={styles.board}>
        {ALL_WEEKDAYS.map((weekday) => {
          const cards = grouped.get(weekday) ?? [];
          const isSelected = weekday === selectedWeekday;
          return (
            <section
              key={weekday}
              aria-labelledby={`schedule-${weekday}`}
              className={isSelected ? styles.column : `${styles.column} ${styles.columnMuted}`}
            >
              <h2 id={`schedule-${weekday}`} className={styles.columnTitle}>
                {copy.schedule.weekdays[weekday - 1]}
              </h2>
              {cards.length > 0 ? (
                <div className={styles.cards}>
                  {cards.map((card) => (
                    <SubjectCard key={card.id} subject={card} />
                  ))}
                </div>
              ) : errorMessage ? null : (
                <EmptyState message={copy.schedule.empty} />
              )}
            </section>
          );
        })}
      </div>
    </main>
  );
}
