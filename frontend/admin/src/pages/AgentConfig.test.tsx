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

// 后端真实契约（backend/agent/app/api/schemas/admin_config.py）：
// GET /admin/agent/prompts 返回裸数组，元素字段为 promptKey / promptContent。
const PROMPTS = [
  { promptKey: 'system', promptContent: '默认提示词' },
  { promptKey: 'planner', promptContent: '规划提示词' },
];

beforeEach(() => {
  vi.clearAllMocks();
  adminAgentApi.prompts.mockResolvedValue(PROMPTS);
  adminAgentApi.promptDetail.mockResolvedValue({ promptKey: 'system', promptContent: '默认提示词' });
  adminAgentApi.config.mockResolvedValue({ model: 'gpt-x', temperature: 0.7, maxTokens: 4000, thinkingBudget: 100 });
});
afterEach(cleanup);

describe('AgentConfig', () => {
  it('按真实契约解析列表并自动选中首个', async () => {
    renderPage();
    expect(await screen.findByRole('button', { name: 'system' })).not.toBeNull();
    expect(screen.getByRole('button', { name: 'planner' })).not.toBeNull();
    expect(await screen.findByDisplayValue('默认提示词')).not.toBeNull();
    expect(screen.getByText('编辑：system')).not.toBeNull();
  });

  it('不会把 promptKey 误读成 key 而渲染出 undefined 条目', async () => {
    renderPage();
    await screen.findByRole('button', { name: 'system' });
    expect(screen.queryByRole('button', { name: 'undefined' })).toBeNull();
  });

  it('切换到另一个提示词会重新加载详情', async () => {
    adminAgentApi.promptDetail.mockImplementation(async (k: string) => ({ promptKey: k, promptContent: `内容-${k}` }));
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

  it('详情加载失败时禁用保存，避免以空内容覆盖提示词', async () => {
    adminAgentApi.promptDetail.mockRejectedValue(new Error('无效的提示词 key'));
    renderPage();

    const btn = await screen.findByRole('button', { name: '保存提示词' });
    await waitFor(() => expect(toastError).toHaveBeenCalled());
    expect(btn).toHaveProperty('disabled', true);

    await userEvent.setup().click(btn);
    expect(adminAgentApi.promptUpdate).not.toHaveBeenCalled();
  });

  it('列表请求失败显示错误态而非「暂无提示词」', async () => {
    adminAgentApi.prompts.mockRejectedValue(new Error('网络错误'));
    renderPage();

    expect(await screen.findByRole('alert')).not.toBeNull();
    expect(screen.getByText('提示词加载失败')).not.toBeNull();
    expect(screen.queryByText('暂无提示词')).toBeNull();
  });

  it('快速切换时丢弃过期响应，content 与标题保持一致', async () => {
    // planner 的响应故意比 system 慢，模拟后发请求先返回/先发后到
    adminAgentApi.promptDetail.mockImplementation(async (k: string) => {
      if (k === 'planner') {
        await new Promise((r) => setTimeout(r, 50));
        return { promptKey: k, promptContent: '内容-planner' };
      }
      await new Promise((r) => setTimeout(r, 10));
      return { promptKey: k, promptContent: '内容-system' };
    });
    const u = userEvent.setup();
    renderPage();
    await screen.findByDisplayValue('内容-system');

    await u.click(screen.getByRole('button', { name: 'planner' }));
    await u.click(screen.getByRole('button', { name: 'system' }));

    // system 是最后发起的请求，其响应必须胜出；planner 的迟到响应应被丢弃
    await waitFor(() => expect(screen.getByText('编辑：system')).not.toBeNull());
    await waitFor(() => expect(screen.getByDisplayValue('内容-system')).not.toBeNull());
    expect(screen.queryByDisplayValue('内容-planner')).toBeNull();
  });

  it('重置失败时给出 toast 错误提示', async () => {
    adminAgentApi.promptReset.mockRejectedValue(new Error('重置失败'));
    const u = userEvent.setup();
    renderPage();
    await screen.findByRole('button', { name: 'system' });

    await u.click(screen.getAllByRole('button', { name: '重置' })[0]!);
    await u.click(await screen.findByRole('button', { name: '确定' }));

    await waitFor(() => expect(toastError).toHaveBeenCalledWith('重置失败'));
  });

  it('任务未选中时保存按钮禁用', async () => {
    adminAgentApi.prompts.mockResolvedValue([]);
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

  it('提交配置保留服务端已有但表单未改动的字段，不被整体替换抹掉', async () => {
    // modelRoute / reasoningEffort 由服务端预置，页面上可见可编辑
    adminAgentApi.config.mockResolvedValue({
      model: 'gpt-x', modelRoute: 'client-route', temperature: 0.7, maxTokens: 4000, thinkingBudget: 100, reasoningEffort: 'high',
    });
    adminAgentApi.configUpdate.mockResolvedValue({});
    const u = userEvent.setup();
    renderPage();
    await screen.findByDisplayValue('gpt-x');

    await u.click(screen.getByRole('button', { name: '保存模型配置' }));

    await waitFor(() => expect(adminAgentApi.configUpdate).toHaveBeenCalled());
    const sent = adminAgentApi.configUpdate.mock.calls[0]![0] as Record<string, unknown>;
    expect(sent.modelRoute).toBe('client-route');
    expect(sent.reasoningEffort).toBe('high');
  });

  it('modelRoute 与 reasoningEffort 可在表单中编辑并提交', async () => {
    adminAgentApi.configUpdate.mockResolvedValue({});
    const u = userEvent.setup();
    renderPage();
    await screen.findByDisplayValue('gpt-x');

    const route = screen.getByLabelText('modelRoute');
    await u.clear(route);
    await u.type(route, 'admin-route');
    const effort = screen.getByLabelText('reasoningEffort');
    await u.clear(effort);
    await u.type(effort, 'low');

    await u.click(screen.getByRole('button', { name: '保存模型配置' }));

    await waitFor(() => expect(adminAgentApi.configUpdate).toHaveBeenCalled());
    const sent = adminAgentApi.configUpdate.mock.calls[0]![0] as Record<string, unknown>;
    expect(sent.modelRoute).toBe('admin-route');
    expect(sent.reasoningEffort).toBe('low');
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
