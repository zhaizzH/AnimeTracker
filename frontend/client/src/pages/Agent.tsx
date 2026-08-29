import { useState } from 'react';
import { Button, Layout, List, Space, theme } from 'antd';
import { MenuFoldOutlined, MenuUnfoldOutlined, DeleteOutlined } from '@ant-design/icons';
import { AgentConversation, useClientAgentChat } from '../components/AgentChat';

const { Sider, Content } = Layout;

export default function Agent() {
  const { token } = theme.useToken();
  const { chat } = useClientAgentChat();
  const { sessions, activeId, streaming, ready, select, create, remove } = chat;
  const [collapsed, setCollapsed] = useState(false);

  return (
    <Layout style={{ height: 'calc(100vh - 64px)' }}>
      <Sider className="od-sider" theme="light" width={240} breakpoint="lg" collapsedWidth={0} trigger={null} collapsed={collapsed} onCollapse={(c) => setCollapsed(c)} style={{ borderRight: `1px solid ${token.colorBorderSecondary}`, background: token.colorBgContainer }}>
        <Button type="primary" block style={{ borderRadius: 0, marginBottom: 12 }} disabled={!ready || streaming} onClick={create}>新建会话</Button>
        <List size="small" dataSource={sessions} renderItem={(s: Record<string, unknown>) => (
          <List.Item style={{ cursor: ready ? 'pointer' : 'default', padding: '8px 12px', background: String(s.id) === activeId ? token.colorPrimaryBg : undefined }} onClick={() => { if (ready && !streaming) void select(String(s.id)); }}>
            <Space>{String((s as { title?: unknown }).title ?? (s as { id?: unknown }).id)}<Button type="text" danger size="small" className="od-session-delete" icon={<DeleteOutlined />} aria-label="删除会话" disabled={!ready || streaming} onClick={(e) => { e.stopPropagation(); void remove(String(s.id)); }} /></Space>
          </List.Item>
        )} />
      </Sider>
      <Content style={{ display: 'flex', flexDirection: 'column', padding: 16 }}>
        <Button type="text" style={{ alignSelf: 'flex-start', marginBottom: 8 }} aria-label={collapsed ? '展开会话列表' : '收起会话列表'} icon={collapsed ? <MenuUnfoldOutlined /> : <MenuFoldOutlined />} onClick={() => setCollapsed(!collapsed)} />
        <AgentConversation />
      </Content>
    </Layout>
  );
}