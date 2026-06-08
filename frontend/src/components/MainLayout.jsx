import React, { useState } from 'react';
import { Outlet, NavLink, useNavigate, useLocation } from 'react-router-dom';
import { useAuth } from '../App';
import {
  LayoutDashboard, ShoppingCart, Package, Warehouse, Users, Building2,
  BarChart3, Settings, LogOut, ClipboardList, Menu, X, CreditCard,
  Search, Bell, Sparkles, ChevronRight,
} from 'lucide-react';
import { Button } from './ui/button';
import { ScrollArea } from './ui/scroll-area';
import {
  DropdownMenu, DropdownMenuContent, DropdownMenuItem,
  DropdownMenuSeparator, DropdownMenuTrigger, DropdownMenuLabel,
} from './ui/dropdown-menu';
import { Avatar, AvatarFallback } from './ui/avatar';

const MainLayout = () => {
  const { user, logout } = useAuth();
  const navigate = useNavigate();
  const location = useLocation();
  const [sidebarOpen, setSidebarOpen] = useState(false);

  const handleLogout = () => { logout(); navigate('/login'); };

  const menuGroups = [
    { title: 'Kryesore', items: [
      { path: '/app/dashboard', icon: LayoutDashboard, label: 'Paneli', roles: ['admin','manager','cashier'] },
      { path: '/pos', icon: ShoppingCart, label: 'Arka', roles: ['admin','manager','cashier'] },
    ]},
    { title: 'Menaxhim', items: [
      { path: '/app/products', icon: Package, label: 'Produktet', roles: ['admin','manager'] },
      { path: '/app/stock', icon: Warehouse, label: 'Stoku', roles: ['admin','manager'] },
      { path: '/app/debts', icon: CreditCard, label: 'Borxhet', roles: ['admin','manager'] },
      { path: '/app/users', icon: Users, label: 'P\u00EBrdoruesit', roles: ['admin','manager'] },
      { path: '/app/branches', icon: Building2, label: 'Deg\u00EBt', roles: ['admin'] },
    ]},
    { title: 'Analitik\u00EB', items: [
      { path: '/app/reports', icon: BarChart3, label: 'Raportet', roles: ['admin','manager'] },
      { path: '/app/audit-logs', icon: ClipboardList, label: 'Audit Log', roles: ['admin'] },
    ]},
    { title: 'Sistemi', items: [
      { path: '/app/settings', icon: Settings, label: 'Cil\u00EBsimet', roles: ['admin'] },
      { path: '/app/super-admin', icon: Sparkles, label: 'Menaxho Firmat', roles: ['super_admin'] },
    ]},
  ];

  const filteredGroups = menuGroups
    .map(g => ({ ...g, items: g.items.filter(i => i.roles.includes(user?.role)) }))
    .filter(g => g.items.length > 0);

  const currentItem = menuGroups.flatMap(g => g.items).find(i => location.pathname.startsWith(i.path));

  const roleLabels = {
    super_admin: 'Super Admin',
    admin: 'Administrator',
    manager: 'Menaxher',
    cashier: 'Ark\u00EBtar',
  };

  const NavItemEl = ({ item }) => (
    <NavLink
      to={item.path}
      onClick={() => setSidebarOpen(false)}
      className={({ isActive }) => `nav-item ${isActive ? 'active' : ''}`}
    >
      <item.icon className="h-[18px] w-[18px] flex-shrink-0" strokeWidth={1.75} />
      <span>{item.label}</span>
    </NavLink>
  );

  return (
    <div className="min-h-screen bg-mesh-subtle">
      {/* Mobile Header */}
      <header className="lg:hidden fixed top-0 left-0 right-0 z-50 glass-strong border-b border-gray-200/60 px-4 py-3">
        <div className="flex items-center justify-between">
          <Button variant="ghost" size="icon" onClick={() => setSidebarOpen(!sidebarOpen)} data-testid="mobile-menu-btn">
            {sidebarOpen ? <X className="h-5 w-5" /> : <Menu className="h-5 w-5" />}
          </Button>
          <div className="flex items-center gap-2">
            <img src="/logo-icon.png" alt="DataPOS" className="h-8 w-8 object-contain" />
            <span className="font-bold text-gray-800 font-display tracking-tight">DataPOS</span>
          </div>
          <DropdownMenu>
            <DropdownMenuTrigger asChild>
              <Button variant="ghost" size="icon" data-testid="user-menu-mobile">
                <Avatar className="h-8 w-8">
                  <AvatarFallback className="bg-gradient-to-br from-[#00a79d] to-[#007a73] text-white text-sm font-semibold">
                    {user?.full_name?.charAt(0) || 'U'}
                  </AvatarFallback>
                </Avatar>
              </Button>
            </DropdownMenuTrigger>
            <DropdownMenuContent align="end" className="w-56">
              <div className="px-3 py-2">
                <p className="font-semibold text-sm">{user?.full_name}</p>
                <p className="text-xs text-gray-500">@{user?.username}</p>
              </div>
              <DropdownMenuSeparator />
              <DropdownMenuItem onClick={handleLogout} className="text-red-600">
                <LogOut className="h-4 w-4 mr-2" />{'\u00C7ky\u00E7u'}
              </DropdownMenuItem>
            </DropdownMenuContent>
          </DropdownMenu>
        </div>
      </header>

      {/* Sidebar */}
      <aside
        className={`fixed inset-y-0 left-0 z-40 w-64 glass-strong border-r border-gray-200/60 transform transition-transform duration-300 ease-in-out lg:translate-x-0 ${sidebarOpen ? 'translate-x-0' : '-translate-x-full'}`}
      >
        <div className="h-16 flex items-center gap-2.5 border-b border-gray-200/60 px-5">
          <div className="relative">
            <img src="/logo-icon.png" alt="DataPOS" className="h-9 w-9 object-contain" />
            <div className="absolute -inset-1 bg-gradient-to-r from-[#00a79d]/20 to-[#00c4b8]/20 rounded-full blur-md -z-10" />
          </div>
          <div className="flex flex-col leading-tight">
            <span className="font-display font-bold text-gray-800 tracking-tight">DataPOS</span>
            <span className="text-[10px] text-gray-500 font-medium tracking-wide uppercase">AI POS System</span>
          </div>
        </div>

        <ScrollArea className="h-[calc(100vh-9rem)] py-4 px-3">
          <nav className="space-y-5">
            {filteredGroups.map((group) => (
              <div key={group.title}>
                <h3 className="px-3 mb-1.5 text-[10px] font-semibold text-gray-400 uppercase tracking-wider">{group.title}</h3>
                <div className="space-y-0.5">
                  {group.items.map((item) => <NavItemEl key={item.path} item={item} />)}
                </div>
              </div>
            ))}
          </nav>
        </ScrollArea>

        <div className="absolute bottom-0 left-0 right-0 p-3 border-t border-gray-200/60 bg-white/50 backdrop-blur-md">
          <DropdownMenu>
            <DropdownMenuTrigger asChild>
              <button className="w-full flex items-center gap-3 p-2 rounded-xl hover:bg-gray-100/80 transition-colors" data-testid="user-menu-desktop">
                <Avatar className="h-9 w-9 ring-2 ring-white shadow-sm">
                  <AvatarFallback className="bg-gradient-to-br from-[#00a79d] to-[#007a73] text-white text-sm font-semibold">
                    {user?.full_name?.charAt(0) || 'U'}
                  </AvatarFallback>
                </Avatar>
                <div className="flex-1 min-w-0 text-left">
                  <p className="text-sm font-semibold text-gray-800 truncate">{user?.full_name}</p>
                  <p className="text-[11px] text-gray-500 truncate">{roleLabels[user?.role] || user?.role}</p>
                </div>
                <ChevronRight className="h-4 w-4 text-gray-400" />
              </button>
            </DropdownMenuTrigger>
            <DropdownMenuContent align="end" className="w-56" side="top">
              <DropdownMenuLabel>
                <p className="text-sm">{user?.full_name}</p>
                <p className="text-xs text-gray-500 font-normal">@{user?.username}</p>
              </DropdownMenuLabel>
              <DropdownMenuSeparator />
              <DropdownMenuItem onClick={() => navigate('/app/settings')}>
                <Settings className="h-4 w-4 mr-2" />{'Cil\u00EBsimet'}
              </DropdownMenuItem>
              <DropdownMenuSeparator />
              <DropdownMenuItem onClick={handleLogout} className="text-red-600">
                <LogOut className="h-4 w-4 mr-2" />{'\u00C7ky\u00E7u'}
              </DropdownMenuItem>
            </DropdownMenuContent>
          </DropdownMenu>
        </div>
      </aside>

      {sidebarOpen && (
        <div className="fixed inset-0 bg-black/30 backdrop-blur-sm z-30 lg:hidden" onClick={() => setSidebarOpen(false)} />
      )}

      <main className="lg:ml-64 min-h-screen pt-16 lg:pt-0">
        <div className="hidden lg:flex sticky top-0 z-20 h-14 items-center justify-between px-6 glass-strong border-b border-gray-200/60">
          <div className="flex items-center gap-2 text-sm">
            <span className="text-gray-400">DataPOS</span>
            <ChevronRight className="h-3.5 w-3.5 text-gray-300" />
            <span className="font-semibold text-gray-800">{currentItem?.label || 'Paneli'}</span>
          </div>
          <div className="flex items-center gap-2">
            <button className="flex items-center gap-2 px-3 py-1.5 text-sm text-gray-500 bg-gray-100/60 hover:bg-gray-100 rounded-lg transition-colors">
              <Search className="h-4 w-4" />
              <span>{'K\u00EBrko...'}</span>
              <kbd className="ml-2">Ctrl K</kbd>
            </button>
            <Button variant="ghost" size="icon" className="relative">
              <Bell className="h-5 w-5 text-gray-600" strokeWidth={1.75} />
              <span className="absolute top-2 right-2 h-2 w-2 bg-red-500 rounded-full" />
            </Button>
          </div>
        </div>
        <div className="p-4 md:p-6 page-content" key={location.pathname}>
          <Outlet />
        </div>
      </main>
    </div>
  );
};

export default MainLayout;