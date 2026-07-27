import { useState, useEffect, useRef } from 'react';
import { Layout, Input, Button, List, Typography, Space, Spin, message, Popconfirm } from 'antd';
import { SendOutlined, PlusOutlined, DeleteOutlined } from '@ant-design/icons';
import { useQuery, useQueryClient } from '@tanstack/react-query';
import { agentApi } from '@/api/agent';
import { useAuthStore } from '@/store/authStore';
import ReactMarkdown from 'react-markdown';

const { Sider, Content } = Layout;
const { Text } = Typography;

interface Session {
  id?: string;
  sessionId?: string;
  title?: string;
}

interface Message {
  role: 'user' | 'assistant';
  content: string;
}

export default function Agent() {
  const [currentSessionId, setCurrentSessionId] = useState<string | null>(null);
  const [messages, setMessages] = useState<Message[]>([]);
  const [inputText, setInputText] = useState('');
  const [isStreaming, setIsStreaming] = useState(false);
  const messagesEndRef = useRef<HTMLDivElement>(null);
  const historyCache = useRef<Map<string, Message[]>>(new Map());
  const queryClient = useQueryClient();
  const { token } = useAuthStore();

  // 加载会话列表
  const { isLoading: sessionsLoading, data: sessions } = useQuery<Session[]>({
    queryKey: ['agent-sessions'],
    queryFn: () => agentApi.sessions() as Promise<Session[]>,
  });

  // 加载历史消息
  const loadHistory = async (sessionId: string) => {
    const cached = historyCache.current.get(sessionId);
    if (cached) { setMessages(cached); return; }
    try {
      const history = await agentApi.history(sessionId) as any;
      const msgs = history || [];
      historyCache.current.set(sessionId, msgs);
      setMessages(msgs);
    } catch {
      setMessages([]);
    }
  };

  const refetchSessions = () => {
    queryClient.invalidateQueries({ queryKey: ['agent-sessions'] });
  };

  const createSession = async () => {
    try {
      const result = await agentApi.createSession() as any;
      setCurrentSessionId(result?.id || result?.sessionId || result?.session_id);
      setMessages([]);
      refetchSessions();
    } catch (err: any) {
      message.error('创建会话失败');
    }
  };

  const deleteSession = async (sessionId: string) => {
    try {
      await agentApi.removeSession(sessionId);
      if (currentSessionId === sessionId) {
        setCurrentSessionId(null);
        setMessages([]);
      }
      refetchSessions();
    } catch {
      message.error('删除失败');
    }
  };

  // SSE 流式发送消息
  const sendMessage = async () => {
    if (!inputText.trim() || isStreaming) return;

    const userMessage: Message = { role: 'user', content: inputText.trim() };
    let sessionId = currentSessionId;

    // 如果没有会话，先创建
    if (!sessionId) {
      try {
        const result = await agentApi.createSession() as any;
        sessionId = result?.id || result?.sessionId || result?.session_id;
        setCurrentSessionId(sessionId);
        refetchSessions();
      } catch { return; }
    }

    setMessages(prev => [...prev, userMessage]);
    setInputText('');
    setIsStreaming(true);

    // 添加空的 AI 消息占位
    const aiMsg: Message = { role: 'assistant', content: '' };
    setMessages(prev => [...prev, aiMsg]);

    try {
      const response = await fetch('/api/agent/stream', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${token}`,
        },
        body: JSON.stringify({ session_id: sessionId, message: userMessage.content }),
      });

      const reader = response.body?.getReader();
      if (!reader) throw new Error('No response stream');

      const decoder = new TextDecoder();
      let fullContent = '';

      while (true) {
        const { done, value } = await reader.read();
        if (done) break;

        const chunk = decoder.decode(value, { stream: true });
        // SSE 格式: "data: {...}\n\n"
        const lines = chunk.split('\n');
        for (const line of lines) {
          if (line.startsWith('data: ')) {
            try {
              const json = JSON.parse(line.slice(6));
              if (json.content) {
                fullContent += json.content;
                setMessages(prev => {
                  const updated = [...prev];
                  updated[updated.length - 1] = { role: 'assistant', content: fullContent };
                  return updated;
                });
              }
            } catch { /* ignore parse errors during streaming */ }
          }
        }
      }
    } catch (err) {
      message.error('请求失败，请重试');
    } finally {
      setIsStreaming(false);
    }
  };

  // 自动滚动到底部
  // 缓存当前会话消息到本地
  useEffect(() => {
    if (currentSessionId && !isStreaming && messages.length > 0) {
      historyCache.current.set(currentSessionId, messages);
    }
  }, [currentSessionId, isStreaming, messages]);

  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages]);

  // 选中会话
  const selectSession = (sessionId: string) => {
    setCurrentSessionId(sessionId);
    loadHistory(sessionId);
  };

  return (
    <Layout style={{ height: 'calc(100vh - 64px)', background: '#fff' }}>
      {/* 侧边栏 — 会话列表 */}
      <Sider width={260} style={{ background: '#fafafa', borderRight: '1px solid #f0f0f0', overflow: 'auto' }}>
        <div style={{ padding: 16 }}>
          <Button type="primary" icon={<PlusOutlined />} onClick={createSession} block>
            新建会话
          </Button>
        </div>
        <List
          loading={sessionsLoading}
          dataSource={sessions ?? []}
          renderItem={(session: any) => (
            <List.Item
              onClick={() => selectSession(session.id || session.sessionId || session.session_id)}
              style={{
                cursor: 'pointer',
                background: currentSessionId === (session.id || session.sessionId || session.session_id) ? '#e6f4ff' : 'transparent',
                padding: '8px 16px',
              }}
              actions={[
                <Popconfirm title="删除此会话？" onConfirm={() => deleteSession(session.id || session.sessionId || session.session_id)}>
                  <DeleteOutlined style={{ color: '#999' }} />
                </Popconfirm>
              ]}
            >
              <Text ellipsis>{session.title || session.id || '未命名会话'}</Text>
            </List.Item>
          )}
        />
      </Sider>

      {/* 主聊天区 */}
      <Content style={{ display: 'flex', flexDirection: 'column' }}>
        <div style={{ flex: 1, overflow: 'auto', padding: 24 }}>
          {messages.length === 0 ? (
            <div style={{ textAlign: 'center', color: '#999', marginTop: 80 }}>
              <Text>开始和 AI 助手对话吧！</Text>
            </div>
          ) : (
            messages.map((msg, idx) => (
              <div key={idx} style={{
                marginBottom: 16,
                textAlign: msg.role === 'user' ? 'right' : 'left',
              }}>
                <div style={{
                  display: 'inline-block',
                  maxWidth: '70%',
                  padding: '12px 16px',
                  borderRadius: 8,
                  background: msg.role === 'user' ? '#1677ff' : '#f5f5f5',
                  color: msg.role === 'user' ? '#fff' : '#333',
                }}>
                  {msg.role === 'assistant' ? (
                    <ReactMarkdown>{msg.content}</ReactMarkdown>
                  ) : (
                    msg.content
                  )}
                </div>
              </div>
            ))
          )}
          <div ref={messagesEndRef} />
        </div>

        {/* 输入区 */}
        <div style={{ padding: '16px 24px', borderTop: '1px solid #f0f0f0' }}>
          <Space.Compact style={{ width: '100%' }}>
            <Input.TextArea
              value={inputText}
              onChange={e => setInputText(e.target.value)}
              onPressEnter={e => {
                if (!e.shiftKey) { e.preventDefault(); sendMessage(); }
              }}
              placeholder="输入消息... (Shift+Enter 换行)"
              rows={2}
              disabled={isStreaming}
            />
            <Button
              type="primary"
              icon={isStreaming ? <Spin /> : <SendOutlined />}
              onClick={sendMessage}
              disabled={!inputText.trim() || isStreaming}
              style={{ height: 'auto' }}
            >
              发送
            </Button>
          </Space.Compact>
        </div>
      </Content>
    </Layout>
  );
}
