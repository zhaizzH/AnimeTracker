import { Card, Col, Row, Segmented, Statistic } from 'antd';
import { useState } from 'react';
import { useQuery } from '@tanstack/react-query';
import { adminDashboardApi, type HotItemVO } from '@shared';
import { BarChart, LineChart } from '../components/charts';

export default function Dashboard() {
  const [days, setDays] = useState(30);
  const ov = useQuery({ queryKey: ['dash', 'overview'], queryFn: adminDashboardApi.overview });
  const tr = useQuery({ queryKey: ['dash', 'trends', days], queryFn: () => adminDashboardApi.trends(days) });
  const cs = useQuery({ queryKey: ['dash', 'cs'], queryFn: adminDashboardApi.collectionStats });
  const ss = useQuery({ queryKey: ['dash', 'ss'], queryFn: adminDashboardApi.subjectStats });
  const ht = useQuery({ queryKey: ['dash', 'hot'], queryFn: () => adminDashboardApi.hot(10) });

  const cards: Array<[string, number | undefined]> = [
    ['用户总数', ov.data?.userCount],
    ['番剧总数', ov.data?.subjectCount],
    ['收藏总数', ov.data?.collectionCount],
    ['今日新增用户', ov.data?.todayNewUsers],
    ['今日新增收藏', ov.data?.todayNewCollections],
    ['今日登录', ov.data?.todayLogins],
  ];
  return (
    <div>
      <Row gutter={[16, 16]}>
        {cards.map(([label, value]) => (
          <Col span={4} key={label}>
            <Card>
              <Statistic title={label} value={value ?? 0} loading={ov.isLoading} />
            </Card>
          </Col>
        ))}
      </Row>
      <Card style={{ marginTop: 16 }} title="趋势">
        <Segmented
          value={days}
          onChange={(v) => setDays(v as number)}
          options={[
            { label: '7天', value: 7 },
            { label: '30天', value: 30 },
            { label: '90天', value: 90 },
          ]}
        />
        <LineChart
          title="每日新增"
          x={(tr.data ?? []).map((t) => t.date)}
          series={[
            { name: '用户', data: (tr.data ?? []).map((t) => t.newUsers) },
            { name: '收藏', data: (tr.data ?? []).map((t) => t.newCollections) },
            { name: '登录', data: (tr.data ?? []).map((t) => t.logins) },
          ]}
        />
      </Card>
      <Row gutter={16} style={{ marginTop: 16 }}>
        <Col span={12}>
          <Card>
            <BarChart
              title="收藏类型分布"
              data={(cs.data?.types ?? []).map((t) => ({
                label: ['想看', '看过', '在看', '搁置', '抛弃'][t.type - 1] ?? String(t.type),
                value: t.count,
              }))}
            />
          </Card>
        </Col>
        <Col span={12}>
          <Card>
            <BarChart
              title="评分分布"
              data={(ss.data?.scoreCounts ?? []).map((r) => ({ label: String(r.rate), value: r.count }))}
            />
          </Card>
        </Col>
      </Row>
      <Row gutter={16} style={{ marginTop: 16 }}>
        <Col span={12}>
          <Card>
            <BarChart
              title="季度条目数"
              data={(ss.data?.seasons ?? []).map((s) => ({ label: s.seasonKey, value: s.count }))}
            />
          </Card>
        </Col>
        <Col span={12}>
          <Card title="热门 Top 10">
            <ol>
              {ht.data?.map((h: HotItemVO) => (
                <li key={h.id}>
                  {h.nameCn ?? h.name}（{h.collectionCount} 收藏）
                </li>
              ))}
            </ol>
          </Card>
        </Col>
      </Row>
    </div>
  );
}
