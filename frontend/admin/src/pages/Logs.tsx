import { useCallback, useEffect, useMemo, useState } from 'react';
import { App, Button, DatePicker, Drawer, Input, Segmented, Select, Table, Tooltip } from 'antd';
import type { TablePaginationConfig, TableProps } from 'antd';
import { DownloadOutlined, EyeOutlined, ReloadOutlined, SearchOutlined } from '@ant-design/icons';
import dayjs from 'dayjs';
import { logsApi } from '../api/logs';
import type { OperationLogStatsVO, OperationLogVO } from '../types/api';

type DateRange = [dayjs.Dayjs, dayjs.Dayjs];

function methodCls(method: string): string {
  return method.toLowerCase();
}

const knownModules = ['AUTH', 'SUBJECT', 'IMPORT', 'ADMIN', 'AGENT', 'USER', 'FILE'];
const knownActions = [
  'LOGIN',
  'LOGOUT',
  'REGISTER',
  'VERIFY_EMAIL',
  'RESET_PASSWORD',
  'ROLE_CHANGE',
  'IMPORT_RUN',
  'SUBJECT_CREATE',
  'SUBJECT_UPDATE',
  'SUBJECT_DELETE',
  'PROMPT_UPDATE',
  'PROMPT_RESET',
  'CONFIG_UPDATE',
  'PASSWORD_CHANGE',
  'FILE_UPLOAD',
];


function csvCell(value: unknown): string {
  const text = String(value ?? '');
  return `"${text.replace(/"/g, '""')}"`;
}

function exportCsv(rows: OperationLogVO[]) {
  const header = ['时间', '用户', '模块', '操作', '方法', '路径', 'IP', '状态', '耗时(ms)', '错误信息'];
  const lines = rows.map((log) =>
    [
      csvCell(log.createdAt),
      csvCell(log.username),
      csvCell(log.module),
      csvCell(log.action),
      csvCell(log.method),
      csvCell(log.path),
      csvCell(log.ip),
      csvCell(log.status === 0 ? '成功' : '失败'),
      csvCell(log.durationMs),
      csvCell(log.errorMsg),
    ].join(','),
  );
  const blob = new Blob([`\uFEFF${[header.join(','), ...lines].join('\n')}`], {
    type: 'text/csv;charset=utf-8',
  });
  const url = URL.createObjectURL(blob);
  const link = document.createElement('a');
  link.href = url;
  link.download = `operation-logs-${dayjs().format('YYYYMMDD-HHmmss')}.csv`;
  link.click();
  URL.revokeObjectURL(url);
}

