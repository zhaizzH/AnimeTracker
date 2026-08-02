import { useState } from 'react';
import { Form, Input, Button, message } from 'antd';
import { Link, useNavigate, useSearchParams } from 'react-router-dom';
import { authApi } from '@/api/auth';
import AuthShell from '@/components/AuthShell';

export default function ResetPassword() {
  const [searchParams] = useSearchParams();
  const email = searchParams.get('email') || '';
  const [loading, setLoading] = useState(false);
  const navigate = useNavigate();

  const onFinish = async (values: { code: string; newPassword: string }) => {
    setLoading(true);
    try {
      await authApi.resetPassword({ email, code: values.code, newPassword: values.newPassword });
      message.success('密码重置成功');
      navigate('/login');
    } catch (err: any) {
      message.error(err.message || '重置失败');
    } finally {
      setLoading(false);
    }
  };

  return (
    <AuthShell title="重置密码" en="RESET PASSWORD" subtitle={`邮箱: ${email}`}>
      <Form onFinish={onFinish} layout="vertical">
        <Form.Item name="code" label="验证码" rules={[{ required: true, len: 6 }]}>
          <Input placeholder="6位验证码" maxLength={6} />
        </Form.Item>
        <Form.Item name="newPassword" label="新密码" rules={[{ required: true, min: 6, max: 128 }]}>
          <Input.Password placeholder="新密码（至少6位）" />
        </Form.Item>
        <Form.Item>
          <Button type="primary" htmlType="submit" loading={loading} block>重置密码</Button>
        </Form.Item>
        <div className="auth-sheet-foot">
          <Link to="/login">返回登录</Link>
        </div>
      </Form>
    </AuthShell>
  );
}
