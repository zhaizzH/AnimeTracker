import { copy } from '@/content/zh-CN';
import { SubjectCard } from '@/features/subjects/subject-card';
import { EmptyState } from '@/components/feedback/empty-state';
import { ErrorState } from '@/components/feedback/error-state';
import type { SubjectCardModel } from '@/features/subjects/model';
import { toDiscoverySearchParams, type DiscoveryQuery } from './search-params';
import styles from './discovery.module.css';

export type DiscoveryResultsProps = {
  query: DiscoveryQuery;
  subjects: SubjectCardModel[];
  total: number;
  /** 取数失败时的安全错误信息（非异常页面） */
  errorMessage?: string;
  /** 后端返回的请求编号，便于排查 */
  requestId?: string;
};

function PageLink({ query, page, children }: { query: DiscoveryQuery; page: number; children: React.ReactNode }) {
  const qs = toDiscoverySearchParams(query, { page });
  return (
    <a className={styles.paginationLink} href={`/discover?${qs}`}>
      {children}
    </a>
  );
}

/**
 * 发现页结果区：卡片网格 + 结果数 + 链接式分页。
 * 分页用规范化查询串（toDiscoverySearchParams），可分享、无需 JS。
 */
export function DiscoveryResults({ query, subjects, total, errorMessage, requestId }: DiscoveryResultsProps) {
  const totalPages = Math.max(1, Math.ceil(total / query.size));
  const hasPrev = query.page > 1;
  const hasNext = query.page < totalPages;

  return (
    <section className={styles.layout}>
      <h1 className={styles.title}>{copy.discovery.title}</h1>
      {errorMessage ? (
        <ErrorState message={errorMessage} requestId={requestId} retryHref="/discover" />
      ) : (
        <>
          <p className={styles.count}>{copy.discovery.results.replace('{{total}}', String(total))}</p>
          {subjects.length > 0 ? (
            <div className={styles.grid}>
              {subjects.map((subject) => (
                <SubjectCard key={subject.id} subject={subject} />
              ))}
            </div>
          ) : (
            <EmptyState message={copy.discovery.empty} />
          )}
          {subjects.length > 0 && (
            <nav className={styles.pagination} aria-label={copy.discovery.title}>
              {hasPrev ? (
                <PageLink query={query} page={query.page - 1}>
                  {copy.discovery.previous}
                </PageLink>
              ) : null}
              <span className={styles.pageInfo}>
                {query.page} / {totalPages}
              </span>
              {hasNext ? (
                <PageLink query={query} page={query.page + 1}>
                  {copy.discovery.next}
                </PageLink>
              ) : null}
            </nav>
          )}
        </>
      )}
    </section>
  );
}
