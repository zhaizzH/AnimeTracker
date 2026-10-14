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

// GET /admin/agent/config 返回生效值 + 逐字段来源（_sources）。
const cfgView = (overrides = {}, sources = {}) => ({
  model: 'gpt-x', modelRoute: 'route-y', temperature: 0.7, maxTokens: 4000, thinkingBudget: 100, reasoningEffort: 'high',
  _sources: {
    model: 'default', modelRoute: 'default', temperature: 'default', maxTokens: 'default',
    thinkingBudget: 'default', reasoningEffort: 'default', ...sources,
  },
  ...overrides,
});

beforeEach(() => {
  vi.clearAllMocks();
  adminAgentApi.prompts.mockResolvedValue(PROMPTS);
  adminAgentApi.promptDetail.mockResolvedValue({ promptKey: 'system', promptContent: '默认提示词' });
  adminAgentApi.config.mockResolvedValue(cfgView());
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

  it('模型配置查询保留 staleTime: Infinity', async () => {
    const { qc } = renderPage();
    await screen.findByRole('button', { name: 'system' });
    const opts = qc.getQueryCache().findAll({ queryKey: ['agent-config'] })[0]?.options;
    expect((opts as { staleTime?: number })?.staleTime).toBe(Infinity);
  });
});

describe('AgentConfig 默认值回显', () => {
  it('default 字段留空并以 placeholder 展示继承值', async () => {
    renderPage();
    // 等待配置查询 resolve 后再断言：输入框随 label 立即渲染，值异步到达
    const model = await screen.findByLabelText('model');
    await waitFor(() => expect(model.getAttribute('placeholder')).toContain('gpt-x'));
    // 继承默认不填进 value，否则用户一保存就把它固化进 Redis
    expect((model as HTMLInputElement).value).toBe('');

    const temp = screen.getByLabelText('temperature');
    expect((temp as HTMLInputElement).value).toBe('');
    expect(temp.getAttribute('placeholder')).toContain('0.7');
  });

  it('override 字段填入实际值，不留 placeholder', async () => {
    adminAgentApi.config.mockResolvedValue(cfgView({ model: 'custom-x' }, { model: 'override' }));
    renderPage();

    const model = await screen.findByLabelText('model');
    await waitFor(() => expect((model as HTMLInputElement).value).toBe('custom-x'));
    expect(model.getAttribute('placeholder')).toBeNull();
  });

  it('override 的 0 值正常展示，不被当成未设置', async () => {
    adminAgentApi.config.mockResolvedValue(cfgView({ temperature: 0 }, { temperature: 'override' }));
    renderPage();

    const temp = await screen.findByLabelText('temperature');
    await waitFor(() => expect((temp as HTMLInputElement).value).toBe('0'));
  });
});

describe('AgentConfig 稀疏提交', () => {
  it('只提交被填写的字段，继承默认的字段不进请求体', async () => {
    adminAgentApi.configUpdate.mockResolvedValue({});
    const u = userEvent.setup();
    renderPage();
    const model = await screen.findByLabelText('model');

    await u.type(model, 'new-model');
    await u.click(screen.getByRole('button', { name: '保存模型配置' }));

    await waitFor(() => expect(adminAgentApi.configUpdate).toHaveBeenCalled());
    // 全部 default 字段都不应出现——这正是"不固化 .env 默认值"的保证
    expect(adminAgentApi.configUpdate.mock.calls[0]![0]).toEqual({ model: 'new-model' });
  });

  it('完全不动表单时提交空对象', async () => {
    adminAgentApi.configUpdate.mockResolvedValue({});
    const u = userEvent.setup();
    renderPage();
    await screen.findByLabelText('model');

    await u.click(screen.getByRole('button', { name: '保存模型配置' }));

    await waitFor(() => expect(adminAgentApi.configUpdate).toHaveBeenCalled());
    expect(adminAgentApi.configUpdate.mock.calls[0]![0]).toEqual({});
  });

  it('清空已覆盖字段即撤销该覆盖', async () => {
    adminAgentApi.config.mockResolvedValue(cfgView({ model: 'custom-x', maxTokens: 512 }, { model: 'override', maxTokens: 'override' }));
    adminAgentApi.configUpdate.mockResolvedValue({});
    const u = userEvent.setup();
    renderPage();
    const model = await screen.findByLabelText('model');
    await waitFor(() => expect((model as HTMLInputElement).value).toBe('custom-x'));

    await u.clear(model);
    await u.click(screen.getByRole('button', { name: '保存模型配置' }));

    await waitFor(() => expect(adminAgentApi.configUpdate).toHaveBeenCalled());
    // model 已清空 → 不在提交体；maxTokens 仍覆盖 → 保留
    expect(adminAgentApi.configUpdate.mock.calls[0]![0]).toEqual({ maxTokens: 512 });
  });

  it('数字字段以数值类型提交，而非字符串', async () => {
    adminAgentApi.configUpdate.mockResolvedValue({});
    const u = userEvent.setup();
    renderPage();
    const temp = await screen.findByLabelText('temperature');

    await u.type(temp, '1.5');
    await u.click(screen.getByRole('button', { name: '保存模型配置' }));

    await waitFor(() => expect(adminAgentApi.configUpdate).toHaveBeenCalled());
    expect(adminAgentApi.configUpdate.mock.calls[0]![0]).toEqual({ temperature: 1.5 });
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
    await screen.findByLabelText('model');
    const spy = vi.spyOn(qc, 'invalidateQueries');

    await u.click(screen.getByRole('button', { name: '保存模型配置' }));

    await waitFor(() => expect(spy).toHaveBeenCalledWith({ queryKey: ['agent-config'] }));
    expect(toastSuccess).toHaveBeenCalledWith('配置已更新');
  });
});
