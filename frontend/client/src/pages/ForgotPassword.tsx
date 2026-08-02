import { useState } from 'react';
import { Form, Input, Button, message } from 'antd';
import { Link, useNavigate } from 'react-router-dom';
import { authApi } from '@/api/auth';
import AuthShell from '@/components/AuthShell';

export default function ForgotPassword() {
  const [loading, setLoading] = useState(false);
  const navigate = useNavigate();

  const onFinish = async (values: { email: string }) => {
    setLoading(true);
    try {
      await authApi.forgotPassword(values);
      message.success('重置验证码已发送到邮箱');
      navigate(`/reset-password?email=${encodeURIComponent(values.email)}`);
    } catch (err: any) {
      message.error(err.message || '发送失败');
    } finally {
      setLoading(false);
    }
  };

  return (
    <AuthShell title="找回密码" en="FORGOT PASSWORD" subtitle="验证码会寄到你登记的邮箱">
      <Form onFinish={onFinish} layout="vertical">
        <Form.Item name="email" label="注册邮箱" rules={[{ required: true, type: 'email' }]}>
          <Input placeholder="请输入注册时使用的邮箱" />
        </Form.Item>
        <Form.Item>
          <Button type="primary" htmlType="submit" loading={loading} block>发送重置验证码</Button>
        </Form.Item>
        <div className="auth-sheet-foot">
          <Link to="/login">返回登录</Link>
        </div>
      </Form>
    </AuthShell>
  );
}
