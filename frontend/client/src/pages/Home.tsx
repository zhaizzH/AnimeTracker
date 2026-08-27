import { useEffect, useState } from 'react';
import { useQuery } from '@tanstack/react-query';
import { useNavigate } from 'react-router-dom';
import { Statistic, Row, Col, Empty } from 'antd';
import { subjectsApi } from '@shared';
import { SubjectGrid } from '../components/SubjectGrid';

const HERO_COUNT = 5;

export default function Home() {
  const navigate = useNavigate();
  const today = new Date().getDay(); // 0=周日
  const total = useQuery({ queryKey: ['subjects', 'total'], queryFn: () => subjectsApi.list({ page: 1, size: 1 }) });
  const todayShows = useQuery({ queryKey: ['schedule', 'today'], queryFn: () => subjectsApi.schedule({ weekday: today, size: 50 }) });
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
      {heroItems.length > 0 && (
        <div className="od-hero" style={{ marginBottom: 32 }}>
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
                  <span>{s.eps} 集</span>
                  <span className="od-hero__dot" aria-hidden="true" />
                  <span>{s.collectionTotal} 人收藏</span>
                </div>
                <button
                  type="button"
                  className="od-hero__cta"
                  onClick={() => navigate(`/subject/${s.id}`)}
                >
                  查看详情
                </button>
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
      <Row gutter={24} style={{ marginBottom: 24 }}>
        <Col span={12}><Statistic title="条目总数" value={total.data?.total ?? 0} loading={total.isLoading} /></Col>
        <Col span={12}><Statistic title="今日放送" value={todayShows.data?.total ?? 0} loading={todayShows.isLoading} /></Col>
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
