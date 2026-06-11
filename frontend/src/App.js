import React, { createContext, useContext, useState, useEffect, useCallback } from 'react';
import { HashRouter, Routes, Route, Navigate, useLocation } from 'react-router-dom';
import axios from 'axios';
import { Toaster, toast } from 'sonner';

// Pages
import Login from './pages/Login';
import Register from './pages/Register';
import GateLogin from './pages/GateLogin';
import Dashboard from './pages/Dashboard';
import POS from './pages/POS';
import Products from './pages/Products';
import Stock from './pages/Stock';
import Users from './pages/Users';
import Branches from './pages/Branches';
import Reports from './pages/Reports';
import Settings from './pages/Settings';
import AuditLogs from './pages/AuditLogs';
import SuperAdmin from './pages/SuperAdmin';
import Debts from './pages/Debts';

// Layout
import MainLayout from './components/MainLayout';

// Remove Emergent badge
const removeEmergentBadge = () => {
  const badge = document.getElementById('emergent-badge');
  if (badge) badge.remove();
  document.querySelectorAll('a[href*="emergent"]').forEach(el => el.remove());
  document.querySelectorAll('body > a[style*="position: fixed"]').forEach(el => {
    if (el.textContent?.includes('Emergent') || el.innerHTML?.includes('emergent')) {
      el.remove();
    }
  });
};

if (typeof window !== 'undefined') {
  removeEmergentBadge();
  setTimeout(removeEmergentBadge, 100);
  setTimeout(removeEmergentBadge, 500);
  setTimeout(removeEmergentBadge, 1000);
  setTimeout(removeEmergentBadge, 2000);
}

// Check if hostname is a real production tenant subdomain (e.g., firma.datapos.pro)
const isProductionTenantHost = () => {
  const hostname = window.location.hostname;
  return /^[a-z0-9-]+\.datapos\.pro$/i.test(hostname);
};

// Update page title based on tenant/user (subdomain only on production hosts)
const updatePageTitle = (userData) => {
  if (isProductionTenantHost()) {
    const subdomain = window.location.hostname.split('.')[0];
    const companyName = subdomain.charAt(0).toUpperCase() + subdomain.slice(1);
    document.title = `DataPOS - ${companyName}`;
  } else if (userData?.tenant?.company_name) {
    document.title = `DataPOS - ${userData.tenant.company_name}`;
  } else if (userData?.company_name) {
    document.title = `DataPOS - ${userData.company_name}`;
  } else if (userData?.role === 'super_admin') {
    document.title = 'DataPOS - Admin';
  } else {
    document.title = 'DataPOS';
  }
};

if (typeof window !== 'undefined') {
  if (isProductionTenantHost()) {
    const subdomain = window.location.hostname.split('.')[0];
    const companyName = subdomain.charAt(0).toUpperCase() + subdomain.slice(1);
    document.title = `DataPOS - ${companyName}`;
  } else {
    document.title = 'DataPOS';
  }
}
// Backend URL
const BACKEND_URL = process.env.REACT_APP_BACKEND_URL || 'https://www.datapos.pro';
const API = `${BACKEND_URL}/api`;

// Get subdomain from current URL (only for production tenant hosts)
const getSubdomain = () => {
  const hostname = window.location.hostname;
  if (!/^[a-z0-9-]+\.datapos\.pro$/i.test(hostname)) return null;
  const parts = hostname.split('.');
  if (parts[0] === 'www' || parts[0] === 'app') return null;
  return parts[0].toLowerCase();
};

// Contexts
const AuthContext = createContext(null);
const TenantContext = createContext(null);

export const useTenant = () => useContext(TenantContext);

export const useAuth = () => {
  const context = useContext(AuthContext);
  if (!context) throw new Error('useAuth must be used within AuthProvider');
  return context;
};

// API instance
export const api = axios.create({
  baseURL: API,
  headers: { 'Content-Type': 'application/json' }
});

api.interceptors.request.use((config) => {
  const token = localStorage.getItem('t3next_token');
  if (token) {
    config.headers.Authorization = `Bearer ${token}`;
  }
  return config;
});

