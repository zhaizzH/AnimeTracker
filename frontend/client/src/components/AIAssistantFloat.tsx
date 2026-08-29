import { useEffect, useRef, useState } from 'react';
import { Button, Tooltip } from 'antd';
import { CloseOutlined, ExpandOutlined, RobotOutlined } from '@ant-design/icons';
import { useLocation, useNavigate } from 'react-router-dom';
import { AgentConversation } from './AgentChat';

export default function AIAssistantFloat() {
  const [open, setOpen] = useState(false);
  const location = useLocation();
  const navigate = useNavigate();
  const wasOpen = useRef(false);

  useEffect(() => { setOpen(false); }, [location.key]);
  useEffect(() => {
    if (!open) return;
    const closeOnEscape = (event: KeyboardEvent) => {
      if (event.key === 'Escape') setOpen(false);
    };
    window.addEventListener('keydown', closeOnEscape);
    return () => window.removeEventListener('keydown', closeOnEscape);
  }, [open]);
  useEffect(() => {
    if (open) document.getElementById('od-agent-float-close')?.focus();
    else if (wasOpen.current) document.getElementById('od-agent-float-trigger')?.focus();
    wasOpen.current = open;
  }, [open]);

  if (location.pathname.replace(/\/+$/, '') === '/agent') return null;

  const toggle = () => {
    setOpen((current) => !current);
  };
  const openFullAgent = () => {
    setOpen(false);
    navigate('/agent');
  };

  return (
    <>
      <Tooltip title="AI 助手" placement="left">
        <Button
          id="od-agent-float-trigger"
          className={`od-agent-float-trigger${open ? ' od-agent-float-trigger--open' : ''}`}
          type="primary"
          shape="circle"
          icon={<RobotOutlined />}
          aria-label={open ? '关闭 AI 助手' : '打开 AI 助手'}
          aria-expanded={open}
          onClick={toggle}
        />
      </Tooltip>
      {open && (
        <section id="od-agent-float-panel" className="od-agent-float-panel" role="dialog" aria-modal="false" aria-label="AI 助手">
          <header className="od-agent-float-title">
            <h2>AI 助手</h2>
            <div className="od-agent-float-actions">
            <Tooltip title="打开完整助手">
              <Button type="text" size="small" icon={<ExpandOutlined />} aria-label="打开完整助手" onClick={openFullAgent} />
            </Tooltip>
              <Button
                id="od-agent-float-close"
                type="text"
                size="small"
                icon={<CloseOutlined />}
                aria-label="关闭 AI 助手对话框"
                onClick={() => setOpen(false)}
              />
            </div>
          </header>
          <div className="od-agent-float-body"><AgentConversation /></div>
        </section>
      )}
    </>
  );
}
