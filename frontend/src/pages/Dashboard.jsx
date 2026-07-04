import React, { useState, useEffect } from 'react';
import { api, useAuth } from '../App';
import { Card, CardContent, CardHeader, CardTitle } from '../components/ui/card';
import { Button } from '../components/ui/button';
import { Input } from '../components/ui/input';
import { Checkbox } from '../components/ui/checkbox';
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '../components/ui/select';
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
  DialogFooter,
} from '../components/ui/dialog';
import {
  DollarSign,
  ShoppingCart,
  Package,
  AlertTriangle,
  TrendingUp,
  TrendingDown,
  ArrowRight,
  RotateCcw,
  Lock,
  Users,
  Calendar,
  Trash2,
  Utensils,
  Store,
  Briefcase,
  Sparkles
} from 'lucide-react';
import { LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, BarChart, Bar } from 'recharts';
import { useNavigate } from 'react-router-dom';
import { toast } from 'sonner';

// Trial Banner Component
const TrialBanner = () => {
  const [trialInfo, setTrialInfo] = React.useState(null);
  const { user } = useAuth();

  React.useEffect(() => {
    const fetchTrialStatus = async () => {
      if (!user?.tenant_id) return;
      try {
        const response = await api.get(`/trial-status/${user.tenant_id}`);
        setTrialInfo(response.data);
      } catch (error) {
        // Silently fail - not critical
      }
    };
    fetchTrialStatus();
  }, [user?.tenant_id]);

  if (!trialInfo || trialInfo.status !== 'trial') return null;

  const { remaining_days, is_expired } = trialInfo;

  if (is_expired) {
    return (
      <div className="bg-red-50 border border-red-200 rounded-lg p-4 flex items-center justify-between">
        <div className="flex items-center gap-3">
          <div className="p-2 bg-red-100 rounded-full">
            <AlertTriangle className="h-5 w-5 text-red-600" />
          </div>
          <div>
            <p className="font-semibold text-red-800">Periudha e Provës Ka Përfunduar!</p>
            <p className="text-sm text-red-600">Ju lutem abonohuni për të vazhduar përdorimin e sistemit.</p>
          </div>
        </div>
        <Button className="bg-red-600 hover:bg-red-700 text-white">
          Abonohu Tani
        </Button>
      </div>
    );
  }

  const isUrgent = remaining_days <= 7;

  return (
    <div className={`${isUrgent ? 'bg-orange-50 border-orange-200' : 'bg-blue-50 border-blue-200'} border rounded-lg p-4 flex items-center justify-between`}>
      <div className="flex items-center gap-3">
        <div className={`p-2 ${isUrgent ? 'bg-orange-100' : 'bg-blue-100'} rounded-full`}>
          <Calendar className={`h-5 w-5 ${isUrgent ? 'text-orange-600' : 'text-blue-600'}`} />
        </div>
        <div>
          <p className={`font-semibold ${isUrgent ? 'text-orange-800' : 'text-blue-800'}`}>
            Periudha e Provës: {remaining_days} ditë të mbetura
          </p>
          <p className={`text-sm ${isUrgent ? 'text-orange-600' : 'text-blue-600'}`}>
            {isUrgent 
              ? 'Abonohuni para se të përfundojë periudha e provës!'
              : 'Po shijoni periudhën falas. Eksporoni të gjitha veçoritë!'}
          </p>
        </div>
      </div>
      <Button className={`${isUrgent ? 'bg-orange-600 hover:bg-orange-700' : 'bg-blue-600 hover:bg-blue-700'} text-white`}>
        Shiko Planet
      </Button>
    </div>
  );
};

