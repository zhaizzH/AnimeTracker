import { createBrowserRouter, Navigate } from 'react-router-dom';
import { lazy, Suspense } from 'react';
import { Skeleton } from '@/components/ui/skeleton';
import { ClientLayout } from './layouts/ClientLayout';
import { RequireAuth, PublicOnly } from './guards';

// fallback 与页面同宽居中，避免 chunk 加载时从无约束宽 Spinner 跳到 1100 窄容器。
const withLoading = (el: React.ReactNode) => (
  <Suspense fallback={<div className="mx-auto w-full max-w-[1100px] p-6"><Skeleton className="mx-auto my-10 h-8 w-24" aria-hidden /></div>}>
    {el}
  </Suspense>
);

const Home = lazy(() => import('./pages/Home'));
const AnimeIndex = lazy(() => import('./pages/AnimeIndex'));
const Schedule = lazy(() => import('./pages/Schedule'));
const SubjectDetail = lazy(() => import('./pages/SubjectDetail'));
const MyCollections = lazy(() => import('./pages/MyCollections'));
const Agent = lazy(() => import('./pages/Agent'));
const Profile = lazy(() => import('./pages/Profile'));
const Login = lazy(() => import('./components/auth/auth-page').then((m) => ({ default: m.AuthPage })));
const VerifyEmail = lazy(() => import('./pages/VerifyEmail'));
const ForgotPassword = lazy(() => import('./pages/ForgotPassword'));
const ResetPassword = lazy(() => import('./pages/ResetPassword'));
const NotFound = lazy(() => import('./pages/NotFound'));

export const router = createBrowserRouter([
  // 认证页面独立于 AppShell：登录/注册等页面独占整屏，不渲染侧栏与顶栏。
  { path: '/login', element: <PublicOnly>{withLoading(<Login />)}</PublicOnly> },
  // 注册已并入登录面板（同一面板内切换），保留旧路径并重定向。
  { path: '/register', element: <PublicOnly><Navigate to="/login" replace /></PublicOnly> },
  { path: '/verify-email', element: <PublicOnly>{withLoading(<VerifyEmail />)}</PublicOnly> },
  { path: '/forgot-password', element: <PublicOnly>{withLoading(<ForgotPassword />)}</PublicOnly> },
  { path: '/reset-password', element: <PublicOnly>{withLoading(<ResetPassword />)}</PublicOnly> },
  // 未知路径渲染 404 页；放在 ClientLayout 外，未登录访问也不被重定向。
  { path: '*', element: withLoading(<NotFound />) },
  {
    path: '/',
    element: <ClientLayout />,
    children: [
      { index: true, element: withLoading(<Home />) },
      { path: 'anime', element: withLoading(<AnimeIndex />) },
      { path: 'schedule', element: withLoading(<Schedule />) },
      { path: 'subject/:id', element: withLoading(<SubjectDetail />) },
      { path: 'my-collections', element: <RequireAuth>{withLoading(<MyCollections />)}</RequireAuth> },
      { path: 'agent', element: <RequireAuth>{withLoading(<Agent />)}</RequireAuth> },
      { path: 'profile', element: <RequireAuth>{withLoading(<Profile />)}</RequireAuth> },
    ],
  },
]);
