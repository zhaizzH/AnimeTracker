import { useQuery } from '@tanstack/react-query';
import { useNavigate } from 'react-router-dom';
import { Statistic, Row, Col } from 'antd';
import { subjectsApi } from '@shared';
import { SubjectGrid } from '../components/SubjectGrid';

export default function Home() {
  const navigate = useNavigate();
  const today = new Date().getDay(); // 0=周日
  const total = useQuery({ queryKey: ['subjects', 'total'], queryFn: () => subjectsApi.list({ page: 1, size: 1 }) });
  const todayShows = useQuery({ queryKey: ['schedule', 'today'], queryFn: () => subjectsApi.schedule({ weekday: today, size: 20 }) });
  return (
    <div style={{ maxWidth: 1100, margin: '0 auto', padding: 24 }}>
      <Row gutter={24} style={{ marginBottom: 24 }}>
        <Col span={12}><Statistic title="条目总数" value={total.data?.total ?? 0} loading={total.isLoading} /></Col>
        <Col span={12}><Statistic title="今日放送" value={todayShows.data?.total ?? 0} loading={todayShows.isLoading} /></Col>
      </Row>
      <h2 style={{ fontSize: 24 }}>今日放送</h2>
      <SubjectGrid items={todayShows.data?.content ?? []} loading={todayShows.isLoading} onItemClick={(s) => navigate(`/subject/${s.id}`)} />
    </div>
  );
}
