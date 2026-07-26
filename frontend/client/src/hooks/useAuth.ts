import { useNavigate } from 'react-router-dom';
import { message } from 'antd';
import { authApi } from '@/api/auth';
import { useAuthStore } from '@/store/authStore';
import type { LoginDTO, RegisterDTO, VerifyEmailDTO } from '@/types';

export function useAuth() {
  const navigate = useNavigate();
  const { login: storeLogin, logout: storeLogout } = useAuthStore();

  const login = async (data: LoginDTO) => {
    try {
      const result = await authApi.login(data) as any;
      storeLogin(result.token, result.refreshToken, result.user);
      message.success('登录成功');
      navigate('/');
    } catch (error: any) {
      message.error(error.message || '登录失败');
      throw error;
    }
  };

  const register = async (data: RegisterDTO) => {
    await authApi.register(data);
    message.success('注册成功，请查收验证邮件');
    navigate(`/verify-email?email=${encodeURIComponent(data.email)}`);
  };

  const verifyEmail = async (data: VerifyEmailDTO) => {
    const result = await authApi.verifyEmail(data) as any;
    storeLogin(result.token, result.refreshToken, result.user);
    message.success('邮箱验证成功');
    navigate('/');
  };

  const logout = async () => {
    try { await authApi.logout(); } catch { /* ignore */ }
    storeLogout();
    navigate('/login');
  };

  return { login, register, verifyEmail, logout };
}
