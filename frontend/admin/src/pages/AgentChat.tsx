import { Button, Input, Layout, List, Space } from 'antd';
import ReactMarkdown from 'react-markdown';
import { adminAgentApi, useAgentChat } from '@shared';

const { Sider, Content } = Layout;
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
        <div style={{ flex: 1, overflow: 'auto', marginBottom: 12 }}>
          {messages.map((m) => <div key={m.id} style={{ textAlign: m.role === 'user' ? 'right' : 'left', marginBottom: 12 }}><ReactMarkdown>{m.content}</ReactMarkdown></div>)}
        </div>
        <Space.Compact style={{ width: '100%' }}>
          <Input placeholder="输入消息…" onPressEnter={(e) => { send((e.target as HTMLInputElement).value); (e.target as HTMLInputElement).value = ''; }} />
          <Button type="primary" disabled={streaming} onClick={() => {
            const el = document.querySelector<HTMLInputElement>('input[placeholder="输入消息…"]');
            if (el) { send(el.value); el.value = ''; }
          }}>发送</Button>
        </Space.Compact>
      </Content>
    </Layout>
  );
}
