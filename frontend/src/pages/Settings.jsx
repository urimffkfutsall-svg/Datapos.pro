import React, { useState, useEffect } from 'react';
import { api } from '../App';
import CouponsTab from '../components/CouponsTab';
import { toast } from 'sonner';
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from '../components/ui/card';
import { Button } from '../components/ui/button';
import { Input } from '../components/ui/input';
import { Label } from '../components/ui/label';
import { Textarea } from '../components/ui/textarea';
import { Switch } from '../components/ui/switch';
import { Separator } from '../components/ui/separator';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '../components/ui/tabs';
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '../components/ui/select';
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from '../components/ui/table';
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
  DialogFooter,
} from '../components/ui/dialog';
import {
  Building2,
  Store,
  Warehouse,
  FileText,
  Receipt,
  Percent,
  Save,
  Plus,
  Edit2,
  Trash2,
  Upload,
  FolderOpen,
  MessageSquare,
  Shield
} from 'lucide-react';

const Settings = () => {
  const [activeTab, setActiveTab] = useState('kompania');
  const [loading, setLoading] = useState(false);
  const [branches, setBranches] = useState([]);
  const [showBranchDialog, setShowBranchDialog] = useState(false);
  const [editingBranch, setEditingBranch] = useState(null);
  
  // Comment Templates
  const [commentTemplates, setCommentTemplates] = useState([]);
  const [showCommentDialog, setShowCommentDialog] = useState(false);
  const [editingComment, setEditingComment] = useState(null);
  const [commentForm, setCommentForm] = useState({
    title: '',
    content: '',
    is_default: false,
    is_active: true
  });
  
  // Company settings
  const [companyData, setCompanyData] = useState({
    company_name: '',
    nui: '',
    nf: '',
    vat_number: '',
    phone: '',
    email: '',
    address: '',
    city: '',
    postal_code: '',
    bank_name: '',
    bank_account: '',
    website: '',
    logo_url: '',
    stamp_url: '',
    whatsapp_qr_url: '',
    show_warranty_in_pos: true,  // Toggle for warranty in POS
  });
  
  // Logo and stamp upload states
  const [uploadingLogo, setUploadingLogo] = useState(false);
  const [uploadingStamp, setUploadingStamp] = useState(false);
  const [regeneratingQR, setRegeneratingQR] = useState(false);

  // POS Settings
  const [posSettings, setPosSettings] = useState({
    eshte_me_tvsh: true,
    norma_tvsh_default: 18.0,
    shfaq_artikuj_me_minus: true,
    lejo_shitjen_me_minus: true,
    gjenero_automatik_numrin: true,
    lejo_shume_zbritje: false,
    orientimi_fatures: 'vertikal',
    valuta: 'EUR',
    simboli_valutes: '€',
    metoda_gjenerimit: 'auto',
    shteku_printer: '',
    printo_automatikisht: false,
    hap_sirtar_automatikisht: false,
  });

  // Branch form
  const [branchForm, setbranchForm] = useState({
    name: '',
    address: '',
    phone: '',
    is_active: true
  });

  // Warehouses (Depot)
  const [warehouses, setWarehouses] = useState([]);
  const [showWarehouseDialog, setShowWarehouseDialog] = useState(false);
  const [editingWarehouse, setEditingWarehouse] = useState(null);
  const [warehouseForm, setWarehouseForm] = useState({
    name: '',
    code: '',
    address: '',
    phone: '',
    is_active: true,
    is_default: false
  });

  // VAT rates
  const [vatRates, setVatRates] = useState([]);
  const [showVatDialog, setShowVatDialog] = useState(false);
  const [editingVat, setEditingVat] = useState(null);
  const [vatForm, setVatForm] = useState({
    name: '',
    rate: 18,
    code: '',
    is_default: false,
    is_active: true
  });

  useEffect(() => {
    loadData();
  }, []);

  const loadData = async () => {
    try {
      const [branchesRes, companyRes, posRes, warehousesRes, vatRes, commentsRes] = await Promise.all([
        api.get('/branches'),
        api.get('/settings/company'),
        api.get('/settings/pos'),
        api.get('/warehouses'),
        api.get('/vat-rates'),
        api.get('/comment-templates').catch(() => ({ data: [] }))
      ]);
      setBranches(branchesRes.data);
      if (companyRes.data) {
        setCompanyData(prev => ({...prev, ...companyRes.data}));
      }
      if (posRes.data) {
        setPosSettings(prev => ({...prev, ...posRes.data}));
      }
      setWarehouses(warehousesRes.data || []);
      setVatRates(vatRes.data || []);
      setCommentTemplates(commentsRes.data || []);
    } catch (error) {
      console.error('Error loading settings:', error);
    }
  };

  // Comment Templates CRUD
  const handleSaveComment = async () => {
    setLoading(true);
    try {
      if (editingComment) {
        await api.put(`/comment-templates/${editingComment.id}`, commentForm);
        toast.success('Template u përditësua me sukses!');
      } else {
        await api.post('/comment-templates', commentForm);
        toast.success('Template u shtua me sukses!');
      }
      setShowCommentDialog(false);
      loadData();
    } catch (error) {
      toast.error('Gabim gjatë ruajtjes së template');
    } finally {
      setLoading(false);
    }
  };

  const handleDeleteComment = async (id) => {
    if (!window.confirm('Jeni i sigurt që doni të fshini këtë template?')) return;
    try {
      await api.delete(`/comment-templates/${id}`);
      toast.success('Template u fshi me sukses!');
      loadData();
    } catch (error) {
      toast.error('Gabim gjatë fshirjes');
    }
  };

  const openCommentDialog = (comment = null) => {
    if (comment) {
      setEditingComment(comment);
      setCommentForm({
        title: comment.title,
        content: comment.content,
        is_default: comment.is_default || false,
        is_active: comment.is_active !== false
      });
    } else {
      setEditingComment(null);
      setCommentForm({
        title: '',
        content: '',
        is_default: false,
        is_active: true
      });
    }
    setShowCommentDialog(true);
  };

  const handleSaveCompany = async () => {
    setLoading(true);
    try {
      await api.put('/settings/company', companyData);
      toast.success('Të dhënat e kompanisë u ruajtën me sukses!');
    } catch (error) {
      toast.error('Gabim gjatë ruajtjes së të dhënave');
    } finally {
      setLoading(false);
    }
  };

  // Auto-save warranty toggle
  const handleWarrantyToggle = async (checked) => {
    const newData = {...companyData, show_warranty_in_pos: checked};
    setCompanyData(newData);
    try {
      await api.put('/settings/company', { show_warranty_in_pos: checked });
      toast.success(checked ? 'Garancioni u aktivizua në arkë' : 'Garancioni u çaktivizua nga arka');
    } catch (error) {
      // Revert on error
      setCompanyData({...companyData, show_warranty_in_pos: !checked});
      toast.error('Gabim gjatë ruajtjes');
    }
  };

  const handleSavePosSettings = async () => {
    setLoading(true);
    try {
      await api.put('/settings/pos', posSettings);
      toast.success('Cilësimet e POS u ruajtën me sukses!');
    } catch (error) {
      toast.error('Gabim gjatë ruajtjes së cilësimeve');
    } finally {
      setLoading(false);
    }
  };

  // Warehouse handlers
  const handleSaveWarehouse = async () => {
    try {
      if (editingWarehouse) {
        await api.put(`/warehouses/${editingWarehouse.id}`, warehouseForm);
        toast.success('Depoja u përditësua me sukses!');
      } else {
        await api.post('/warehouses', warehouseForm);
        toast.success('Depoja u shtua me sukses!');
      }
      setShowWarehouseDialog(false);
      setEditingWarehouse(null);
      setWarehouseForm({ name: '', code: '', address: '', phone: '', is_active: true, is_default: false });
      loadData();
    } catch (error) {
      toast.error('Gabim gjatë ruajtjes së depos');
    }
  };

  const handleEditWarehouse = (warehouse) => {
    setEditingWarehouse(warehouse);
    setWarehouseForm({
      name: warehouse.name,
      code: warehouse.code || '',
      address: warehouse.address || '',
      phone: warehouse.phone || '',
      is_active: warehouse.is_active,
      is_default: warehouse.is_default
    });
    setShowWarehouseDialog(true);
  };

  const handleDeleteWarehouse = async (id) => {
    if (window.confirm('Jeni të sigurt që dëshironi të fshini këtë depo?')) {
      try {
        await api.delete(`/warehouses/${id}`);
        toast.success('Depoja u fshi me sukses!');
        loadData();
      } catch (error) {
        toast.error('Gabim gjatë fshirjes së depos');
      }
    }
  };

  // VAT handlers
  const handleSaveVat = async () => {
    try {
      if (editingVat) {
        await api.put(`/vat-rates/${editingVat.id}`, vatForm);
        toast.success('Norma e TVSH u përditësua me sukses!');
      } else {
        await api.post('/vat-rates', vatForm);
        toast.success('Norma e TVSH u shtua me sukses!');
      }
      setShowVatDialog(false);
      setEditingVat(null);
      setVatForm({ name: '', rate: 18, code: '', is_default: false, is_active: true });
      loadData();
    } catch (error) {
      toast.error('Gabim gjatë ruajtjes së normës TVSH');
    }
  };

  const handleEditVat = (vat) => {
    setEditingVat(vat);
    setVatForm({
      name: vat.name,
      rate: vat.rate,
      code: vat.code || '',
      is_default: vat.is_default,
      is_active: vat.is_active
    });
    setShowVatDialog(true);
  };

  const handleDeleteVat = async (id) => {
    if (window.confirm('Jeni të sigurt që dëshironi të fshini këtë normë TVSH?')) {
      try {
        await api.delete(`/vat-rates/${id}`);
        toast.success('Norma e TVSH u fshi me sukses!');
        loadData();
      } catch (error) {
        toast.error('Gabim gjatë fshirjes së normës TVSH');
      }
    }
  };

  const handleSaveBranch = async () => {
    try {
      if (editingBranch) {
        await api.put(`/branches/${editingBranch.id}`, branchForm);
        toast.success('Dega u përditësua');
      } else {
        await api.post('/branches', branchForm);
        toast.success('Dega u krijua');
      }
      setShowBranchDialog(false);
      setEditingBranch(null);
      setbranchForm({ name: '', address: '', phone: '', is_active: true });
      loadData();
    } catch (error) {
      toast.error(error.response?.data?.detail || 'Gabim gjatë ruajtjes');
    }
  };

  const handleDeleteBranch = async (branch) => {
    if (!window.confirm(`Jeni të sigurt që doni të fshini degën "${branch.name}"?`)) return;
    try {
      await api.delete(`/branches/${branch.id}`);
      toast.success('Dega u fshi');
      loadData();
    } catch (error) {
      toast.error('Gabim gjatë fshirjes');
    }
  };

  // Logo upload handler
  const handleLogoUpload = async (event) => {
    const file = event.target.files?.[0];
    if (!file) return;
    
    // Validate file type
    const allowedTypes = ['image/png', 'image/jpeg', 'image/jpg', 'image/gif', 'image/webp'];
    if (!allowedTypes.includes(file.type)) {
      toast.error('Formati i file-it nuk lejohet. Përdorni: PNG, JPG, GIF, WEBP');
      return;
    }
    
    // Validate file size (max 5MB)
    if (file.size > 5 * 1024 * 1024) {
      toast.error('File-i është shumë i madh. Maksimumi: 5MB');
      return;
    }
    
    setUploadingLogo(true);
    try {
      const formData = new FormData();
      formData.append('file', file);
      
      const response = await api.post('/upload/logo', formData, {
        headers: { 'Content-Type': 'multipart/form-data' }
      });
      
      setCompanyData(prev => ({ ...prev, logo_url: response.data.url }));
      toast.success('Logo u ngarkua me sukses!');
    } catch (error) {
      toast.error(error.response?.data?.detail || 'Gabim gjatë ngarkimit të logos');
    } finally {
      setUploadingLogo(false);
    }
  };

  // Stamp upload handler (Vula Digjitale)
  const handleStampUpload = async (event) => {
    const file = event.target.files?.[0];
    if (!file) return;
    
    // Validate file type
    const allowedTypes = ['image/png', 'image/jpeg', 'image/jpg', 'image/gif', 'image/webp'];
    if (!allowedTypes.includes(file.type)) {
      toast.error('Formati i file-it nuk lejohet. Përdorni: PNG, JPG, GIF, WEBP');
      return;
    }
    
    // Validate file size (max 5MB)
    if (file.size > 5 * 1024 * 1024) {
      toast.error('File-i është shumë i madh. Maksimumi: 5MB');
      return;
    }
    
    setUploadingStamp(true);
    try {
      const formData = new FormData();
      formData.append('file', file);
      
      const response = await api.post('/upload/stamp', formData, {
        headers: { 'Content-Type': 'multipart/form-data' }
      });
      
      setCompanyData(prev => ({ ...prev, stamp_url: response.data.url }));
      toast.success('Vula digjitale u ngarkua me sukses!');
    } catch (error) {
      toast.error(error.response?.data?.detail || 'Gabim gjatë ngarkimit të vulës');
    } finally {
      setUploadingStamp(false);
    }
  };

  // Remove stamp
  const handleRemoveStamp = async () => {
    if (!window.confirm('Jeni të sigurt që doni të fshini vulën digjitale?')) return;
    
    try {
      await api.delete('/upload/tenant/current/stamp').catch(() => {});
      setCompanyData(prev => ({ ...prev, stamp_url: '' }));
      toast.success('Vula digjitale u fshi');
    } catch (error) {
      // Just clear locally if API fails
      setCompanyData(prev => ({ ...prev, stamp_url: '' }));
    }
  };

  // Regenerate WhatsApp QR Code
  const handleRegenerateQR = async () => {
    if (!companyData.phone) {
      toast.error('Vendosni numrin e telefonit dhe ruajeni përpara se të gjeneroni QR code');
      return;
    }
    
    setRegeneratingQR(true);
    try {
      const response = await api.post('/settings/regenerate-whatsapp-qr');
      setCompanyData(prev => ({ ...prev, whatsapp_qr_url: response.data.whatsapp_qr_url }));
      toast.success('QR code u gjenerua me sukses!');
    } catch (error) {
      toast.error(error.response?.data?.detail || 'Gabim gjatë gjenerimit të QR code');
    } finally {
      setRegeneratingQR(false);
    }
  };

  const editBranch = (branch) => {
    setEditingBranch(branch);
    setbranchForm({
      name: branch.name,
      address: branch.address || '',
      phone: branch.phone || '',
      is_active: branch.is_active
    });
    setShowBranchDialog(true);
  };

  return (
    <div className="space-y-6 animate-fade-in" data-testid="settings-page">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-gray-900">Konfigurimet</h1>
          <p className="text-gray-500">Menaxho cilësimet e sistemit</p>
        </div>
      </div>

      {/* Tabs */}
      <Tabs value={activeTab} onValueChange={setActiveTab} className="space-y-6">
        <TabsList className="bg-white border shadow-sm p-1 h-auto flex-wrap">
          <TabsTrigger value="kompania" className="data-[state=active]:bg-[#00a79d] data-[state=active]:text-white">
            <Building2 className="h-4 w-4 mr-2" />
            KOMPANIA
          </TabsTrigger>
          <TabsTrigger value="filialet" className="data-[state=active]:bg-[#00a79d] data-[state=active]:text-white">
            <Store className="h-4 w-4 mr-2" />
            FILIALET
          </TabsTrigger>
          <TabsTrigger value="depot" className="data-[state=active]:bg-[#00a79d] data-[state=active]:text-white">
            <Warehouse className="h-4 w-4 mr-2" />
            DEPOT
          </TabsTrigger>
          <TabsTrigger value="projektet" className="data-[state=active]:bg-[#00a79d] data-[state=active]:text-white">
            <FolderOpen className="h-4 w-4 mr-2" />
            PROJEKTET
          </TabsTrigger>
          <TabsTrigger value="numri" className="data-[state=active]:bg-[#00a79d] data-[state=active]:text-white">
            <FileText className="h-4 w-4 mr-2" />
            NUMRI DOKUMENTIT
          </TabsTrigger>
          <TabsTrigger value="shabllonet" className="data-[state=active]:bg-[#00a79d] data-[state=active]:text-white">
            <Receipt className="h-4 w-4 mr-2" />
            SHABLLONET E FATURAVE
          </TabsTrigger>
          <TabsTrigger value="tvsh" className="data-[state=active]:bg-[#00a79d] data-[state=active]:text-white">
            <Percent className="h-4 w-4 mr-2" />
            TVSH
          </TabsTrigger>
          <TabsTrigger value="kuponet" className="data-[state=active]:bg-[#00a79d] data-[state=active]:text-white">
            <Percent className="h-4 w-4 mr-2" />
            Kuponet
          </TabsTrigger>
        </TabsList>

        {/* KOMPANIA Tab */}
        <TabsContent value="kompania">
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
            {/* Left Column - Company Info */}
            <Card className="border border-gray-200/60 rounded-3xl shadow-sm bg-white/80 backdrop-blur-md">
              <CardHeader className="pb-4">
                <Button 
                  onClick={handleSaveCompany} 
                  disabled={loading}
                  className="w-fit bg-[#00a79d] hover:bg-[#008f86] rounded-xl shadow-md shadow-[#00a79d]/20"
                >
                  <Save className="h-4 w-4 mr-2" />
                  {loading ? 'Po ruhet...' : 'Ruaj të Dhënat'}
                </Button>
              </CardHeader>
              <CardContent className="space-y-4">
                <div className="space-y-2">
                  <Label>Emri i kompanisë</Label>
                  <Input
                    value={companyData.company_name}
                    onChange={(e) => setCompanyData({ ...companyData, company_name: e.target.value })}
                    placeholder="Emri i kompanisë"
                  />
                </div>

                <div className="space-y-2">
                  <Label>NUI (Numri Unik Identifikues)</Label>
                  <Input
                    value={companyData.nui}
                    onChange={(e) => setCompanyData({ ...companyData, nui: e.target.value })}
                    placeholder="Numri Unik i Identifikimit"
                  />
                </div>

                <div className="space-y-2">
                  <Label>NF (Numri Fiskal)</Label>
                  <Input
                    value={companyData.nf}
                    onChange={(e) => setCompanyData({ ...companyData, nf: e.target.value })}
                    placeholder="Numri Fiskal"
                  />
                </div>

                <div className="space-y-2">
                  <Label>Numri i TVSH-së</Label>
                  <Input
                    value={companyData.vat_number}
                    onChange={(e) => setCompanyData({ ...companyData, vat_number: e.target.value })}
                    placeholder="Numri i TVSH-së"
                  />
                </div>

                <div className="space-y-2">
                  <Label>Telefoni</Label>
                  <Input
                    value={companyData.phone}
                    onChange={(e) => setCompanyData({ ...companyData, phone: e.target.value })}
                    placeholder="+383 XX XXX XXX"
                  />
                </div>

                <div className="space-y-2">
                  <Label>Email</Label>
                  <Input
                    type="email"
                    value={companyData.email}
                    onChange={(e) => setCompanyData({ ...companyData, email: e.target.value })}
                    placeholder="email@kompania.com"
                  />
                </div>

                <div className="space-y-2">
                  <Label>Website</Label>
                  <Input
                    value={companyData.website}
                    onChange={(e) => setCompanyData({ ...companyData, website: e.target.value })}
                    placeholder="www.kompania.com"
                  />
                </div>

                <div className="space-y-2">
                  <Label>Adresa</Label>
                  <Input
                    value={companyData.address}
                    onChange={(e) => setCompanyData({ ...companyData, address: e.target.value })}
                    placeholder="Adresa e kompanisë"
                  />
                </div>

                <div className="grid grid-cols-2 gap-4">
                  <div className="space-y-2">
                    <Label>Qyteti</Label>
                    <Input
                      value={companyData.city}
                      onChange={(e) => setCompanyData({ ...companyData, city: e.target.value })}
                      placeholder="Qyteti"
                    />
                  </div>
                  <div className="space-y-2">
                    <Label>Kodi Postar</Label>
                    <Input
                      value={companyData.postal_code}
                      onChange={(e) => setCompanyData({ ...companyData, postal_code: e.target.value })}
                      placeholder="10000"
                    />
                  </div>
                </div>

                <div className="space-y-2">
                  <Label>Banka</Label>
                  <Input
                    value={companyData.bank_name}
                    onChange={(e) => setCompanyData({ ...companyData, bank_name: e.target.value })}
                    placeholder="Emri i bankës"
                  />
                </div>

                <div className="space-y-2">
                  <Label>Llogaria Bankare</Label>
                  <Input
                    value={companyData.bank_account}
                    onChange={(e) => setCompanyData({ ...companyData, bank_account: e.target.value })}
                    placeholder="IBAN ose numri i llogarisë"
                  />
                </div>

                {/* Logo Upload Section */}
                <Separator className="my-4" />
                <div className="space-y-4">
                  <Label className="text-base font-semibold">Logo e Kompanisë</Label>
                  <p className="text-sm text-gray-500">Ngarkoni logon e kompanisë që do të shfaqet në fatura dhe dokumente</p>
                  
                  <div className="flex items-start gap-4">
                    {companyData.logo_url ? (
                      <div className="relative">
                        <img 
                          src={companyData.logo_url} 
                          alt="Logo" 
                          className="w-24 h-24 object-contain border rounded-lg bg-gray-50"
                        />
                        <button 
                          onClick={() => setCompanyData({ ...companyData, logo_url: '' })}
                          className="absolute -top-2 -right-2 bg-red-500 text-white rounded-full w-6 h-6 flex items-center justify-center text-xs hover:bg-red-600"
                        >
                          ×
                        </button>
                      </div>
                    ) : (
                      <div className="w-24 h-24 border-2 border-dashed rounded-lg flex items-center justify-center bg-gray-50">
                        <Upload className="h-8 w-8 text-gray-400" />
                      </div>
                    )}
                    <div className="flex-1">
                      <input
                        type="file"
                        accept="image/png,image/jpeg,image/jpg,image/gif,image/webp"
                        onChange={handleLogoUpload}
                        className="hidden"
                        id="logo-upload"
                        disabled={uploadingLogo}
                      />
                      <label htmlFor="logo-upload">
                        <Button 
                          variant="outline" 
                          className="cursor-pointer" 
                          disabled={uploadingLogo}
                          asChild
                        >
                          <span>
                            <Upload className="h-4 w-4 mr-2" />
                            {uploadingLogo ? 'Po ngarkohet...' : 'Ngarko Logo'}
                          </span>
                        </Button>
                      </label>
                      <p className="text-xs text-gray-500 mt-2">PNG, JPG, GIF ose WEBP. Max 5MB.</p>
                    </div>
                  </div>
                </div>

                {/* Digital Stamp Upload Section - Vula Digjitale */}
                <Separator className="my-4" />
                <div className="space-y-4">
                  <Label className="text-base font-semibold">Vula Digjitale</Label>
                  <p className="text-sm text-gray-500">Ngarkoni vulën digjitale të kompanisë që do të shfaqet në faturën A4</p>
                  
                  <div className="flex items-start gap-4">
                    {companyData.stamp_url ? (
                      <div className="relative">
                        <img 
                          src={companyData.stamp_url} 
                          alt="Vula Digjitale" 
                          className="w-24 h-24 object-contain border rounded-lg bg-gray-50"
                          style={{ mixBlendMode: 'multiply' }}
                        />
                        <button 
                          onClick={handleRemoveStamp}
                          className="absolute -top-2 -right-2 bg-red-500 text-white rounded-full w-6 h-6 flex items-center justify-center text-xs hover:bg-red-600"
                        >
                          ×
                        </button>
                      </div>
                    ) : (
                      <div className="w-24 h-24 border-2 border-dashed rounded-lg flex items-center justify-center bg-gray-50">
                        <div className="text-center">
                          <div className="text-2xl text-gray-400">🔏</div>
                          <span className="text-xs text-gray-400">Vula</span>
                        </div>
                      </div>
                    )}
                    <div className="flex-1">
                      <input
                        type="file"
                        accept="image/png,image/jpeg,image/jpg,image/gif,image/webp"
                        onChange={handleStampUpload}
                        className="hidden"
                        id="stamp-upload"
                        disabled={uploadingStamp}
                      />
                      <label htmlFor="stamp-upload">
                        <Button 
                          variant="outline" 
                          className="cursor-pointer" 
                          disabled={uploadingStamp}
                          asChild
                        >
                          <span>
                            <Upload className="h-4 w-4 mr-2" />
                            {uploadingStamp ? 'Po ngarkohet...' : 'Ngarko Vulën'}
                          </span>
                        </Button>
                      </label>
                      <p className="text-xs text-gray-500 mt-2">Rekomandohet PNG me sfond transparent. Max 5MB.</p>
                      <p className="text-xs text-blue-600 mt-1">💡 Vula do të shfaqet automatikisht në faturën A4</p>
                    </div>
                  </div>
                </div>

                {/* WhatsApp QR Code Section */}
                <Separator className="my-4" />
                <div className="space-y-4">
                  <Label className="text-base font-semibold">QR Code për WhatsApp</Label>
                  <p className="text-sm text-gray-500">
                    Ky QR code lidhet me numrin e telefonit të firmës dhe shfaqet në kuponin termik. 
                    Klientët mund ta skanojnë për t'ju kontaktuar në WhatsApp.
                  </p>
                  
                  <div className="flex items-start gap-4">
                    {companyData.whatsapp_qr_url ? (
                      <div className="relative">
                        <img 
                          src={companyData.whatsapp_qr_url} 
                          alt="WhatsApp QR Code" 
                          className="w-24 h-24 object-contain border rounded-lg bg-white"
                        />
                      </div>
                    ) : (
                      <div className="w-24 h-24 border-2 border-dashed rounded-lg flex items-center justify-center bg-gray-50">
                        <div className="text-center">
                          <div className="text-2xl text-gray-400">📱</div>
                          <span className="text-xs text-gray-400">QR</span>
                        </div>
                      </div>
                    )}
                    <div className="flex-1">
                      <Button 
                        variant="outline" 
                        onClick={handleRegenerateQR}
                        disabled={regeneratingQR || !companyData.phone}
                      >
                        {regeneratingQR ? 'Po gjenerohet...' : companyData.whatsapp_qr_url ? 'Ri-gjenero QR Code' : 'Gjenero QR Code'}
                      </Button>
                      {!companyData.phone && (
                        <p className="text-xs text-orange-600 mt-2">⚠️ Vendosni numrin e telefonit dhe ruajeni për të gjeneruar QR code</p>
                      )}
                      {companyData.phone && (
                        <p className="text-xs text-gray-500 mt-2">Numri: {companyData.phone}</p>
                      )}
                      <p className="text-xs text-green-600 mt-1">💡 QR code do të shfaqet në kuponin termik</p>
                    </div>
                  </div>
                </div>

                {/* Warranty Toggle Section */}
                <Separator className="my-4" />
                <div className="space-y-4">
                  <Label className="text-base font-semibold">Garancioni në Arkë</Label>
                  <div className="flex items-center justify-between p-4 border rounded-lg bg-gray-50">
                    <div>
                      <p className="font-medium">Shfaq butonat e Garancionit në POS</p>
                      <p className="text-sm text-gray-500">
                        Aktivizo/Çaktivizo shfaqjen e butonave "Garancioni" dhe "Garancione" në arkë. 
                        Për firmat që nuk përdorin garancione, mund ta çaktivizoni.
                      </p>
                    </div>
                    <div className="flex items-center gap-2">
                      <span className={!companyData.show_warranty_in_pos ? 'text-gray-900 font-medium' : 'text-gray-400'}>Jo</span>
                      <Switch
                        checked={companyData.show_warranty_in_pos}
                        onCheckedChange={handleWarrantyToggle}
                      />
                      <span className={companyData.show_warranty_in_pos ? 'text-gray-900 font-medium' : 'text-gray-400'}>Po</span>
                    </div>
                  </div>
                  <p className="text-xs text-blue-600">💡 Ndryshimi ruhet automatikisht</p>
                </div>
              </CardContent>
            </Card>

            {/* Right Column - POS Settings */}
            <Card className="border border-gray-200/60 rounded-3xl shadow-sm bg-white/80 backdrop-blur-md">
              <CardHeader>
                <CardTitle>Cilësimet e POS</CardTitle>
              </CardHeader>
              <CardContent className="space-y-6">
                <div className="flex items-center justify-between">
                  <div>
                    <p className="font-medium">Është me Tvsh</p>
                    <p className="text-sm text-gray-500">Aktivizo kalkulimin e TVSH</p>
                  </div>
                  <div className="flex items-center gap-2">
                    <span className={!posSettings.eshte_me_tvsh ? 'text-gray-900' : 'text-gray-400'}>Jo</span>
                    <Switch
                      checked={posSettings.eshte_me_tvsh}
                      onCheckedChange={(checked) => setPosSettings({ ...posSettings, eshte_me_tvsh: checked })}
                    />
                    <span className={posSettings.eshte_me_tvsh ? 'text-green-600' : 'text-gray-400'}>Po</span>
                  </div>
                </div>

                <Separator />

                <div className="flex items-center justify-between">
                  <div>
                    <p className="font-medium">Shfaq Artikuj me minus</p>
                    <p className="text-sm text-gray-500">Shfaq produktet me stok negativ</p>
                  </div>
                  <div className="flex items-center gap-2">
                    <span className={!posSettings.shfaq_artikuj_me_minus ? 'text-gray-900' : 'text-gray-400'}>Jo</span>
                    <Switch
                      checked={posSettings.shfaq_artikuj_me_minus}
                      onCheckedChange={(checked) => setPosSettings({ ...posSettings, shfaq_artikuj_me_minus: checked })}
                    />
                    <span className={posSettings.shfaq_artikuj_me_minus ? 'text-green-600' : 'text-gray-400'}>Po</span>
                  </div>
                </div>

                <Separator />

                <div className="flex items-center justify-between">
                  <div>
                    <p className="font-medium">Lejo shitjen me minus</p>
                    <p className="text-sm text-gray-500">Lejo shitjen kur stoku është negativ</p>
                  </div>
                  <div className="flex items-center gap-2">
                    <span className={!posSettings.lejo_shitjen_me_minus ? 'text-gray-900' : 'text-gray-400'}>Jo</span>
                    <Switch
                      checked={posSettings.lejo_shitjen_me_minus}
                      onCheckedChange={(checked) => setPosSettings({ ...posSettings, lejo_shitjen_me_minus: checked })}
                    />
                    <span className={posSettings.lejo_shitjen_me_minus ? 'text-green-600' : 'text-gray-400'}>Po</span>
                  </div>
                </div>

                <Separator />

                <div className="flex items-center justify-between">
                  <div>
                    <p className="font-medium">Gjenero në mënyrë automatike numrin e faturës</p>
                    <p className="text-sm text-gray-500">Numri i faturës gjenerohet automatikisht</p>
                  </div>
                  <div className="flex items-center gap-2">
                    <span className={!posSettings.gjenero_automatik_numrin ? 'text-gray-900' : 'text-gray-400'}>Jo</span>
                    <Switch
                      checked={posSettings.gjenero_automatik_numrin}
                      onCheckedChange={(checked) => setPosSettings({ ...posSettings, gjenero_automatik_numrin: checked })}
                    />
                    <span className={posSettings.gjenero_automatik_numrin ? 'text-green-600' : 'text-gray-400'}>Po</span>
                  </div>
                </div>

                <Separator />

                <div className="flex items-center justify-between">
                  <div>
                    <p className="font-medium">Lejo shitjen me shumë zbritje</p>
                    <p className="text-sm text-gray-500">Lejo zbritje të shumëfishta në një artikull</p>
                  </div>
                  <div className="flex items-center gap-2">
                    <span className={!posSettings.lejo_shume_zbritje ? 'text-gray-900' : 'text-gray-400'}>Jo</span>
                    <Switch
                      checked={posSettings.lejo_shume_zbritje}
                      onCheckedChange={(checked) => setPosSettings({ ...posSettings, lejo_shume_zbritje: checked })}
                    />
                    <span className={posSettings.lejo_shume_zbritje ? 'text-green-600' : 'text-gray-400'}>Po</span>
                  </div>
                </div>

                <Separator />

                <div className="flex items-center justify-between">
                  <div>
                    <p className="font-medium">Kam restaurant</p>
                    <p className="text-sm text-gray-500">Aktivizo modulin e restorantit</p>
                  </div>
                  <div className="flex items-center gap-2">
                    <span className={!posSettings.kam_restaurant ? 'text-gray-900' : 'text-gray-400'}>Jo</span>
                    <Switch
                      checked={posSettings.kam_restaurant}
                      onCheckedChange={(checked) => setPosSettings({ ...posSettings, kam_restaurant: checked })}
                    />
                    <span className={posSettings.kam_restaurant ? 'text-green-600' : 'text-gray-400'}>Po</span>
                  </div>
                </div>

                <Separator />

                <div className="flex items-center justify-between">
                  <div>
                    <p className="font-medium">Orientimi i faturës</p>
                    <p className="text-sm text-gray-500">Orientimi i printimit të faturës</p>
                  </div>
                  <div className="flex items-center gap-2">
                    <span className={posSettings.orientimi_fatures === 'horizontal' ? 'text-gray-900' : 'text-gray-400'}>Horizontal</span>
                    <Switch
                      checked={posSettings.orientimi_fatures === 'vertikal'}
                      onCheckedChange={(checked) => setPosSettings({ ...posSettings, orientimi_fatures: checked ? 'vertikal' : 'horizontal' })}
                    />
                    <span className={posSettings.orientimi_fatures === 'vertikal' ? 'text-[#00a79d]' : 'text-gray-400'}>Vertikal</span>
                  </div>
                </div>

                <Separator />

                <div className="grid grid-cols-2 gap-4">
                  <div className="space-y-2">
                    <Label>Valuta</Label>
                    <Select
                      value={posSettings.valuta}
                      onValueChange={(value) => setPosSettings({ ...posSettings, valuta: value })}
                    >
                      <SelectTrigger>
                        <SelectValue />
                      </SelectTrigger>
                      <SelectContent>
                        <SelectItem value="EUR">EUR</SelectItem>
                        <SelectItem value="USD">USD</SelectItem>
                        <SelectItem value="ALL">ALL</SelectItem>
                        <SelectItem value="CHF">CHF</SelectItem>
                      </SelectContent>
                    </Select>
                  </div>
                  <div className="space-y-2">
                    <Label>Simboli</Label>
                    <Input
                      value={posSettings.simboli_valutes}
                      onChange={(e) => setPosSettings({ ...posSettings, simboli_valutes: e.target.value })}
                      placeholder="€"
                    />
                  </div>
                </div>

                <div className="space-y-2">
                  <Label>Metoda e gjenerimit të numrit të faturës</Label>
                  <Input
                    value={posSettings.metoda_gjenerimit}
                    onChange={(e) => setPosSettings({ ...posSettings, metoda_gjenerimit: e.target.value })}
                    placeholder="3"
                  />
                  <p className="text-xs text-gray-500">1. Ditore, 2. Mujore, 3. Vjetore</p>
                </div>

                <div className="space-y-2">
                  <Label>Shteku për printer fiskal</Label>
                  <Input
                    value={posSettings.shteku_printer}
                    onChange={(e) => setPosSettings({ ...posSettings, shteku_printer: e.target.value })}
                    placeholder="Shtegu i printerit"
                  />
                </div>

                <div className="space-y-2">
                  <Label>Partneri default</Label>
                  <Select
                    value={posSettings.partneri_default}
                    onValueChange={(value) => setPosSettings({ ...posSettings, partneri_default: value })}
                  >
                    <SelectTrigger>
                      <SelectValue placeholder="Zgjidh partnerin" />
                    </SelectTrigger>
                    <SelectContent>
                      <SelectItem value="partneri">Partneri</SelectItem>
                    </SelectContent>
                  </Select>
                </div>

                <div className="space-y-2">
                  <p className="text-sm text-gray-500">Formati i numrit të faturës: <span className="font-medium">Shembull: {posSettings.formati_numrit}</span></p>
                </div>

                <Separator />

                <div className="space-y-2">
                  <Label>Logo</Label>
                  <div className="flex items-center gap-4">
                    <Button variant="outline" className="gap-2">
                      <Upload className="h-4 w-4" />
                      Zgjidh Skedarin
                    </Button>
                    <span className="text-sm text-gray-500">Nuk është zgjedhur asnjë skedar</span>
                  </div>
                </div>

                <div className="space-y-2">
                  <Label>Vulë digjitale</Label>
                  <div className="flex items-center gap-4">
                    <Button variant="outline" className="gap-2">
                      <Upload className="h-4 w-4" />
                      Zgjidh Skedarin
                    </Button>
                    <span className="text-sm text-gray-500">Nuk është zgjedhur asnjë skedar</span>
                  </div>
                </div>

                <Button onClick={handleSavePosSettings} className="w-full bg-[#00a79d] hover:bg-[#008f86] rounded-xl shadow-md shadow-[#00a79d]/20">
                  <Save className="h-4 w-4 mr-2" />
                  Ruaj Cilësimet
                </Button>
              </CardContent>
            </Card>
          </div>
        </TabsContent>

        {/* FILIALET Tab */}
        <TabsContent value="filialet">
          <Card className="border border-gray-200/60 rounded-3xl shadow-sm bg-white/80 backdrop-blur-md">
            <CardHeader className="flex flex-row items-center justify-between">
              <CardTitle>Filialet / Degët</CardTitle>
              <Button 
                className="bg-[#00a79d] hover:bg-[#008f86] rounded-xl shadow-md shadow-[#00a79d]/20"
                onClick={() => {
                  setEditingBranch(null);
                  setbranchForm({ name: '', address: '', phone: '', is_active: true });
                  setShowBranchDialog(true);
                }}
              >
                <Plus className="h-4 w-4 mr-2" />
                Shto Filial
              </Button>
            </CardHeader>
            <CardContent>
              <Table>
                <TableHeader>
                  <TableRow>
                    <TableHead>Emri</TableHead>
                    <TableHead>Adresa</TableHead>
                    <TableHead>Telefoni</TableHead>
                    <TableHead>Statusi</TableHead>
                    <TableHead className="text-right">Veprime</TableHead>
                  </TableRow>
                </TableHeader>
                <TableBody>
                  {branches.map((branch) => (
                    <TableRow key={branch.id}>
                      <TableCell className="font-medium">{branch.name}</TableCell>
                      <TableCell>{branch.address || '-'}</TableCell>
                      <TableCell>{branch.phone || '-'}</TableCell>
                      <TableCell>
                        <span className={`px-2 py-1 rounded-full text-xs ${branch.is_active ? 'bg-green-100 text-green-700' : 'bg-red-100 text-red-700'}`}>
                          {branch.is_active ? 'Aktiv' : 'Joaktiv'}
                        </span>
                      </TableCell>
                      <TableCell className="text-right">
                        <Button variant="ghost" size="icon" onClick={() => editBranch(branch)}>
                          <Edit2 className="h-4 w-4" />
                        </Button>
                        <Button variant="ghost" size="icon" className="text-red-500" onClick={() => handleDeleteBranch(branch)}>
                          <Trash2 className="h-4 w-4" />
                        </Button>
                      </TableCell>
                    </TableRow>
                  ))}
                  {branches.length === 0 && (
                    <TableRow>
                      <TableCell colSpan={5} className="text-center py-8 text-gray-500">
                        Nuk ka filiale të regjistruara
                      </TableCell>
                    </TableRow>
                  )}
                </TableBody>
              </Table>
            </CardContent>
          </Card>
        </TabsContent>

        {/* DEPOT Tab */}
        <TabsContent value="depot">
          <Card className="border border-gray-200/60 rounded-3xl shadow-sm bg-white/80 backdrop-blur-md">
            <CardHeader className="flex flex-row items-center justify-between">
              <CardTitle>Depot / Magazinat</CardTitle>
              <Button 
                className="bg-[#00a79d] hover:bg-[#008f86] rounded-xl shadow-md shadow-[#00a79d]/20"
                onClick={() => {
                  setEditingWarehouse(null);
                  setWarehouseForm({ name: '', code: '', address: '', phone: '', is_active: true, is_default: false });
                  setShowWarehouseDialog(true);
                }}
              >
                <Plus className="h-4 w-4 mr-2" />
                Shto Depo
              </Button>
            </CardHeader>
            <CardContent>
              <Table>
                <TableHeader>
                  <TableRow>
                    <TableHead>Emri</TableHead>
                    <TableHead>Kodi</TableHead>
                    <TableHead>Adresa</TableHead>
                    <TableHead>Telefoni</TableHead>
                    <TableHead>Statusi</TableHead>
                    <TableHead className="text-right">Veprime</TableHead>
                  </TableRow>
                </TableHeader>
                <TableBody>
                  {warehouses.map((warehouse) => (
                    <TableRow key={warehouse.id}>
                      <TableCell className="font-medium">
                        {warehouse.name}
                        {warehouse.is_default && (
                          <span className="ml-2 px-2 py-0.5 rounded-full text-xs bg-blue-100 text-blue-700">
                            Default
                          </span>
                        )}
                      </TableCell>
                      <TableCell>{warehouse.code || '-'}</TableCell>
                      <TableCell>{warehouse.address || '-'}</TableCell>
                      <TableCell>{warehouse.phone || '-'}</TableCell>
                      <TableCell>
                        <span className={`px-2 py-1 rounded-full text-xs ${warehouse.is_active ? 'bg-green-100 text-green-700' : 'bg-red-100 text-red-700'}`}>
                          {warehouse.is_active ? 'Aktiv' : 'Joaktiv'}
                        </span>
                      </TableCell>
                      <TableCell className="text-right">
                        <Button variant="ghost" size="icon" onClick={() => handleEditWarehouse(warehouse)}>
                          <Edit2 className="h-4 w-4" />
                        </Button>
                        <Button variant="ghost" size="icon" className="text-red-500" onClick={() => handleDeleteWarehouse(warehouse.id)}>
                          <Trash2 className="h-4 w-4" />
                        </Button>
                      </TableCell>
                    </TableRow>
                  ))}
                  {warehouses.length === 0 && (
                    <TableRow>
                      <TableCell colSpan={6} className="text-center py-8 text-gray-500">
                        Nuk ka depo të regjistruara
                      </TableCell>
                    </TableRow>
                  )}
                </TableBody>
              </Table>
            </CardContent>
          </Card>
        </TabsContent>

        {/* PROJEKTET Tab */}
        <TabsContent value="projektet">
          <Card className="border border-gray-200/60 rounded-3xl shadow-sm bg-white/80 backdrop-blur-md">
            <CardHeader className="flex flex-row items-center justify-between">
              <CardTitle>Projektet</CardTitle>
              <Button className="bg-[#00a79d] hover:bg-[#008f86] rounded-xl shadow-md shadow-[#00a79d]/20">
                <Plus className="h-4 w-4 mr-2" />
                Shto Projekt
              </Button>
            </CardHeader>
            <CardContent>
              <Table>
                <TableHeader>
                  <TableRow>
                    <TableHead>Emri</TableHead>
                    <TableHead>Përshkrimi</TableHead>
                    <TableHead>Data Fillimit</TableHead>
                    <TableHead>Statusi</TableHead>
                    <TableHead className="text-right">Veprime</TableHead>
                  </TableRow>
                </TableHeader>
                <TableBody>
                  <TableRow>
                    <TableCell colSpan={5} className="text-center py-8 text-gray-500">
                      Nuk ka projekte të regjistruara
                    </TableCell>
                  </TableRow>
                </TableBody>
              </Table>
            </CardContent>
          </Card>
        </TabsContent>

        {/* NUMRI DOKUMENTIT Tab */}
        <TabsContent value="numri">
          <Card className="border border-gray-200/60 rounded-3xl shadow-sm bg-white/80 backdrop-blur-md">
            <CardHeader>
              <CardTitle>Numërimi i Dokumenteve</CardTitle>
              <CardDescription>Konfiguro formatin e numërimit të dokumenteve</CardDescription>
            </CardHeader>
            <CardContent className="space-y-6">
              <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                <div className="space-y-4">
                  <div className="space-y-2">
                    <Label>Formati i Faturës së Shitjes</Label>
                    <Input defaultValue="SH-{YYYY}-{MM}-{NNNN}" placeholder="SH-{YYYY}-{MM}-{NNNN}" />
                  </div>
                  <div className="space-y-2">
                    <Label>Formati i Faturës së Blerjes</Label>
                    <Input defaultValue="BL-{YYYY}-{MM}-{NNNN}" placeholder="BL-{YYYY}-{MM}-{NNNN}" />
                  </div>
                  <div className="space-y-2">
                    <Label>Formati i Ofertës</Label>
                    <Input defaultValue="OF-{YYYY}-{NNNN}" placeholder="OF-{YYYY}-{NNNN}" />
                  </div>
                </div>
                <div className="p-4 bg-gray-50 rounded-lg">
                  <h4 className="font-medium mb-2">Variablat e disponueshme:</h4>
                  <ul className="text-sm text-gray-600 space-y-1">
                    <li><code className="bg-gray-200 px-1 rounded">{'{YYYY}'}</code> - Viti (4 shifra)</li>
                    <li><code className="bg-gray-200 px-1 rounded">{'{YY}'}</code> - Viti (2 shifra)</li>
                    <li><code className="bg-gray-200 px-1 rounded">{'{MM}'}</code> - Muaji</li>
                    <li><code className="bg-gray-200 px-1 rounded">{'{DD}'}</code> - Dita</li>
                    <li><code className="bg-gray-200 px-1 rounded">{'{NNNN}'}</code> - Numri rendor</li>
                  </ul>
                </div>
              </div>
              <Button className="bg-[#00a79d] hover:bg-[#008f86] rounded-xl shadow-md shadow-[#00a79d]/20">
                <Save className="h-4 w-4 mr-2" />
                Ruaj Formatet
              </Button>
            </CardContent>
          </Card>
        </TabsContent>

        {/* SHABLLONET E FATURAVE Tab */}
        <TabsContent value="shabllonet">
          {/* Printer Info Banner */}
          <div className="bg-blue-50 border border-blue-200 rounded-lg p-4 mb-6">
            <div className="flex items-start gap-3">
              <Receipt className="h-5 w-5 text-blue-600 mt-0.5 flex-shrink-0" />
              <div>
                <h4 className="font-medium text-blue-800 mb-1">Si të zgjidhni Printerin?</h4>
                <p className="text-sm text-blue-700">
                  Kur klikoni butonin &quot;Printo&quot; në çdo dokument (kupon termik 80mm ose faturë A4), do të hapet një dialog 
                  ku mund të zgjidhni printerin tuaj të preferuar nga lista e të gjithë printerëve të instaluar në kompjuter. 
                  Për printer termik, sigurohuni që të keni konfiguruar madhësinë e letrës si 80mm në cilësimet e printerit.
                </p>
              </div>
            </div>
          </div>
          
          {/* Comment Templates Section */}
          <Card className="border border-gray-200/60 rounded-3xl shadow-sm bg-white/80 backdrop-blur-md mb-6">
            <CardHeader className="flex flex-row items-center justify-between">
              <div>
                <CardTitle className="flex items-center gap-2">
                  <MessageSquare className="h-5 w-5" />
                  Komentet e Kuponit
                </CardTitle>
                <CardDescription>Menaxho template-t e komenteve për kuponat termike</CardDescription>
              </div>
              <Button 
                className="bg-[#00a79d] hover:bg-[#008f86] rounded-xl shadow-md shadow-[#00a79d]/20"
                onClick={() => openCommentDialog()}
              >
                <Plus className="h-4 w-4 mr-2" />
                Shto Koment
              </Button>
            </CardHeader>
            <CardContent>
              {commentTemplates.length === 0 ? (
                <div className="text-center py-8 text-gray-500">
                  <MessageSquare className="h-12 w-12 mx-auto mb-3 opacity-30" />
                  <p>Nuk ka template komentesh</p>
                  <p className="text-sm mt-1">Shtoni komentet që shfaqen shpesh në kuponat termike</p>
                </div>
              ) : (
                <div className="space-y-3">
                  {commentTemplates.map((template) => (
                    <div 
                      key={template.id}
                      className={`flex items-center justify-between p-4 border rounded-lg ${
                        template.is_default ? 'border-[#00a79d] bg-[#00a79d]/5' : 'bg-gray-50'
                      } ${!template.is_active ? 'opacity-50' : ''}`}
                    >
                      <div className="flex-1">
                        <div className="flex items-center gap-2">
                          <span className="font-medium">{template.title}</span>
                          {template.is_default && (
                            <span className="px-2 py-0.5 text-xs bg-[#00a79d] text-white rounded-full">
                              Default
                            </span>
                          )}
                          {!template.is_active && (
                            <span className="px-2 py-0.5 text-xs bg-gray-400 text-white rounded-full">
                              Jo Aktiv
                            </span>
                          )}
                        </div>
                        <p className="text-sm text-gray-600 mt-1 line-clamp-2">{template.content}</p>
                      </div>
                      <div className="flex gap-2 ml-4">
                        <Button
                          size="sm"
                          variant="outline"
                          onClick={() => openCommentDialog(template)}
                        >
                          <Edit2 className="h-4 w-4" />
                        </Button>
                        <Button
                          size="sm"
                          variant="outline"
                          className="text-red-500 hover:bg-red-50"
                          onClick={() => handleDeleteComment(template.id)}
                        >
                          <Trash2 className="h-4 w-4" />
                        </Button>
                      </div>
                    </div>
                  ))}
                </div>
              )}
            </CardContent>
          </Card>

          {/* Invoice Templates Section */}
          <Card className="border border-gray-200/60 rounded-3xl shadow-sm bg-white/80 backdrop-blur-md">
            <CardHeader className="flex flex-row items-center justify-between">
              <div>
                <CardTitle>Shabllonet e Faturave</CardTitle>
                <CardDescription>Menaxho template-t e faturave dhe dokumenteve</CardDescription>
              </div>
              <Button className="bg-[#00a79d] hover:bg-[#008f86] rounded-xl shadow-md shadow-[#00a79d]/20">
                <Plus className="h-4 w-4 mr-2" />
                Shto Shabllon
              </Button>
            </CardHeader>
            <CardContent>
              <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                <Card className="border hover:border-[#00a79d] cursor-pointer transition-colors">
                  <CardContent className="p-4">
                    <div className="h-32 bg-gray-100 rounded mb-3 flex items-center justify-center">
                      <Receipt className="h-12 w-12 text-gray-400" />
                    </div>
                    <p className="font-medium">Faturë Standarde</p>
                    <p className="text-sm text-gray-500">A4 - Portrait</p>
                  </CardContent>
                </Card>
                <Card className="border hover:border-[#00a79d] cursor-pointer transition-colors">
                  <CardContent className="p-4">
                    <div className="h-32 bg-gray-100 rounded mb-3 flex items-center justify-center">
                      <Receipt className="h-12 w-12 text-gray-400" />
                    </div>
                    <p className="font-medium">Faturë Termike</p>
                    <p className="text-sm text-gray-500">80mm - Receipt</p>
                  </CardContent>
                </Card>
                <Card className="border hover:border-[#00a79d] cursor-pointer transition-colors">
                  <CardContent className="p-4">
                    <div className="h-32 bg-gray-100 rounded mb-3 flex items-center justify-center">
                      <Receipt className="h-12 w-12 text-gray-400" />
                    </div>
                    <p className="font-medium">Ofertë</p>
                    <p className="text-sm text-gray-500">A4 - Portrait</p>
                  </CardContent>
                </Card>
              </div>
            </CardContent>
          </Card>
        </TabsContent>

        {/* TVSH Tab */}
        <TabsContent value="tvsh">
          <Card className="border border-gray-200/60 rounded-3xl shadow-sm bg-white/80 backdrop-blur-md">
            <CardHeader className="flex flex-row items-center justify-between">
              <div>
                <CardTitle>Normat e TVSH-së</CardTitle>
                <CardDescription>Menaxho normat e tatimit mbi vlerën e shtuar</CardDescription>
              </div>
              <Button 
                className="bg-[#00a79d] hover:bg-[#008f86] rounded-xl shadow-md shadow-[#00a79d]/20"
                onClick={() => {
                  setEditingVat(null);
                  setVatForm({ name: '', rate: 18, code: '', is_default: false, is_active: true });
                  setShowVatDialog(true);
                }}
              >
                <Plus className="h-4 w-4 mr-2" />
                Shto Normë
              </Button>
            </CardHeader>
            <CardContent>
              <Table>
                <TableHeader>
                  <TableRow>
                    <TableHead>Emri</TableHead>
                    <TableHead>Kodi</TableHead>
                    <TableHead>Norma (%)</TableHead>
                    <TableHead>Default</TableHead>
                    <TableHead>Statusi</TableHead>
                    <TableHead className="text-right">Veprime</TableHead>
                  </TableRow>
                </TableHeader>
                <TableBody>
                  {vatRates.map((vat) => (
                    <TableRow key={vat.id}>
                      <TableCell className="font-medium">{vat.name}</TableCell>
                      <TableCell>{vat.code || '-'}</TableCell>
                      <TableCell>{vat.rate}%</TableCell>
                      <TableCell>
                        {vat.is_default && (
                          <span className="px-2 py-1 rounded-full text-xs bg-blue-100 text-blue-700">
                            Default
                          </span>
                        )}
                      </TableCell>
                      <TableCell>
                        <span className={`px-2 py-1 rounded-full text-xs ${vat.is_active ? 'bg-green-100 text-green-700' : 'bg-red-100 text-red-700'}`}>
                          {vat.is_active ? 'Aktiv' : 'Joaktiv'}
                        </span>
                      </TableCell>
                      <TableCell className="text-right">
                        <Button variant="ghost" size="icon" onClick={() => handleEditVat(vat)}>
                          <Edit2 className="h-4 w-4" />
                        </Button>
                        <Button variant="ghost" size="icon" className="text-red-500" onClick={() => handleDeleteVat(vat.id)}>
                          <Trash2 className="h-4 w-4" />
                        </Button>
                      </TableCell>
                    </TableRow>
                  ))}
                  {vatRates.length === 0 && (
                    <TableRow>
                      <TableCell colSpan={6} className="text-center py-8 text-gray-500">
                        Nuk ka norma TVSH të regjistruara
                      </TableCell>
                    </TableRow>
                  )}
                </TableBody>
              </Table>
            </CardContent>
          </Card>
        </TabsContent>
        <TabsContent value="kuponet">
          <CouponsTab />
        </TabsContent>
      </Tabs>

      {/* Branch Dialog */}
      <Dialog open={showBranchDialog} onOpenChange={setShowBranchDialog}>
        <DialogContent>
          <DialogHeader>
            <DialogTitle>{editingBranch ? 'Modifiko Filialin' : 'Shto Filial të Ri'}</DialogTitle>
          </DialogHeader>
          <div className="space-y-4 py-4">
            <div className="space-y-2">
              <Label>Emri i Filialit</Label>
              <Input
                value={branchForm.name}
                onChange={(e) => setbranchForm({ ...branchForm, name: e.target.value })}
                placeholder="p.sh. Dega Qendrore"
              />
            </div>
            <div className="space-y-2">
              <Label>Adresa</Label>
              <Input
                value={branchForm.address}
                onChange={(e) => setbranchForm({ ...branchForm, address: e.target.value })}
                placeholder="Adresa e filialit"
              />
            </div>
            <div className="space-y-2">
              <Label>Telefoni</Label>
              <Input
                value={branchForm.phone}
                onChange={(e) => setbranchForm({ ...branchForm, phone: e.target.value })}
                placeholder="+383 XX XXX XXX"
              />
            </div>
          </div>
          <DialogFooter>
            <Button variant="outline" onClick={() => setShowBranchDialog(false)}>Anulo</Button>
            <Button onClick={handleSaveBranch} className="bg-[#00a79d] hover:bg-[#008f86] rounded-xl shadow-md shadow-[#00a79d]/20">
              {editingBranch ? 'Ruaj' : 'Shto'}
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>

      {/* Warehouse Dialog */}
      <Dialog open={showWarehouseDialog} onOpenChange={setShowWarehouseDialog}>
        <DialogContent>
          <DialogHeader>
            <DialogTitle>{editingWarehouse ? 'Modifiko Depon' : 'Shto Depo të Re'}</DialogTitle>
          </DialogHeader>
          <div className="space-y-4 py-4">
            <div className="space-y-2">
              <Label>Emri i Depos *</Label>
              <Input
                value={warehouseForm.name}
                onChange={(e) => setWarehouseForm({ ...warehouseForm, name: e.target.value })}
                placeholder="p.sh. Depoja Qendrore"
              />
            </div>
            <div className="space-y-2">
              <Label>Kodi</Label>
              <Input
                value={warehouseForm.code}
                onChange={(e) => setWarehouseForm({ ...warehouseForm, code: e.target.value })}
                placeholder="p.sh. DEP-01"
              />
            </div>
            <div className="space-y-2">
              <Label>Adresa</Label>
              <Input
                value={warehouseForm.address}
                onChange={(e) => setWarehouseForm({ ...warehouseForm, address: e.target.value })}
                placeholder="Adresa e depos"
              />
            </div>
            <div className="space-y-2">
              <Label>Telefoni</Label>
              <Input
                value={warehouseForm.phone}
                onChange={(e) => setWarehouseForm({ ...warehouseForm, phone: e.target.value })}
                placeholder="+383 XX XXX XXX"
              />
            </div>
            <div className="flex items-center gap-4">
              <div className="flex items-center gap-2">
                <Switch
                  checked={warehouseForm.is_active}
                  onCheckedChange={(checked) => setWarehouseForm({ ...warehouseForm, is_active: checked })}
                />
                <Label>Aktive</Label>
              </div>
              <div className="flex items-center gap-2">
                <Switch
                  checked={warehouseForm.is_default}
                  onCheckedChange={(checked) => setWarehouseForm({ ...warehouseForm, is_default: checked })}
                />
                <Label>Default</Label>
              </div>
            </div>
          </div>
          <DialogFooter>
            <Button variant="outline" onClick={() => setShowWarehouseDialog(false)}>Anulo</Button>
            <Button onClick={handleSaveWarehouse} className="bg-[#00a79d] hover:bg-[#008f86] rounded-xl shadow-md shadow-[#00a79d]/20" disabled={!warehouseForm.name}>
              {editingWarehouse ? 'Ruaj' : 'Shto'}
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>

      {/* VAT Dialog */}
      <Dialog open={showVatDialog} onOpenChange={setShowVatDialog}>
        <DialogContent>
          <DialogHeader>
            <DialogTitle>{editingVat ? 'Modifiko Normën TVSH' : 'Shto Normë TVSH të Re'}</DialogTitle>
          </DialogHeader>
          <div className="space-y-4 py-4">
            <div className="space-y-2">
              <Label>Emri *</Label>
              <Input
                value={vatForm.name}
                onChange={(e) => setVatForm({ ...vatForm, name: e.target.value })}
                placeholder="p.sh. TVSH Standard"
              />
            </div>
            <div className="space-y-2">
              <Label>Norma (%) *</Label>
              <Input
                type="number"
                min="0"
                max="100"
                step="0.5"
                value={vatForm.rate}
                onChange={(e) => setVatForm({ ...vatForm, rate: parseFloat(e.target.value) || 0 })}
                placeholder="18"
              />
            </div>
            <div className="space-y-2">
              <Label>Kodi</Label>
              <Input
                value={vatForm.code}
                onChange={(e) => setVatForm({ ...vatForm, code: e.target.value })}
                placeholder="p.sh. 18"
              />
            </div>
            <div className="flex items-center gap-4">
              <div className="flex items-center gap-2">
                <Switch
                  checked={vatForm.is_active}
                  onCheckedChange={(checked) => setVatForm({ ...vatForm, is_active: checked })}
                />
                <Label>Aktive</Label>
              </div>
              <div className="flex items-center gap-2">
                <Switch
                  checked={vatForm.is_default}
                  onCheckedChange={(checked) => setVatForm({ ...vatForm, is_default: checked })}
                />
                <Label>Default</Label>
              </div>
            </div>
          </div>
          <DialogFooter>
            <Button variant="outline" onClick={() => setShowVatDialog(false)}>Anulo</Button>
            <Button onClick={handleSaveVat} className="bg-[#00a79d] hover:bg-[#008f86] rounded-xl shadow-md shadow-[#00a79d]/20" disabled={!vatForm.name}>
              {editingVat ? 'Ruaj' : 'Shto'}
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>

      {/* Comment Template Dialog */}
      <Dialog open={showCommentDialog} onOpenChange={setShowCommentDialog}>
        <DialogContent className="sm:max-w-md">
          <DialogHeader>
            <DialogTitle className="flex items-center gap-2">
              <MessageSquare className="h-5 w-5" />
              {editingComment ? 'Edito Komentin' : 'Shto Koment të Ri'}
            </DialogTitle>
          </DialogHeader>
          <div className="space-y-4">
            <div>
              <Label>Titulli</Label>
              <Input
                value={commentForm.title}
                onChange={(e) => setCommentForm({...commentForm, title: e.target.value})}
                placeholder="p.sh. Faleminderit"
              />
            </div>
            <div>
              <Label>Përmbajtja</Label>
              <Textarea
                value={commentForm.content}
                onChange={(e) => setCommentForm({...commentForm, content: e.target.value})}
                placeholder="p.sh. Faleminderit për blerjen! Ju mirëpresim përsëri."
                rows={4}
              />
            </div>
            <div className="flex items-center justify-between">
              <div className="flex items-center gap-2">
                <Switch
                  checked={commentForm.is_default}
                  onCheckedChange={(checked) => setCommentForm({...commentForm, is_default: checked})}
                />
                <Label className="cursor-pointer">Komenti Default</Label>
              </div>
              <div className="flex items-center gap-2">
                <Switch
                  checked={commentForm.is_active}
                  onCheckedChange={(checked) => setCommentForm({...commentForm, is_active: checked})}
                />
                <Label className="cursor-pointer">Aktiv</Label>
              </div>
            </div>
            {commentForm.is_default && (
              <p className="text-xs text-gray-500">
                Ky koment do të zgjidhet automatikisht kur printoni kuponin.
              </p>
            )}
          </div>
          <DialogFooter>
            <Button variant="outline" onClick={() => setShowCommentDialog(false)}>Anulo</Button>
            <Button 
              onClick={handleSaveComment} 
              className="bg-[#00a79d] hover:bg-[#008f86] rounded-xl shadow-md shadow-[#00a79d]/20" 
              disabled={!commentForm.title || !commentForm.content || loading}
            >
              {loading ? 'Duke ruajtur...' : (editingComment ? 'Ruaj' : 'Shto')}
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>
    </div>
  );
};

export default Settings;
