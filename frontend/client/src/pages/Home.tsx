import { useEffect, useState } from 'react';
import { useQuery } from '@tanstack/react-query';
import { Link } from 'react-router-dom';
import { subjectsApi } from '@shared';
import { SubjectGrid } from '@/components/SubjectGrid';

const HERO_COUNT = 5;

export default function Home() {
  const today = new Date().getDay(); // 0=周日
  const total = useQuery({ queryKey: ['subjects', 'total'], queryFn: () => subjectsApi.list({ page: 1, size: 1 }) });
  const todayShows = useQuery({ queryKey: ['schedule', 'today'], queryFn: () => subjectsApi.schedule({ weekday: today, size: 100 }) });
  const heroItems = todayShows.data?.content?.slice(0, HERO_COUNT) ?? [];
  const [active, setActive] = useState(0);

  // 数据刷新时回到第一张
  useEffect(() => { setActive(0); }, [todayShows.dataUpdatedAt]);
  // 单张时不自动轮播；prefers-reduced-motion 由 CSS 处理
  useEffect(() => {
    if (heroItems.length <= 1) return;
    const timer = setInterval(() => setActive((i) => (i + 1) % heroItems.length), 5000);
    return () => clearInterval(timer);
  }, [heroItems.length]);

  return (
    <div className="mx-auto w-full max-w-[1400px] p-6">
      <div className="mb-6 grid gap-6 lg:grid-cols-3">
        <div className="rounded-xl border bg-card p-6">
          <h2 className="text-xl font-semibold">
            番剧<span className="text-primary">全量</span>资料库
          </h2>
          <dl className="mt-4 grid grid-cols-[auto_1fr] gap-x-4 gap-y-2 text-sm">
            <dt className="text-muted-foreground">数据来源</dt><dd>Bangumi 权威数据</dd>
            <dt className="text-muted-foreground">每周放送</dt><dd>逐日刷新播出表</dd>
            <dt className="text-muted-foreground">追番管理</dt><dd>收藏 · 进度同步</dd>
            <dt className="text-muted-foreground">AI 助手</dt><dd>智能推荐新番</dd>
          </dl>
          <div className="mt-5 flex gap-3">
            <Link className="rounded-md bg-primary px-4 py-2 text-sm text-primary-foreground hover:bg-primary/90" to="/anime">番剧索引</Link>
            <Link className="rounded-md border px-4 py-2 text-sm hover:bg-accent" to="/schedule">每周追番</Link>
          </div>
          <div className="mt-6 flex gap-8">
            <div>
              <div className="text-xs text-muted-foreground">条目总数</div>
              <div className="text-2xl font-semibold">{total.isLoading ? '—' : total.data?.total ?? 0}</div>
            </div>
            <div>
              <div className="text-xs text-muted-foreground">今日放送</div>
              <div className="text-2xl font-semibold">{todayShows.isLoading ? '—' : todayShows.data?.total ?? 0}</div>
            </div>
          </div>
        </div>

        <div className="lg:col-span-2">
          {heroItems.length > 0 && (
            <section
              className="relative aspect-[16/9] overflow-hidden rounded-xl border bg-muted"
              aria-label="今日高分番剧"
              data-testid="hero"
            >
              {heroItems.map((s, i) => (
                <div
                  key={s.id}
                  data-testid="hero-slide"
                  data-active={i === active ? 'true' : 'false'}
                  aria-hidden={i !== active}
                  className={
                    'absolute inset-0 transition-opacity duration-500 ' +
                    (i === active ? 'opacity-100' : 'pointer-events-none opacity-0')
                  }
                >
                  {s.image && (
                    <img
                      className="size-full object-cover"
                      src={s.image}
                      alt={s.nameCn ?? s.name}
                      fetchPriority={i === 0 ? 'high' : 'low'}
                      onError={(e) => { e.currentTarget.style.display = 'none'; }}
                    />
                  )}
                  <div className="absolute inset-0 bg-gradient-to-t from-black/80 via-black/30 to-transparent" aria-hidden />
                  <div className="absolute inset-x-0 bottom-0 p-6 text-white">
                    <div className="text-xs text-white/70">今日高分 · 第 {i + 1} 名</div>
                    <h1 data-testid="hero-title" className="mt-1 text-2xl font-semibold">{s.nameCn ?? s.name}</h1>
                    <div className="mt-2 flex items-center gap-2 text-sm text-white/85">
                      <span>{s.score > 0 ? `${s.score.toFixed(1)} 分` : '未评分'}</span>
                      {s.eps > 0 && <><span aria-hidden>·</span><span>{s.eps} 集</span></>}
                      {s.collectionTotal != null && <><span aria-hidden>·</span><span>{s.collectionTotal} 人收藏</span></>}
                    </div>
                    <Link className="mt-3 inline-block rounded-md bg-white/90 px-4 py-1.5 text-sm text-black hover:bg-white" to={`/subject/${s.id}`}>
                      查看详情
                    </Link>
                  </div>
                </div>
              ))}
              {heroItems.length > 1 && (
                <div className="absolute right-6 bottom-6 flex gap-2" role="tablist" aria-label="今日高分番剧">
                  {heroItems.map((s, i) => (
                    <button
                      key={s.id}
                      type="button"
                      role="tab"
                      aria-selected={i === active}
                      aria-label={`第 ${i + 1} 名：${s.nameCn ?? s.name}`}
                      className={'size-2.5 rounded-full ' + (i === active ? 'bg-white' : 'bg-white/40')}
                      onClick={() => setActive(i)}
                    />
                  ))}
                </div>
              )}
            </section>
          )}
        </div>
      </div>

      <h2 className="mb-4 text-xl font-semibold">今日放送</h2>
      <SubjectGrid items={todayShows.data?.content ?? []} loading={todayShows.isLoading} emptyText="今日暂无放送" />
    </div>
  );
}
