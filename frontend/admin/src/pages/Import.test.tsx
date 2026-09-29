import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest';
import { cleanup, render, screen, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import ImportPage from './Import';

const adminImportApi = vi.hoisted(() => ({
  records: vi.fn(),
  status: vi.fn(),
  run: vi.fn(),
}));
const toastSuccess = vi.hoisted(() => vi.fn());
const toastError = vi.hoisted(() => vi.fn());

vi.mock('@shared', () => ({ adminImportApi }));
vi.mock('@/lib/toast', () => ({ toastSuccess, toastError }));

function renderImport() {
  const qc = new QueryClient({ defaultOptions: { queries: { retry: false } } });
  return {
    qc,
    ...render(
      <QueryClientProvider client={qc}>
        <ImportPage />
      </QueryClientProvider>,
    ),
  };
}

const RECORD = {
  id: 1, season: '2026-summer', startedAt: '2026-07-01', completedAt: '2026-07-02',
  status: 'COMPLETED', subjectCount: 10, errorMessage: '',
};

beforeEach(() => vi.clearAllMocks());
afterEach(cleanup);

describe('Import', () => {
  it('轮询 import-status 并展示最近导入与计数', async () => {
    adminImportApi.records.mockResolvedValue({ content: [RECORD], total: 1 });
    adminImportApi.status.mockResolvedValue({
      lastImportedAt: '2026-07-02', completedCount: 5, failedCount: 1, totalLogs: 6,
    });
    const { qc } = renderImport();

    expect(await screen.findByText('最近导入：2026-07-02')).not.toBeNull();
    expect(screen.getByText('成功 5 · 失败 1')).not.toBeNull();
    // 轮询配置：确认 query 以 3000ms 间隔注册
    const opts = qc.getQueryCache().findAll({ queryKey: ['import-status'] })[0]?.options;
    expect((opts as { refetchInterval?: number })?.refetchInterval).toBe(3000);
  });

  it('totalLogs > 0 时失效 import-records', async () => {
    adminImportApi.records.mockResolvedValue({ content: [RECORD], total: 1 });
    adminImportApi.status.mockResolvedValue({
      lastImportedAt: '2026-07-02', completedCount: 5, failedCount: 1, totalLogs: 6,
    });
    // spy 必须在渲染前挂上：effect 在首次拿到 status 数据时就会触发。
    const qc = new QueryClient({ defaultOptions: { queries: { retry: false } } });
    const spy = vi.spyOn(qc, 'invalidateQueries');
    render(
      <QueryClientProvider client={qc}>
        <ImportPage />
      </QueryClientProvider>,
    );

    await waitFor(() => expect(spy).toHaveBeenCalledWith({ queryKey: ['import-records'] }));
    // 失效后记录列表确实重新拉取
    await waitFor(() => expect(adminImportApi.records.mock.calls.length).toBeGreaterThan(1));
  });

  it('模式切换时仅渲染对应条件字段', async () => {
    adminImportApi.records.mockResolvedValue({ content: [], total: 0 });
    adminImportApi.status.mockResolvedValue({ lastImportedAt: null, completedCount: 0, failedCount: 0, totalLogs: 0 });
    const u = userEvent.setup();
    renderImport();

    // 默认 season：有季度选择器，无起始日期。
    // 「季度」同时出现在列头与表单 label，用 combobox role 精确定位。
    expect(await screen.findByRole('combobox', { name: '季度' })).not.toBeNull();
    expect(screen.queryByLabelText('起始日期')).toBeNull();

    await u.click(screen.getByRole('radio', { name: '自某日起' }));
    expect(await screen.findByLabelText('起始日期')).not.toBeNull();
    expect(screen.queryByRole('combobox', { name: '季度' })).toBeNull();

    await u.click(screen.getByRole('radio', { name: '全量' }));
    await waitFor(() => expect(screen.queryByLabelText('起始日期')).toBeNull());
    expect(screen.queryByRole('combobox', { name: '季度' })).toBeNull();
  });

  it('触发导入携带当前模式参数并提示结果', async () => {
    adminImportApi.records.mockResolvedValue({ content: [], total: 0 });
    adminImportApi.status.mockResolvedValue({ lastImportedAt: null, completedCount: 0, failedCount: 0, totalLogs: 0 });
    adminImportApi.run.mockResolvedValue('导入已触发');
    const u = userEvent.setup();
    renderImport();
    await screen.findByRole('combobox', { name: '季度' });

    await u.click(screen.getByRole('button', { name: '触发导入' }));

    await waitFor(() =>
      expect(adminImportApi.run).toHaveBeenCalledWith({
        mode: 'season', key: undefined, since: undefined, workers: undefined,
      }),
    );
    expect(toastSuccess).toHaveBeenCalledWith('导入已触发');
  });

  it('空记录显示空态', async () => {
    adminImportApi.records.mockResolvedValue({ content: [], total: 0 });
    adminImportApi.status.mockResolvedValue({ lastImportedAt: null, completedCount: 0, failedCount: 0, totalLogs: 0 });
    renderImport();
    expect(await screen.findByText('暂无导入记录')).not.toBeNull();
  });
});
