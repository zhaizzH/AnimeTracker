import { useState, useEffect } from 'react';
import { Row, Col, Card, Statistic, Tabs } from 'antd';
import { subjectsApi } from '@/api/subjects';
import SubjectCard from '@/components/SubjectCard';
import { getCurrentQuarter } from '@/utils';
import type { SubjectListVO } from '@/types';

const WEEKDAYS = ['周日', '周一', '周二', '周三', '周四', '周五', '周六', '周日'];

export default function Home() {
  const [totalSubjects, setTotalSubjects] = useState(0);
  const [seasonTotal, setSeasonTotal] = useState(0);
  const [scheduleData, setScheduleData] = useState<Record<number, SubjectListVO[]>>({});

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
        const result = await subjectsApi.schedule({ weekday: -1, size: 100 }) as any;
        const grouped: Record<number, SubjectListVO[]> = {};
        (result.content || []).forEach((s: SubjectListVO) => {
          const wd = s.airWeekday ?? 0;
          if (!grouped[wd]) grouped[wd] = [];
          grouped[wd].push(s);
        });
        setScheduleData(grouped);
      } catch { /* ignore */ }
    }
    fetchSchedule();
  }, []);

  const today = new Date().getDay();
  const tabItems = Array.from({ length: 7 }, (_, i) => ({
    key: String(i),
    label: WEEKDAYS[i],
    children: (
      <Row gutter={[16, 16]}>
        {(scheduleData[i] || []).map(subject => (
          <Col key={subject.id}>
            <SubjectCard
              subject={subject}
              extra={<span style={{ color: '#1677ff' }}>{subject.airDate || ''}</span>}
            />
          </Col>
        ))}
        {(!scheduleData[i] || scheduleData[i].length === 0) && (
          <Col><span style={{ color: '#999' }}>暂无放送</span></Col>
        )}
      </Row>
    ),
  }));

  return (
    <div>
      <Row gutter={24} style={{ marginBottom: 24 }}>
        <Col span={12}>
          <Card><Statistic title="条目总数" value={totalSubjects} /></Card>
        </Col>
        <Col span={12}>
          <Card><Statistic title="本季新番" value={seasonTotal} /></Card>
        </Col>
      </Row>

      <Tabs defaultActiveKey={String(today)} items={tabItems} />
    </div>
  );
}
