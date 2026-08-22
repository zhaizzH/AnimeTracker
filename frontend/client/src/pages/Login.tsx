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
    <div className="od-auth">
      <div className="od-brand">AnimeTracker</div>
      <Card title="登录">
        <Form layout="vertical" onFinish={onFinish}>
          <Form.Item name="username" label="用户名/邮箱" rules={[{ required: true }]}>
            <Input aria-label="用户名/邮箱" autoComplete="username" spellCheck={false} />
          </Form.Item>
          <Form.Item name="password" label="密码" rules={[{ required: true, min: 6 }]}>
            <Input.Password aria-label="密码" autoComplete="current-password" />
          </Form.Item>
          <Button type="primary" htmlType="submit" block>登录</Button>
        </Form>
        <div className="od-auth-foot">
          <Link to="/register">没有账号？去注册</Link>
          <Link to="/forgot-password">忘记密码</Link>
        </div>
      </Card>
    </div>
  );
}
