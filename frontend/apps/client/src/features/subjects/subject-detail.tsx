import Image from 'next/image';
import { copy } from '@/content/zh-CN';
import { seasonFromAirDate } from '@/features/subjects/model';
import type { paths } from '@animetracker/api-contract';
import styles from './subject-detail.module.css';

// 详情与剧集的 schema 是内联类型（非命名 schema），从 paths 派生，避免手写 DTO。
type DetailData = NonNullable<
  NonNullable<
    NonNullable<paths['/api/client/subjects/{id}']['get']['responses'][200]>['content']['application/json']
  >['data']
>;
type EpisodeArray = NonNullable<
  NonNullable<
    paths['/api/client/subjects/{id}/episodes']['get']['responses'][200]
  >['content']['application/json']
>['data'];

export type SubjectDetailModel = DetailData;
export type EpisodeModel = NonNullable<EpisodeArray>[number];

export type SubjectDetailProps = {
  subject: SubjectDetailModel;
  episodes: EpisodeModel[];
};

function scoreLabel(score?: number): string {
  return score != null ? `${score} ${copy.subject.scoreUnit}` : copy.common.notAvailable;
}

/** 关联作品链接的可见文本：`关联作品：迷宫饭`。 */
function relationLabel(nameCn?: string, name?: string): string {
  const title = nameCn || name || copy.common.notAvailable;
  return `${copy.detail.relations}：${title}`;
}

/**
 * 番剧详情页正文：标题、评分/年份/季度/标签、简介、剧集列表（region）、关联作品。
 * 空值统一在此兜底，SSR 后 JS 执行前即可见。
 */
export function SubjectDetail({ subject, episodes }: SubjectDetailProps) {
  const title = subject.nameCn || subject.name || copy.common.notAvailable;
  const originalTitle = subject.nameCn ? subject.name : undefined;
  const coverAlt = `${title} ${copy.subject.cover}`;
  const meta: Array<[string, string]> = [
    [copy.detail.score, scoreLabel(subject.score)],
    [copy.detail.year, subject.airDate ? subject.airDate.slice(0, 4) : copy.common.notAvailable],
    [copy.detail.season, seasonFromAirDate(subject.airDate) ?? copy.common.notAvailable],
    [copy.detail.airedAt, subject.airDate ?? copy.common.notAvailable],
  ];

  const cover = subject.image ? (
    <Image src={subject.image} alt={coverAlt} fill sizes="(min-width: 64rem) 18rem, 45vw" priority />
  ) : (
    <span className={styles.fallback} aria-hidden="true">
      {title.slice(0, 1)}
    </span>
  );

  return (
    <main id="main" className={styles.page}>
      <article>
        <header className={styles.header}>
          <div className={styles.cover}>{cover}</div>
          <div className={styles.heading}>
            <h1 className={styles.title}>{title}</h1>
            {originalTitle ? <p className={styles.original}>{originalTitle}</p> : null}
            <dl className={styles.meta}>
              {meta.map(([label, value]) => (
                <div key={label} className={styles.metaItem}>
                  <dt>{label}</dt>
                  <dd>{value}</dd>
                </div>
              ))}
            </dl>
          </div>
        </header>

        {subject.tags && subject.tags.length > 0 ? (
          <section className={styles.block}>
            <h2>{copy.detail.tags}</h2>
            <ul className={styles.tags}>
              {subject.tags.map((tag) => (
                <li key={tag.id ?? tag.name} className={styles.tag}>
                  {tag.name}
                </li>
              ))}
            </ul>
          </section>
        ) : null}

        {subject.summary ? (
          <section className={styles.block}>
            <h2>{copy.detail.overview}</h2>
            <p className={styles.summary}>{subject.summary}</p>
          </section>
        ) : null}

        {episodes.length > 0 ? (
          <section className={styles.block} role="region" aria-label={copy.detail.episodes}>
            <h2>{copy.detail.episodes}</h2>
            <ol className={styles.episodes}>
              {episodes.map((ep) => (
                <li key={ep.id ?? `${ep.subjectId}-${ep.sort}`} className={styles.episode}>
                  <span className={styles.episodeNo}>第 {ep.sort} 集</span>
                  <span>{ep.nameCn || ep.name || copy.common.notAvailable}</span>
                  {ep.airdate ? <time dateTime={ep.airdate}>{ep.airdate}</time> : null}
                </li>
              ))}
            </ol>
          </section>
        ) : null}

        {subject.relations && subject.relations.length > 0 ? (
          <section className={styles.block}>
            <h2>{copy.detail.relations}</h2>
            <ul className={styles.relations}>
              {subject.relations.map((rel, index) => {
                const related = rel.relatedSubject;
                if (!related) return null;
                return (
                  <li key={related.id ?? index}>
                    <a href={`/subjects/${related.id}`}>{relationLabel(related.nameCn, related.name)}</a>
                  </li>
                );
              })}
            </ul>
          </section>
        ) : null}
      </article>
    </main>
  );
}
