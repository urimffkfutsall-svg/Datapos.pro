import React, { useState, useEffect } from 'react';
import { api, useAuth } from '../App';
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from '../components/ui/card';
import { Button } from '../components/ui/button';
import { Input } from '../components/ui/input';
import { Label } from '../components/ui/label';
import { Textarea } from '../components/ui/textarea';
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
  DialogFooter,
} from '../components/ui/dialog';
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '../components/ui/select';
import { 
  Building2,
  Plus,
  Edit2,
  Trash2,
  Users,
  ShoppingCart,
  ExternalLink,
  Palette,
  Image,
  Mail,
  Phone,
  MapPin,
  CreditCard,
  AlertTriangle,
  CheckCircle,
  Clock,
  UserPlus,
  Key,
  Copy,
  Eye,
  EyeOff,
  Calendar,
  Ban,
  RefreshCw, Sparkles, Globe, UserCircle, ChevronRight } from 'lucide-react';
import { toast } from 'sonner';

const SuperAdmin = () => {
  const { user } = useAuth();
  const [tenants, setTenants] = useState([]);
  const [loading, setLoading] = useState(true);
  const [showDialog, setShowDialog] = useState(false);
  const [showUserDialog, setShowUserDialog] = useState(false);
  const [showUsersListDialog, setShowUsersListDialog] = useState(false);
  const [selectedTenant, setSelectedTenant] = useState(null);
  const [tenantUsers, setTenantUsers] = useState([]);
  const [editingTenant, setEditingTenant] = useState(null);
  const [showPassword, setShowPassword] = useState(false);
  const [formData, setFormData] = useState({
    name: '',
    company_name: '',
    email: '',
    phone: '',
    address: '',
    logo_url: '',
    primary_color: '#00a79d',
    secondary_color: '#f3f4f6',
    stripe_payment_link: '',
    admin_username: '',
    admin_password: '',
    admin_full_name: '',
    subscription_months: 1
  });
  const [showSubscriptionDialog, setShowSubscriptionDialog] = useState(false);
  const [subscriptionData, setSubscriptionData] = useState({
    tenant_id: '',
    months: 1,
    action: 'extend' // extend, suspend, activate
  });
  const [userFormData, setUserFormData] = useState({
    username: '',
    password: '',
    full_name: '',
    role: 'admin',
    pin: ''
  });

  // Calculate remaining trial days
  const calculateRemainingDays = (expiresDate) => {
    if (!expiresDate) return 0;
    try {
      const expires = new Date(expiresDate);
      const now = new Date();
      const diff = expires - now;
      return Math.max(0, Math.ceil(diff / (1000 * 60 * 60 * 24)));
    } catch {
      return 0;
    }
  };

  useEffect(() => {
    loadTenants();
  }, []);

  const loadTenants = async () => {
    try {
      const response = await api.get('/tenants');
      setTenants(response.data);
    } catch (error) {
      toast.error('Gabim gjatë ngarkimit të firmave');
    } finally {
      setLoading(false);
    }
  };

  const openCreateDialog = () => {
    setEditingTenant(null);
    setFormData({
      name: '',
      company_name: '',
      email: '',
      phone: '',
      address: '',
      logo_url: '',
      primary_color: '#00a79d',
      secondary_color: '#f3f4f6',
      stripe_payment_link: '',
      admin_username: '',
      admin_password: '',
      admin_full_name: '',
      subscription_months: 1
    });
    setShowDialog(true);
  };

  const openEditDialog = (tenant) => {
    setEditingTenant(tenant);
    setFormData({
      name: tenant.name,
      company_name: tenant.company_name,
      email: tenant.email,
      phone: tenant.phone || '',
      address: tenant.address || '',
      logo_url: tenant.logo_url || '',
      primary_color: tenant.primary_color || '#00a79d',
      secondary_color: tenant.secondary_color || '#f3f4f6',
      stripe_payment_link: tenant.stripe_payment_link || '',
      admin_username: '',
      admin_password: '',
      admin_full_name: '',
      subscription_months: 1
    });
    setShowDialog(true);
  };

  const openSubscriptionDialog = (tenant) => {
    setSubscriptionData({
      tenant_id: tenant.id,
      tenant_name: tenant.company_name,
      months: 1,
      action: 'extend',
      current_expires: tenant.subscription_expires,
      current_status: tenant.status
    });
    setShowSubscriptionDialog(true);
  };

  const handleSubscriptionUpdate = async () => {
    setLoading(true);
    try {
      let newExpires;
      let newStatus = subscriptionData.current_status;
      
      if (subscriptionData.action === 'extend') {
        // Calculate new expiration date
        const baseDate = subscriptionData.current_expires 
          ? new Date(subscriptionData.current_expires) 
          : new Date();
        
        // If current date is past expiration, start from today
        if (baseDate < new Date()) {
          baseDate.setTime(new Date().getTime());
        }
        
        baseDate.setMonth(baseDate.getMonth() + parseInt(subscriptionData.months));
        newExpires = baseDate.toISOString();
        newStatus = 'active';
      } else if (subscriptionData.action === 'suspend') {
        newStatus = 'suspended';
        newExpires = subscriptionData.current_expires;
      } else if (subscriptionData.action === 'activate') {
        newStatus = 'active';
        newExpires = subscriptionData.current_expires;
      }
      
      await api.put(`/tenants/${subscriptionData.tenant_id}`, {
        subscription_expires: newExpires,
        status: newStatus
      });
      
      toast.success('Abonimi u përditësua me sukses!');
      setShowSubscriptionDialog(false);
      loadTenants();
    } catch (error) {
      toast.error('Gabim gjatë përditësimit të abonimit');
    } finally {
      setLoading(false);
    }
  };

  const handleSubmit = async () => {
    setLoading(true);
    try {
      if (editingTenant) {
        await api.put(`/tenants/${editingTenant.id}`, {
          company_name: formData.company_name,
          email: formData.email,
          phone: formData.phone,
          address: formData.address,
          logo_url: formData.logo_url,
          primary_color: formData.primary_color,
          secondary_color: formData.secondary_color,
          stripe_payment_link: formData.stripe_payment_link
        });
        toast.success('Firma u përditësua me sukses!');
      } else {
        await api.post('/tenants', formData);
        toast.success('Firma u krijua me sukses!');
      }
      setShowDialog(false);
      loadTenants();
    } catch (error) {
      toast.error(error.response?.data?.detail || 'Gabim gjatë ruajtjes');
    } finally {
      setLoading(false);
    }
  };

  const handleDelete = async (tenantId) => {
    if (!window.confirm('Jeni i sigurt? Kjo do të fshijë firmën dhe TË GJITHA të dhënat e saj!')) return;
    if (!window.confirm('KUJDES: Ky veprim NUK mund të kthehet! Konfirmoni përsëri.')) return;
    
    try {
      await api.delete(`/tenants/${tenantId}`);
      toast.success('Firma u fshi me sukses');
      loadTenants();
    } catch (error) {
      toast.error('Gabim gjatë fshirjes');
    }
  };

  const updateTenantStatus = async (tenantId, status) => {
    try {
      await api.put(`/tenants/${tenantId}`, { status });
      toast.success('Statusi u përditësua');
      loadTenants();
    } catch (error) {
      toast.error('Gabim gjatë përditësimit');
    }
  };

  const getStatusBadge = (status) => {
    switch (status) {
      case 'active':
        return <span className="px-2 py-1 text-xs bg-green-100 text-green-700 rounded-full flex items-center gap-1"><CheckCircle className="h-3 w-3" /> Aktiv</span>;
      case 'suspended':
        return <span className="px-2 py-1 text-xs bg-red-100 text-red-700 rounded-full flex items-center gap-1"><AlertTriangle className="h-3 w-3" /> Pezulluar</span>;
      case 'trial':
        return <span className="px-2 py-1 text-xs bg-yellow-100 text-yellow-700 rounded-full flex items-center gap-1"><Clock className="h-3 w-3" /> Trial</span>;
      default:
        return null;
    }
  };

  // User Management Functions
  const openUserDialog = (tenant) => {
    setSelectedTenant(tenant);
    setUserFormData({
      username: '',
      password: '',
      full_name: '',
      role: 'admin',
      pin: ''
    });
    setShowUserDialog(true);
  };

  const openUsersListDialog = async (tenant) => {
    setSelectedTenant(tenant);
    setShowUsersListDialog(true);
    try {
      const response = await api.get(`/tenants/${tenant.id}/users`);
      setTenantUsers(response.data);
    } catch (error) {
      toast.error('Gabim gjatë ngarkimit të përdoruesve');
      setTenantUsers([]);
    }
  };

  const handleCreateUser = async () => {
    if (!userFormData.username || !userFormData.password || !userFormData.full_name) {
      toast.error('Plotësoni të gjitha fushat e detyrueshme');
      return;
    }
    
    setLoading(true);
    try {
      await api.post(`/tenants/${selectedTenant.id}/users`, userFormData);
      toast.success('Përdoruesi u krijua me sukses!');
      setShowUserDialog(false);
      loadTenants();
    } catch (error) {
      toast.error(error.response?.data?.detail || 'Gabim gjatë krijimit');
    } finally {
      setLoading(false);
    }
  };

  const handleDeleteUser = async (userId) => {
    if (!window.confirm('Jeni i sigurt që doni të fshini këtë përdorues?')) return;
    
    try {
      await api.delete(`/tenants/${selectedTenant.id}/users/${userId}`);
      toast.success('Përdoruesi u fshi');
      // Refresh user list
      const response = await api.get(`/tenants/${selectedTenant.id}/users`);
      setTenantUsers(response.data);
      loadTenants();
    } catch (error) {
      toast.error('Gabim gjatë fshirjes');
    }
  };

  const copyToClipboard = (text) => {
    navigator.clipboard.writeText(text);
    toast.success('U kopjua!');
  };

  if (user?.role !== 'super_admin') {
    return (
      <div className="flex items-center justify-center h-full">
        <Card className="p-8 text-center">
          <AlertTriangle className="h-12 w-12 text-red-500 mx-auto mb-4" />
          <h2 className="text-xl font-bold mb-2">Akses i Ndaluar</h2>
          <p className="text-gray-500">Vetëm Super Admin ka akses në këtë faqe.</p>
        </Card>
      </div>
    );
  }

  return (
    <div className="space-y-6" data-testid="super-admin-page">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-gray-900">Menaxhimi i Firmave</h1>
          <p className="text-gray-500">Shto, edito dhe menaxho firmat që përdorin sistemin</p>
        </div>
        <Button 
          className="bg-[#00a79d] hover:bg-[#008f86]"
          onClick={openCreateDialog}
          data-testid="add-tenant-btn"
        >
          <Plus className="h-4 w-4 mr-2" />
          Shto Firmë të Re
        </Button>
      </div>

      {/* Stats */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
        <Card className="border-0 shadow-sm">
          <CardContent className="pt-6">
            <div className="flex items-center gap-4">
              <div className="p-3 bg-blue-100 rounded-lg">
                <Building2 className="h-6 w-6 text-blue-600" />
              </div>
              <div>
                <p className="text-2xl font-bold">{tenants.length}</p>
                <p className="text-sm text-gray-500">Firma Totale</p>
              </div>
            </div>
          </CardContent>
        </Card>
        <Card className="border-0 shadow-sm">
          <CardContent className="pt-6">
            <div className="flex items-center gap-4">
              <div className="p-3 bg-green-100 rounded-lg">
                <CheckCircle className="h-6 w-6 text-green-600" />
              </div>
              <div>
                <p className="text-2xl font-bold">{tenants.filter(t => t.status === 'active').length}</p>
                <p className="text-sm text-gray-500">Aktive</p>
              </div>
            </div>
          </CardContent>
        </Card>
        <Card className="border-0 shadow-sm">
          <CardContent className="pt-6">
            <div className="flex items-center gap-4">
              <div className="p-3 bg-yellow-100 rounded-lg">
                <Clock className="h-6 w-6 text-yellow-600" />
              </div>
              <div>
                <p className="text-2xl font-bold">{tenants.filter(t => t.status === 'trial').length}</p>
                <p className="text-sm text-gray-500">Trial</p>
              </div>
            </div>
          </CardContent>
        </Card>
        <Card className="border-0 shadow-sm">
          <CardContent className="pt-6">
            <div className="flex items-center gap-4">
              <div className="p-3 bg-purple-100 rounded-lg">
                <Users className="h-6 w-6 text-purple-600" />
              </div>
              <div>
                <p className="text-2xl font-bold">{tenants.reduce((sum, t) => sum + (t.users_count || 0), 0)}</p>
                <p className="text-sm text-gray-500">Përdorues Total</p>
              </div>
            </div>
          </CardContent>
        </Card>
      </div>

      {/* Tenants List */}
      <Card className="border-0 shadow-sm">
        <CardHeader>
          <CardTitle>Lista e Firmave</CardTitle>
        </CardHeader>
        <CardContent>
          {loading ? (
            <div className="flex justify-center py-8">
              <div className="spinner" />
            </div>
          ) : tenants.length === 0 ? (
            <div className="text-center py-12">
              <Building2 className="h-16 w-16 text-gray-300 mx-auto mb-4" />
              <p className="text-gray-500">Ende nuk ka firma të regjistruara</p>
              <Button className="mt-4" onClick={openCreateDialog}>
                <Plus className="h-4 w-4 mr-2" />
                Shto Firmën e Parë
              </Button>
            </div>
          ) : (
            <div className="space-y-4">
              {tenants.map((tenant) => (
                <div 
                  key={tenant.id}
                  className="border rounded-lg p-4 hover:shadow-md transition-shadow"
                  style={{ borderLeftColor: tenant.primary_color, borderLeftWidth: '4px' }}
                >
                  <div className="flex items-start justify-between">
                    <div className="flex items-start gap-4">
                      {tenant.logo_url ? (
                        <img src={tenant.logo_url} alt="" className="h-12 w-12 object-contain rounded" />
                      ) : (
                        <div 
                          className="h-12 w-12 rounded flex items-center justify-center text-white font-bold"
                          style={{ backgroundColor: tenant.primary_color }}
                        >
                          {tenant.company_name?.charAt(0) || 'F'}
                        </div>
                      )}
                      <div>
                        <div className="flex items-center gap-2">
                          <h3 className="font-semibold text-lg">{tenant.company_name}</h3>
                          {getStatusBadge(tenant.status)}
                        </div>
                        <p className="text-sm text-gray-500">{tenant.name}.app.com</p>
                        <div className="flex items-center gap-4 mt-2 text-sm text-gray-600">
                          <span className="flex items-center gap-1">
                            <Mail className="h-3 w-3" /> {tenant.email}
                          </span>
                          {tenant.phone && (
                            <span className="flex items-center gap-1">
                              <Phone className="h-3 w-3" /> {tenant.phone}
                            </span>
                          )}
                        </div>
                      </div>
                    </div>
                    <div className="flex items-center gap-2">
                      <div className="text-right mr-4">
                        <p className="text-sm"><Users className="h-3 w-3 inline mr-1" />{tenant.users_count || 0} përdorues</p>
                        <p className="text-sm"><ShoppingCart className="h-3 w-3 inline mr-1" />{tenant.sales_count || 0} shitje</p>
                        {tenant.subscription_expires && (
                          <p className={`text-xs mt-1 ${calculateRemainingDays(tenant.subscription_expires) <= 7 ? 'text-red-600 font-semibold' : calculateRemainingDays(tenant.subscription_expires) <= 30 ? 'text-orange-600' : 'text-green-600'}`}>
                            <Calendar className="h-3 w-3 inline mr-1" />
                            Abonimi: {calculateRemainingDays(tenant.subscription_expires)} ditë
                          </p>
                        )}
                      </div>
                      <Button 
                        variant="outline" 
                        size="sm"
                        className="text-purple-500 hover:bg-purple-50"
                        onClick={() => openSubscriptionDialog(tenant)}
                        title="Menaxho Abonimin"
                      >
                        <Calendar className="h-4 w-4" />
                      </Button>
                      <Select 
                        value={tenant.status} 
                        onValueChange={(value) => updateTenantStatus(tenant.id, value)}
                      >
                        <SelectTrigger className="w-28 h-8">
                          <SelectValue />
                        </SelectTrigger>
                        <SelectContent>
                          <SelectItem value="active">Aktiv</SelectItem>
                          <SelectItem value="trial">Trial</SelectItem>
                          <SelectItem value="suspended">Pezullo</SelectItem>
                        </SelectContent>
                      </Select>
                      <Button variant="outline" size="sm" onClick={() => openEditDialog(tenant)}>
                        <Edit2 className="h-4 w-4" />
                      </Button>
                      <Button 
                        variant="outline" 
                        size="sm"
                        className="text-blue-500 hover:bg-blue-50"
                        onClick={() => openUserDialog(tenant)}
                        title="Shto Përdorues"
                      >
                        <UserPlus className="h-4 w-4" />
                      </Button>
                      <Button 
                        variant="outline" 
                        size="sm"
                        onClick={() => openUsersListDialog(tenant)}
                        title="Shiko Përdoruesit"
                      >
                        <Users className="h-4 w-4" />
                      </Button>
                      <Button 
                        variant="outline" 
                        size="sm" 
                        className="text-red-500 hover:bg-red-50"
                        onClick={() => handleDelete(tenant.id)}
                      >
                        <Trash2 className="h-4 w-4" />
                      </Button>
                    </div>
                  </div>
                  {tenant.stripe_payment_link && (
                    <div className="mt-3 pt-3 border-t">
                      <a 
                        href={tenant.stripe_payment_link} 
                        target="_blank" 
                        rel="noopener noreferrer"
                        className="text-sm text-blue-600 hover:underline flex items-center gap-1"
                      >
                        <CreditCard className="h-3 w-3" /> Link Pagese Stripe
                        <ExternalLink className="h-3 w-3" />
                      </a>
                    </div>
                  )}
                </div>
              ))}
            </div>
          )}
        </CardContent>
      </Card>

      {/* Add/Edit Dialog */}
      <Dialog open={showDialog} onOpenChange={setShowDialog}>
        <DialogContent className="sm:max-w-4xl max-h-[92vh] overflow-y-auto p-0 rounded-3xl border-0 shadow-2xl">
          {/* Hero header */}
          <div className="bg-gradient-to-br from-[#00a79d] via-[#009891] to-[#007a73] p-7 text-white relative overflow-hidden">
            <div className="absolute -right-12 -top-12 w-48 h-48 bg-white/10 rounded-full blur-3xl pointer-events-none" />
            <div className="absolute right-20 top-16 w-32 h-32 bg-white/5 rounded-full blur-2xl pointer-events-none" />
            <div className="relative flex items-center gap-4">
              <div className="w-16 h-16 rounded-2xl bg-white/20 backdrop-blur-sm flex items-center justify-center border border-white/30 shadow-lg">
                {editingTenant ? <Edit2 className="h-8 w-8 text-white" /> : <Sparkles className="h-8 w-8 text-white" />}
              </div>
              <div>
                <DialogTitle className="text-2xl font-bold text-white tracking-tight">
                  {editingTenant ? 'Edito Firmën' : 'Shto Firmë të Re'}
                </DialogTitle>
                <p className="text-white/85 text-sm mt-1">
                  {editingTenant ? 'Përditëso të dhënat e firmës ekzistuese' : 'Krijo një firmë të re me vetëm pak hapa të shpejtë'}
                </p>
              </div>
            </div>
          </div>

          {/* Body */}
          <div className="p-6 space-y-5 bg-gradient-to-b from-gray-50/60 to-white">

            {/* Section 1: Informacioni i Firmës */}
            <div className="bg-white rounded-2xl p-5 shadow-sm border border-gray-100">
              <div className="flex items-center gap-2.5 mb-5">
                <div className="w-9 h-9 rounded-xl bg-[#00a79d]/10 flex items-center justify-center">
                  <Building2 className="h-4 w-4 text-[#00a79d]" />
                </div>
                <div>
                  <h3 className="font-semibold text-gray-900">Informacioni i Firmës</h3>
                  <p className="text-xs text-gray-500">Të dhënat bazë të identifikimit</p>
                </div>
              </div>

              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                <div>
                  <Label className="text-xs font-medium text-gray-700 mb-1.5 block">
                    Identifikuesi (subdomain) <span className="text-[#00a79d]">*</span>
                  </Label>
                  <div className="relative">
                    <Globe className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-gray-400 pointer-events-none" />
                    <Input
                      value={formData.name}
                      onChange={(e) => setFormData({...formData, name: e.target.value.toLowerCase().replace(/[^a-z0-9]/g, '')})}
                      placeholder="p.sh. mobilshopurimi"
                      disabled={editingTenant}
                      className="pl-9 rounded-xl bg-gray-50 border-gray-200 focus-visible:ring-2 focus-visible:ring-[#00a79d]/30 focus-visible:border-[#00a79d] disabled:bg-gray-100"
                    />
                  </div>
                  <p className="text-xs text-gray-500 mt-1.5 flex items-center gap-1">
                    <ChevronRight className="h-3 w-3" />
                    <span className="font-mono">{formData.name || 'firma'}.app.com</span>
                  </p>
                </div>

                <div>
                  <Label className="text-xs font-medium text-gray-700 mb-1.5 block">
                    Emri i Kompanisë <span className="text-[#00a79d]">*</span>
                  </Label>
                  <div className="relative">
                    <Building2 className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-gray-400 pointer-events-none" />
                    <Input
                      value={formData.company_name}
                      onChange={(e) => setFormData({...formData, company_name: e.target.value})}
                      placeholder="p.sh. Mobilshopurimi SH.P.K"
                      className="pl-9 rounded-xl bg-gray-50 border-gray-200 focus-visible:ring-2 focus-visible:ring-[#00a79d]/30 focus-visible:border-[#00a79d]"
                    />
                  </div>
                </div>

                <div>
                  <Label className="text-xs font-medium text-gray-700 mb-1.5 block">
                    Email <span className="text-[#00a79d]">*</span>
                  </Label>
                  <div className="relative">
                    <Mail className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-gray-400 pointer-events-none" />
                    <Input
                      type="email"
                      value={formData.email}
                      onChange={(e) => setFormData({...formData, email: e.target.value})}
                      placeholder="info@kompania.com"
                      className="pl-9 rounded-xl bg-gray-50 border-gray-200 focus-visible:ring-2 focus-visible:ring-[#00a79d]/30 focus-visible:border-[#00a79d]"
                    />
                  </div>
                </div>

                <div>
                  <Label className="text-xs font-medium text-gray-700 mb-1.5 block">Telefoni</Label>
                  <div className="relative">
                    <Phone className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-gray-400 pointer-events-none" />
                    <Input
                      value={formData.phone}
                      onChange={(e) => setFormData({...formData, phone: e.target.value})}
                      placeholder="+383 44 123 456"
                      className="pl-9 rounded-xl bg-gray-50 border-gray-200 focus-visible:ring-2 focus-visible:ring-[#00a79d]/30 focus-visible:border-[#00a79d]"
                    />
                  </div>
                </div>

                <div className="md:col-span-2">
                  <Label className="text-xs font-medium text-gray-700 mb-1.5 block">Adresa</Label>
                  <div className="relative">
                    <MapPin className="absolute left-3 top-3 h-4 w-4 text-gray-400 pointer-events-none" />
                    <Textarea
                      value={formData.address}
                      onChange={(e) => setFormData({...formData, address: e.target.value})}
                      placeholder="Rruga, Qyteti, Shteti"
                      rows={2}
                      className="pl-9 rounded-xl bg-gray-50 border-gray-200 focus-visible:ring-2 focus-visible:ring-[#00a79d]/30 focus-visible:border-[#00a79d] resize-none"
                    />
                  </div>
                </div>
              </div>
            </div>

            {/* Section 2: Branding & Pagesa */}
            <div className="bg-white rounded-2xl p-5 shadow-sm border border-gray-100">
              <div className="flex items-center gap-2.5 mb-5">
                <div className="w-9 h-9 rounded-xl bg-purple-100 flex items-center justify-center">
                  <Palette className="h-4 w-4 text-purple-600" />
                </div>
                <div>
                  <h3 className="font-semibold text-gray-900">Branding & Pagesa</h3>
                  <p className="text-xs text-gray-500">Identiteti vizual dhe metoda e pagesës</p>
                </div>
              </div>

              <div className="space-y-4">
                <div>
                  <Label className="text-xs font-medium text-gray-700 mb-1.5 block">URL e Logos</Label>
                  <div className="flex items-center gap-3">
                    <div className="flex-1 relative">
                      <Globe className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-gray-400 pointer-events-none" />
                      <Input
                        value={formData.logo_url}
                        onChange={(e) => setFormData({...formData, logo_url: e.target.value})}
                        placeholder="https://example.com/logo.png"
                        className="pl-9 rounded-xl bg-gray-50 border-gray-200 focus-visible:ring-2 focus-visible:ring-[#00a79d]/30 focus-visible:border-[#00a79d]"
                      />
                    </div>
                    <div className="w-14 h-14 rounded-xl border-2 border-dashed border-gray-200 bg-gray-50 flex items-center justify-center overflow-hidden shrink-0">
                      {formData.logo_url ? (
                        <img src={formData.logo_url} alt="" className="w-full h-full object-contain" onError={(e) => e.target.style.display = 'none'} />
                      ) : (
                        <Building2 className="h-5 w-5 text-gray-300" />
                      )}
                    </div>
                  </div>
                </div>

                <div className="grid grid-cols-2 gap-4">
                  <div>
                    <Label className="text-xs font-medium text-gray-700 mb-1.5 block">Ngjyra Primare</Label>
                    <div className="flex gap-2 items-center bg-gray-50 border border-gray-200 rounded-xl p-1.5">
                      <input
                        type="color"
                        value={formData.primary_color}
                        onChange={(e) => setFormData({...formData, primary_color: e.target.value})}
                        className="w-10 h-10 rounded-lg cursor-pointer border-0 bg-transparent"
                      />
                      <input
                        value={formData.primary_color}
                        onChange={(e) => setFormData({...formData, primary_color: e.target.value})}
                        className="flex-1 bg-transparent border-0 outline-none font-mono text-sm text-gray-700"
                      />
                    </div>
                  </div>
                  <div>
                    <Label className="text-xs font-medium text-gray-700 mb-1.5 block">Ngjyra Sekondare</Label>
                    <div className="flex gap-2 items-center bg-gray-50 border border-gray-200 rounded-xl p-1.5">
                      <input
                        type="color"
                        value={formData.secondary_color}
                        onChange={(e) => setFormData({...formData, secondary_color: e.target.value})}
                        className="w-10 h-10 rounded-lg cursor-pointer border-0 bg-transparent"
                      />
                      <input
                        value={formData.secondary_color}
                        onChange={(e) => setFormData({...formData, secondary_color: e.target.value})}
                        className="flex-1 bg-transparent border-0 outline-none font-mono text-sm text-gray-700"
                      />
                    </div>
                  </div>
                </div>

                <div>
                  <Label className="text-xs font-medium text-gray-700 mb-1.5 block">Link Pagese Stripe</Label>
                  <div className="relative">
                    <CreditCard className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-gray-400 pointer-events-none" />
                    <Input
                      value={formData.stripe_payment_link}
                      onChange={(e) => setFormData({...formData, stripe_payment_link: e.target.value})}
                      placeholder="https://buy.stripe.com/..."
                      className="pl-9 rounded-xl bg-gray-50 border-gray-200 focus-visible:ring-2 focus-visible:ring-[#00a79d]/30 focus-visible:border-[#00a79d]"
                    />
                  </div>
                </div>
              </div>
            </div>

            {!editingTenant && (
              <>
                {/* Section 3: Admin i Firmës */}
                <div className="bg-white rounded-2xl p-5 shadow-sm border border-gray-100">
                  <div className="flex items-center gap-2.5 mb-5">
                    <div className="w-9 h-9 rounded-xl bg-blue-100 flex items-center justify-center">
                      <UserCircle className="h-4 w-4 text-blue-600" />
                    </div>
                    <div>
                      <h3 className="font-semibold text-gray-900">Admin i Firmës</h3>
                      <p className="text-xs text-gray-500">Krijo llogarinë e administratorit kryesor</p>
                    </div>
                  </div>

                  <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                    <div>
                      <Label className="text-xs font-medium text-gray-700 mb-1.5 block">
                        Emri i Plotë <span className="text-[#00a79d]">*</span>
                      </Label>
                      <div className="relative">
                        <UserCircle className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-gray-400 pointer-events-none" />
                        <Input
                          value={formData.admin_full_name}
                          onChange={(e) => setFormData({...formData, admin_full_name: e.target.value})}
                          placeholder="Emri Mbiemri"
                          className="pl-9 rounded-xl bg-gray-50 border-gray-200 focus-visible:ring-2 focus-visible:ring-[#00a79d]/30 focus-visible:border-[#00a79d]"
                        />
                      </div>
                    </div>
                    <div>
                      <Label className="text-xs font-medium text-gray-700 mb-1.5 block">
                        Username <span className="text-[#00a79d]">*</span>
                      </Label>
                      <div className="relative">
                        <Users className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-gray-400 pointer-events-none" />
                        <Input
                          value={formData.admin_username}
                          onChange={(e) => setFormData({...formData, admin_username: e.target.value})}
                          placeholder="admin_firma"
                          className="pl-9 rounded-xl bg-gray-50 border-gray-200 focus-visible:ring-2 focus-visible:ring-[#00a79d]/30 focus-visible:border-[#00a79d]"
                        />
                      </div>
                    </div>
                    <div>
                      <Label className="text-xs font-medium text-gray-700 mb-1.5 block">
                        Fjalëkalimi <span className="text-[#00a79d]">*</span>
                      </Label>
                      <div className="relative">
                        <Key className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-gray-400 pointer-events-none" />
                        <Input
                          type="password"
                          value={formData.admin_password}
                          onChange={(e) => setFormData({...formData, admin_password: e.target.value})}
                          placeholder="••••••••"
                          className="pl-9 rounded-xl bg-gray-50 border-gray-200 focus-visible:ring-2 focus-visible:ring-[#00a79d]/30 focus-visible:border-[#00a79d]"
                        />
                      </div>
                    </div>
                  </div>
                </div>

                {/* Section 4: Plani i Abonimit */}
                <div className="bg-white rounded-2xl p-5 shadow-sm border border-gray-100">
                  <div className="flex items-center gap-2.5 mb-5">
                    <div className="w-9 h-9 rounded-xl bg-amber-100 flex items-center justify-center">
                      <Calendar className="h-4 w-4 text-amber-600" />
                    </div>
                    <div>
                      <h3 className="font-semibold text-gray-900">Plani i Abonimit</h3>
                      <p className="text-xs text-gray-500">Zgjidh kohëzgjatjen e abonimit fillestar</p>
                    </div>
                  </div>

                  <div className="grid grid-cols-2 md:grid-cols-4 gap-3">
                    {[
                      { months: 1,  price: 20,  label: '1 Muaj',  perMonth: '20€/muaj' },
                      { months: 3,  price: 60,  label: '3 Muaj',  perMonth: '20€/muaj' },
                      { months: 6,  price: 120, label: '6 Muaj',  perMonth: '20€/muaj' },
                      { months: 12, price: 150, label: '12 Muaj', perMonth: '12.5€/muaj', badge: 'Kursim 80€' },
                    ].map((plan) => {
                      const selected = formData.subscription_months === plan.months;
                      return (
                        <button
                          type="button"
                          key={plan.months}
                          onClick={() => setFormData({...formData, subscription_months: plan.months})}
                          className={`relative text-left p-4 rounded-2xl border-2 transition-all ${selected ? 'border-[#00a79d] bg-[#00a79d]/5 shadow-md shadow-[#00a79d]/20' : 'border-gray-200 bg-white hover:border-[#00a79d]/40 hover:bg-gray-50'}`}
                        >
                          {plan.badge && (
                            <span className="absolute -top-2 left-3 text-[10px] font-bold bg-gradient-to-r from-amber-500 to-orange-500 text-white px-2 py-0.5 rounded-full shadow">
                              {plan.badge}
                            </span>
                          )}
                          {selected && (
                            <CheckCircle className="absolute top-2 right-2 h-4 w-4 text-[#00a79d]" />
                          )}
                          <p className="text-xs font-medium text-gray-500">{plan.label}</p>
                          <p className="text-2xl font-bold text-gray-900 mt-1">{plan.price}€</p>
                          <p className="text-xs text-gray-400 mt-0.5">{plan.perMonth}</p>
                        </button>
                      );
                    })}
                  </div>
                </div>
              </>
            )}
          </div>

          {/* Footer */}
          <div className="bg-white border-t border-gray-100 px-6 py-4 flex items-center justify-between gap-3">
            <p className="text-xs text-gray-400 flex items-center gap-1.5">
              <Sparkles className="h-3 w-3 text-[#00a79d]" />
              <span>Fuqizuar nga DataPOS AI</span>
            </p>
            <div className="flex gap-2">
              <Button variant="outline" onClick={() => setShowDialog(false)} className="rounded-xl border-gray-200 hover:bg-gray-50">
                Anulo
              </Button>
              <Button
                onClick={handleSubmit}
                className="bg-gradient-to-r from-[#00a79d] to-[#008f86] hover:from-[#008f86] hover:to-[#007a73] text-white rounded-xl shadow-lg shadow-[#00a79d]/30 transition-all"
                disabled={loading || !formData.name || !formData.company_name || !formData.email || (!editingTenant && (!formData.admin_username || !formData.admin_password || !formData.admin_full_name))}
              >
                {loading ? (
                  <span className="flex items-center gap-2">
                    <div className="spinner border-white border-t-transparent w-4 h-4" />
                    Duke ruajtur...
                  </span>
                ) : (
                  <span className="flex items-center gap-2">
                    {editingTenant ? <Edit2 className="h-4 w-4" /> : <Sparkles className="h-4 w-4" />}
                    {editingTenant ? 'Ruaj Ndryshimet' : 'Krijo Firmën'}
                  </span>
                )}
              </Button>
            </div>
          </div>
        </DialogContent>
      </Dialog>

      {/* Add User Dialog */}
      <Dialog open={showUserDialog} onOpenChange={setShowUserDialog}>
        <DialogContent className="sm:max-w-md">
          <DialogHeader>
            <DialogTitle className="flex items-center gap-2">
              <UserPlus className="h-5 w-5" />
              Shto Përdorues për {selectedTenant?.company_name}
            </DialogTitle>
          </DialogHeader>
          
          <div className="space-y-4">
            <div>
              <Label>Emri i Plotë *</Label>
              <Input
                value={userFormData.full_name}
                onChange={(e) => setUserFormData({...userFormData, full_name: e.target.value})}
                placeholder="Emri Mbiemri"
              />
            </div>
            
            <div>
              <Label>Username *</Label>
              <Input
                value={userFormData.username}
                onChange={(e) => setUserFormData({...userFormData, username: e.target.value})}
                placeholder="username"
              />
            </div>
            
            <div>
              <Label>Fjalëkalimi *</Label>
              <div className="relative">
                <Input
                  type={showPassword ? "text" : "password"}
                  value={userFormData.password}
                  onChange={(e) => setUserFormData({...userFormData, password: e.target.value})}
                  placeholder="••••••••"
                />
                <button 
                  type="button"
                  className="absolute right-2 top-1/2 -translate-y-1/2 text-gray-400 hover:text-gray-600"
                  onClick={() => setShowPassword(!showPassword)}
                >
                  {showPassword ? <EyeOff className="h-4 w-4" /> : <Eye className="h-4 w-4" />}
                </button>
              </div>
            </div>
            
            <div>
              <Label>PIN (Opsional - për kyçje të shpejtë)</Label>
              <Input
                value={userFormData.pin}
                onChange={(e) => setUserFormData({...userFormData, pin: e.target.value.replace(/\D/g, '').slice(0, 4)})}
                placeholder="4 shifra"
                maxLength={4}
              />
            </div>
            
            <div>
              <Label>Roli *</Label>
              <Select 
                value={userFormData.role} 
                onValueChange={(value) => setUserFormData({...userFormData, role: value})}
              >
                <SelectTrigger>
                  <SelectValue />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="admin">Administrator</SelectItem>
                  <SelectItem value="cashier">Arkëtar</SelectItem>
                </SelectContent>
              </Select>
            </div>
          </div>
          
          <DialogFooter className="mt-6">
            <Button variant="outline" onClick={() => setShowUserDialog(false)}>Anulo</Button>
            <Button 
              onClick={handleCreateUser} 
              className="bg-[#00a79d] hover:bg-[#008f86]"
              disabled={loading || !userFormData.username || !userFormData.password || !userFormData.full_name}
            >
              {loading ? 'Duke krijuar...' : 'Krijo Përdoruesin'}
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>

      {/* Users List Dialog */}
      <Dialog open={showUsersListDialog} onOpenChange={setShowUsersListDialog}>
        <DialogContent className="sm:max-w-2xl max-h-[80vh] overflow-y-auto">
          <DialogHeader>
            <DialogTitle className="flex items-center gap-2">
              <Users className="h-5 w-5" />
              Përdoruesit e {selectedTenant?.company_name}
            </DialogTitle>
          </DialogHeader>
          
          <div className="space-y-3">
            {tenantUsers.length === 0 ? (
              <p className="text-center text-gray-500 py-8">Nuk ka përdorues</p>
            ) : (
              tenantUsers.map((u) => (
                <div key={u.id} className="flex items-center justify-between p-3 border rounded-lg">
                  <div className="flex items-center gap-3">
                    <div className={`h-10 w-10 rounded-full flex items-center justify-center text-white font-medium ${u.role === 'admin' ? 'bg-purple-500' : 'bg-blue-500'}`}>
                      {u.full_name?.charAt(0) || u.username?.charAt(0) || '?'}
                    </div>
                    <div>
                      <p className="font-medium">{u.full_name || u.username}</p>
                      <div className="flex items-center gap-2 text-sm text-gray-500">
                        <span className="flex items-center gap-1">
                          <Key className="h-3 w-3" /> {u.username}
                        </span>
                        {u.pin && (
                          <span className="text-xs bg-gray-100 px-2 py-0.5 rounded">PIN: {u.pin}</span>
                        )}
                      </div>
                    </div>
                  </div>
                  <div className="flex items-center gap-2">
                    <span className={`px-2 py-1 text-xs rounded ${u.role === 'admin' ? 'bg-purple-100 text-purple-700' : 'bg-blue-100 text-blue-700'}`}>
                      {u.role === 'admin' ? 'Admin' : 'Arkëtar'}
                    </span>
                    <Button 
                      variant="ghost" 
                      size="sm"
                      onClick={() => copyToClipboard(`Username: ${u.username}\nPassword: (të njëjtin që vendosët)\n${u.pin ? `PIN: ${u.pin}` : ''}`)}
                      title="Kopjo kredencialet"
                    >
                      <Copy className="h-4 w-4" />
                    </Button>
                    <Button 
                      variant="ghost" 
                      size="sm"
                      className="text-red-500 hover:bg-red-50"
                      onClick={() => handleDeleteUser(u.id)}
                    >
                      <Trash2 className="h-4 w-4" />
                    </Button>
                  </div>
                </div>
              ))
            )}
          </div>
          
          <DialogFooter className="mt-4">
            <Button variant="outline" onClick={() => setShowUsersListDialog(false)}>Mbyll</Button>
            <Button 
              onClick={() => {
                setShowUsersListDialog(false);
                openUserDialog(selectedTenant);
              }}
              className="bg-[#00a79d] hover:bg-[#008f86]"
            >
              <UserPlus className="h-4 w-4 mr-2" />
              Shto Përdorues të Ri
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>

      {/* Subscription Management Dialog */}
      <Dialog open={showSubscriptionDialog} onOpenChange={setShowSubscriptionDialog}>
        <DialogContent className="sm:max-w-md">
          <DialogHeader>
            <DialogTitle className="flex items-center gap-2">
              <Calendar className="h-5 w-5 text-purple-500" />
              Menaxho Abonimin
            </DialogTitle>
          </DialogHeader>
          
          <div className="space-y-4">
            <div className="bg-gray-50 rounded-lg p-4">
              <p className="font-medium text-gray-900">{subscriptionData.tenant_name}</p>
              <div className="mt-2 space-y-1 text-sm">
                <p className="text-gray-600">
                  Statusi aktual: 
                  <span className={`ml-2 px-2 py-0.5 rounded text-xs ${
                    subscriptionData.current_status === 'active' ? 'bg-green-100 text-green-700' :
                    subscriptionData.current_status === 'suspended' ? 'bg-red-100 text-red-700' :
                    'bg-yellow-100 text-yellow-700'
                  }`}>
                    {subscriptionData.current_status === 'active' ? 'Aktiv' : 
                     subscriptionData.current_status === 'suspended' ? 'Pezulluar' : 'Trial'}
                  </span>
                </p>
                {subscriptionData.current_expires && (
                  <p className="text-gray-600">
                    Skadon: 
                    <span className={`ml-2 font-medium ${calculateRemainingDays(subscriptionData.current_expires) <= 7 ? 'text-red-600' : 'text-gray-900'}`}>
                      {new Date(subscriptionData.current_expires).toLocaleDateString('sq-AL')}
                      ({calculateRemainingDays(subscriptionData.current_expires)} ditë)
                    </span>
                  </p>
                )}
              </div>
            </div>

            <div>
              <Label>Veprimi</Label>
              <Select 
                value={subscriptionData.action} 
                onValueChange={(value) => setSubscriptionData({...subscriptionData, action: value})}
              >
                <SelectTrigger>
                  <SelectValue />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="extend">
                    <span className="flex items-center gap-2">
                      <RefreshCw className="h-4 w-4 text-green-500" />
                      Zgjat Abonimin
                    </span>
                  </SelectItem>
                  <SelectItem value="suspend">
                    <span className="flex items-center gap-2">
                      <Ban className="h-4 w-4 text-red-500" />
                      Pezullo Abonimin
                    </span>
                  </SelectItem>
                  <SelectItem value="activate">
                    <span className="flex items-center gap-2">
                      <CheckCircle className="h-4 w-4 text-green-500" />
                      Aktivizo Përsëri
                    </span>
                  </SelectItem>
                </SelectContent>
              </Select>
            </div>

            {subscriptionData.action === 'extend' && (
              <div>
                <Label>Shto Muaj</Label>
                <Select 
                  value={subscriptionData.months.toString()} 
                  onValueChange={(value) => setSubscriptionData({...subscriptionData, months: parseInt(value)})}
                >
                  <SelectTrigger>
                    <SelectValue />
                  </SelectTrigger>
                  <SelectContent>
                    <SelectItem value="1">1 Muaj - 20€</SelectItem>
                    <SelectItem value="3">3 Muaj - 60€</SelectItem>
                    <SelectItem value="6">6 Muaj - 120€</SelectItem>
                    <SelectItem value="12">12 Muaj - 150€ (Kurseni 80€)</SelectItem>
                  </SelectContent>
                </Select>
                <p className="text-xs text-gray-500 mt-2">
                  Data e re e skadimit: {(() => {
                    const baseDate = subscriptionData.current_expires 
                      ? new Date(subscriptionData.current_expires) 
                      : new Date();
                    if (baseDate < new Date()) baseDate.setTime(new Date().getTime());
                    baseDate.setMonth(baseDate.getMonth() + parseInt(subscriptionData.months));
                    return baseDate.toLocaleDateString('sq-AL');
                  })()}
                </p>
              </div>
            )}

            {subscriptionData.action === 'suspend' && (
              <div className="bg-red-50 border border-red-200 rounded-lg p-3">
                <p className="text-sm text-red-700">
                  <AlertTriangle className="h-4 w-4 inline mr-1" />
                  Pezullimi do të bllokojë aksesin e të gjithë përdoruesve të kësaj firme në sistem.
                </p>
              </div>
            )}
          </div>
          
          <DialogFooter className="mt-6">
            <Button variant="outline" onClick={() => setShowSubscriptionDialog(false)}>Anulo</Button>
            <Button 
              onClick={handleSubscriptionUpdate}
              className={subscriptionData.action === 'suspend' ? 'bg-red-500 hover:bg-red-600' : 'bg-[#00a79d] hover:bg-[#008f86]'}
              disabled={loading}
            >
              {loading ? 'Duke përditësuar...' : 
               subscriptionData.action === 'extend' ? 'Zgjat Abonimin' :
               subscriptionData.action === 'suspend' ? 'Pezullo' : 'Aktivizo'}
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>
    </div>
  );
};

export default SuperAdmin;
