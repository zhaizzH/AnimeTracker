import { useState, useMemo } from 'react';
import { Tabs, Select, Spin } from 'antd';
import { useQuery } from '@tanstack/react-query';
import { subjectsApi } from '@/api/subjects';
import SubjectCard from '@/components/SubjectCard';
import PageHeading from '@/components/PageHeading';
import { getCurrentQuarter } from '@/utils';
import type { SubjectListVO } from '@/types';

const WEEKDAYS = ['周一', '周二', '周三', '周四', '周五', '周六', '周日'];
const toMondayBased = (d: number) => (d + 6) % 7;

const quarters = [
  { value: 'spring', label: '春' },
  { value: 'summer', label: '夏' },
  { value: 'autumn', label: '秋' },
  { value: 'winter', label: '冬' },
];

export default function Schedule() {
  const year = new Date().getFullYear();
  const [selectedYear, setSelectedYear] = useState(year);
  const [selectedQuarter, setSelectedQuarter] = useState(getCurrentQuarter());

  const { data, isLoading } = useQuery({
    queryKey: ['schedule', selectedYear, selectedQuarter],
    queryFn: () => subjectsApi.scheduleAll({
      weekday: -1,
      year: selectedYear,
      quarter: selectedQuarter,
    }),
  });

  const grouped = useMemo(() => {
    const map: Record<number, SubjectListVO[]> = {};
    data?.content?.forEach((s: SubjectListVO) => {
      const wd = toMondayBased(s.airWeekday ?? 0);
      if (!map[wd]) map[wd] = [];
      map[wd].push(s);
    });
    return map;
  }, [data]);

  const years = Array.from({ length: year + 10 - 1950 + 1 }, (_, i) => 1950 + i);
  const quarterLabel = quarters.find(q => q.value === selectedQuarter)?.label || '';

  const tabItems = Array.from({ length: 7 }, (_, i) => ({
    key: String(i),
    label: `${WEEKDAYS[i]} (${(grouped[i] || []).length})`,
    children: (
      <div className="day-panel">
        <div className="day-panel-title">
          <span>{WEEKDAYS[i]}放送</span>
          <span>{(grouped[i] || []).length} 部</span>
        </div>
        <div className="poster-grid">
          {(grouped[i] || []).map(s => (
            <SubjectCard subject={s} key={s.id} extra={s.airDate || ''} />
          ))}
        </div>
        {(!grouped[i] || grouped[i].length === 0) && (
          <p style={{ margin: 0, color: 'var(--ink-soft)' }}>当日暂无放送。</p>
        )}
      </div>
    ),
  }));

  return (
    <div>
      <PageHeading
        index="02 / AIRING"
        title="放送表"
        subtitle={`${selectedYear} 年 ${quarterLabel}季 · 按周查看`}
        actions={
          <>
            <Select
              value={selectedYear}
              onChange={setSelectedYear}
              style={{ width: 104 }}
              options={years.map(y => ({ value: y, label: `${y}年` }))}
            />
            <Select
              value={selectedQuarter}
              onChange={setSelectedQuarter}
              style={{ width: 76 }}
              options={quarters.map(q => ({ value: q.value, label: `${q.label}季` }))}
            />
          </>
        }
      />

      {isLoading ? <Spin className="paper-loading" /> : (
        <Tabs
          className="schedule-tabs paper-tabs"
          defaultActiveKey={String(toMondayBased(new Date().getDay()))}
          items={tabItems}
        />
      )}
    </div>
  );
}
