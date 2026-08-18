import { Button, Card, Form, Input, message } from 'antd';
import { Link, useNavigate } from 'react-router-dom';
import { authApi } from '@shared';

type RegisterForm = { username: string; email: string; password: string; confirm: string };

export default function Register() {
  const navigate = useNavigate();
  const onFinish = async (v: RegisterForm) => {
    try {
      await authApi.register({ username: v.username, email: v.email, password: v.password });
      message.success('注册成功，请查收验证码邮件');
      navigate('/verify-email?email=' + encodeURIComponent(v.email));
    } catch (e) { message.error((e as Error).message); }
  };
  return (
    <div style={{ maxWidth: 360, margin: '60px auto' }}>
      <Card title="注册 AnimeTracker">
        <Form layout="vertical" onFinish={onFinish}>
          <Form.Item name="username" label="用户名" rules={[{ required: true }]}>
            <Input aria-label="用户名" />
          </Form.Item>
          <Form.Item name="email" label="邮箱" rules={[{ required: true, type: 'email' }]}>
            <Input aria-label="邮箱" />
          </Form.Item>
          <Form.Item name="password" label="密码" rules={[{ required: true, min: 6 }]}>
            <Input.Password aria-label="密码" />
          </Form.Item>
          <Form.Item
            name="confirm"
            label="确认密码"
            dependencies={['password']}
            rules={[
              { required: true },
              ({ getFieldValue }) => ({
                validator: (_, value) =>
                  !value || getFieldValue('password') === value
                    ? Promise.resolve()
                    : Promise.reject(new Error('两次输入的密码不一致')),
              }),
            ]}
          >
            <Input.Password aria-label="确认密码" />
          </Form.Item>
          <Button type="primary" htmlType="submit" block>注册</Button>
        </Form>
        <div style={{ marginTop: 12, textAlign: 'center' }}>
          <Link to="/login">已有账号？去登录</Link>
        </div>
      </Card>
    </div>
  );
}
