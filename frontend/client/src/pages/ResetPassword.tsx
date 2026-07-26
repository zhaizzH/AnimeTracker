import { useState } from 'react';
import { Form, Input, Button, Card, Typography, message } from 'antd';
import { Link, useNavigate, useSearchParams } from 'react-router-dom';
import { authApi } from '@/api/auth';

const { Title } = Typography;

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
    <div style={{ display: 'flex', justifyContent: 'center', alignItems: 'center', minHeight: '100vh', background: '#f5f5f5' }}>
      <Card style={{ width: 400 }}>
        <Title level={3} style={{ textAlign: 'center' }}>重置密码</Title>
        <Typography.Text>邮箱: <strong>{email}</strong></Typography.Text>
        <Form onFinish={onFinish} layout="vertical" style={{ marginTop: 16 }}>
          <Form.Item name="code" label="验证码" rules={[{ required: true, len: 6 }]}>
            <Input placeholder="6位验证码" maxLength={6} />
          </Form.Item>
          <Form.Item name="newPassword" label="新密码" rules={[{ required: true, min: 6, max: 128 }]}>
            <Input.Password placeholder="新密码（至少6位）" />
          </Form.Item>
          <Form.Item>
            <Button type="primary" htmlType="submit" loading={loading} block>重置密码</Button>
          </Form.Item>
          <div style={{ textAlign: 'center' }}>
            <Link to="/login">返回登录</Link>
          </div>
        </Form>
      </Card>
    </div>
  );
}
