import React, { useState } from 'react';
import { Outlet, NavLink, useNavigate, useLocation } from 'react-router-dom';
import { useAuth } from '../App';
import {
  LayoutDashboard, ShoppingCart, Package, Warehouse, Users, Building2,
  BarChart3, Settings, LogOut, ClipboardList, Menu, X, CreditCard,
  Search, Bell, Sparkles, Sun, Moon,
} from 'lucide-react';
import { Avatar, AvatarFallback } from './ui/avatar';

const MainLayout = () => {
  const { user, logout } = useAuth();
  const navigate = useNavigate();
  const location = useLocation();
  const [sidebarOpen, setSidebarOpen] = useState(false);
  const [darkMode, setDarkMode] = useState(false);

  const handleLogout = () => { logout(); navigate('/login'); };

  const menuItems = [
    { path: '/app/dashboard',    icon: LayoutDashboard, label: 'Paneli',          roles: ['admin','manager','cashier'] },
    { path: '/pos',              icon: ShoppingCart,    label: 'Arka POS',        roles: ['admin','manager','cashier'] },
    { path: '/app/products',     icon: Package,         label: 'Produktet',       roles: ['admin','manager'] },
    { path: '/app/stock',        icon: Warehouse,       label: 'Stoku',           roles: ['admin','manager'] },
    { path: '/app/debts',        icon: CreditCard,      label: 'Borxhet',         roles: ['admin','manager'] },
    { path: '/app/users',        icon: Users,           label: 'Perdoruesit',     roles: ['admin','manager'] },
    { path: '/app/branches',     icon: Building2,       label: 'Deget',           roles: ['admin'] },
    { path: '/app/reports',      icon: BarChart3,       label: 'Raportet',        roles: ['admin','manager'] },
    { path: '/app/audit-logs',   icon: ClipboardList,   label: 'Audit Log',       roles: ['admin'] },
    { path: '/app/settings',     icon: Settings,        label: 'Cilesimet',       roles: ['admin'] },
    { path: '/app/super-admin',  icon: Sparkles,        label: 'Menaxho Firmat',  roles: ['super_admin'] },
  ];

  const filteredItems = menuItems.filter(i => i.roles.includes(user?.role));
  const currentItem = menuItems.find(i => location.pathname.startsWith(i.path));

  const roleLabels = {
    super_admin: 'Super Admin',
    admin: 'Administrator',
    manager: 'Menaxher',
    cashier: 'Arketar',
  };

  const navItemClass = ({ isActive }) =>
    "flex items-center gap-3 px-4 py-2.5 rounded-xl transition-all text-sm font-medium " +
    (isActive
      ? "bg-white text-[#1E3A8A] shadow-lg font-semibold"
      : "text-blue-100 hover:bg-white/10 hover:text-white");

  return (
    <div className="min-h-screen bg-gray-50">
      {/* Mobile Header */}
      <header className="lg:hidden fixed top-0 left-0 right-0 z-50 bg-white border-b border-gray-200 px-4 py-3 shadow-sm">
        <div className="flex items-center justify-between">
          <button
            onClick={() => setSidebarOpen(!sidebarOpen)}
            className="w-10 h-10 flex items-center justify-center rounded-lg hover:bg-gray-100"
          >
            {sidebarOpen ? <X className="h-5 w-5" /> : <Menu className="h-5 w-5" />}
          </button>
          <div className="flex items-center gap-2">
            <div className="w-8 h-8 bg-[#2563EB] rounded-lg flex items-center justify-center">
              <Sparkles className="h-4 w-4 text-white" />
            </div>
            <span className="font-bold text-gray-800">DataPOS</span>
          </div>
          <div className="w-10" />
        </div>
      </header>

      {/* Sidebar */}
      <aside
        className={
          "fixed inset-y-0 left-0 z-40 w-64 bg-gradient-to-b from-[#1E3A8A] via-[#1E40AF] to-[#2563EB] transform transition-transform duration-300 ease-in-out lg:translate-x-0 flex flex-col shadow-2xl " +
          (sidebarOpen ? "translate-x-0" : "-translate-x-full lg:translate-x-0")
        }
      >
        {/* Brand */}
        <div className="h-14 flex items-center gap-2.5 px-5 border-b border-white/10 flex-shrink-0">
          <div className="w-8 h-8 bg-white/15 rounded-lg flex items-center justify-center">
            <Sparkles className="h-4 w-4 text-white" />
          </div>
          <div className="flex flex-col leading-tight">
            <span className="font-bold text-white tracking-tight text-sm">DataPOS</span>
            <span className="text-[9px] text-blue-200 font-medium tracking-wider uppercase">POS System</span>
          </div>
        </div>

        {/* User profile card */}
        <div className="px-5 py-5 border-b border-white/10 flex-shrink-0">
          <div className="flex flex-col items-center text-center">
            <Avatar className="h-16 w-16 ring-4 ring-white/20 mb-3">
              <AvatarFallback className="bg-white text-[#1E3A8A] text-2xl font-bold">
                {user?.full_name?.charAt(0)?.toUpperCase() || user?.username?.charAt(0)?.toUpperCase() || 'U'}
              </AvatarFallback>
            </Avatar>
            <p className="text-sm font-semibold text-white truncate max-w-full">
              {user?.full_name || user?.username || 'Perdorues'}
            </p>
            <p className="text-[11px] text-blue-200 truncate max-w-full mt-0.5">
              {user?.email || ('@' + (user?.username || 'user'))}
            </p>
            <span className="mt-2 text-[10px] font-medium bg-white/15 text-white px-2.5 py-0.5 rounded-full">
              {roleLabels[user?.role] || user?.role}
            </span>
          </div>
        </div>

        {/* Nav items */}
        <div className="flex-1 overflow-y-auto py-4 px-3 min-h-0">
          <nav className="space-y-1">
            {filteredItems.map((item) => {
              const Icon = item.icon;
              return (
                <NavLink
                  key={item.path}
                  to={item.path}
                  onClick={() => setSidebarOpen(false)}
                  className={navItemClass}
                >
                  <Icon className="h-[18px] w-[18px] flex-shrink-0" strokeWidth={2} />
                  <span>{item.label}</span>
                </NavLink>
              );
            })}
          </nav>
        </div>

        {/* Logout */}
        <div className="p-3 border-t border-white/10 flex-shrink-0">
          <button
            onClick={handleLogout}
            className="w-full flex items-center gap-3 px-4 py-2.5 rounded-xl text-blue-100 hover:bg-red-500/20 hover:text-white transition-all text-sm font-medium"
          >
            <LogOut className="h-[18px] w-[18px]" strokeWidth={2} />
            <span>Ckycu</span>
          </button>
        </div>
      </aside>

      {/* Mobile overlay */}
      {sidebarOpen && (
        <div
          className="fixed inset-0 bg-black/40 backdrop-blur-sm z-30 lg:hidden"
          onClick={() => setSidebarOpen(false)}
        />
      )}

      {/* Main */}
      <main className="lg:ml-64 min-h-screen pt-16 lg:pt-0">
        {/* Desktop Header */}
        <div className="hidden lg:flex sticky top-0 z-20 h-20 items-center justify-between px-8 bg-white border-b border-gray-200 shadow-sm">
          <div>
            <h1 className="text-xl font-bold text-gray-900">
              Welcome, {user?.full_name || user?.username || 'Perdorues'} !
            </h1>
            <p className="text-xs text-gray-500 mt-0.5">
              {currentItem?.label || 'Paneli'}
            </p>
          </div>
          <div className="flex items-center gap-3">
            <div className="relative">
              <Search className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-gray-400" />
              <input
                type="text"
                placeholder="Kerko..."
                className="pl-9 pr-4 h-10 w-64 bg-gray-100 rounded-lg text-sm border-0 focus:ring-2 focus:ring-[#2563EB] focus:bg-white outline-none transition-all"
              />
            </div>
            <button
              onClick={() => setDarkMode(!darkMode)}
              className="w-10 h-10 flex items-center justify-center bg-gray-100 hover:bg-gray-200 rounded-lg transition-colors"
              title="Ndrysho temen"
            >
              {darkMode ? <Sun className="h-5 w-5 text-gray-600" /> : <Moon className="h-5 w-5 text-gray-600" />}
            </button>
            <button className="relative w-10 h-10 flex items-center justify-center bg-gray-100 hover:bg-gray-200 rounded-lg transition-colors">
              <Bell className="h-5 w-5 text-gray-600" strokeWidth={1.75} />
              <span className="absolute top-2 right-2 h-2 w-2 bg-red-500 rounded-full ring-2 ring-white" />
            </button>
          </div>
        </div>

        {/* Page content */}
        <div className="p-4 md:p-6" key={location.pathname}>
          <Outlet />
        </div>
      </main>
    </div>
  );
};

export default MainLayout;