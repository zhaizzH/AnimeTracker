import { createContext, type ReactNode, useCallback, useContext, useEffect, useRef, useState } from 'react';
import { Button, Collapse, Empty, Input, message, Space, Typography } from 'antd';
import { agentApi, type ChatMsg, useAgentChat } from '@shared';
import AgentMarkdown from './AgentMarkdown';

const clientAgentApi = {
  listSessions: agentApi.listSessions,
  createSession: agentApi.createSession,
  history: agentApi.history,
  deleteSession: agentApi.deleteSession,
  streamBody: agentApi.streamBody,
  streamUrl: '/api/client/agent/stream',
  health: agentApi.health,
};

type AgentChatState = ReturnType<typeof useAgentChat>;
interface AgentChatContextValue {
  activate: () => void;
  chat: AgentChatState;
}

const AgentChatContext = createContext<AgentChatContextValue | null>(null);

export function AgentChatProvider({ children }: { children: ReactNode }) {
  const [enabled, setEnabled] = useState(false);
  const chat = useAgentChat(clientAgentApi, { enabled });
  const activate = useCallback(() => setEnabled(true), []);
  return <AgentChatContext.Provider value={{ activate, chat }}>{children}</AgentChatContext.Provider>;
}

export function useClientAgentChat() {
  const value = useContext(AgentChatContext);
  if (!value) throw new Error('useClientAgentChat must be used inside AgentChatProvider');
  return value;
}

function ThinkingCollapse({ text, streaming }: { text: string; streaming: boolean }) {
  const [open, setOpen] = useState(true);
  useEffect(() => { if (!streaming) setOpen(false); }, [streaming]);
  return (
    <Collapse
      ghost
      size="small"
      activeKey={open ? 'thinking' : []}
      onChange={(keys) => setOpen(keys.includes('thinking'))}
      items={[{
        key: 'thinking',
        label: <Typography.Text type="secondary">思考过程</Typography.Text>,
        children: <Typography.Text type="secondary" className="od-agent-thinking">{text}</Typography.Text>,
      }]}
    />
  );
}

export function AgentConversation() {
  const { activate, chat } = useClientAgentChat();
  const { messages, activeId, health, streaming, ready, send } = chat;
  const [input, setInput] = useState('');
  const scrollRef = useRef<HTMLDivElement>(null);

  useEffect(() => { activate(); }, [activate]);
  useEffect(() => {
    const el = scrollRef.current;
    if (el) el.scrollTop = el.scrollHeight;
  }, [messages]);

  const prevHealth = useRef(health);
  useEffect(() => {
    if (health === 'unavailable' && prevHealth.current !== 'unavailable') {
      message.warning({ content: 'AI 助手连接失败，请检查服务', duration: 3 });
    }
    prevHealth.current = health;
  }, [health]);

  const submit = () => {
    if (!ready || !input.trim() || streaming || !activeId) return;
    void send(input);
    setInput('');
  };

  const renderMessage = (message: ChatMsg) => (
    <div key={message.id} className={`od-agent-message od-agent-message--${message.role}`}>
      {message.thinking && <ThinkingCollapse text={message.thinking} streaming={streaming} />}
      {message.role === 'assistant' && !message.content ? <Typography.Text type="secondary">思考中…</Typography.Text> : <AgentMarkdown>{message.content}</AgentMarkdown>}
    </div>
  );

  return (
    <section className="od-agent-conversation" aria-label="AI 对话">
      <div ref={scrollRef} className="od-agent-messages" aria-live="polite">
        {messages.length > 0 ? messages.map(renderMessage) : (
          <Empty image={Empty.PRESENTED_IMAGE_SIMPLE} description={activeId ? '开始一段对话吧' : '正在连接 AI 助手…'} />
        )}
      </div>
      <Space.Compact className="od-agent-composer">
        <Input
          aria-label="发送给 AI 助手的消息"
          placeholder="输入消息…"
          value={input}
          disabled={!ready || !activeId}
          onChange={(event) => setInput(event.target.value)}
          onPressEnter={submit}
        />
        <Button type="primary" loading={streaming} disabled={!ready || !activeId} onClick={submit}>发送</Button>
      </Space.Compact>
    </section>
  );
}
