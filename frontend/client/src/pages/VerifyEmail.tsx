import { Button, Card, Form, Input, message } from 'antd';
import { useNavigate, useSearchParams } from 'react-router-dom';
import { authApi, publishSessionAvailable, useAuthStore } from '@shared';

export default function VerifyEmail() {
  const navigate = useNavigate();
  const [params] = useSearchParams();
  const email = params.get('email') ?? '';
  const setAuthenticated = useAuthStore((s) => s.setAuthenticated);
  const onFinish = async (v: { code: string }) => {
    try {
      const data = await authApi.verifyEmail({ email, code: v.code });
      setAuthenticated(data);
      publishSessionAvailable();
      message.success('邮箱验证成功');
      navigate('/', { replace: true });
    } catch (e) { message.error((e as Error).message); }
  };
  return (
    <div className="od-auth">
      <div className="od-brand">AnimeTracker</div>
      <Card title="验证邮箱">
        <p style={{ marginTop: 0 }}>验证码已发送至：{email || '（未提供邮箱）'}</p>
        <Form layout="vertical" onFinish={onFinish}>
          <Form.Item name="code" label="验证码" rules={[{ required: true, len: 6 }]}>
            <Input aria-label="验证码" maxLength={6} placeholder="6 位验证码" />
          </Form.Item>
          <Button type="primary" htmlType="submit" block>验证</Button>
        </Form>
      </Card>
    </div>
  );
}
