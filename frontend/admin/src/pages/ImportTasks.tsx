import { useCallback, useEffect, useRef, useState } from 'react';
import { App, Button, DatePicker, Form, Input, InputNumber, Select, Table, Tooltip } from 'antd';
import type { TableProps } from 'antd';
import { PlayCircleOutlined, ReloadOutlined } from '@ant-design/icons';
import dayjs from 'dayjs';
import { importsApi } from '../api/imports';
import type { ImportMode, ImportRecordVO, ImportStatusVO } from '../types/api';

interface RunImportValues {
  mode: ImportMode;
  key?: string;
  since?: dayjs.Dayjs;
  workers?: number;
}

const statusMeta: Record<ImportRecordVO['status'], { label: string; cls: string }> = {
  RUNNING: { label: '运行中', cls: 'running' },
  COMPLETED: { label: '已完成', cls: 'success' },
  FAILED: { label: '失败', cls: 'failed' },
};

export default function ImportTasks() {
  const { message } = App.useApp();
  const [status, setStatus] = useState<ImportStatusVO>({
    lastImportedAt: null,
    totalSubjects: 0,
    recentRecords: [],
  });
  const [loading, setLoading] = useState(false);
  const [running, setRunning] = useState(false);
  const [form] = Form.useForm<RunImportValues>();
  const mode = Form.useWatch('mode', form) ?? 'recent';
  const timerRef = useRef<number | null>(null);

  const records = status.recentRecords ?? [];
  const runningRecord = records.find((r) => r.status === 'RUNNING') ?? null;
  const completedCount = records.filter((r) => r.status === 'COMPLETED').length;
  const failedCount = records.filter((r) => r.status === 'FAILED').length;
  const runningCount = records.filter((r) => r.status === 'RUNNING').length;

  const loadStatus = useCallback(async (silent = false) => {
    if (!silent) setLoading(true);
    try {
      const data = await importsApi.status();
      setStatus(data);
      setRunning((data.recentRecords ?? []).some((r) => r.status === 'RUNNING'));
    } catch (error) {
      if (!silent) message.error(error instanceof Error ? error.message : '导入状态加载失败');
    } finally {
      if (!silent) setLoading(false);
    }
  }, [message]);

  useEffect(() => {
    loadStatus();
  }, [loadStatus]);

  useEffect(() => {
    if (!running) return undefined;
    timerRef.current = window.setInterval(() => {
      loadStatus(true);
    }, 5000);
    return () => {
      if (timerRef.current) window.clearInterval(timerRef.current);
    };
  }, [running, loadStatus]);

  useEffect(() => {
    return () => {
      if (timerRef.current) window.clearTimeout(timerRef.current);
    };
  }, []);

  const runImport = async (values: RunImportValues) => {
    setLoading(true);
    try {
      await importsApi.run({
        mode: values.mode,
        key: values.mode === 'season' ? values.key : undefined,
        since: values.mode === 'since' ? values.since?.format('YYYY-MM-DD') : undefined,
        workers: values.workers,
      });
      message.success('导入任务已提交，正在后台执行');
      await loadStatus(true);
    } catch (error) {
      message.error(error instanceof Error ? error.message : '导入任务提交失败');
    } finally {
      setLoading(false);
    }
  };

  const columns: TableProps<ImportRecordVO>['columns'] = [
    {
      title: 'ID',
      dataIndex: 'id',
      width: 64,
      className: 'num',
      render: (value: number) => `#${value}`,
    },
    {
      title: '季度 / 范围',
      dataIndex: 'season',
      render: (value: string) => <span className="cell-mono">{value || '-'}</span>,
    },
    {
      title: '状态',
      dataIndex: 'status',
      width: 112,
      render: (value: ImportRecordVO['status']) => (
        <span className={`status-tag ${statusMeta[value].cls}`}>
          <span className={`status-dot${value === 'RUNNING' ? ' running' : ''}`} />
          {statusMeta[value].label}
        </span>
      ),
    },
    {
      title: '条目数',
      dataIndex: 'subjectCount',
      width: 84,
      className: 'num',
      render: (value: number) => (value > 0 ? value : '-'),
    },
    {
      title: '开始时间',
      dataIndex: 'startedAt',
      width: 164,
      className: 'num',
      render: (value: string) => value ?? '-',
    },
    {
      title: '完成时间',
      dataIndex: 'completedAt',
      width: 164,
      className: 'num',
      render: (value?: string | null) => value ?? '-',
    },
    {
      title: '错误信息',
      dataIndex: 'errorMessage',
      width: 240,
      ellipsis: true,
      render: (value?: string | null) => (value ? <span className="error-text">{value}</span> : '-'),
    },
  ];

  return (
    <div className="dash-stack">
      <div className="dash-toolbar">
        <div>
          <div className="dash-toolbar-sub">接口 · POST /api/admin/import/run?mode=&key=&since=&workers=</div>
        </div>
        <div className="dash-toolbar-actions">
          <Tooltip title="刷新导入状态">
            <Button icon={<ReloadOutlined spin={loading} />} onClick={() => loadStatus()} />
          </Tooltip>
        </div>
      </div>

      <div className="mini-stats">
        <div className="mini-stat tone-cyan">
          <div>
            <div className="mini-stat-label">当前条目总数</div>
            <div className="mini-stat-value">{Number(status.totalSubjects ?? 0).toLocaleString()}</div>
          </div>
        </div>
        <div className="mini-stat tone-green">
          <div>
            <div className="mini-stat-label">成功任务</div>
            <div className="mini-stat-value">{completedCount}</div>
          </div>
        </div>
        <div className="mini-stat tone-red">
          <div>
            <div className="mini-stat-label">失败任务</div>
            <div className="mini-stat-value">{failedCount}</div>
          </div>
        </div>
        <div className="mini-stat tone-amber">
          <div>
            <div className="mini-stat-label">最近导入</div>
            <div className="mini-stat-value mini-value-sm">{status.lastImportedAt ?? '-'}</div>
          </div>
        </div>
      </div>

      <div className="split-grid">
        <section className="panel">
          <div className="panel-head">
            <div>
              <h3 className="panel-title">
                <span className="seq">01</span>运行导入
              </h3>
              <div className="panel-sub">选择模式并提交任务</div>
            </div>
            <span className="panel-note">异步任务</span>
          </div>
          <Form
            form={form}
            layout="vertical"
            initialValues={{ mode: 'recent', key: '2026-summer', workers: 10 }}
            onFinish={runImport}
          >
            <Form.Item name="mode" label="导入模式" rules={[{ required: true, message: '请选择导入模式' }]}>
              <Select
                options={[
                  { value: 'full', label: '全量导入' },
                  { value: 'season', label: '季度导入' },
                  { value: 'recent', label: '近期更新' },
                  { value: 'since', label: '指定日期起' },
                ]}
              />
            </Form.Item>
            <Form.Item
              name="key"
              label="季度标识"
              rules={[{ required: mode === 'season', message: '季度模式必填季度标识' }]}
            >
              <Input placeholder="2026-summer" disabled={mode !== 'season'} />
            </Form.Item>
            <Form.Item
              name="since"
              label="起始日期"
              rules={[{ required: mode === 'since', message: '指定日期模式必填起始日期' }]}
            >
              <DatePicker style={{ width: '100%' }} disabled={mode !== 'since'} />
            </Form.Item>
            <Form.Item name="workers" label="并发线程">
              <InputNumber min={1} max={16} style={{ width: '100%' }} />
            </Form.Item>
            <Button type="primary" htmlType="submit" block icon={<PlayCircleOutlined />} disabled={!!running} loading={loading}>
              {running ? '导入运行中' : '启动导入'}
            </Button>
          </Form>
        </section>

        <div className="split-stack">
          <section className="panel">
            <div className="panel-head">
              <div>
                <h3 className="panel-title">
                  <span className="seq">02</span>当前任务
                </h3>
                <div className="panel-sub">GET /api/admin/import/status</div>
              </div>
              <span className="panel-note">{runningRecord ? '繁忙' : '空闲'}</span>
            </div>
            {runningRecord ? (
              <div className="current-task">
                <div className="current-task-row">
                  <span className="status-tag running">
                    <span className="status-dot running" />
                    运行中
                  </span>
                  <span className="cell-mono">{runningRecord.season || '-'}</span>
                </div>
                <div className="current-task-meta">
                  <span>#ID {runningRecord.id}</span>
                  <span>{runningRecord.startedAt ?? '-'}</span>
                </div>
                <div className="progress-track">
                  <div className="progress-fill" style={{ width: '72%' }} />
                </div>
                <div className="progress-note">正在抓取 Bangumi 数据，状态每 5 秒自动刷新</div>
              </div>
            ) : (
              <div className="current-task idle">
                <span className="status-tag neutral">
                  <span className="status-dot" />
                  空闲
                </span>
                <p className="panel-sub">当前无运行中的导入任务，最近一次完成于 {status.lastImportedAt ?? '-'}。</p>
              </div>
            )}
          </section>

          <section className="panel table-panel">
            <div className="panel-head">
              <div>
                <h3 className="panel-title">
                  <span className="seq">03</span>导入历史
                </h3>
                <div className="panel-sub">最近 {records.length} 次任务记录</div>
              </div>
              <span className="panel-note">运行中 {runningCount}</span>
            </div>
            <Table<ImportRecordVO>
              rowKey="id"
              columns={columns}
              dataSource={records}
              size="middle"
              pagination={{
                pageSize: 10,
                showTotal: (count) => `共 ${count} 条`,
              }}
              scroll={{ x: 900 }}
            />
          </section>
        </div>
      </div>
    </div>
  );
}
