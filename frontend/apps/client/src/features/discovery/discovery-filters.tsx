import { copy } from '@/content/zh-CN';
import type { DiscoveryQuery, SortField } from './search-params';
import styles from './discovery.module.css';

export type DiscoveryTag = { name?: string };

export type DiscoveryFiltersProps = {
  query: DiscoveryQuery;
  tags: DiscoveryTag[];
  years: number[];
};

const WEEKDAYS_BACKEND = Array.from({ length: 7 }, (_, w) => w); // 0=周日 … 6=周六
const SCORE_MIN_OPTIONS = ['0', '6', '7', '8', '9'];

const SORT_OPTIONS: { value: SortField; label: string }[] = [
  { value: 'collection_total', label: copy.discovery.sortPopular },
  { value: 'score', label: copy.discovery.sortScore },
  { value: 'rank', label: copy.discovery.sortRank },
];

/** 后端星期 0=周日…6=周六 对齐到文案数组下标。 */
function weekdayLabel(backendWeekday: number): string {
  return copy.schedule.weekdays[(backendWeekday + 6) % 7];
}

/**
 * 发现页筛选条：原生 form GET 提交到 /discover，无需 JS 即可工作。
 * 所有筛选通过原生 input/select 承载，值取自 URL（defaultValue，节水化引导）。
 */
export function DiscoveryFilters({ query, tags, years }: DiscoveryFiltersProps) {
  return (
    <form className={styles.filters} method="get" action="/discover">
      <div className={styles.fieldGroup}>
        <input
          className={styles.input}
          type="text"
          name="q"
          aria-label={copy.search.label}
          placeholder={copy.discovery.keywordPlaceholder}
          defaultValue={query.q}
        />
      </div>

      <label className={styles.field}>
        <span className={styles.fieldLabel}>{copy.discovery.tag}</span>
        <div className={styles.tagList} role="group" aria-label={copy.discovery.tag}>
          {tags.map((tag) => {
            const name = tag.name ?? '';
            return (
              <label key={name} className={styles.check}>
                <input type="checkbox" name="tag" value={name} defaultChecked={query.tag.includes(name)} />
                <span>{name}</span>
              </label>
            );
          })}
        </div>
      </label>

      <label className={styles.field}>
        <span className={styles.fieldLabel}>{copy.discovery.year}</span>
        <select className={styles.select} name="year" defaultValue={query.year ?? ''}>
          <option value="">{copy.common.all}</option>
          {years.map((y) => (
            <option key={y} value={y}>
              {y}
            </option>
          ))}
        </select>
      </label>

      <label className={styles.field}>
        <span className={styles.fieldLabel}>{copy.discovery.weekday}</span>
        <select className={styles.select} name="weekday" defaultValue={query.weekday ?? ''}>
          <option value="">{copy.common.all}</option>
          {WEEKDAYS_BACKEND.map((w) => (
            <option key={w} value={w}>
              {weekdayLabel(w)}
            </option>
          ))}
        </select>
      </label>

      <label className={styles.field}>
        <span className={styles.fieldLabel}>{copy.discovery.score}</span>
        <select className={styles.select} name="scoreMin" defaultValue={query.scoreMin ?? ''}>
          <option value="">{copy.common.all}</option>
          {SCORE_MIN_OPTIONS.map((s) => (
            <option key={s} value={s}>
              {s} {copy.subject.scoreUnit}
            </option>
          ))}
        </select>
      </label>

      <div className={styles.fieldGroup}>
        <label className={styles.fieldInline}>
          <span className={styles.fieldLabel}>{copy.discovery.sort}</span>
          <select className={styles.select} name="sort" defaultValue={query.sort ?? ''}>
            <option value="">{copy.common.all}</option>
            {SORT_OPTIONS.map((opt) => (
              <option key={opt.value} value={opt.value}>
                {opt.label}
              </option>
            ))}
          </select>
        </label>

        <label className={styles.fieldInline}>
          <span className={styles.fieldLabel}>{copy.discovery.direction}</span>
          <select className={styles.select} name="order" defaultValue={query.order}>
            <option value="desc">{copy.discovery.directionDesc}</option>
            <option value="asc">{copy.discovery.directionAsc}</option>
          </select>
        </label>
      </div>

      <div className={styles.actions}>
        <button className={styles.button} type="submit">
          {copy.discovery.filter}
        </button>
        <a className={styles.link} href="/discover">
          {copy.discovery.reset}
        </a>
      </div>
    </form>
  );
}