api.interceptors.response.use(
  (response) => response,
  (error) => {
    if (error.response?.status === 401) {
      const token = localStorage.getItem('t3next_token');
      if (token) {
        localStorage.removeItem('t3next_token');
        localStorage.removeItem('t3next_user');
        window.location.href = '/#/login';
      }
    }
    return Promise.reject(error);
  }
);

// Tenant Provider
const TenantProvider = ({ children }) => {
  const [tenant, setTenant] = useState(null);
  const [tenantLoading, setTenantLoading] = useState(false);

  useEffect(() => {
    const subdomain = getSubdomain();
    if (!subdomain) return;

    setTenantLoading(true);
    const fetchTenant = async () => {
      try {
        const response = await axios.get(`${API}/tenants/by-subdomain/${subdomain}`);
        setTenant(response.data);
        document.title = `${response.data.company_name || response.data.name} - POS`;
        localStorage.setItem('tenant_context', JSON.stringify(response.data));
      } catch (error) {
        console.error('Failed to fetch tenant:', error);
      } finally {
        setTenantLoading(false);
      }
    };
    fetchTenant();
  }, []);

  const value = { tenant, tenantLoading, subdomain: getSubdomain() };
  return <TenantContext.Provider value={value}>{children}</TenantContext.Provider>;
};

// Auth Provider
const AuthProvider = ({ children }) => {
  const [user, setUser] = useState(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const isNewSession = sessionStorage.getItem('ipos_session_active') !== 'true';
    if (isNewSession) {
      localStorage.removeItem('t3next_token');
      localStorage.removeItem('t3next_user');
      sessionStorage.setItem('ipos_session_active', 'true');
      setLoading(false);
      return;
    }
    const savedUser = localStorage.getItem('t3next_user');
    const savedToken = localStorage.getItem('t3next_token');
    if (savedUser && savedToken) {
      setUser(JSON.parse(savedUser));
    }
    setLoading(false);
  }, []);

  useEffect(() => {
    const handleVisibilityChange = () => {
      if (document.visibilityState === 'hidden') {
        sessionStorage.removeItem('ipos_session_active');
      }
    };
    const handleBeforeUnload = () => {
      sessionStorage.removeItem('ipos_session_active');
    };
    document.addEventListener('visibilitychange', handleVisibilityChange);
    window.addEventListener('beforeunload', handleBeforeUnload);
    return () => {
      document.removeEventListener('visibilitychange', handleVisibilityChange);
      window.removeEventListener('beforeunload', handleBeforeUnload);
    };
  }, []);

  const login = async (username, password) => {
    try {
      const response = await api.post('/auth/login', { username, password });
      const { access_token, user: userData } = response.data;
      localStorage.setItem('t3next_token', access_token);
      localStorage.setItem('t3next_user', JSON.stringify(userData));
      sessionStorage.setItem('ipos_session_active', 'true');
      setUser(userData);
      updatePageTitle(userData);
      toast.success('MirÃ«sevini!');
      return { success: true };
    } catch (error) {
      const message = error.response?.data?.detail || 'Gabim gjatÃ« kyÃ§jes';
      const status = error.response?.status || 500;
      if (status !== 402) {
        toast.error(message);
      }
      return { success: false, error: message, status };
    }
  };

  const logout = useCallback(() => {
    localStorage.removeItem('t3next_token');
    localStorage.removeItem('t3next_user');
    sessionStorage.removeItem('ipos_session_active');
    setUser(null);
    toast.info('U Ã§kyÃ§Ã«t me sukses');
  }, []);

  const value = { user, login, logout, loading, isAuthenticated: !!user };
  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>;
};

// Protected Route
const ProtectedRoute = ({ children, allowedRoles }) => {
  const { user, loading, isAuthenticated } = useAuth();
  const location = useLocation();

  if (loading) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-gray-50">
        <div className="spinner" />
      </div>
    );
  }

  if (!isAuthenticated) {
    return <Navigate to="/login" state={{ from: location }} replace />;
  }

  if (allowedRoles && !allowedRoles.includes(user.role)) {
    return <Navigate to={user.role === 'super_admin' ? "/app/super-admin" : "/dashboard"} replace />;
  }

  return children;
};

