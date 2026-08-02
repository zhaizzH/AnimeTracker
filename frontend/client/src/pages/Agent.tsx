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
  const [toolStatus, setToolStatus] = useState('');
  const [thinking, setThinking] = useState('');
  const messagesEndRef = useRef<HTMLDivElement>(null);
  const historyCache = useRef<Map<string, Message[]>>(new Map());
  const queryClient = useQueryClient();
  const { token } = useAuthStore();

  const { isLoading: sessionsLoading, data: sessions, isError: sessionsError } = useQuery<Session[]>({
    queryKey: ['agent-sessions'],
    queryFn: () => agentApi.sessions() as Promise<Session[]>,
    retry: 1,
  });

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
      message.error('加载历史失败，请重试');
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

  const sendMessage = async () => {
    if (!inputText.trim() || isStreaming) return;

    const userMessage: Message = { role: 'user', content: inputText.trim() };
    let sessionId = currentSessionId;

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
    setThinking('');
    setToolStatus('');
    setIsStreaming(true);

    const aiMsg: Message = { role: 'assistant', content: '' };
    setMessages(prev => [...prev, aiMsg]);

    try {
      const response = await fetch('/api/agent/stream', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${token}`,
        },
        body: JSON.stringify({ session_id: sessionId, content: userMessage.content }),
      });

      const reader = response.body?.getReader();
      if (!reader) throw new Error('No response stream');

      const decoder = new TextDecoder();
      let fullContent = '';

      while (true) {
        const { done, value } = await reader.read();
        if (done) break;

        const chunk = decoder.decode(value, { stream: true });
        const lines = chunk.split('\n');
        for (const line of lines) {
          if (!line.startsWith('data: ')) continue;
          try {
            const json = JSON.parse(line.slice(6));
            if (json.type === 'answer' && json.content?.text) {
              fullContent += json.content.text;
              setMessages(prev => {
                const updated = [...prev];
                updated[updated.length - 1] = { role: 'assistant', content: fullContent };
                return updated;
              });
            } else if (json.type === 'thinking' && json.content?.text) {
              setThinking(prev => prev + json.content.text);
            } else if (json.type === 'function_call' && json.content?.state === 'start') {
              setToolStatus(json.content.message || '正在处理...');
            } else if (json.type === 'function_call' && json.content?.state === 'end') {
              setToolStatus('');
            } else if (json.is_end) {
              setToolStatus('');
            }
          } catch { /* 忽略流式中的解析错误 */ }
        }
      }
    } catch (err) {
      message.error('请求失败，请重试');
    } finally {
      setIsStreaming(false);
    }
  };

  // 进入对话时默认打开最近一次对话(后端已按 updated_at 倒序,sessions[0] 即最近)
  useEffect(() => {
    if (currentSessionId || !sessions || sessions.length === 0) return;
    const sid = (sessions[0] as any).session_id || (sessions[0] as any).sessionId || (sessions[0] as any).id;
    setCurrentSessionId(sid);
    loadHistory(sid);
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [currentSessionId, sessions]);

  useEffect(() => {
    if (currentSessionId && !isStreaming && messages.length > 0) {
      historyCache.current.set(currentSessionId, messages);
    }
  }, [currentSessionId, isStreaming, messages]);

  useEffect(() => {
    // 思考/工具状态变化时容器高度也在变,只依赖 messages 会导致思考期间不滚底
    messagesEndRef.current?.scrollIntoView({ behavior: isStreaming ? 'auto' : 'smooth' });
  }, [messages, thinking, toolStatus, isStreaming]);

  const selectSession = (sessionId: string) => {
    setCurrentSessionId(sessionId);
    loadHistory(sessionId);
  };

  return (
    <Layout className="agent-book">
      <Sider width={260}>
        <div className="agent-sider-head">
          <h3>会话档案</h3>
          <Button type="primary" icon={<PlusOutlined />} onClick={createSession} block>
            新开一页
          </Button>
        </div>
        {!sessionsLoading && sessionsError && (
          <div style={{ padding: 12, textAlign: 'center' }}>
            <Text type="secondary" style={{ display: 'block', marginBottom: 8 }}>加载会话失败</Text>
            <Button size="small" onClick={refetchSessions}>重试</Button>
          </div>
        )}
        <List
          className="agent-session-list"
          loading={sessionsLoading}
          dataSource={sessions ?? []}
          split={false}
          renderItem={(session: any, idx: number) => {
            const sid = session.id || session.sessionId || session.session_id;
            return (
              <div
                className={`agent-session-item ${currentSessionId === sid ? 'active' : ''}`}
                onClick={() => selectSession(sid)}
              >
                <Space size={6} style={{ minWidth: 0 }}>
                  <span className="session-no">{String(idx + 1).padStart(2, '0')}</span>
                  <Text ellipsis style={{ color: 'inherit' }}>
                    {session.title || session.id || '未命名会话'}
                  </Text>
                </Space>
                <Popconfirm
                  title="删除此会话？"
                  onConfirm={e => { e?.stopPropagation(); deleteSession(sid); }}
                  onCancel={e => e?.stopPropagation()}
                >
                  <DeleteOutlined
                    style={{ color: 'var(--ink-faint)' }}
                    onClick={e => e.stopPropagation()}
                  />
                </Popconfirm>
              </div>
            );
          }}
        />
      </Sider>

      <Content className="agent-chat">
        <div className="agent-chat-scroll">
          {messages.length === 0 ? (
            <div className="agent-empty">开始和 AI 助手对话吧。</div>
          ) : (
            messages.map((msg, idx) => (
              <div key={idx} className={`agent-message ${msg.role}`}>
                <div className={`agent-bubble ${msg.role}`}>
                  {msg.role === 'assistant' ? (
                    <>
                      {/* 思考过程只属于当前正在回答的最后一条消息;流中展开,结束后自动折叠 */}
                      {thinking && idx === messages.length - 1 && (
                        <details open={isStreaming} style={{ marginBottom: 8, opacity: 0.6, fontSize: 12 }}>
                          <summary>思考过程</summary>
                          <pre style={{ whiteSpace: 'pre-wrap' }}>{thinking}</pre>
                        </details>
                      )}
                      <div className="agent-markdown">
                        {msg.content ? (
                          <ReactMarkdown>{msg.content}</ReactMarkdown>
                        ) : isStreaming ? (
                          <Text type="secondary">正在思考…</Text>
                        ) : null}
                      </div>
                    </>
                  ) : (
                    msg.content
                  )}
                </div>
              </div>
            ))
          )}
          <div ref={messagesEndRef} />
        </div>

        <div className="agent-input-bar">
          {toolStatus && <Text type="secondary" style={{ display: 'block', marginBottom: 8 }}>{toolStatus}</Text>}
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
