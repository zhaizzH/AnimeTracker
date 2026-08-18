import { useState } from 'react';
import { useQuery } from '@tanstack/react-query';
import { useNavigate } from 'react-router-dom';
import { Select, Space, Tabs } from 'antd';
import { subjectsApi } from '@shared';
import { SubjectGrid } from '../components/SubjectGrid';

const QUARTERS = { spring: '春', summer: '夏', autumn: '秋', winter: '冬' };
export default function Schedule() {
  const navigate = useNavigate();
  const now = new Date();
  const [year, setYear] = useState(now.getFullYear());
  const [quarter, setQuarter] = useState('summer');
  const { data, isLoading } = useQuery({ queryKey: ['schedule', year, quarter], queryFn: () => subjectsApi.schedule({ year, quarter, size: 100 }) });
  const items = Array.from({ length: 7 }, (_, i) => ({ key: String(i), label: ['周日', '周一', '周二', '周三', '周四', '周五', '周六'][i], children: <SubjectGrid items={(data?.content ?? []).filter((s) => s.airWeekday === i)} loading={isLoading} onItemClick={(s) => navigate(`/subject/${s.id}`)} /> }));
  return (
    <div style={{ maxWidth: 1100, margin: '0 auto', padding: 24 }}>
      <Space style={{ marginBottom: 16 }}>
        <Select value={year} onChange={setYear} options={[year - 1, year, year + 1].map((y) => ({ value: y, label: `${y}` }))} style={{ width: 110 }} />
        <Select value={quarter} onChange={setQuarter} options={Object.entries(QUARTERS).map(([v, label]) => ({ value: v, label }))} style={{ width: 90 }} />
      </Space>
      <Tabs items={items} />
    </div>
  );
}
