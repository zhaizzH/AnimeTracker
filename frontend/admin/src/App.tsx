import { Navigate, Outlet, Route, Routes } from 'react-router-dom';
import AdminLayout from './layouts/AdminLayout';
import AgentConfig from './pages/AgentConfig';
import Dashboard from './pages/Dashboard';
import ImportTasks from './pages/ImportTasks';
import Login from './pages/Login';
import Logs from './pages/Logs';
import Subjects from './pages/Subjects';
import Users from './pages/Users';
import { useAuthStore } from './store/authStore';

function ProtectedLayout() {
  const token = useAuthStore((s) => s.token);
  if (!token) {
    return <Navigate to="/login" replace />;
  }
  return (
    <AdminLayout>
      <Outlet />
    </AdminLayout>
  );
}

export default function App() {
  return (
    <Routes>
      <Route path="/login" element={<Login />} />
      <Route element={<ProtectedLayout />}>
        <Route path="/dashboard" element={<Dashboard />} />
        <Route path="/subjects" element={<Subjects />} />
        <Route path="/users" element={<Users />} />
        <Route path="/import" element={<ImportTasks />} />
        <Route path="/logs" element={<Logs />} />
        <Route path="/agent" element={<AgentConfig />} />
      </Route>
      <Route path="*" element={<Navigate to="/dashboard" replace />} />
    </Routes>
  );
}
