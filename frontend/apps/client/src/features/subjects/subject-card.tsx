import Image from 'next/image';
import { copy } from '@/content/zh-CN';
import type { SubjectCardModel } from './model';
import styles from './subject-card.module.css';

export type SubjectCardProps = {
  subject: SubjectCardModel;
  priority?: boolean;
};

/**
 * 单个番剧卡片：每张卡片只有一个链接，指向 /subjects/{id}。
 * 封面缺省时回退为文字占位，评分与集数以文本暴露（不只用颜色区分）。
 */
export function SubjectCard({ subject, priority = false }: SubjectCardProps) {
  const { title, originalTitle, imageUrl, scoreLabel, seasonLabel, episodeLabel, href } = subject;
  const coverAlt = `${title} ${copy.subject.cover}`;

  const cover = imageUrl ? (
    <Image src={imageUrl} alt={coverAlt} fill sizes="(min-width: 64rem) 12rem, 40vw" priority={priority} />
  ) : (
    <span className={styles.fallback} aria-hidden="true">
      {title.slice(0, 1)}
    </span>
  );

  return (
    <a className={styles.card} href={href}>
      <div className={styles.cover}>{cover}</div>
      <div className={styles.body}>
        <h3 className={styles.title}>{title}</h3>
        {originalTitle ? <p className={styles.original}>{originalTitle}</p> : null}
        <ul className={styles.meta}>
          <li>{seasonLabel}</li>
          <li>{episodeLabel}</li>
          <li>{scoreLabel}</li>
        </ul>
      </div>
    </a>
  );
}
