import { useState } from 'react';
import { Button, Input, Layout, List, Space, Typography } from 'antd';
import ReactMarkdown from 'react-markdown';
import { useAgentChat } from '../hooks/useAgentChat';

const { Sider, Content } = Layout;
export default function Agent() {
  const { messages, sessions, activeId, health, streaming, send, select, create, remove } = useAgentChat();
  const [input, setInput] = useState('');
  const submit = () => { if (!input.trim() || streaming) return; send(input); setInput(''); };

  return (
    <Layout style={{ height: 'calc(100vh - 64px)' }}>
      <Sider theme="light" width={240} style={{ borderRight: '1px solid #eee' }}>
        <Button type="primary" block style={{ margin: 12 }} onClick={create}>新建会话</Button>
        <List size="small" dataSource={sessions} renderItem={(s: Record<string, unknown>) => (
          <List.Item style={{ cursor: 'pointer', padding: '8px 12px', background: String(s.id) === activeId ? '#f0f5f1' : undefined }} onClick={() => select(String(s.id))}>
            <Space>{String((s as { title?: unknown }).title ?? (s as { id?: unknown }).id)}{activeId === String(s.id) && <Button size="small" danger onClick={(e) => { e.stopPropagation(); remove(String(s.id)); }}>删</Button>}</Space>
          </List.Item>
        )} />
      </Sider>
      <Content style={{ display: 'flex', flexDirection: 'column', padding: 16 }}>
        <Typography.Text type="secondary">Agent 状态：{health}</Typography.Text>
        <div style={{ flex: 1, overflow: 'auto', margin: '12px 0' }}>
          {messages.map((m) => <div key={m.id} style={{ textAlign: m.role === 'user' ? 'right' : 'left', marginBottom: 12 }}><ReactMarkdown>{m.content}</ReactMarkdown></div>)}
        </div>
        <Space.Compact style={{ width: '100%' }}>
          <Input placeholder="输入消息…" value={input} onChange={(e) => setInput(e.target.value)} onPressEnter={submit} />
          <Button type="primary" onClick={submit} disabled={streaming}>发送</Button>
        </Space.Compact>
      </Content>
    </Layout>
  );
}
