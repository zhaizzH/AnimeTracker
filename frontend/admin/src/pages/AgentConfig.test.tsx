import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest';
import { cleanup, render, screen, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import AgentConfig from './AgentConfig';

const adminAgentApi = vi.hoisted(() => ({
  prompts: vi.fn(), promptDetail: vi.fn(), promptUpdate: vi.fn(), promptReset: vi.fn(),
  config: vi.fn(), configUpdate: vi.fn(),
}));
const toastSuccess = vi.hoisted(() => vi.fn());
const toastError = vi.hoisted(() => vi.fn());

vi.mock('@shared', () => ({ adminAgentApi }));
vi.mock('@/lib/toast', () => ({ toastSuccess, toastError }));

function renderPage() {
  const qc = new QueryClient({ defaultOptions: { queries: { retry: false } } });
  return { qc, ...render(
    <QueryClientProvider client={qc}>
      <AgentConfig />
    </QueryClientProvider>,
  ) };
}

beforeEach(() => {
  vi.clearAllMocks();
  adminAgentApi.prompts.mockResolvedValue({ keys: ['system', 'planner'] });
  adminAgentApi.promptDetail.mockResolvedValue({ promptContent: '默认提示词' });
  adminAgentApi.config.mockResolvedValue({ model: 'gpt-x', temperature: 0.7, maxTokens: 4000, thinkingBudget: 100 });
});
afterEach(cleanup);

describe('AgentConfig', () => {
  it('加载提示词列表并自动选中首个', async () => {
    renderPage();
    expect(await screen.findByRole('button', { name: 'system' })).not.toBeNull();
    expect(screen.getByRole('button', { name: 'planner' })).not.toBeNull();
    expect(await screen.findByDisplayValue('默认提示词')).not.toBeNull();
    expect(screen.getByText('编辑：system')).not.toBeNull();
  });

  it('切换到另一个提示词会重新加载详情', async () => {
    adminAgentApi.promptDetail.mockImplementation(async (k: string) => ({ promptContent: `内容-${k}` }));
    const u = userEvent.setup();
    renderPage();
    await screen.findByDisplayValue('内容-system');

    await u.click(screen.getByRole('button', { name: 'planner' }));
    expect(await screen.findByDisplayValue('内容-planner')).not.toBeNull();
  });

  it('保存提示词调用 promptUpdate', async () => {
    adminAgentApi.promptUpdate.mockResolvedValue({});
    const u = userEvent.setup();
    renderPage();
    const ta = await screen.findByLabelText('提示词内容');
    await u.tripleClick(ta);
    await u.keyboard('新内容');
    await u.click(screen.getByRole('button', { name: '保存提示词' }));

    await waitFor(() => expect(adminAgentApi.promptUpdate).toHaveBeenCalledWith('system', { promptContent: '新内容' }));
  });

  it('任务未选中时保存按钮禁用', async () => {
    adminAgentApi.prompts.mockResolvedValue({ keys: [] });
    renderPage();
    expect(await screen.findByText('暂无提示词')).not.toBeNull();
    expect(screen.getByRole('button', { name: '保存提示词' })).toHaveProperty('disabled', true);
  });

  it('模型配置回填并保留 staleTime: Infinity', async () => {
    const { qc } = renderPage();
    expect(await screen.findByDisplayValue('gpt-x')).not.toBeNull();
    const opts = qc.getQueryCache().findAll({ queryKey: ['agent-config'] })[0]?.options;
    expect((opts as { staleTime?: number })?.staleTime).toBe(Infinity);
    expect(screen.getByDisplayValue('0.7')).not.toBeNull();
  });

  it('temperature 超出 0-2 被拦截，不发请求', async () => {
    const u = userEvent.setup();
    renderPage();
    const temp = await screen.findByLabelText('temperature');
    await u.tripleClick(temp);
    await u.keyboard('3');

    // 原生 min/max 约束已使输入非法，浏览器会阻止表单提交；
    // 同时保留 React 侧兜底校验（见 submitCfg），两条路径都必须不发出请求。
    expect(temp).toHaveProperty('validity.rangeOverflow', true);
    await u.click(screen.getByRole('button', { name: '保存模型配置' }));

    expect(adminAgentApi.configUpdate).not.toHaveBeenCalled();
  });

  it('保存配置后失效 agent-config', async () => {
    adminAgentApi.configUpdate.mockResolvedValue({});
    const u = userEvent.setup();
    const { qc } = renderPage();
    await screen.findByDisplayValue('gpt-x');
    const spy = vi.spyOn(qc, 'invalidateQueries');

    await u.click(screen.getByRole('button', { name: '保存模型配置' }));

    await waitFor(() => expect(spy).toHaveBeenCalledWith({ queryKey: ['agent-config'] }));
    expect(toastSuccess).toHaveBeenCalledWith('配置已更新');
  });
});
