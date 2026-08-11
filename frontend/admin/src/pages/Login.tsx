import { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { App, Button, Form, Input } from 'antd';
import { ArrowRightOutlined, LockOutlined, UserOutlined } from '@ant-design/icons';
import { useAuthStore } from '../store/authStore';
import { authApi } from '../api/auth';
import ThemeToggle from '../components/ThemeToggle';

interface LoginFormValues {
  username: string;
  password: string;
}

const feedLines = [
  { tag: '启动', text: 'animetracker-admin 预览版 0.1.0', tone: '' },
  { tag: '认证', text: 'POST /api/client/auth/login -> 200 OK', tone: 'feed-ok' },
  { tag: '系统', text: '看板数据已就绪，等待操作员...', tone: '' },
  { tag: '提示', text: '请使用管理员账号登录', tone: 'feed-warn' },
];

export default function Login() {
  const navigate = useNavigate();
  const signIn = useAuthStore((s) => s.signIn);
  const { message } = App.useApp();
  const [loading, setLoading] = useState(false);

  const onFinish = async (values: LoginFormValues) => {
    setLoading(true);
    try {
      const data = await authApi.login(values);
      if (data.user.role !== 'ADMIN') {
        throw new Error('当前账号权限不足，无法进入管理控制台');
      }
      signIn(data.token, data.refreshToken, data.user);
      message.success('登录成功，正在进入控制台');
      navigate('/dashboard');
    } catch (error) {
      message.error(error instanceof Error ? error.message : '登录失败，请检查账号密码');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="login-page">
      <div className="login-theme-toggle">
        <ThemeToggle />
      </div>
      <section className="login-console">
        <div className="login-brand">
          <span className="login-brand-mark">AT</span>
          <div>
            <h1>ANIMETRACKER</h1>
            <div className="login-brand-sub">管理终端</div>
          </div>
        </div>
        <div className="login-feed">
          {feedLines.map((line, index) => (
            <div className="feed-line" key={line.tag}>
              <span className="feed-tag">[{line.tag}]</span>
              <span className={line.tone}>{line.text}</span>
              {index === feedLines.length - 1 && <span className="login-cursor" />}
            </div>
          ))}
        </div>
        <div className="login-meta">
          <span>构建 0.1.0 / 预览版</span>
          <span>节点 CN-SH-01</span>
        </div>
      </section>
      <section className="login-panel-wrap">
        <div className="login-frame">
          <h2 className="login-title">控制台登录</h2>
          <div className="login-subtitle">需要管理员授权</div>
          <Form<LoginFormValues> layout="vertical" requiredMark={false} onFinish={onFinish} size="large">
            <Form.Item name="username" label="账号" rules={[{ required: true, message: '请输入账号' }]}>
              <Input prefix={<UserOutlined />} placeholder="请输入用户名" autoComplete="username" />
            </Form.Item>
            <Form.Item name="password" label="密码" rules={[{ required: true, message: '请输入密码' }]}>
              <Input.Password
                prefix={<LockOutlined />}
                placeholder="请输入密码"
                autoComplete="current-password"
              />
            </Form.Item>
            <Button type="primary" htmlType="submit" block loading={loading}>
              进入控制台 <ArrowRightOutlined />
            </Button>
          </Form>
          <div className="login-demo">
            <span>生产环境</span>
            <span className="demo-state">
              <span className="status-dot running" />
              接口在线
            </span>
          </div>
        </div>
      </section>
    </div>
  );
}
