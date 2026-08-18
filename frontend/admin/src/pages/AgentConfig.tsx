import { useEffect, useState } from 'react';
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';
import { Button, Card, Col, Descriptions, Form, Input, InputNumber, List, Popconfirm, Row, message } from 'antd';
import { adminAgentApi } from '@shared';

export default function AgentConfig() {
  const qc = useQueryClient();
  const [keys, setKeys] = useState<string[]>([]);
  const [selected, setSelected] = useState<string | null>(null);
  const [content, setContent] = useState('');
  const [cfgForm] = Form.useForm();
  const promptsData = useQuery({ queryKey: ['prompts'], queryFn: adminAgentApi.prompts, staleTime: Infinity });
  const modelCfg = useQuery({ queryKey: ['agent-config'], queryFn: adminAgentApi.config, staleTime: Infinity });

  useEffect(() => {
    const raw = promptsData.data;
    if (raw && !keys.length) {
      // Python 返回结构以实际为准；常见为 { keys: [...] } 或 [{key,...}]；集中在此适配
      const ks = Array.isArray(raw) ? raw.map((x: Record<string, unknown>) => String(x.key)) : Array.isArray((raw as { keys?: unknown }).keys) ? ((raw as { keys: unknown }).keys as string[]) : [];
      setKeys(ks);
      if (ks[0]) loadDetail(ks[0]);
    }
  }, [promptsData.data]);
  const loadDetail = async (k: string) => { setSelected(k); const d = await adminAgentApi.promptDetail(k).catch(() => ({})); setContent(String((d as { promptContent?: unknown }).promptContent ?? '')); };
  const savePrompt = useMutation({ mutationFn: () => adminAgentApi.promptUpdate(selected!, { promptContent: content }), onSuccess: () => message.success('提示词已更新'), onError: (e) => message.error((e as Error).message) });
  const resetPrompt = useMutation({ mutationFn: (k: string) => adminAgentApi.promptReset(k), onSuccess: () => { message.success('已重置为默认'); if (selected) loadDetail(selected); } });
  const saveCfg = useMutation({
    mutationFn: (v: Record<string, unknown>) => adminAgentApi.configUpdate(v), onSuccess: () => { message.success('配置已更新'); qc.invalidateQueries({ queryKey: ['agent-config'] }); }, onError: (e) => message.error((e as Error).message),
  });
  return (
    <Row gutter={16}>
      <Col span={10}>
        <Card title="提示词">
          <List dataSource={keys} renderItem={(k) => (
            <List.Item style={{ cursor: 'pointer', background: k === selected ? '#f0f5f1' : undefined }} onClick={() => loadDetail(k)} actions={[
              <Popconfirm key="r" title="重置为默认？" onConfirm={() => resetPrompt.mutate(k)}><Button size="small" danger>重置</Button></Popconfirm>,
            ]}>{k}</List.Item>
          )} />
        </Card>
      </Col>
      <Col span={14}>
        <Card title={selected ? `编辑：${selected}` : '提示词详情'}>
          <Input.TextArea rows={12} value={content} onChange={(e) => setContent(e.target.value)} />
          <Button type="primary" style={{ marginTop: 12 }} loading={savePrompt.isPending} disabled={!selected} onClick={() => savePrompt.mutate()}>保存提示词</Button>
        </Card>
        <Card title="模型配置" style={{ marginTop: 16 }}>
          <Form form={cfgForm} layout="vertical" onFinish={(v) => saveCfg.mutate(v)} initialValues={modelCfg.data as Record<string, unknown> | undefined}>
            <Form.Item name="model" label="模型"><Input aria-label="模型" /></Form.Item>
            <Form.Item name="temperature" label="temperature（0-2）" rules={[{ type: 'number', min: 0, max: 2 }]}><InputNumber aria-label="temperature" min={0} max={2} step={0.1} style={{ width: '100%' }} /></Form.Item>
            <Form.Item name="maxTokens" label="maxTokens"><InputNumber aria-label="maxTokens" min={1} style={{ width: '100%' }} /></Form.Item>
            <Form.Item name="thinkingBudget" label="thinkingBudget"><InputNumber aria-label="thinkingBudget" min={0} style={{ width: '100%' }} /></Form.Item>
            <Button type="primary" htmlType="submit">保存模型配置</Button>
          </Form>
        </Card>
      </Col>
    </Row>
  );
}
