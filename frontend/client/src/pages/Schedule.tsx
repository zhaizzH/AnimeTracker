import { useState, useMemo } from 'react';
import { Tabs, Row, Col, Select, Spin, Empty } from 'antd';
import { useQuery } from '@tanstack/react-query';
import { subjectsApi } from '@/api/subjects';
import SubjectCard from '@/components/SubjectCard';
import { getCurrentQuarter } from '@/utils';
import type { SubjectListVO } from '@/types';

const WEEKDAYS = ['周日', '周一', '周二', '周三', '周四', '周五', '周六'];

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
    queryFn: () => subjectsApi.schedule({
      weekday: -1,
      year: selectedYear,
      quarter: selectedQuarter,
      size: 100,
    }),
  });

  const grouped = useMemo(() => {
    const map: Record<number, SubjectListVO[]> = {};
    data?.content?.forEach((s: SubjectListVO) => {
      const wd = s.airWeekday ?? 0;
      if (!map[wd]) map[wd] = [];
      map[wd].push(s);
    });
    return map;
  }, [data]);

  const years = Array.from({ length: year + 10 - 1950 + 1 }, (_, i) => 1950 + i);

  const tabItems = Array.from({ length: 7 }, (_, i) => ({
    key: String(i),
    label: `${WEEKDAYS[i]} (${(grouped[i] || []).length})`,
    children: (
      <Row gutter={[16, 16]} style={{ marginTop: 16 }}>
        {(grouped[i] || []).map(s => (
          <Col key={s.id}>
            <SubjectCard
              subject={s}
              extra={<span style={{ color: '#1677ff' }}>{s.airDate || ''}</span>}
            />
          </Col>
        ))}
        {(!grouped[i] || grouped[i].length === 0) && (
          <Col span={24}><Empty description="本周日无放送" /></Col>
        )}
      </Row>
    ),
  }));

  return (
    <div>
      <div style={{ marginBottom: 16 }}>
        <Select value={selectedYear} onChange={setSelectedYear} style={{ width: 100, marginRight: 8 }}
          options={years.map(y => ({ value: y, label: `${y}年` }))} />
        <Select value={selectedQuarter} onChange={setSelectedQuarter} style={{ width: 80 }}
          options={quarters.map(q => ({ value: q.value, label: q.label }))} />
      </div>

      {isLoading ? <Spin style={{ display: 'block', margin: '40px auto' }} /> : (
        <Tabs defaultActiveKey={String(new Date().getDay())} items={tabItems} />
      )}
    </div>
  );
}