// App Routes
const AppRoutes = () => {
  const { isAuthenticated, loading, user } = useAuth();

  if (loading) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-gray-50">
        <div className="spinner" />
      </div>
    );
  }

  return (
    <Routes>
      <Route path="/" element={isAuthenticated ? <Navigate to={user?.role === 'cashier' ? '/pos' : user?.role === 'super_admin' ? '/app/super-admin' : '/dashboard'} /> : <Navigate to="/login" />} />
      <Route path="/register" element={isAuthenticated ? <Navigate to={user?.role === 'cashier' ? '/pos' : user?.role === 'super_admin' ? '/app/super-admin' : '/dashboard'} /> : <Register />} />
      <Route path="/gate" element={isAuthenticated ? <Navigate to="/login" /> : <GateLogin />} />
      <Route path="/login" element={
        isAuthenticated ? (
          user?.role === 'cashier' ? <Navigate to="/pos" /> : user?.role === 'super_admin' ? <Navigate to="/app/super-admin" /> : <Navigate to="/dashboard" />
        ) : (
          <Login />
        )
      } />

      <Route path="/pos" element={
        <ProtectedRoute>
          <POS />
        </ProtectedRoute>
      } />

      <Route path="/app" element={<ProtectedRoute><MainLayout /></ProtectedRoute>}>
        <Route index element={<Navigate to={user?.role === 'super_admin' ? "/app/super-admin" : "/app/dashboard"} replace />} />
        <Route path="dashboard" element={<Dashboard />} />
        <Route path="products" element={
          <ProtectedRoute allowedRoles={['admin', 'manager']}>
            <Products />
          </ProtectedRoute>
        } />
        <Route path="stock" element={
          <ProtectedRoute allowedRoles={['admin', 'manager']}>
            <Stock />
          </ProtectedRoute>
        } />
        <Route path="users" element={
          <ProtectedRoute allowedRoles={['admin', 'manager']}>
            <Users />
          </ProtectedRoute>
        } />
        <Route path="branches" element={
          <ProtectedRoute allowedRoles={['admin']}>
            <Branches />
          </ProtectedRoute>
        } />
        <Route path="reports" element={
          <ProtectedRoute allowedRoles={['admin', 'manager']}>
            <Reports />
          </ProtectedRoute>
        } />
        <Route path="debts" element={
          <ProtectedRoute allowedRoles={['admin', 'manager']}>
            <Debts />
          </ProtectedRoute>
        } />
        <Route path="settings" element={
          <ProtectedRoute allowedRoles={['admin']}>
            <Settings />
          </ProtectedRoute>
        } />
        <Route path="audit-logs" element={
          <ProtectedRoute allowedRoles={['admin']}>
            <AuditLogs />
          </ProtectedRoute>
        } />
        <Route path="super-admin" element={
          <ProtectedRoute allowedRoles={['super_admin']}>
            <SuperAdmin />
          </ProtectedRoute>
        } />
      </Route>

      {/* Legacy routes - redirect to new paths */}
      <Route path="/dashboard" element={<Navigate to="/app/dashboard" replace />} />
      <Route path="/products" element={<Navigate to="/app/products" replace />} />
      <Route path="/stock" element={<Navigate to="/app/stock" replace />} />
      <Route path="/users" element={<Navigate to="/app/users" replace />} />
      <Route path="/branches" element={<Navigate to="/app/branches" replace />} />
      <Route path="/reports" element={<Navigate to="/app/reports" replace />} />
      <Route path="/settings" element={<Navigate to="/app/settings" replace />} />
      <Route path="/audit-logs" element={<Navigate to="/app/audit-logs" replace />} />
      <Route path="/super-admin" element={<Navigate to="/app/super-admin" replace />} />

      <Route path="*" element={<Navigate to="/" replace />} />
    </Routes>
  );
};

function App() {
  return (
    <HashRouter>
      <TenantProvider>
        <AuthProvider>
          {/* toast njoftimet u caktivizuan */}
          <AppRoutes />
        </AuthProvider>
      </TenantProvider>
    </HashRouter>
  );
}

export default App;