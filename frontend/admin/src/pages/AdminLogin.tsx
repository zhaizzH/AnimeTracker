import { Button, Card, Form, Input, message } from 'antd';
import { useNavigate } from 'react-router-dom';
import { authApi, useAuthStore } from '@shared';

export default function AdminLogin() {
  const navigate = useNavigate();
  const setLogin = useAuthStore((s) => s.setLogin);
  const logout = useAuthStore((s) => s.logout);
  const onFinish = async (v: { username: string; password: string }) => {
    try {
      const data = await authApi.login(v);
      if (data.user.role !== 'ADMIN') { message.error('该账号无管理权限'); logout(); return; }
      setLogin(data); navigate('/admin/dashboard', { replace: true });
    } catch (e) { message.error((e as Error).message); }
  };
  return (
    <div style={{ maxWidth: 360, margin: '80px auto' }}>
      <Card title="AnimeTracker 管理后台">
        <Form layout="vertical" onFinish={onFinish}>
          <Form.Item name="username" label="用户名/邮箱" rules={[{ required: true }]}><Input aria-label="用户名/邮箱" /></Form.Item>
          <Form.Item name="password" label="密码" rules={[{ required: true }]}><Input.Password aria-label="密码" /></Form.Item>
          <Button type="primary" htmlType="submit" block>登录</Button>
        </Form>
      </Card>
    </div>
  );
}
