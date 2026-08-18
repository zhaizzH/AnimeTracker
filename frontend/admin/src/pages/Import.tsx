import { useEffect, useState } from 'react';
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';
import { Button, Form, Input, InputNumber, Radio, Select, Space, Table, message } from 'antd';
import { adminImportApi, type ImportRecordVO } from '@shared';

export default function ImportPage() {
  const qc = useQueryClient();
  const [mode, setMode] = useState<'full' | 'season' | 'recent' | 'since'>('season');
  const [page, setPage] = useState(1);
  const [statusFilter, setStatusFilter] = useState<string>('');
  const rec = useQuery({ queryKey: ['import-records', page, statusFilter], queryFn: () => adminImportApi.records({ page, size: 10, status: statusFilter || undefined }) });
  const st = useQuery({ queryKey: ['import-status'], queryFn: adminImportApi.status, refetchInterval: 3000 });
  const runMut = useMutation({ mutationFn: (v: Record<string, unknown>) => adminImportApi.run(v as { mode: 'full' | 'season' | 'recent' | 'since'; key?: string; since?: string; workers?: number }), onSuccess: (d) => { message.success(d || '导入已触发'); qc.invalidateQueries({ queryKey: ['import-status'] }); }, onError: (e) => message.error((e as Error).message) });
  useEffect(() => { if (st.data && (st.data.totalLogs > 0)) qc.invalidateQueries({ queryKey: ['import-records'] }); }, [st.data, qc]);
  return (
    <div>
      <Form layout="inline" initialValues={{ mode }} onFinish={(v) => runMut.mutate(v)} style={{ marginBottom: 16 }}>
        <Form.Item name="mode" label="模式" rules={[{ required: true }]}>
          <Radio.Group onChange={(e) => setMode(e.target.value)} options={[{ label: '全量', value: 'full' }, { label: '季度', value: 'season' }, { label: '近期', value: 'recent' }, { label: '自某日起', value: 'since' }]} />
        </Form.Item>
        {mode === 'season' && <Form.Item name="key" label="季度"><Select style={{ width: 160 }} options={['2026-summer', '2026-spring', '2025-winter'].map((k) => ({ value: k, label: k }))} placeholder="2026-summer" /></Form.Item>}
        {mode === 'since' && <Form.Item name="since" label="起始日期"><Input placeholder="2026-01-01" /></Form.Item>}
        <Form.Item name="workers" label="并发"><InputNumber min={1} /></Form.Item>
        <Button type="primary" htmlType="submit" loading={runMut.isPending}>触发导入</Button>
      </Form>
      <Space style={{ marginBottom: 8 }}>
        <span>最近导入：{st.data?.lastImportedAt ?? '从未导入'}</span>
        <span>成功 {st.data?.completedCount ?? 0} · 失败 {st.data?.failedCount ?? 0}</span>
      </Space>
      <Select style={{ width: 160, marginBottom: 8 }} placeholder="状态筛选" allowClear value={statusFilter} onChange={setStatusFilter} options={[{ value: 'RUNNING', label: '运行中' }, { value: 'COMPLETED', label: '已完成' }, { value: 'FAILED', label: '失败' }]} />
      <Table rowKey="id" dataSource={rec.data?.content ?? []} loading={rec.isLoading} pagination={{ current: page, total: rec.data?.total, pageSize: 10, onChange: setPage }} columns={[
        { title: '季度', dataIndex: 'season' }, { title: '开始', dataIndex: 'startedAt' }, { title: '完成', dataIndex: 'completedAt' },
        { title: '状态', dataIndex: 'status', render: (v: string) => ({ RUNNING: '运行中', COMPLETED: '已完成', FAILED: '失败' })[v] ?? v },
        { title: '条目数', dataIndex: 'subjectCount' }, { title: '错误', dataIndex: 'errorMessage' },
      ]} />
    </div>
  );
}
