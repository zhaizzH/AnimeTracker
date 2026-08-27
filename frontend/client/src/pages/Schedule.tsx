import { useState } from 'react';
import { useQuery } from '@tanstack/react-query';
import { useSearchParams } from 'react-router-dom';
import { Select, Space, Tabs } from 'antd';
import { subjectsApi } from '@shared';
import { SubjectGrid } from '../components/SubjectGrid';

const QUARTERS = { spring: '春', summer: '夏', autumn: '秋', winter: '冬' };
const WEEK = ['周一', '周二', '周三', '周四', '周五', '周六', '周日'];
const weekdayIndex = (w: number) => (w + 6) % 7; // JS getDay() 0=周日 → 周一=0
// 后端 airWeekday/weekday: 0=周日…6=周六；标签页下标 i: 0=周一…6=周日，互转
const tabToWeekday = (i: number) => (i + 1) % 7;

export default function Schedule() {
  const now = new Date();
  const [params, setParams] = useSearchParams();
  const year = Number(params.get('year') ?? now.getFullYear());
  const quarter = params.get('quarter') ?? 'summer';
  const active = params.get('tab') ?? String(weekdayIndex(now.getDay()));
  const patch = (p: Record<string, string>) => {
    const next = { year: String(year), quarter, tab: active, ...p };
    setParams(next);
  };
  // 后端按 airWeekday 升序分页、size 上限 100 会截断尾部星期 → 按天查询；仅加载当前查看的星期
  const { data, isLoading } = useQuery({ queryKey: ['schedule', year, quarter, active], queryFn: () => subjectsApi.schedule({ year, quarter, weekday: tabToWeekday(Number(active)), size: 100 }) });
  const items = WEEK.map((label, i) => ({ key: String(i), label, children: <SubjectGrid items={(data?.content ?? []).filter((s) => s.airWeekday === tabToWeekday(i))} loading={isLoading} /> }));
  return (
    <div style={{ maxWidth: 1400, margin: '0 auto', padding: 24 }}>
      <Space style={{ marginBottom: 16 }}>
        <Select value={year} onChange={(v) => patch({ year: String(v) })} options={[year - 1, year, year + 1].map((y) => ({ value: y, label: `${y}` }))} style={{ width: 110 }} />
        <Select value={quarter} onChange={(v) => patch({ quarter: v })} options={Object.entries(QUARTERS).map(([v, label]) => ({ value: v, label }))} style={{ width: 90 }} />
      </Space>
      <Tabs items={items} activeKey={active} onChange={(k) => patch({ tab: k })} />
    </div>
  );
}