const Dashboard = () => {
  const { user } = useAuth();
  const navigate = useNavigate();
  const [stats, setStats] = useState(null);
  const [loading, setLoading] = useState(true);
  const [branches, setBranches] = useState([]);
  const [selectedBranch, setSelectedBranch] = useState('all');
  
  // Reset functionality states
  const [showResetDialog, setShowResetDialog] = useState(false);
  const [resetStep, setResetStep] = useState(1); // 1: password, 2: select users, 3: confirm
  const [resetPassword, setResetPassword] = useState('');
  const [resetType, setResetType] = useState(''); // 'all', 'daily', 'user_specific'
  const [usersForReset, setUsersForReset] = useState([]);
  const [selectedUsers, setSelectedUsers] = useState([]);
  const [resetLoading, setResetLoading] = useState(false);
  
  // Backup functionality states
  const [showBackupsDialog, setShowBackupsDialog] = useState(false);
  const [backups, setBackups] = useState([]);
  const [backupsLoading, setBackupsLoading] = useState(false);
  const [showRestoreDialog, setShowRestoreDialog] = useState(false);
  const [selectedBackup, setSelectedBackup] = useState(null);
  const [restorePassword, setRestorePassword] = useState('');

  useEffect(() => {
    loadData();
  }, [selectedBranch]);

  const loadData = async () => {
    try {
      setLoading(true);
      const params = selectedBranch !== 'all' ? { branch_id: selectedBranch } : {};
      const [statsRes, branchesRes] = await Promise.all([
        api.get('/reports/dashboard', { params }),
        api.get('/branches')
      ]);
      setStats(statsRes.data);
      setBranches(branchesRes.data);
    } catch (error) {
      console.error('Error loading dashboard:', error);
    } finally {
      setLoading(false);
    }
  };

  const formatCurrency = (value) => `€${(value || 0).toFixed(2)}`;

  // Reset functionality
  const openResetDialog = (type) => {
    setResetType(type);
    setResetStep(1);
    setResetPassword('');
    setSelectedUsers([]);
    setShowResetDialog(true);
  };

  const verifyPassword = async () => {
    if (!resetPassword) {
      toast.error('Ju lutem shkruani fjalëkalimin');
      return;
    }
    
    setResetLoading(true);
    try {
      await api.post('/admin/verify-password', { password: resetPassword });
      
      if (resetType === 'user_specific') {
        // Load users for selection
        const response = await api.get('/admin/users-for-reset');
        setUsersForReset(response.data);
        setResetStep(2);
      } else {
        // Go directly to confirmation
        setResetStep(3);
      }
    } catch (error) {
      toast.error(error.response?.data?.detail || 'Fjalëkalimi i gabuar');
    } finally {
      setResetLoading(false);
    }
  };

  const toggleUserSelection = (userId) => {
    setSelectedUsers(prev => 
      prev.includes(userId) 
        ? prev.filter(id => id !== userId)
        : [...prev, userId]
    );
  };

  const selectAllUsers = () => {
    if (selectedUsers.length === usersForReset.length) {
      setSelectedUsers([]);
    } else {
      setSelectedUsers(usersForReset.map(u => u.id));
    }
  };

  const executeReset = async () => {
    if (resetType === 'user_specific' && selectedUsers.length === 0) {
      toast.error('Zgjidhni të paktën një përdorues');
      return;
    }
    
    setResetLoading(true);
    try {
      const response = await api.post('/admin/reset-data', {
        admin_password: resetPassword,
        reset_type: resetType,
        user_ids: resetType === 'user_specific' ? selectedUsers : null
      });
      
      toast.success(
        `Të dhënat u resetuan: ${response.data.deleted.sales} shitje, ${response.data.deleted.cash_drawers} arka. Backup ID: ${response.data.backup_id?.slice(0,8)}...`
      );
      setShowResetDialog(false);
      loadData(); // Refresh dashboard
    } catch (error) {
      toast.error(error.response?.data?.detail || 'Gabim gjatë resetimit');
    } finally {
      setResetLoading(false);
    }
  };

  const getResetTypeLabel = () => {
    switch (resetType) {
      case 'all': return 'Të gjitha të dhënat';
      case 'daily': return 'Përmbledhja e ditës';
      case 'user_specific': return 'Përdorues të zgjedhur';
      default: return '';
    }
  };

  // Backup functionality
  const loadBackups = async () => {
    setBackupsLoading(true);
    try {
      const response = await api.get('/admin/backups');
      setBackups(response.data);
    } catch (error) {
      toast.error('Gabim gjatë ngarkimit të backup-eve');
    } finally {
      setBackupsLoading(false);
    }
  };

  const openBackupsDialog = () => {
    loadBackups();
    setShowBackupsDialog(true);
  };

  const openRestoreDialog = (backup) => {
    setSelectedBackup(backup);
    setRestorePassword('');
    setShowRestoreDialog(true);
  };

  const executeRestore = async () => {
    if (!restorePassword) {
      toast.error('Ju lutem shkruani fjalëkalimin');
      return;
    }
    
    setBackupsLoading(true);
    try {
      const response = await api.post(`/admin/backups/${selectedBackup.id}/restore`, {
        admin_password: restorePassword
      });
      
      toast.success(
        `Të dhënat u rikthyen: ${response.data.restored.sales} shitje, ${response.data.restored.cash_drawers} arka`
      );
      setShowRestoreDialog(false);
      setShowBackupsDialog(false);
      loadData(); // Refresh dashboard
    } catch (error) {
      toast.error(error.response?.data?.detail || 'Gabim gjatë rikthimit');
    } finally {
      setBackupsLoading(false);
    }
  };

  const deleteBackup = async (backupId) => {
    if (!window.confirm('Jeni i sigurt që doni të fshini këtë backup? Kjo veprim nuk mund të kthehet.')) {
      return;
    }
    
    try {
      await api.delete(`/admin/backups/${backupId}`);
      toast.success('Backup u fshi');
      loadBackups();
    } catch (error) {
      toast.error('Gabim gjatë fshirjes');
    }
  };

  const getResetTypeText = (type) => {
    switch (type) {
      case 'all': return 'Të gjitha';
      case 'daily': return 'Ditor';
      case 'user_specific': return 'Përdorues';
      default: return type;
    }
  };

  // Mock chart data - in production would come from API
  const salesChartData = [
    { name: 'Hën', sales: 1200 },
    { name: 'Mar', sales: 1900 },
    { name: 'Mër', sales: 1500 },
    { name: 'Enj', sales: 2100 },
    { name: 'Pre', sales: 2400 },
    { name: 'Sht', sales: 1800 },
    { name: 'Die', sales: 900 },
  ];

  const topProductsData = [
    { name: 'Qumësht', sales: 150 },
    { name: 'Bukë', sales: 120 },
    { name: 'Ujë', sales: 100 },
    { name: 'Kafe', sales: 80 },
    { name: 'Sheqer', sales: 60 },
  ];

  if (loading) {
    return (
      <div className="flex items-center justify-center h-96">
        <div className="spinner" />
      </div>
    );
  }

  return (
    <div className="space-y-6 animate-fade-in" data-testid="dashboard-page">
      {/* Trial Banner */}
      <TrialBanner />
      
      {/* Header */}
      <div className="flex flex-col md:flex-row md:items-center md:justify-between gap-4">
        <div>
          <h1 className="text-2xl md:text-3xl font-bold text-gray-900">
            Mirësevini, {user?.full_name}!
          </h1>
          <p className="text-gray-500 mt-1">Përmbledhja e ditës</p>
        </div>
        
        {user?.role === 'admin' && branches.length > 0 && (
          <Select value={selectedBranch} onValueChange={setSelectedBranch}>
            <SelectTrigger className="w-[200px]" data-testid="branch-filter">
              <SelectValue placeholder="Zgjidh degën" />
            </SelectTrigger>
            <SelectContent>
              <SelectItem value="all">Të gjitha degët</SelectItem>
              {branches.map((branch) => (
                <SelectItem key={branch.id} value={branch.id}>
                  {branch.name}
                </SelectItem>
              ))}
            </SelectContent>
          </Select>
        )}
      </div>

      {/* KPI Cards */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
        <Card className="border border-gray-200/60 rounded-3xl shadow-sm bg-white/80 backdrop-blur-md hover-lift" data-testid="kpi-sales">
          <CardContent className="p-6">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm font-medium text-gray-500">Shitjet Sot</p>
                <p className="text-2xl font-bold text-gray-900 mt-1">
                  {formatCurrency(stats?.total_sales_today)}
                </p>
                <div className="flex items-center gap-1 mt-2">
                  <TrendingUp className="h-4 w-4 text-green-500" />
                  <span className="text-sm text-green-500">+12.5%</span>
                </div>
              </div>
              <div className="h-12 w-12 rounded-2xl bg-gradient-to-br from-[#2563EB]/15 to-[#2563EB]/5 flex items-center justify-center">
                <DollarSign className="h-6 w-6 text-[#2563EB]" />
              </div>
            </div>
          </CardContent>
        </Card>

        <Card className="border border-gray-200/60 rounded-3xl shadow-sm bg-white/80 backdrop-blur-md hover-lift" data-testid="kpi-transactions">
          <CardContent className="p-6">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm font-medium text-gray-500">Transaksionet</p>
                <p className="text-2xl font-bold text-gray-900 mt-1">
                  {stats?.total_transactions_today || 0}
                </p>
                <div className="flex items-center gap-1 mt-2">
                  <TrendingUp className="h-4 w-4 text-green-500" />
                  <span className="text-sm text-green-500">+8.2%</span>
                </div>
              </div>
              <div className="h-12 w-12 rounded-2xl bg-gradient-to-br from-[#2563EB]/15 to-[#2563EB]/5 flex items-center justify-center">
                <ShoppingCart className="h-6 w-6 text-[#2563EB]" />
              </div>
            </div>
          </CardContent>
        </Card>

        <Card className="border border-gray-200/60 rounded-3xl shadow-sm bg-white/80 backdrop-blur-md hover-lift" data-testid="kpi-products">
          <CardContent className="p-6">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm font-medium text-gray-500">Produktet</p>
                <p className="text-2xl font-bold text-gray-900 mt-1">
                  {stats?.total_products || 0}
                </p>
                <p className="text-sm text-gray-400 mt-2">Në total</p>
              </div>
              <div className="h-12 w-12 rounded-2xl bg-green-100 flex items-center justify-center">
                <Package className="h-6 w-6 text-green-600" />
              </div>
            </div>
          </CardContent>
        </Card>

        <Card className="border border-gray-200/60 rounded-3xl shadow-sm bg-white/80 backdrop-blur-md hover-lift" data-testid="kpi-lowstock">
          <CardContent className="p-6">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm font-medium text-gray-500">Stok i Ulët</p>
                <p className="text-2xl font-bold text-gray-900 mt-1">
                  {stats?.low_stock_products || 0}
                </p>
                <p className="text-sm text-orange-500 mt-2">Kërkon vëmendje</p>
              </div>
              <div className="h-12 w-12 rounded-2xl bg-orange-100 flex items-center justify-center">
                <AlertTriangle className="h-6 w-6 text-orange-500" />
              </div>
            </div>
          </CardContent>
        </Card>
      </div>

      {/* Charts Row */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Sales Chart */}
        <Card className="border border-gray-200/60 rounded-3xl shadow-sm bg-white/80 backdrop-blur-md">
          <CardHeader className="pb-2">
            <CardTitle className="text-lg font-bold tracking-tight">Shitjet Javore</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="h-72">
              <ResponsiveContainer width="100%" height="100%">
                <LineChart data={salesChartData}>
                  <CartesianGrid strokeDasharray="3 3" stroke="#E2E8F0" />
                  <XAxis dataKey="name" stroke="#64748B" fontSize={12} />
                  <YAxis stroke="#64748B" fontSize={12} />
                  <Tooltip
                    contentStyle={{
                      backgroundColor: 'white',
                      border: '1px solid #E2E8F0',
                      borderRadius: '8px',
                    }}
                  />
                  <Line
                    type="monotone"
                    dataKey="sales"
                    stroke="#2563EB"
                    strokeWidth={3}
                    dot={{ fill: '#2563EB', strokeWidth: 2 }}
                    activeDot={{ r: 6, fill: '#2563EB' }}
                  />
                </LineChart>
              </ResponsiveContainer>
            </div>
          </CardContent>
        </Card>

        {/* Top Products */}
        <Card className="border border-gray-200/60 rounded-3xl shadow-sm bg-white/80 backdrop-blur-md">
          <CardHeader className="pb-2">
            <CardTitle className="text-lg font-bold tracking-tight">Produktet më të Shitura</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="h-72">
              <ResponsiveContainer width="100%" height="100%">
                <BarChart data={stats?.top_products || []} layout="vertical">
                  <CartesianGrid strokeDasharray="3 3" stroke="#E2E8F0" />
                  <XAxis type="number" stroke="#64748B" fontSize={12} />
                  <YAxis dataKey="name" type="category" stroke="#64748B" fontSize={12} width={60} />
                  <Tooltip
                    contentStyle={{
                      backgroundColor: 'white',
                      border: '1px solid #E2E8F0',
                      borderRadius: '8px',
                    }}
                  />
                  <Bar dataKey="sales" fill="#2563EB" radius={[0, 4, 4, 0]} />
                </BarChart>
              </ResponsiveContainer>
            </div>
          </CardContent>
        </Card>
      </div>

      {/* Recent Sales & Quick Actions */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Recent Sales */}
        <Card className="border border-gray-200/60 rounded-3xl shadow-sm bg-white/80 backdrop-blur-md lg:col-span-2">
          <CardHeader className="flex flex-row items-center justify-between pb-2">
            <CardTitle className="text-lg font-bold tracking-tight">Shitjet e Fundit</CardTitle>
            <Button
              variant="ghost"
              size="sm"
              onClick={() => navigate('/reports')}
              className="text-[#2563EB] hover:text-[#D32F2F]"
            >
              Shiko të gjitha
              <ArrowRight className="h-4 w-4 ml-1" />
            </Button>
          </CardHeader>
          <CardContent>
            <div className="space-y-3">
              {stats?.recent_sales?.slice(0, 5).map((sale, index) => (
                <div
                  key={sale.id || index}
                  className="flex items-center justify-between p-3 rounded-lg bg-gray-50 hover:bg-[#E0F7FA]/50 transition-colors"
                >
                  <div>
                    <p className="font-medium text-gray-900">{sale.receipt_number}</p>
                    <p className="text-sm text-gray-500">
                      {new Date(sale.created_at).toLocaleString('sq-AL')}
                    </p>
                  </div>
                  <div className="text-right">
                    <p className="font-semibold text-gray-900">{formatCurrency(sale.grand_total)}</p>
                    <p className="text-xs text-gray-500 capitalize">{sale.payment_method}</p>
                  </div>
                </div>
              )) || (
                <p className="text-center text-gray-500 py-8">Nuk ka shitje sot</p>
              )}
            </div>
          </CardContent>
        </Card>

        {/* Quick Actions */}
        <Card className="border border-gray-200/60 rounded-3xl shadow-sm bg-white/80 backdrop-blur-md">
          <CardHeader className="pb-2">
            <CardTitle className="text-lg font-bold tracking-tight">Veprime të Shpejta</CardTitle>
          </CardHeader>
          <CardContent className="space-y-3">
            <Button
              className="w-full justify-start gap-3 h-12 bg-[#2563EB] hover:bg-[#1D4ED8] text-white"
              onClick={() => navigate('/pos')}
              data-testid="quick-action-pos"
            >
              <ShoppingCart className="h-5 w-5" />
              Hap Arkën
            </Button>
            <Button
              variant="outline"
              className="w-full justify-start gap-3 h-12"
              onClick={() => navigate('/products')}
              data-testid="quick-action-products"
            >
              <Package className="h-5 w-5" />
              Shto Produkt
            </Button>
            <Button
              variant="outline"
              className="w-full justify-start gap-3 h-12"
              onClick={() => navigate('/stock')}
              data-testid="quick-action-stock"
            >
              <AlertTriangle className="h-5 w-5" />
              Kontrollo Stokun
            </Button>
            <Button
              variant="outline"
              className="w-full justify-start gap-3 h-12"
              onClick={() => navigate('/reports')}
              data-testid="quick-action-reports"
            >
              <TrendingUp className="h-5 w-5" />
              Shiko Raportet
            </Button>
            
            {/* Admin Reset Options - Only visible to admins */}
            {user?.role === 'admin' && (
              <>
                <div className="border-t pt-3 mt-3">
                  <p className="text-xs text-gray-500 mb-2 font-medium">Veprime Administrative</p>
                </div>
                <Button
                  variant="outline"
                  className="w-full justify-start gap-3 h-12 border-orange-300 text-orange-600 hover:bg-orange-50"
                  onClick={() => openResetDialog('daily')}
                  data-testid="quick-action-reset-daily"
                >
                  <Calendar className="h-5 w-5" />
                  Reseto Ditën (0)
                </Button>
                <Button
                  variant="outline"
                  className="w-full justify-start gap-3 h-12 border-red-300 text-red-600 hover:bg-red-50"
                  onClick={() => openResetDialog('user_specific')}
                  data-testid="quick-action-reset-users"
                >
                  <Users className="h-5 w-5" />
                  Reseto Përdorues
                </Button>
                <Button
                  variant="outline"
                  className="w-full justify-start gap-3 h-12 border-red-500 text-red-700 hover:bg-red-100"
                  onClick={() => openResetDialog('all')}
                  data-testid="quick-action-reset-all"
                >
                  <Trash2 className="h-5 w-5" />
                  Reseto Të Gjitha
                </Button>
                <Button
                  variant="outline"
                  className="w-full justify-start gap-3 h-12 border-blue-400 text-blue-600 hover:bg-blue-50"
                  onClick={openBackupsDialog}
                  data-testid="quick-action-backups"
                >
                  <RotateCcw className="h-5 w-5" />
                  Shiko Backup-et
                </Button>
              </>
            )}
          </CardContent>
        </Card>
      </div>

      {/* Coming Soon Apps */}
      <Card className="border border-gray-200/60 rounded-3xl shadow-sm bg-white/80 backdrop-blur-md">
        <CardHeader className="pb-2">
          <CardTitle className="text-lg font-bold tracking-tight flex items-center gap-2">
            <Sparkles className="h-5 w-5 text-[#2563EB]" />
            Aplikacione të Reja - Së Shpejti
          </CardTitle>
          <p className="text-sm text-gray-500">Sistemet e ardhshme që do të lehtësojnë punën tuaj</p>
        </CardHeader>
        <CardContent>
          <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
            {/* Restaurant Management */}
            <div className="relative p-6 rounded-xl bg-gradient-to-br from-orange-50 to-orange-100 border border-orange-200 overflow-hidden group hover:shadow-md transition-all">
              <div className="absolute top-3 right-3">
                <span className="px-2 py-1 text-xs font-semibold bg-orange-500 text-white rounded-full">
                  SË SHPEJTI
                </span>
              </div>
              <div className="w-14 h-14 bg-orange-500/20 rounded-2xl flex items-center justify-center mb-4">
                <Utensils className="w-7 h-7 text-orange-600" />
              </div>
              <h3 className="font-semibold text-gray-900 mb-2">Menaxhimi i Restoranteve</h3>
              <p className="text-sm text-gray-600">
                Sistemi i plotë për menaxhimin e restoranteve: porosi, tavolina, menu dixhitale, stafi i kuzhinës.
              </p>
              <ul className="mt-3 space-y-1">
                <li className="text-xs text-gray-500 flex items-center gap-1">
                  <div className="w-1 h-1 bg-orange-500 rounded-full"></div>
                  Menaxhim i tavolinave
                </li>
                <li className="text-xs text-gray-500 flex items-center gap-1">
                  <div className="w-1 h-1 bg-orange-500 rounded-full"></div>
                  Porosi në kohë reale
                </li>
                <li className="text-xs text-gray-500 flex items-center gap-1">
                  <div className="w-1 h-1 bg-orange-500 rounded-full"></div>
                  Menu dixhitale me QR
                </li>
              </ul>
            </div>

            {/* Mobile Shop Management */}
            <div className="relative p-6 rounded-xl bg-gradient-to-br from-blue-50 to-blue-100 border border-blue-200 overflow-hidden group hover:shadow-md transition-all">
              <div className="absolute top-3 right-3">
                <span className="px-2 py-1 text-xs font-semibold bg-blue-500 text-white rounded-full">
                  SË SHPEJTI
                </span>
              </div>
              <div className="w-14 h-14 bg-blue-500/20 rounded-2xl flex items-center justify-center mb-4">
                <Store className="w-7 h-7 text-blue-600" />
              </div>
              <h3 className="font-semibold text-gray-900 mb-2">Menaxhimi i Mobilshopave</h3>
              <p className="text-sm text-gray-600">
                Sistemi i avancuar për dyqanet e telefonave: servisim, shitje, inventar, garanci, riparime.
              </p>
              <ul className="mt-3 space-y-1">
                <li className="text-xs text-gray-500 flex items-center gap-1">
                  <div className="w-1 h-1 bg-blue-500 rounded-full"></div>
                  Menaxhim i riparimeve
                </li>
                <li className="text-xs text-gray-500 flex items-center gap-1">
                  <div className="w-1 h-1 bg-blue-500 rounded-full"></div>
                  Inventar i telefonave
                </li>
                <li className="text-xs text-gray-500 flex items-center gap-1">
                  <div className="w-1 h-1 bg-blue-500 rounded-full"></div>
                  Gjurmim i garancive
                </li>
              </ul>
            </div>

            {/* Employee Management */}
            <div className="relative p-6 rounded-xl bg-gradient-to-br from-purple-50 to-purple-100 border border-purple-200 overflow-hidden group hover:shadow-md transition-all">
              <div className="absolute top-3 right-3">
                <span className="px-2 py-1 text-xs font-semibold bg-purple-500 text-white rounded-full">
                  SË SHPEJTI
                </span>
              </div>
              <div className="w-14 h-14 bg-purple-500/20 rounded-2xl flex items-center justify-center mb-4">
                <Briefcase className="w-7 h-7 text-purple-600" />
              </div>
              <h3 className="font-semibold text-gray-900 mb-2">Menaxhimi i Punëtorëve</h3>
              <p className="text-sm text-gray-600">
                Sistemi komplet për menaxhimin e punëve dhe punëtorëve: orari, paga, pushime, detyra.
              </p>
              <ul className="mt-3 space-y-1">
                <li className="text-xs text-gray-500 flex items-center gap-1">
                  <div className="w-1 h-1 bg-purple-500 rounded-full"></div>
                  Orari i punës
                </li>
                <li className="text-xs text-gray-500 flex items-center gap-1">
                  <div className="w-1 h-1 bg-purple-500 rounded-full"></div>
                  Llogaritja e pagave
                </li>
                <li className="text-xs text-gray-500 flex items-center gap-1">
                  <div className="w-1 h-1 bg-purple-500 rounded-full"></div>
                  Menaxhimi i pushimeve
                </li>
              </ul>
            </div>
          </div>
        </CardContent>
      </Card>

      {/* Reset Dialog */}
      <Dialog open={showResetDialog} onOpenChange={setShowResetDialog}>
        <DialogContent className="sm:max-w-md">
          <DialogHeader>
            <DialogTitle className="flex items-center gap-2 text-red-600">
              <RotateCcw className="h-5 w-5" />
              Reseto Të Dhënat
            </DialogTitle>
          </DialogHeader>

          {/* Step 1: Password Verification */}
          {resetStep === 1 && (
            <div className="space-y-4">
              <div className="p-4 bg-yellow-50 border border-yellow-200 rounded-lg">
                <p className="text-sm text-yellow-800">
                  <strong>Kujdes!</strong> Jeni duke bërë: <strong>{getResetTypeLabel()}</strong>
                </p>
                <p className="text-xs text-yellow-700 mt-1">
                  Kjo veprim nuk mund të kthehet mbrapsht.
                </p>
              </div>
              
              <div className="space-y-2">
                <label className="text-sm font-medium flex items-center gap-2">
                  <Lock className="h-4 w-4" />
                  Fjalëkalimi i Administratorit
                </label>
                <Input
                  type="password"
                  placeholder="Shkruani fjalëkalimin..."
                  value={resetPassword}
                  onChange={(e) => setResetPassword(e.target.value)}
                  onKeyDown={(e) => e.key === 'Enter' && verifyPassword()}
                  autoFocus
                />
              </div>
              
              <DialogFooter>
                <Button variant="outline" onClick={() => setShowResetDialog(false)}>
                  Anulo
                </Button>
                <Button 
                  onClick={verifyPassword} 
                  disabled={resetLoading}
                  className="bg-red-600 hover:bg-red-700"
                >
                  {resetLoading ? 'Duke verifikuar...' : 'Vazhdo'}
                </Button>
              </DialogFooter>
            </div>
          )}

          {/* Step 2: User Selection (only for user_specific) */}
          {resetStep === 2 && (
            <div className="space-y-4">
              <div className="flex items-center justify-between">
                <p className="text-sm text-gray-600">Zgjidhni përdoruesit për reset:</p>
                <Button variant="ghost" size="sm" onClick={selectAllUsers}>
                  {selectedUsers.length === usersForReset.length ? 'Hiq të gjitha' : 'Zgjidh të gjitha'}
                </Button>
              </div>
              
              <div className="max-h-64 overflow-y-auto space-y-2 border rounded-lg p-2">
                {usersForReset.map((u) => (
                  <div
                    key={u.id}
                    className={`flex items-center gap-3 p-3 rounded-lg cursor-pointer transition-colors ${
                      selectedUsers.includes(u.id) ? 'bg-red-50 border border-red-200' : 'bg-gray-50 hover:bg-gray-100'
                    }`}
                    onClick={() => toggleUserSelection(u.id)}
                  >
                    <Checkbox
                      checked={selectedUsers.includes(u.id)}
                      className="border-red-500 data-[state=checked]:bg-red-500"
                    />
                    <div className="flex-1">
                      <p className="font-medium">{u.full_name || u.username}</p>
                      <p className="text-xs text-gray-500">{u.role}</p>
                    </div>
                    <div className="text-right">
                      <p className="text-sm font-semibold">€{u.total_sales.toFixed(2)}</p>
                      <p className="text-xs text-gray-500">{u.sales_count} shitje</p>
                    </div>
                  </div>
                ))}
              </div>
              
              <DialogFooter>
                <Button variant="outline" onClick={() => setResetStep(1)}>
                  Mbrapa
                </Button>
                <Button 
                  onClick={() => setResetStep(3)} 
                  disabled={selectedUsers.length === 0}
                  className="bg-red-600 hover:bg-red-700"
                >
                  Vazhdo ({selectedUsers.length} zgjedhur)
                </Button>
              </DialogFooter>
            </div>
          )}

          {/* Step 3: Final Confirmation */}
          {resetStep === 3 && (
            <div className="space-y-4">
              <div className="p-4 bg-red-50 border border-red-200 rounded-lg">
                <p className="text-sm text-red-800 font-medium">
                  Jeni i sigurt që doni të vazhdoni?
                </p>
                <p className="text-xs text-red-700 mt-2">
                  Do të fshihen: <strong>{getResetTypeLabel()}</strong>
                </p>
                {resetType === 'user_specific' && (
                  <p className="text-xs text-red-700">
                    Përdorues të zgjedhur: {selectedUsers.length}
                  </p>
                )}
                {resetType === 'daily' && (
                  <p className="text-xs text-red-700">
                    Shitjet dhe arkat e sotme do të fshihen
                  </p>
                )}
                {resetType === 'all' && (
                  <p className="text-xs text-red-700">
                    TË GJITHA shitjet, arkat dhe lëvizjet e stokut do të fshihen
                  </p>
                )}
              </div>
              
              <DialogFooter>
                <Button variant="outline" onClick={() => setResetStep(resetType === 'user_specific' ? 2 : 1)}>
                  Mbrapa
                </Button>
                <Button 
                  onClick={executeReset} 
                  disabled={resetLoading}
                  className="bg-red-600 hover:bg-red-700"
                >
                  {resetLoading ? 'Duke resetuar...' : 'Konfirmo Resetimin'}
                </Button>
              </DialogFooter>
            </div>
          )}
        </DialogContent>
      </Dialog>

      {/* Backups Dialog */}
      <Dialog open={showBackupsDialog} onOpenChange={setShowBackupsDialog}>
        <DialogContent className="sm:max-w-2xl">
          <DialogHeader>
            <DialogTitle className="flex items-center gap-2 text-blue-600">
              <RotateCcw className="h-5 w-5" />
              Backup-et e Ruajtura
            </DialogTitle>
          </DialogHeader>

          {backupsLoading ? (
            <div className="flex items-center justify-center py-8">
              <div className="spinner" />
            </div>
          ) : backups.length === 0 ? (
            <div className="text-center py-8 text-gray-500">
              <RotateCcw className="h-12 w-12 mx-auto mb-3 opacity-30" />
              <p>Nuk ka backup të ruajtura</p>
              <p className="text-sm mt-1">Backup-et krijohen automatikisht kur bëni reset</p>
            </div>
          ) : (
            <div className="max-h-96 overflow-y-auto space-y-3">
              {backups.map((backup) => (
                <div
                  key={backup.id}
                  className={`p-4 border rounded-lg ${backup.restored_at ? 'bg-green-50 border-green-200' : 'bg-gray-50'}`}
                >
                  <div className="flex items-center justify-between">
                    <div>
                      <div className="flex items-center gap-2">
                        <span className={`px-2 py-0.5 text-xs rounded-full ${
                          backup.reset_type === 'all' ? 'bg-red-100 text-red-700' :
                          backup.reset_type === 'daily' ? 'bg-orange-100 text-orange-700' :
                          'bg-blue-100 text-blue-700'
                        }`}>
                          {getResetTypeText(backup.reset_type)}
                        </span>
                        {backup.restored_at && (
                          <span className="px-2 py-0.5 text-xs bg-green-100 text-green-700 rounded-full">
                            Rikthyer
                          </span>
                        )}
                      </div>
                      <p className="text-sm font-medium mt-1">
                        {new Date(backup.created_at).toLocaleString('sq-AL')}
                      </p>
                      <p className="text-xs text-gray-500">
                        Nga: {backup.created_by_name}
                      </p>
                    </div>
                    <div className="text-right">
                      <p className="text-sm">
                        <span className="font-medium">{backup.deleted_counts?.sales || 0}</span> shitje
                      </p>
                      <p className="text-xs text-gray-500">
                        {backup.deleted_counts?.cash_drawers || 0} arka
                      </p>
                    </div>
                  </div>
                  <div className="flex gap-2 mt-3">
                    {!backup.restored_at && (
                      <Button
                        size="sm"
                        variant="outline"
                        className="border-green-500 text-green-600 hover:bg-green-50"
                        onClick={() => openRestoreDialog(backup)}
                      >
                        <RotateCcw className="h-3 w-3 mr-1" />
                        Rikthe
                      </Button>
                    )}
                    <Button
                      size="sm"
                      variant="outline"
                      className="border-red-300 text-red-500 hover:bg-red-50"
                      onClick={() => deleteBackup(backup.id)}
                    >
                      <Trash2 className="h-3 w-3 mr-1" />
                      Fshi
                    </Button>
                  </div>
                </div>
              ))}
            </div>
          )}

          <DialogFooter>
            <Button variant="outline" onClick={() => setShowBackupsDialog(false)}>
              Mbyll
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>

      {/* Restore Confirmation Dialog */}
      <Dialog open={showRestoreDialog} onOpenChange={setShowRestoreDialog}>
        <DialogContent className="sm:max-w-md">
          <DialogHeader>
            <DialogTitle className="flex items-center gap-2 text-green-600">
              <RotateCcw className="h-5 w-5" />
              Rikthe Backup-in
            </DialogTitle>
          </DialogHeader>

          <div className="space-y-4">
            <div className="p-4 bg-blue-50 border border-blue-200 rounded-lg">
              <p className="text-sm text-blue-800">
                Do të rikthehen të dhënat nga backup i datës:
              </p>
              <p className="text-sm font-medium text-blue-900 mt-1">
                {selectedBackup && new Date(selectedBackup.created_at).toLocaleString('sq-AL')}
              </p>
              <p className="text-xs text-blue-700 mt-2">
                {selectedBackup?.deleted_counts?.sales || 0} shitje, {selectedBackup?.deleted_counts?.cash_drawers || 0} arka
              </p>
            </div>

            <div className="space-y-2">
              <label className="text-sm font-medium flex items-center gap-2">
                <Lock className="h-4 w-4" />
                Fjalëkalimi i Administratorit
              </label>
              <Input
                type="password"
                placeholder="Shkruani fjalëkalimin..."
                value={restorePassword}
                onChange={(e) => setRestorePassword(e.target.value)}
                onKeyDown={(e) => e.key === 'Enter' && executeRestore()}
                autoFocus
              />
            </div>

            <DialogFooter>
              <Button variant="outline" onClick={() => setShowRestoreDialog(false)}>
                Anulo
              </Button>
              <Button
                onClick={executeRestore}
                disabled={backupsLoading}
                className="bg-green-600 hover:bg-green-700"
              >
                {backupsLoading ? 'Duke rikthyer...' : 'Konfirmo Rikthimin'}
              </Button>
            </DialogFooter>
          </div>
        </DialogContent>
      </Dialog>
    </div>
  );
};

export default Dashboard;
