import { Layout } from 'antd';
import { Outlet } from 'react-router-dom';
import AppHeader from './Header';

const { Content } = Layout;

export default function AppLayout() {
  return (
    <Layout style={{ minHeight: '100vh' }}>
      <AppHeader />
      <Content className="page-shell">
        <Outlet />
      </Content>
    </Layout>
  );
}
