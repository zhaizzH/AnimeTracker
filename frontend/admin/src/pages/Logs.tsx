import { useMemo, useState } from 'react';
import { useQuery } from '@tanstack/react-query';
import { Card, Col, DatePicker, Input, Row, Select, Space, Statistic, Table } from 'antd';
import { adminLogsApi } from '@shared';

export default function Logs() {
  const [filter, setFilter] = useState<Record<string, unknown>>({});
  const [page, setPage] = useState(1);
  const { data, isLoading } = useQuery({ queryKey: ['logs', filter, page], queryFn: () => adminLogsApi.list({ page, size: 20, ...filter }) });
  const stats = data?.content.stats;
  return (
    <div>
      <Row gutter={[8, 8]} style={{ marginBottom: 12 }}>
        <Col><Select allowClear placeholder="模块" style={{ width: 130 }} onChange={(v) => { setFilter((f) => ({ ...f, module: v })); }} options={['AUTH', 'USER', 'SUBJECT', 'IMPORT', 'ADMIN'].map((m) => ({ value: m, label: m }))} /></Col>
        <Col><Select allowClear placeholder="状态" style={{ width: 110 }} onChange={(v) => { setFilter((f) => ({ ...f, status: v })); }} options={[{ value: 0, label: '成功' }, { value: 1, label: '失败' }]} /></Col>
        <Col><Input placeholder="用户名/邮箱" style={{ width: 160 }} allowClear onBlur={(e) => setFilter((f) => ({ ...f, username: e.target.value }))} /></Col>
        <Col><DatePicker.RangePicker onChange={(r) => setFilter((f) => ({ ...f, start: r?.[0]?.format('YYYY-MM-DD'), end: r?.[1]?.format('YYYY-MM-DD') }))} /></Col>
      </Row>
      <Row gutter={16} style={{ marginBottom: 16 }}>
        {[['总数', stats?.total], ['成功', stats?.successCount], ['失败', stats?.failedCount], ['平均耗时(ms)', stats?.avgDurationMs]].map(([label, v]) => (
          <Col span={6} key={label as string}><Card size="small"><Statistic title={label as string} value={v ?? 0} /></Card></Col>
        ))}
      </Row>
      <Table rowKey="id" loading={isLoading} dataSource={data?.content.content ?? []} pagination={{ current: page, total: data?.content.total, pageSize: 20, onChange: setPage }} columns={[
        { title: 'ID', dataIndex: 'id', width: 70 }, { title: '用户', dataIndex: 'username' }, { title: '模块', dataIndex: 'module' },
        { title: '动作', dataIndex: 'action', render: (v: string) => <a onClick={() => { setFilter((f) => ({ ...f, action: v })); setPage(1); }}>{v}</a> }, { title: '路径', dataIndex: 'path' }, { title: 'IP', dataIndex: 'ip' },
        { title: '状态', dataIndex: 'status', render: (v: number) => (v === 0 ? '成功' : '失败') }, { title: '耗时(ms)', dataIndex: 'durationMs' }, { title: '时间', dataIndex: 'createdAt' },
      ]} />
    </div>
  );
}
