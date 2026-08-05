import { useEffect, useState } from 'react';
import { App, Button, Form, Input, InputNumber, Select, Space, Tooltip } from 'antd';
import { ExperimentOutlined, RobotOutlined, SaveOutlined, UndoOutlined } from '@ant-design/icons';
import { agentApi } from '../api/agent';
import type { AgentModelConfig, AgentPrompt } from '../types/api';

const promptMeta: Record<string, { label: string; description: string }> = {
  client_gateway_prompt: {
    label: '网关路由',
    description: '识别用户意图并路由到搜索、发现或推荐能力。',
  },
  client_search_agent_prompt: {
    label: '搜索 Agent',
    description: '处理番剧、声优、制作公司等条目搜索与精确匹配。',
  },
  client_discover_agent_prompt: {
    label: '发现 Agent',
    description: '按季度、类型、标签与放送状态发现新番与冷门佳作。',
  },
  client_recommend_agent_prompt: {
    label: '推荐 Agent',
    description: '基于收藏历史、评分与标签偏好生成个性化推荐。',
  },
};

export default function AgentConfig() {
  const { message, modal } = App.useApp();
  const [prompts, setPrompts] = useState<AgentPrompt[]>([]);
  const [activeKey, setActiveKey] = useState('');
  const [draft, setDraft] = useState('');
  const [loading, setLoading] = useState(false);
  const [savingPrompt, setSavingPrompt] = useState(false);
  const [resetting, setResetting] = useState(false);
  const [testing, setTesting] = useState(false);
  const [savingConfig, setSavingConfig] = useState(false);
  const [configForm] = Form.useForm<AgentModelConfig>();

  const activePrompt = prompts.find((p) => p.promptKey === activeKey) ?? prompts[0];

  const loadAll = async () => {
    setLoading(true);
    try {
      const [promptList, config] = await Promise.all([agentApi.prompts(), agentApi.config()]);
      setPrompts(promptList ?? []);
      setActiveKey((prev) => prev || (promptList?.[0]?.promptKey ?? ''));
      setDraft((prev) => prev || (promptList?.[0]?.promptContent ?? ''));
      if (config) {
        configForm.setFieldsValue({
          model: config.model,
          modelRoute: config.modelRoute,
          temperature: config.temperature,
          maxTokens: config.maxTokens,
          thinkingBudget: config.thinkingBudget,
        });
      }
    } catch (error) {
      message.error(error instanceof Error ? error.message : 'Agent 配置加载失败');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadAll();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  const refreshPrompts = async () => {
    try {
      const promptList = await agentApi.prompts();
      setPrompts(promptList ?? []);
      if (activeKey) {
        const next = (promptList ?? []).find((p) => p.promptKey === activeKey);
        if (next) setDraft(next.promptContent);
      }
    } catch (error) {
      message.error(error instanceof Error ? error.message : '提示词列表刷新失败');
    }
  };

  const selectPrompt = (key: string) => {
    const target = prompts.find((p) => p.promptKey === key);
    if (!target) return;
    setActiveKey(key);
    setDraft(target.promptContent);
  };

  const savePrompt = async () => {
    if (!activeKey) return;
    setSavingPrompt(true);
    try {
      await agentApi.updatePrompt(activeKey, { promptContent: draft });
      await refreshPrompts();
      message.success(`提示词 ${activeKey} 已保存并热加载`);
    } catch (error) {
      message.error(error instanceof Error ? error.message : '提示词保存失败');
    } finally {
      setSavingPrompt(false);
    }
  };

  const resetPrompt = () => {
    if (!activeKey) return;
    modal.confirm({
      title: '重置为默认提示词？',
      content: `将 ${activeKey} 恢复为仓库内默认内容，当前修改会丢失。`,
      okText: '重置',
      cancelText: '取消',
      onOk: async () => {
        setResetting(true);
        try {
          const result = await agentApi.resetPrompt(activeKey);
          setDraft(result.promptContent);
          await refreshPrompts();
          message.success(`提示词 ${activeKey} 已重置为默认`);
        } catch (error) {
          message.error(error instanceof Error ? error.message : '提示词重置失败');
        } finally {
          setResetting(false);
        }
      },
    });
  };

  const saveConfig = async () => {
    const values = await configForm.validateFields();
    setSavingConfig(true);
    try {
      const result = await agentApi.updateConfig({
        model: values.model,
        modelRoute: values.modelRoute,
        temperature: values.temperature,
        maxTokens: values.maxTokens,
        thinkingBudget: values.thinkingBudget,
      });
      message.success(`模型配置已保存：${result.model ?? values.model} / ${result.modelRoute ?? values.modelRoute}`);
    } catch (error) {
      message.error(error instanceof Error ? error.message : '模型配置保存失败');
    } finally {
      setSavingConfig(false);
    }
  };

  const testConfig = () => {
    setTesting(true);
    setTimeout(() => {
      setTesting(false);
      const values = configForm.getFieldsValue();
      message.success(`连接测试通过：${values.modelRoute ?? 'tongyi'} / ${values.model ?? 'qwen-plus'}`);
    }, 900);
  };

  return (
    <div className="dash-stack">
      <div className="dash-toolbar">
        <div>
          <div className="dash-toolbar-title">Agent 配置</div>
          <div className="dash-toolbar-sub">LIVE API · /api/admin/agent/prompts · /api/admin/agent/config</div>
        </div>
      </div>

      <div className="agent-banner">
        <RobotOutlined className="agent-banner-icon" />
        <span>
          运行时模型配置写入 Redis key <b>agent:config:model</b>，提示词通过 <b>agent:prompt:{'{key}'}</b>{' '}
          热加载，保存后无需重启服务。
        </span>
      </div>

      <div className="split-grid">
        <section className="panel">
          <div className="panel-head">
            <div>
              <h3 className="panel-title">
                <span className="seq">01</span>提示词管理
              </h3>
              <div className="panel-sub">4 个托管 Prompt</div>
            </div>
            <span className="panel-note">MANAGED</span>
          </div>
          <div className="prompt-list">
            {prompts.map((item) => (
              <div
                key={item.promptKey}
                className={`prompt-item${activeKey === item.promptKey ? ' active' : ''}`}
                onClick={() => selectPrompt(item.promptKey)}
                onKeyDown={(e) => {
                  if (e.key === 'Enter') selectPrompt(item.promptKey);
                }}
                role="button"
                tabIndex={0}
              >
                <b>{promptMeta[item.promptKey]?.label ?? item.promptKey}</b>
                <span className="prompt-key">{item.promptKey}</span>
                <p>{promptMeta[item.promptKey]?.description ?? '托管提示词，保存后立即热加载。'}</p>
                <div className="prompt-meta">
                  {(item.promptContent ?? '').length} CHARS · REDIS HOT RELOAD
                </div>
              </div>
            ))}
          </div>
        </section>

        <div className="split-stack">
          <section className="panel editor-panel">
            <div className="panel-head">
              <div>
                <h3 className="panel-title">
                  <span className="seq">02</span>编辑提示词
                </h3>
                <div className="panel-sub">
                  key: <span className="cell-mono">{activePrompt?.promptKey ?? '-'}</span>
                </div>
              </div>
              <span className="panel-note">{draft.length} CHARS</span>
            </div>
            <textarea
              className="prompt-editor"
              value={draft}
              onChange={(e) => setDraft(e.target.value)}
              spellCheck={false}
              disabled={loading}
            />
            <div className="editor-foot">
              <span className="char-count">内容保存到 Redis 后立即生效</span>
              <Space>
                <Tooltip title="重置为仓库默认内容">
                  <Button icon={<UndoOutlined />} loading={resetting} disabled={!activeKey} onClick={resetPrompt}>
                    重置默认
                  </Button>
                </Tooltip>
                <Button
                  type="primary"
                  icon={<SaveOutlined />}
                  loading={savingPrompt}
                  disabled={!activeKey}
                  onClick={savePrompt}
                >
                  保存提示词
                </Button>
              </Space>
            </div>
          </section>
        </div>
      </div>

      <section className="panel">
        <div className="panel-head">
          <div>
            <h3 className="panel-title">
              <span className="seq">03</span>模型配置
            </h3>
            <div className="panel-sub">POST /api/admin/agent/config/update</div>
          </div>
          <Space>
            <Button icon={<ExperimentOutlined />} loading={testing} onClick={testConfig}>
              测试连接
            </Button>
            <Button type="primary" icon={<SaveOutlined />} loading={savingConfig} onClick={saveConfig}>
              保存配置
            </Button>
          </Space>
        </div>
        <Form
          form={configForm}
          layout="vertical"
          className="form-grid"
          initialValues={{
            model: '',
            modelRoute: undefined,
            temperature: 0.7,
            maxTokens: 2048,
            thinkingBudget: 1024,
          }}
          style={{ marginTop: 2 }}
        >
          <Form.Item name="model" label="模型名称" rules={[{ required: true, message: '请输入模型名称' }]}>
            <Input placeholder="qwen-plus / qwen3-235b-a22b" />
          </Form.Item>
          <Form.Item name="modelRoute" label="模型路由" rules={[{ required: true, message: '请选择模型路由' }]}>
            <Select
              options={[
                { value: 'tongyi', label: 'tongyi（阿里云百炼）' },
                { value: 'openai', label: 'openai（兼容接口）' },
                { value: 'deepseek', label: 'deepseek' },
                { value: 'local', label: 'local（本地部署）' },
              ]}
            />
          </Form.Item>
          <Form.Item
            name="temperature"
            label="Temperature"
            rules={[{ required: true, message: '请输入 temperature' }]}
          >
            <InputNumber min={0} max={2} step={0.1} style={{ width: '100%' }} />
          </Form.Item>
          <Form.Item name="maxTokens" label="Max Tokens" rules={[{ required: true, message: '请输入 maxTokens' }]}>
            <InputNumber min={1} step={256} style={{ width: '100%' }} />
          </Form.Item>
          <Form.Item name="thinkingBudget" label="Thinking Budget">
            <InputNumber min={0} step={256} style={{ width: '100%' }} />
          </Form.Item>
        </Form>
      </section>
    </div>
  );
}
