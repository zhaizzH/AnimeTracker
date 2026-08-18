import { Button, Card, Form, Input, message } from 'antd';
import { Link, useLocation, useNavigate } from 'react-router-dom';
import { authApi, useAuthStore } from '@shared';

export default function Login() {
  const navigate = useNavigate();
  const location = useLocation();
  const setLogin = useAuthStore((s) => s.setLogin);
  const onFinish = async (v: { username: string; password: string }) => {
    try {
      const data = await authApi.login(v);
      setLogin(data);
      const from = (location.state as { from?: string } | null)?.from ?? '/';
      navigate(from, { replace: true });
    } catch (e) { message.error((e as Error).message); }
  };
  return (
    <div style={{ maxWidth: 360, margin: '60px auto' }}>
      <Card title="登录 AnimeTracker">
        <Form layout="vertical" onFinish={onFinish}>
          <Form.Item name="username" label="用户名/邮箱" rules={[{ required: true }]}>
            <Input aria-label="用户名/邮箱" />
          </Form.Item>
          <Form.Item name="password" label="密码" rules={[{ required: true, min: 6 }]}>
            <Input.Password aria-label="密码" />
          </Form.Item>
          <Button type="primary" htmlType="submit" block>登录</Button>
        </Form>
        <div style={{ marginTop: 12, display: 'flex', justifyContent: 'space-between' }}>
          <Link to="/register">没有账号？去注册</Link>
          <Link to="/forgot-password">忘记密码</Link>
        </div>
      </Card>
    </div>
  );
}
