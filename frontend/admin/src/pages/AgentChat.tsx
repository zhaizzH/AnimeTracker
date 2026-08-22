import { Button, Collapse, Input, Layout, List, Space, Typography } from 'antd';
import ReactMarkdown from 'react-markdown';
import { useEffect, useRef, useState } from 'react';
import { adminAgentApi, useAgentChat, type ChatMsg } from '@shared';

const { Sider, Content } = Layout;

function ThinkingCollapse({ text, streaming }: { text: string; streaming: boolean }) {
  const [open, setOpen] = useState(true);
  // 回答完成后自动收起；流式期间保持展开
  useEffect(() => { if (!streaming) setOpen(false); }, [streaming]);
  return (
    <Collapse
      ghost
      size="small"
      activeKey={open ? 't' : []}
      onChange={(keys) => setOpen(keys.includes('t'))}
      items={[{ key: 't', label: <Typography.Text type="secondary">思考过程</Typography.Text>, children: <Typography.Text type="secondary" style={{ whiteSpace: 'pre-wrap' }}>{text}</Typography.Text> }]}
    />
  );
}

export default function AgentChat() {
  const api = {
    listSessions: adminAgentApi.chatSessions,
    createSession: adminAgentApi.chatCreateSession,
    history: adminAgentApi.chatHistory,
    deleteSession: adminAgentApi.chatDeleteSession,
    streamBody: adminAgentApi.chatStreamBody,
    streamUrl: '/api/admin/agent/chat/stream',
  };
  const { messages, sessions, activeId, streaming, send, select, create, remove } = useAgentChat(api);
  const [input, setInput] = useState('');
  const scrollRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    const el = scrollRef.current;
    if (el) el.scrollTop = el.scrollHeight;
  }, [messages]);

  const submit = () => {
    if (!input.trim() || streaming) return;
    send(input);
    setInput('');
  };

  const renderItem = (m: ChatMsg) => (
    <div key={m.id} style={{ textAlign: m.role === 'user' ? 'right' : 'left', marginBottom: 12 }}>
      {m.thinking && <ThinkingCollapse text={m.thinking} streaming={streaming} />}
      <div style={{ display: 'inline-block', maxWidth: '80%', textAlign: 'left', background: m.role === 'user' ? '#e6f4ff' : '#f5f5f5', padding: '8px 12px', borderRadius: 8 }}><ReactMarkdown>{m.content}</ReactMarkdown></div>
    </div>
  );

  return (
    <Layout style={{ height: 'calc(100vh - 120px)' }}>
      <Sider theme="light" width={240} style={{ borderRight: '1px solid #eee' }}>
        <Button type="primary" block style={{ margin: 12 }} onClick={create}>新建会话</Button>
        <List size="small" dataSource={sessions} renderItem={(s: Record<string, unknown>) => (
          <List.Item style={{ cursor: 'pointer', padding: '8px 12px', background: String(s.id) === activeId ? '#f0f5f1' : undefined }} onClick={() => select(String(s.id))}>
            <Space>{String((s as { title?: unknown }).title ?? (s as { id?: unknown }).id)}{activeId === String(s.id) && <Button size="small" danger onClick={(e) => { e.stopPropagation(); remove(String(s.id)); }}>删</Button>}</Space>
          </List.Item>
        )} />
      </Sider>
      <Content style={{ display: 'flex', flexDirection: 'column', padding: 16 }}>
        <div ref={scrollRef} style={{ flex: 1, overflow: 'auto', marginBottom: 12 }}>
          {messages.map(renderItem)}
        </div>
        <Space.Compact style={{ width: '100%' }}>
          <Input placeholder="输入消息…" value={input} onChange={(e) => setInput(e.target.value)} onPressEnter={submit} disabled={streaming} />
          <Button type="primary" disabled={streaming || !input.trim()} onClick={submit}>发送</Button>
        </Space.Compact>
      </Content>
    </Layout>
  );
}
