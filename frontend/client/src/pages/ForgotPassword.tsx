import { Button, Card, Form, Input, message } from 'antd';
import { Link, useNavigate } from 'react-router-dom';
import { authApi } from '@shared';

export default function ForgotPassword() {
  const navigate = useNavigate();
  const onFinish = async (v: { email: string }) => {
    try {
      await authApi.forgotPassword({ email: v.email });
      message.success('验证码已发送（邮箱不存在时也提示成功）');
      navigate('/reset-password?email=' + encodeURIComponent(v.email));
    } catch (e) { message.error((e as Error).message); }
  };
  return (
    <div style={{ maxWidth: 360, margin: '60px auto' }}>
      <Card title="找回密码">
        <Form layout="vertical" onFinish={onFinish}>
          <Form.Item name="email" label="邮箱" rules={[{ required: true, type: 'email' }]}>
            <Input aria-label="邮箱" />
          </Form.Item>
          <Button type="primary" htmlType="submit" block>发送验证码</Button>
        </Form>
        <div style={{ marginTop: 12, textAlign: 'center' }}>
          <Link to="/login">回到登录</Link>
        </div>
      </Card>
    </div>
  );
}
