import { useEffect, useState } from 'react';
import { Form, Input, Button, message } from 'antd';
import { useNavigate, useSearchParams } from 'react-router-dom';
import { authApi } from '@/api/auth';
import { useAuthStore } from '@/store/authStore';
import AuthShell from '@/components/AuthShell';

const RESEND_INTERVAL = 60;

export default function VerifyEmail() {
  const [searchParams] = useSearchParams();
  const email = searchParams.get('email') || '';
  const [loading, setLoading] = useState(false);
  const [resending, setResending] = useState(false);
  const [countdown, setCountdown] = useState(0);
  const navigate = useNavigate();
  const login = useAuthStore(s => s.login);

  useEffect(() => {
    if (countdown <= 0) return;
    const timer = setInterval(() => setCountdown((c) => c - 1), 1000);
    return () => clearInterval(timer);
  }, [countdown]);

  const onFinish = async (values: { code: string }) => {
    setLoading(true);
    try {
      const result = await authApi.verifyEmail({ email, code: values.code }) as any;
      login(result.token, result.refreshToken, result.user);
      message.success('邮箱验证成功');
      navigate('/');
    } catch (err: any) {
      message.error(err.message || '验证失败');
    } finally {
      setLoading(false);
    }
  };

  const resendCode = async () => {
    setCountdown(RESEND_INTERVAL);
    setResending(true);
    try {
      await authApi.resendCode({ email });
      message.success('验证码已重新发送');
    } catch (err: any) {
      message.error(err.message || '发送失败');
    } finally {
      setResending(false);
    }
  };

  return (
    <AuthShell title="验证邮箱" en="VERIFY EMAIL" subtitle={`验证码已发送至 ${email}`}>
      <Form onFinish={onFinish} layout="vertical">
        <Form.Item name="code" label="6位验证码" rules={[{ required: true, len: 6 }]}>
          <Input.OTP length={6} />
        </Form.Item>
        <Form.Item>
          <Button type="primary" htmlType="submit" loading={loading} block>验证</Button>
        </Form.Item>
        <Button type="link" onClick={resendCode} loading={resending} disabled={countdown > 0} block>
          {countdown > 0 ? `重新发送验证码（${countdown}s）` : '重新发送验证码'}
        </Button>
      </Form>
    </AuthShell>
  );
}
