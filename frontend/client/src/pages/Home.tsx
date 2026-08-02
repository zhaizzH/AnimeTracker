import { useState, useEffect } from 'react';
import { Tabs } from 'antd';
import { subjectsApi } from '@/api/subjects';
import SubjectCard from '@/components/SubjectCard';
import PageHeading from '@/components/PageHeading';
import { getCurrentQuarter } from '@/utils';
import type { SubjectListVO } from '@/types';

const WEEKDAYS = ['周一', '周二', '周三', '周四', '周五', '周六', '周日'];
const toMondayBased = (d: number) => (d + 6) % 7;

function getWeekDates() {
  const today = new Date();
  const monday = new Date(today);
  monday.setDate(today.getDate() - toMondayBased(today.getDay()));
  return Array.from({ length: 7 }, (_, i) => {
    const date = new Date(monday);
    date.setDate(monday.getDate() + i);
    return date;
  });
}

export default function Home() {
  const [totalSubjects, setTotalSubjects] = useState(0);
  const [seasonTotal, setSeasonTotal] = useState(0);
  const [scheduleData, setScheduleData] = useState<Record<number, SubjectListVO[]>>({});
  const weekDates = getWeekDates();

  useEffect(() => {
    async function fetchStats() {
      try {
        const [all, season] = await Promise.all([
          subjectsApi.list({ page: 1, size: 1 }),
          subjectsApi.season(new Date().getFullYear(), getCurrentQuarter(), 1, 1),
        ]);
        setTotalSubjects((all as any).total || 0);
        setSeasonTotal((season as any).total || 0);
      } catch { /* ignore */ }
    }
    fetchStats();
  }, []);

  useEffect(() => {
    async function fetchSchedule() {
      try {
        const result = await subjectsApi.scheduleAll({ weekday: -1 });
        const grouped: Record<number, SubjectListVO[]> = {};
        result.content.forEach((s: SubjectListVO) => {
          const wd = toMondayBased(s.airWeekday ?? 0);
          if (!grouped[wd]) grouped[wd] = [];
          grouped[wd].push(s);
        });
        setScheduleData(grouped);
      } catch { /* ignore */ }
    }
    fetchSchedule();
  }, []);

  const today = toMondayBased(new Date().getDay());
  const todayList = scheduleData[today] || [];
  const weekRange = `${weekDates[0].getMonth() + 1}月${weekDates[0].getDate()}日 - ${weekDates[6].getMonth() + 1}月${weekDates[6].getDate()}日`;
  const tabItems = Array.from({ length: 7 }, (_, i) => ({
    key: String(i),
    label: `${WEEKDAYS[i]} ${weekDates[i].getMonth() + 1}/${weekDates[i].getDate()}${i === today ? ' · 今' : ''}`,
    children: (
      <div className="day-panel">
        <div className="day-panel-title">
          <span>{WEEKDAYS[i]}放送 · {weekDates[i].getMonth() + 1}月{weekDates[i].getDate()}日</span>
          <span>{(scheduleData[i] || []).length} 部</span>
        </div>
        <div className="poster-grid">
          {(scheduleData[i] || []).map(subject => (
            <SubjectCard
              subject={subject}
              key={subject.id}
              extra={subject.airDate || ''}
            />
          ))}
        </div>
        {(!scheduleData[i] || scheduleData[i].length === 0) && (
          <p style={{ margin: 0, color: 'var(--ink-soft)' }}>当日暂无放送。</p>
        )}
      </div>
    ),
  }));

  return (
    <div>
      <PageHeading
        index="01 / TODAY"
        title="今日放送"
        subtitle={`${weekRange} · 把本周的每一部番都记下来`}
      />

      <div className="home-stats">
        <div className="home-stat">
          <div className="home-stat-label">本季新番 / SEASON</div>
          <div className="home-stat-value">{seasonTotal}<small>部</small></div>
        </div>
        <div className="home-stat">
          <div className="home-stat-label">条目总数 / TOTAL</div>
          <div className="home-stat-value">{totalSubjects}<small>条</small></div>
        </div>
        <div className="home-stat">
          <div className="home-stat-label">今日放送 / AIRING</div>
          <div className="home-stat-value">{todayList.length}<small>部</small></div>
        </div>
      </div>

      <Tabs className="paper-tabs" defaultActiveKey={String(today)} items={tabItems} />
    </div>
  );
}
