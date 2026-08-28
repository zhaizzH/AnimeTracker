import { useEffect, useState } from 'react';
import { useQuery } from '@tanstack/react-query';
import { Link } from 'react-router-dom';
import { Statistic, Row, Col, Empty, Card } from 'antd';
import { subjectsApi } from '@shared';
import { SubjectGrid } from '../components/SubjectGrid';

const HERO_COUNT = 5;

export default function Home() {
  const today = new Date().getDay(); // 0=周日
  const total = useQuery({ queryKey: ['subjects', 'total'], queryFn: () => subjectsApi.list({ page: 1, size: 1 }) });
  const todayShows = useQuery({ queryKey: ['schedule', 'today'], queryFn: () => subjectsApi.schedule({ weekday: today, size: 100 }) }); // ponytail: 后端单页上限 100，首页一次取全，超上限时再谈分页
  const heroItems = todayShows.data?.content?.slice(0, HERO_COUNT) ?? [];
  const [active, setActive] = useState(0);

  // 数据刷新时回到第一张
  useEffect(() => { setActive(0); }, [todayShows.dataUpdatedAt]);
  // 单张时不自动轮播；prefers-reduced-motion 由 CSS 处理（禁过渡，切换瞬时完成）
  useEffect(() => {
    if (heroItems.length <= 1) return;
    const timer = setInterval(() => setActive((i) => (i + 1) % heroItems.length), 5000);
    return () => clearInterval(timer);
  }, [heroItems.length]);

  return (
    <div style={{ maxWidth: 1400, margin: '0 auto', padding: 24 }}>
      <Row gutter={24} align="stretch" style={{ marginBottom: 24 }}>
        <Col xs={24} lg={8}>
          <Card className="home-side">
            <h2 className="home-side__title">番剧<span className="home-side__accent">全量</span>资料库</h2>
            <dl className="home-side__tags">
              <dt>数据来源</dt><dd>Bangumi 权威数据</dd>
              <dt>每周放送</dt><dd>逐日刷新播出表</dd>
              <dt>追番管理</dt><dd>收藏 · 进度同步</dd>
              <dt>AI 助手</dt><dd>智能推荐新番</dd>
            </dl>
            <div className="home-side__actions">
              <Link className="home-side__btn home-side__btn--primary" to="/anime">
                <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" aria-hidden="true"><path d="m21 21-4.34-4.34" /><circle cx="11" cy="11" r="8" /></svg>
                番剧索引
              </Link>
              <Link className="home-side__btn" to="/schedule">
                <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" aria-hidden="true"><path d="M8 2v4" /><path d="M16 2v4" /><rect width="18" height="18" x="3" y="4" rx="2" /><path d="M3 10h18" /><path d="M8 14h.01" /><path d="M12 14h.01" /><path d="M16 14h.01" /></svg>
                每周追番
              </Link>
            </div>
            <div className="home-side__stats">
              <Statistic title="条目总数" value={total.data?.total ?? 0} loading={total.isLoading} />
              <Statistic title="今日放送" value={todayShows.data?.total ?? 0} loading={todayShows.isLoading} />
            </div>
          </Card>
        </Col>
        <Col xs={24} lg={16}>
          {heroItems.length > 0 && (
            <div className="od-hero">
              {heroItems.length > 1 && <div key={active} className="od-hero__progress" />}
              {heroItems.map((s, i) => (
                <div key={s.id} className={`od-hero__slide${i === active ? ' is-active' : ''}`}>
                  <div className="od-hero__fallback" aria-hidden="true" />
                  {s.image && (
                    <img
                      className="od-hero__img"
                      src={s.image}
                      alt={s.nameCn ?? s.name}
                      fetchPriority={i === 0 ? 'high' : 'low'}
                      onError={(e) => { e.currentTarget.style.display = 'none'; }}
                    />
                  )}
                  <div className="od-hero__scrim" aria-hidden="true" />
                  <div className="od-hero__body">
                    <div className="od-hero__kicker">今日高分 · 第 {i + 1} 名</div>
                    <h1 className="od-hero__title">{s.nameCn ?? s.name}</h1>
                    <div className="od-hero__meta">
                      <span>{s.score > 0 ? `${s.score.toFixed(1)} 分` : '未评分'}</span>
                      <span className="od-hero__dot" aria-hidden="true" />
                      {s.eps > 0 && (
                        <>
                          <span className="od-hero__dot" aria-hidden="true" />
                          <span>{s.eps} 集</span>
                        </>
                      )}
                      {s.collectionTotal != null && (
                        <>
                          <span className="od-hero__dot" aria-hidden="true" />
                          <span>{s.collectionTotal} 人收藏</span>
                        </>
                      )}
                    </div>
                    <Link className="od-hero__cta" to={`/subject/${s.id}`}>
                      查看详情
                    </Link>
                  </div>
                </div>
              ))}
              {heroItems.length > 1 && (
                <>
                  <div className="od-hero__counter" aria-hidden="true">{active + 1} / {heroItems.length}</div>
                  <div className="od-hero__dots" role="tablist" aria-label="今日高分番剧">
                    {heroItems.map((s, i) => (
                      <button
                        key={s.id}
                        type="button"
                        role="tab"
                        aria-selected={i === active}
                        aria-label={`第 ${i + 1} 名：${s.nameCn ?? s.name}`}
                        className={`od-hero__dot-btn${i === active ? ' is-active' : ''}`}
                        onClick={() => setActive(i)}
                      />
                    ))}
                  </div>
                </>
              )}
            </div>
          )}
        </Col>
      </Row>
      <h2 style={{ fontSize: 24 }}>今日放送</h2>
      {todayShows.data?.content?.length ? (
        <SubjectGrid items={todayShows.data.content} loading={todayShows.isLoading} />
      ) : (
        <Empty description="今日暂无放送" style={{ margin: 40 }} />
      )}
    </div>
  );
}