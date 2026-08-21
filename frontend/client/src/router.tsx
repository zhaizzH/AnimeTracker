import { createBrowserRouter, Navigate } from 'react-router-dom';
import { lazy, Suspense } from 'react';
import { Spin } from 'antd';
import { ClientLayout } from './layouts/ClientLayout';
import { RequireAuth, PublicOnly } from './guards';

// fallback 与页面同宽居中，避免 chunk 加载时从无约束宽 Spinner 跳到 1100 窄容器
const withLoading = (el: React.ReactNode) => <Suspense fallback={<div style={{ maxWidth: 1100, margin: '0 auto', padding: 24 }}><Spin style={{ display: 'block', margin: '40px auto' }} /></div>}>{el}</Suspense>;
const Home = lazy(() => import('./pages/Home'));
const AnimeIndex = lazy(() => import('./pages/AnimeIndex'));
const Schedule = lazy(() => import('./pages/Schedule'));
const SubjectDetail = lazy(() => import('./pages/SubjectDetail'));
const MyCollections = lazy(() => import('./pages/MyCollections'));
const Agent = lazy(() => import('./pages/Agent'));
const Profile = lazy(() => import('./pages/Profile'));
const Login = lazy(() => import('./pages/Login'));
const Register = lazy(() => import('./pages/Register'));
const VerifyEmail = lazy(() => import('./pages/VerifyEmail'));
const ForgotPassword = lazy(() => import('./pages/ForgotPassword'));
const ResetPassword = lazy(() => import('./pages/ResetPassword'));

export const router = createBrowserRouter([
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
      { path: 'login', element: <PublicOnly>{withLoading(<Login />)}</PublicOnly> },
      { path: 'register', element: <PublicOnly>{withLoading(<Register />)}</PublicOnly> },
      { path: 'verify-email', element: <PublicOnly>{withLoading(<VerifyEmail />)}</PublicOnly> },
      { path: 'forgot-password', element: <PublicOnly>{withLoading(<ForgotPassword />)}</PublicOnly> },
      { path: 'reset-password', element: <PublicOnly>{withLoading(<ResetPassword />)}</PublicOnly> },
      { path: '*', element: <Navigate to="/" replace /> },
    ],
  },
]);