export default function Logs() {
  const { message } = App.useApp();
  const [username, setUsername] = useState('');
  const [moduleFilter, setModuleFilter] = useState('all');
  const [actionFilter, setActionFilter] = useState('all');
  const [range, setRange] = useState<DateRange | null>(null);
  const [list, setList] = useState<OperationLogVO[]>([]);
  const [page, setPage] = useState(1);
  const [pageSize, setPageSize] = useState(10);
  const [total, setTotal] = useState(0);
  const [loading, setLoading] = useState(false);
  const [detail, setDetail] = useState<OperationLogVO | null>(null);
  const [statusFilter, setStatusFilter] = useState<'all' | 'success' | 'failed'>('all');
  const [stats, setStats] = useState<OperationLogStatsVO | null>(null);

  const modules = useMemo(
    () => ['all', ...Array.from(new Set([...knownModules, ...list.map((l) => l.module).filter(Boolean)]))],
    [list],
  );
  const actions = useMemo(
    () => ['all', ...Array.from(new Set([...knownActions, ...list.map((l) => l.action).filter(Boolean)]))],
    [list],
  );

  const load = useCallback(
    async (nextPage: number, nextSize: number) => {
      setLoading(true);
      try {
        const result = await logsApi.list({
          page: nextPage,
          size: nextSize,
          username: username.trim() || undefined,
          module: moduleFilter === 'all' ? undefined : moduleFilter,
          action: actionFilter === 'all' ? undefined : actionFilter,
          status: statusFilter === 'all' ? undefined : statusFilter === 'success' ? 0 : 1,
          start: range?.[0] ? range[0].format('YYYY-MM-DD') : undefined,
          end: range?.[1] ? range[1].format('YYYY-MM-DD') : undefined,
        });
        setList(result.content ?? []);
        setTotal(result.total ?? 0);
        setPage(result.page ?? nextPage);
        setPageSize(result.size ?? nextSize);
        setStats(result.stats ?? null);
      } catch (error) {
        message.error(error instanceof Error ? error.message : '日志加载失败');
      } finally {
        setLoading(false);
      }
    },
    [actionFilter, message, moduleFilter, range, statusFilter, username],
  );

  useEffect(() => {
    load(1, pageSize);
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [moduleFilter, actionFilter, range, statusFilter, username]);

  const failedCount = stats?.failedCount ?? 0;
  const successCount = stats?.successCount ?? 0;
  const avgDuration = stats?.avgDurationMs ?? 0;

  const resetFilters = () => {
    setUsername('');
    setModuleFilter('all');
    setActionFilter('all');
    setRange(null);
    setStatusFilter('all');
    setPage(1);
    load(1, pageSize);
    message.success('筛选条件已重置');
  };

  const handleSearch = () => {
    setPage(1);
    load(1, pageSize);
  };

  const handleTableChange = (pagination: TablePaginationConfig) => {
    const nextPage = pagination.current ?? 1;
    const nextSize = pagination.pageSize ?? pageSize;
    setPage(nextPage);
    setPageSize(nextSize);
    load(nextPage, nextSize);
  };

  const [exporting, setExporting] = useState(false);

  /** 导出全部日志（按当前筛选条件分页拉全） */
  const exportAll = async () => {
    setExporting(true);
    try {
      const params = {
        username: username.trim() || undefined,
        module: moduleFilter === 'all' ? undefined : moduleFilter,
        action: actionFilter === 'all' ? undefined : actionFilter,
        status: statusFilter === 'all' ? undefined : statusFilter === 'success' ? 0 : 1,
        start: range?.[0] ? range[0].format('YYYY-MM-DD') : undefined,
        end: range?.[1] ? range[1].format('YYYY-MM-DD') : undefined,
      };
      let all: OperationLogVO[] = [];
      let page = 1;
      const pageSize = 100;
      while (true) {
        const result = await logsApi.list({ ...params, page, size: pageSize });
        all = all.concat(result.content ?? []);
        if (all.length >= (result.total ?? 0)) break;
        page += 1;
      }
      if (all.length === 0) {
        message.warning('当前筛选条件下无日志可导出');
        return;
      }
      exportCsv(all);
      message.success(`已导出 ${all.length} 条日志`);
    } catch (error) {
      message.error(error instanceof Error ? error.message : '日志导出失败');
    } finally {
      setExporting(false);
    }
  };

  const columns: TableProps<OperationLogVO>['columns'] = [
    {
      title: '时间',
      dataIndex: 'createdAt',
      width: 164,
      className: 'num',
      render: (value: string) => <span className="cell-mono">{value}</span>,
    },
    {
      title: '用户',
      dataIndex: 'username',
      width: 170,
      render: (_, log) => (
        <div className="user-cell">
          <span className="user-id">#{log.userId}</span>
          <span className="cell-mono">{log.username}</span>
        </div>
      ),
    },
    {
      title: '模块',
      dataIndex: 'module',
      width: 116,
      render: (value: string) => <span className="module-chip">{value}</span>,
    },
    {
      title: '操作',
      dataIndex: 'action',
      width: 170,
      render: (value: string) => <span className="cell-mono action-text">{value}</span>,
    },
    {
      title: '请求',
      render: (_, log) => (
        <div className="request-cell">
          <span className={`method-tag ${methodCls(log.method)}`}>{log.method}</span>
          <span className="path-text">{log.path}</span>
        </div>
      ),
    },
    {
      title: 'IP',
      dataIndex: 'ip',
      width: 130,
      className: 'num',
      render: (value: string) => <span className="cell-mono">{value}</span>,
    },
    {
      title: '状态',
      dataIndex: 'status',
      width: 84,
      render: (value: number) => (
        <span className={`status-tag ${value === 0 ? 'success' : 'failed'}`}>
          <span className="status-dot" />
          {value === 0 ? '成功' : '失败'}
        </span>
      ),
    },
    {
      title: '耗时',
      dataIndex: 'durationMs',
      width: 96,
      className: 'num',
      render: (value: number) => <span className="cell-mono">{value} ms</span>,
    },
    {
      title: '详情',
      width: 72,
      render: (_, log) => (
        <Tooltip title="查看日志详情">
          <Button type="text" size="small" icon={<EyeOutlined />} onClick={() => setDetail(log)} />
        </Tooltip>
      ),
    },
  ];

  return (
    <div className="dash-stack">
      <div className="dash-toolbar">
        <div>
          <div className="dash-toolbar-sub">接口 · GET /api/admin/logs?page=&size=&module=&action=&username=&status=&start=&end=</div>
        </div>
        <div className="dash-toolbar-actions">
          <Button icon={<DownloadOutlined />} loading={exporting} onClick={exportAll}>
            导出 CSV
          </Button>
          <Tooltip title="刷新日志">
            <Button icon={<ReloadOutlined spin={loading} />} onClick={() => load(page, pageSize)} />
          </Tooltip>
        </div>
      </div>

      <div className="mini-stats">
        <div className="mini-stat tone-cyan">
          <div>
            <div className="mini-stat-label">日志总数</div>
            <div className="mini-stat-value">{stats?.total?.toLocaleString() ?? 0}</div>
          </div>
        </div>
        <div className="mini-stat tone-red">
          <div>
            <div className="mini-stat-label">失败日志</div>
            <div className="mini-stat-value">{failedCount.toLocaleString()}</div>
          </div>
        </div>
        <div className="mini-stat tone-green">
          <div>
            <div className="mini-stat-label">成功日志</div>
            <div className="mini-stat-value">{successCount.toLocaleString()}</div>
          </div>
        </div>
        <div className="mini-stat tone-amber">
          <div>
            <div className="mini-stat-label">平均耗时</div>
            <div className="mini-stat-value mini-value-sm">{avgDuration.toLocaleString()} ms</div>
          </div>
        </div>
      </div>

      <div className="filter-panel logs-filter">
        <div className="filter-item">
          <span>用户</span>
          <Input
            allowClear
            prefix={<SearchOutlined />}
            placeholder="用户名"
            value={username}
            onChange={(e) => setUsername(e.target.value)}
            onPressEnter={handleSearch}
            style={{ width: 170 }}
          />
        </div>
        <div className="filter-item">
          <span>模块</span>
          <Select
            value={moduleFilter}
            onChange={setModuleFilter}
            style={{ width: 140 }}
            options={modules.map((m) => ({ value: m, label: m === 'all' ? '全部模块' : m }))}
          />
        </div>
        <div className="filter-item">
          <span>操作</span>
          <Select
            value={actionFilter}
            onChange={setActionFilter}
            style={{ width: 170 }}
            options={actions.map((a) => ({ value: a, label: a === 'all' ? '全部操作' : a }))}
          />
        </div>
        <div className="filter-item">
          <span>时间范围</span>
          <DatePicker.RangePicker
            value={range}
            onChange={(value) => setRange(value as DateRange | null)}
            allowClear
          />
        </div>
        <div className="filter-spacer" />
        <div className="filter-item">
          <span>状态</span>
          <Segmented
            value={statusFilter}
            onChange={(value) => setStatusFilter(value as 'all' | 'success' | 'failed')}
            options={[
              { value: 'all', label: '全部' },
              { value: 'success', label: '成功' },
              { value: 'failed', label: '失败' },
            ]}
          />
        </div>
        <Button onClick={resetFilters}>重置</Button>
        <Button type="primary" ghost icon={<SearchOutlined />} onClick={handleSearch}>
          查询
        </Button>
        <span className="filter-count">总数 {total.toLocaleString()}</span>
      </div>

      <section className="panel table-panel">
        <div className="panel-head">
          <div>
            <h3 className="panel-title">
              <span className="seq">01</span>日志明细
            </h3>
            <div className="panel-sub">
              覆盖登录、条目、用户、导入与 Agent 管理操作 · 统计为全部日志（按当前筛选条件）
            </div>
          </div>
          <span className="panel-note">按 ID 倒序</span>
        </div>
        <Table<OperationLogVO>
          rowKey="id"
          columns={columns}
          dataSource={list}
          loading={loading}
          size="middle"
          onChange={handleTableChange}
          pagination={{
            current: page,
            pageSize,
            total,
            showSizeChanger: true,
            pageSizeOptions: [10, 20, 50],
            showTotal: (count) => `共 ${count} 条`,
          }}
          scroll={{ x: 1240 }}
        />
      </section>

      <Drawer
        title={`日志详情 #${detail?.id ?? ''}`}
        width={520}
        open={!!detail}
        onClose={() => setDetail(null)}
      >
        {detail && (
          <div className="detail-list">
            <div className="detail-item">
              <span>请求路径</span>
              <div className="mono">{detail.path}</div>
            </div>
            <div className="detail-item">
              <span>请求方法</span>
              <div className="mono">{detail.method}</div>
            </div>
            <div className="detail-item">
              <span>请求参数</span>
              <div className="mono">{detail.params ?? '-'}</div>
            </div>
            <div className="detail-item">
              <span>模块</span>
              <div>{detail.module}</div>
            </div>
            <div className="detail-item">
              <span>操作</span>
              <div className="mono">{detail.action}</div>
            </div>
            <div className="detail-item">
              <span>用户</span>
              <div className="mono">
                #{detail.userId} · {detail.username}
              </div>
            </div>
            <div className="detail-item">
              <span>IP 地址</span>
              <div className="mono">{detail.ip}</div>
            </div>
            <div className="detail-item">
              <span>User-Agent</span>
              <div className="mono">{detail.userAgent}</div>
            </div>
            <div className="detail-item">
              <span>状态码</span>
              <div>
                <span className={`status-tag ${detail.status === 0 ? 'success' : 'failed'}`}>
                  <span className="status-dot" />
                  {detail.status === 0 ? '成功' : '失败'}
                </span>
              </div>
            </div>
            <div className="detail-item">
              <span>耗时</span>
              <div className="mono">{detail.durationMs} ms</div>
            </div>
            <div className="detail-item">
              <span>错误信息</span>
              <div className="mono">{detail.errorMsg ?? '-'}</div>
            </div>
            <div className="detail-item">
              <span>时间</span>
              <div className="mono">{detail.createdAt}</div>
            </div>
          </div>
        )}
      </Drawer>
    </div>
  );
}
