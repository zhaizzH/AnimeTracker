import { useState } from 'react';
import { Form, Input, Button, message } from 'antd';
import { UserOutlined, LockOutlined } from '@ant-design/icons';
import { Link, useNavigate } from 'react-router-dom';
import { authApi } from '@/api/auth';
import { useAuthStore } from '@/store/authStore';
import AuthShell from '@/components/AuthShell';

export default function Login() {
  const [loading, setLoading] = useState(false);
  const navigate = useNavigate();
  const login = useAuthStore(s => s.login);

  const onFinish = async (values: { username: string; password: string }) => {
    setLoading(true);
    try {
      const result = await authApi.login(values) as any;
      login(result.token, result.refreshToken, result.user);
      message.success('登录成功');
      navigate('/');
    } catch (err: any) {
      message.error(err.message || '登录失败');
    } finally {
      setLoading(false);
    }
  };

  return (
    <AuthShell title="登录" en="SIGN IN" subtitle="记下你正在追的每一部">
      <Form onFinish={onFinish} layout="vertical">
        <Form.Item name="username" rules={[{ required: true, message: '请输入用户名' }]}>
          <Input prefix={<UserOutlined />} placeholder="用户名" />
        </Form.Item>
        <Form.Item name="password" rules={[{ required: true, message: '请输入密码' }]}>
          <Input.Password prefix={<LockOutlined />} placeholder="密码" />
        </Form.Item>
        <Form.Item>
          <Button type="primary" htmlType="submit" loading={loading} block>登录</Button>
        </Form.Item>
        <div className="auth-sheet-foot">
          <Link to="/register">没有账号？去注册</Link>
          <span style={{ margin: '0 8px' }}>|</span>
          <Link to="/forgot-password">忘记密码</Link>
        </div>
      </Form>
    </AuthShell>
  );
}
