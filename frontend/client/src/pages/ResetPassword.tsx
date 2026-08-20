import { Button, Card, Form, Input, message } from 'antd';
import { useNavigate, useSearchParams } from 'react-router-dom';
import { authApi } from '@shared';

type ResetForm = { email: string; code: string; newPassword: string; confirm: string };

export default function ResetPassword() {
  const navigate = useNavigate();
  const [params] = useSearchParams();
  const email = params.get('email') ?? '';
  const onFinish = async (v: ResetForm) => {
    try {
      await authApi.resetPassword({ email: v.email, code: v.code, newPassword: v.newPassword });
      message.success('密码已重置，请重新登录');
      navigate('/login');
    } catch (e) { message.error((e as Error).message); }
  };
  return (
    <div className="od-auth">
      <div className="od-brand">AnimeTracker</div>
      <Card title="重置密码">
        <Form layout="vertical" onFinish={onFinish} initialValues={{ email }}>
          <Form.Item name="email" label="邮箱" rules={[{ required: true, type: 'email' }]}>
            <Input aria-label="邮箱" />
          </Form.Item>
          <Form.Item name="code" label="验证码" rules={[{ required: true, len: 6 }]}>
            <Input aria-label="验证码" maxLength={6} placeholder="6 位验证码" />
          </Form.Item>
          <Form.Item name="newPassword" label="新密码" rules={[{ required: true, min: 6 }]}>
            <Input.Password aria-label="新密码" />
          </Form.Item>
          <Form.Item
            name="confirm"
            label="确认新密码"
            dependencies={['newPassword']}
            rules={[
              { required: true },
              ({ getFieldValue }) => ({
                validator: (_, value) =>
                  !value || getFieldValue('newPassword') === value
                    ? Promise.resolve()
                    : Promise.reject(new Error('两次输入的密码不一致')),
              }),
            ]}
          >
            <Input.Password aria-label="确认新密码" />
          </Form.Item>
          <Button type="primary" htmlType="submit" block>重置密码</Button>
        </Form>
      </Card>
    </div>
  );
}
