import { lazy, Suspense, useEffect } from 'react';
import { Routes, Route } from 'react-router-dom';
import AppLayout from './components/Layout';
import ProtectedRoute from './components/ProtectedRoute';
import { useAuthStore } from './store/authStore';

// 懒加载页面
const Home = lazy(() => import('./pages/Home'));
const AnimeIndex = lazy(() => import('./pages/AnimeIndex'));
const SubjectDetail = lazy(() => import('./pages/SubjectDetail'));
const Schedule = lazy(() => import('./pages/Schedule'));
const MyCollections = lazy(() => import('./pages/MyCollections'));
const Agent = lazy(() => import('./pages/Agent'));
const Login = lazy(() => import('./pages/Login'));
const Register = lazy(() => import('./pages/Register'));
const VerifyEmail = lazy(() => import('./pages/VerifyEmail'));
const ForgotPassword = lazy(() => import('./pages/ForgotPassword'));
const ResetPassword = lazy(() => import('./pages/ResetPassword'));
const Profile = lazy(() => import('./pages/Profile'));

// 简易 Loading 组件
function PageLoading() {
  return <div className="paper-loading">加载中...</div>;
}

export default function App() {
  const { hydrate } = useAuthStore();

  useEffect(() => {
    hydrate();
  }, [hydrate]);

  return (
    <Suspense fallback={<PageLoading />}>
      <Routes>
        {/* 认证页面（无布局） */}
        <Route path="/login" element={<Login />} />
        <Route path="/register" element={<Register />} />
        <Route path="/verify-email" element={<VerifyEmail />} />
        <Route path="/forgot-password" element={<ForgotPassword />} />
        <Route path="/reset-password" element={<ResetPassword />} />

        {/* 主布局页面 */}
        <Route element={<AppLayout />}>
          <Route path="/" element={<Home />} />
          <Route path="/anime" element={<AnimeIndex />} />
          <Route path="/subject/:id" element={<SubjectDetail />} />
          <Route path="/schedule" element={<Schedule />} />

          {/* 需登录 */}
          <Route path="/my-collections" element={<ProtectedRoute><MyCollections /></ProtectedRoute>} />
          <Route path="/agent" element={<ProtectedRoute><Agent /></ProtectedRoute>} />
          <Route path="/profile" element={<ProtectedRoute><Profile /></ProtectedRoute>} />
        </Route>
      </Routes>
    </Suspense>
  );
}
