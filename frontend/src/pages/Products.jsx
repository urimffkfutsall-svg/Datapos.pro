import React, { useState, useEffect, useRef } from 'react';
import { api } from '../App';
import { toast } from 'sonner';
import { Card, CardContent, CardHeader, CardTitle } from '../components/ui/card';
import { Button } from '../components/ui/button';
import { Input } from '../components/ui/input';
import { Label } from '../components/ui/label';
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
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from '../components/ui/table';
import { Badge } from '../components/ui/badge';
import {
  Plus,
  Search,
  Edit2,
  Trash2,
  Package,
  Download,
  Upload,
  Filter,
  Image as ImageIcon,
  X,
  Boxes,
} from 'lucide-react';

const Products = () => {
  const [products, setProducts] = useState([]);
  const [categories, setCategories] = useState([]);
  const [branches, setBranches] = useState([]);
  const [loading, setLoading] = useState(true);
  const [search, setSearch] = useState('');
  const [categoryFilter, setCategoryFilter] = useState('all');
  const [showDialog, setShowDialog] = useState(false);
  const [editingProduct, setEditingProduct] = useState(null);
  const [stockAdjustQty, setStockAdjustQty] = useState('');
  const [stockAdjustReason, setStockAdjustReason] = useState('');
  const [stockAdjustLoading, setStockAdjustLoading] = useState(false);
  const importInputRef = useRef(null);
  const [formData, setFormData] = useState({
    name: '',
    barcode: '',
    purchase_price: '',
    sale_price: '',
    category: '',
    subcategory: '',
    vat_rate: '0',
    expiry_date: '',
    supplier: '',
    unit: 'copë',
    initial_stock: '',
    branch_id: '',
    image_url: '',
    is_package: false,
    units_per_package: '',
    package_price: '',
  });

  useEffect(() => {
    loadData();
  }, [categoryFilter]);

  // Llogarit automatikisht çmimin e pakos: package_price = units × sale_price
  useEffect(() => {
    if (!formData.is_package) return;
    const sp = parseFloat(formData.sale_price);
    const u = parseFloat(formData.units_per_package);
    if (sp > 0 && u > 0) {
      const total = (sp * u).toFixed(2);
      setFormData((prev) => (prev.package_price === total ? prev : { ...prev, package_price: total }));
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [formData.is_package, formData.sale_price, formData.units_per_package]);

const handleStockAdjust = async (type) => {
  if (!editingProduct) return;
  const qty = parseFloat(stockAdjustQty);
  if (!qty || qty <= 0) { toast.error('Vendos një sasi të vlefshme'); return; }
  if (!stockAdjustReason.trim()) { toast.error('Shkruaj arsyen e ndryshimit'); return; }
  try {
    setStockAdjustLoading(true);
    await api.post('/stock/movements', {
      product_id: editingProduct.id,
      movement_type: type,
      quantity: qty,
      reason: stockAdjustReason.trim(),
      branch_id: editingProduct.branch_id || null,
    });
    toast.success(type === 'in' ? '+' + qty + ' u shtua në stok' : '-' + qty + ' u hoq nga stoku');
    setStockAdjustQty('');
    setStockAdjustReason('');
    await loadData();
  } catch (err) {
    toast.error(err.response?.data?.detail || 'Gabim gjatë ndryshimit të stokut');
  } finally {
    setStockAdjustLoading(false);
  }
};
  const loadData = async () => {
    try {
      setLoading(true);
      const params = categoryFilter !== 'all' ? { category: categoryFilter } : {};
      const [productsRes, categoriesRes, branchesRes] = await Promise.all([
        api.get('/products', { params }),
        api.get('/categories'),
        api.get('/branches')
      ]);
      setProducts(productsRes.data);
      setCategories(categoriesRes.data);
      setBranches(branchesRes.data);
    } catch (error) {
      console.error('Error loading products:', error);
      toast.error('Gabim gjatë ngarkimit të produkteve');
    } finally {
      setLoading(false);
    }
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    try {
      const metadata = {
        ...(editingProduct && editingProduct.metadata ? editingProduct.metadata : {}),
        image_url: formData.image_url || null,
        is_package: !!formData.is_package,
        units_per_package: formData.is_package && formData.units_per_package ? parseInt(formData.units_per_package, 10) : null,
        package_price: formData.is_package && formData.package_price ? parseFloat(formData.package_price) : null,
      };

      const data = {
        name: formData.name,
        barcode: formData.barcode,
        category: formData.category,
        subcategory: formData.subcategory,
        supplier: formData.supplier,
        unit: formData.unit,
        expiry_date: formData.expiry_date,
        purchase_price: formData.purchase_price ? parseFloat(formData.purchase_price) : null,
        sale_price: formData.sale_price ? parseFloat(formData.sale_price) : null,
        vat_rate: formData.vat_rate ? parseFloat(formData.vat_rate) : null,
        initial_stock: formData.initial_stock ? parseFloat(formData.initial_stock) : 0,
        branch_id: formData.branch_id || null,
        metadata,
      };

      if (editingProduct) {
        await api.put(`/products/${editingProduct.id}`, data);
        toast.success('Produkti u përditësua me sukses');
      } else {
        await api.post('/products', data);
        toast.success('Produkti u shtua me sukses');
      }

      setShowDialog(false);
      resetForm();
      loadData();
    } catch (error) {
      toast.error(error.response?.data?.detail || 'Gabim gjatë ruajtjes');
    }
  };

  const handleImageChange = (e) => {
    const file = e.target.files?.[0];
    if (!file) return;
    if (!file.type.startsWith('image/')) {
      toast.error('Ju lutem zgjidhni një skedar fotografie');
      return;
    }
    if (file.size > 2 * 1024 * 1024) {
      toast.error('Fotoja është shumë e madhe (maksimumi 2MB)');
      return;
    }
    const reader = new FileReader();
    reader.onload = () => setFormData((prev) => ({ ...prev, image_url: reader.result }));
    reader.onerror = () => toast.error('Gabim gjatë leximit të fotos');
    reader.readAsDataURL(file);
  };

  const csvEscape = (v) => {
    const s = (v === null || v === undefined) ? '' : String(v);
    return '"' + s.replace(/"/g, '""') + '"';
  };

  const handleExport = () => {
    if (!products || products.length === 0) {
      toast.error('Nuk ka produkte për eksport');
      return;
    }
    const headers = ['name', 'barcode', 'purchase_price', 'sale_price', 'category', 'subcategory', 'vat_rate', 'unit', 'supplier', 'expiry_date', 'current_stock'];
    const lines = [headers.join(',')];
    products.forEach((p) => {
      lines.push(headers.map((h) => csvEscape(p[h])).join(','));
    });
    const csv = lines.join('\n');
    const blob = new Blob(['\ufeff' + csv], { type: 'text/csv;charset=utf-8;' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `produktet_${new Date().toISOString().slice(0, 10)}.csv`;
    document.body.appendChild(a);
    a.click();
    document.body.removeChild(a);
    URL.revokeObjectURL(url);
    toast.success(`U eksportuan ${products.length} produkte`);
  };

  const parseCSV = (text) => {
    const rows = [];
    let row = [];
    let field = '';
    let inQuotes = false;
    for (let i = 0; i < text.length; i++) {
      const c = text[i];
      if (inQuotes) {
        if (c === '"') {
          if (text[i + 1] === '"') { field += '"'; i++; }
          else { inQuotes = false; }
        } else { field += c; }
      } else {
        if (c === '"') { inQuotes = true; }
        else if (c === ',') { row.push(field); field = ''; }
        else if (c === '\n') { row.push(field); rows.push(row); row = []; field = ''; }
        else if (c === '\r') { /* injoro */ }
        else { field += c; }
      }
    }
    if (field !== '' || row.length > 0) { row.push(field); rows.push(row); }
    return rows;
  };

  const handleImportFile = async (e) => {
    const file = e.target.files?.[0];
    if (!file) return;
    try {
      const raw = await file.text();
      const text = raw.replace(/^\ufeff/, '');
      const rows = parseCSV(text).filter((r) => r.length && r.some((c) => (c || '').trim() !== ''));
      if (rows.length < 2) {
        toast.error('Skedari është bosh ose pa rreshta të dhënash');
        return;
      }
      const headers = rows[0].map((h) => (h || '').trim());
      const idx = (name) => headers.indexOf(name);
      const get = (cols, name) => {
        const i = idx(name);
        return i >= 0 ? (cols[i] || '').trim() : '';
      };
      let ok = 0;
      let fail = 0;
      for (let r = 1; r < rows.length; r++) {
        const cols = rows[r];
        const name = get(cols, 'name');
        if (!name) { fail++; continue; }
        const payload = {
          name,
          barcode: get(cols, 'barcode') || null,
          purchase_price: get(cols, 'purchase_price') ? parseFloat(get(cols, 'purchase_price')) : null,
          sale_price: get(cols, 'sale_price') ? parseFloat(get(cols, 'sale_price')) : null,
          category: get(cols, 'category') || null,
          subcategory: get(cols, 'subcategory') || null,
          vat_rate: get(cols, 'vat_rate') ? parseFloat(get(cols, 'vat_rate')) : null,
          unit: get(cols, 'unit') || 'copë',
          supplier: get(cols, 'supplier') || null,
          expiry_date: get(cols, 'expiry_date') || null,
          initial_stock: get(cols, 'current_stock') ? parseFloat(get(cols, 'current_stock')) : 0,
        };
        try {
          await api.post('/products', payload);
          ok++;
        } catch (err) {
          fail++;
        }
      }
      if (ok > 0) toast.success(`Importi përfundoi: ${ok} u shtuan${fail > 0 ? `, ${fail} dështuan` : ''}`);
      else toast.error(`Asnjë produkt nuk u shtua (${fail} dështuan)`);
      loadData();
    } catch (err) {
      toast.error('Gabim gjatë importimit të skedarit');
    } finally {
      e.target.value = '';
    }
  };

  const handleEdit = (product) => {
    setEditingProduct(product);
    const md = product.metadata || {};
    setFormData({
      name: product.name || '',
      barcode: product.barcode || '',
      purchase_price: product.purchase_price?.toString() || '',
      sale_price: product.sale_price?.toString() || '',
      category: product.category || '',
      subcategory: product.subcategory || '',
      vat_rate: product.vat_rate?.toString() || '0',
      expiry_date: product.expiry_date || '',
      supplier: product.supplier || '',
      unit: product.unit || 'copë',
      initial_stock: '',
      branch_id: product.branch_id || '',
      image_url: md.image_url || '',
      is_package: !!md.is_package,
      units_per_package: md.units_per_package != null ? String(md.units_per_package) : '',
      package_price: md.package_price != null ? String(md.package_price) : '',
    });
    setShowDialog(true);
  };

  const handleDelete = async (product) => {
    if (!window.confirm(`Jeni të sigurt që doni të fshini produktin "${product.name || product.id}"?`)) {
      return;
    }

    try {
      await api.delete(`/products/${product.id}`);
      toast.success('Produkti u fshi me sukses');
      loadData();
    } catch (error) {
      toast.error(error.response?.data?.detail || 'Gabim gjatë fshirjes');
    }
  };

  const resetForm = () => {
    setEditingProduct(null);
    setStockAdjustQty('');
    setStockAdjustReason('');
    setFormData({
      name: '',
      barcode: '',
      purchase_price: '',
      sale_price: '',
      category: '',
      subcategory: '',
      vat_rate: '0',
      expiry_date: '',
      supplier: '',
      unit: 'copë',
      initial_stock: '',
      branch_id: '',
      image_url: '',
      is_package: false,
      units_per_package: '',
      package_price: '',
    });
  };

  const filteredProducts = products.filter((p) =>
    (p.name?.toLowerCase().includes(search.toLowerCase()) ||
      p.barcode?.includes(search) ||
      p.category?.toLowerCase().includes(search.toLowerCase()))
  );

  const getStockStatus = (stock) => {
    if (stock <= 0) return { label: 'Pa stok', variant: 'destructive' };
    if (stock < 10) return { label: 'I ulët', variant: 'warning' };
    return { label: 'Në stok', variant: 'success' };
  };

  const perUnitPreview = (() => {
    const pp = parseFloat(formData.package_price);
    const u = parseFloat(formData.units_per_package);
    if (pp > 0 && u > 0) return (pp / u).toFixed(2);
    return null;
  })();

  return (
    <div className="space-y-6 animate-fade-in" data-testid="products-page">
      {/* Header */}
      <div className="flex flex-col md:flex-row md:items-center md:justify-between gap-4">
        <div>
          <h1 className="text-2xl font-bold text-gray-900">Produktet</h1>
          <p className="text-gray-500">Menaxho produktet e marketit</p>
        </div>
        <div className="flex gap-2">
          <Button variant="outline" className="gap-2" onClick={handleExport}>
            <Download className="h-4 w-4" />
            Eksporto
          </Button>
          <Button variant="outline" className="gap-2" onClick={() => importInputRef.current?.click()}>
            <Upload className="h-4 w-4" />
            Importo
          </Button>
          <input
            ref={importInputRef}
            type="file"
            accept=".csv,text/csv"
            className="hidden"
            onChange={handleImportFile}
          />
          <Button
            className="bg-[#2563EB] hover:bg-[#1D4ED8] gap-2"
            onClick={() => {
              resetForm();
              setShowDialog(true);
            }}
            data-testid="add-product-btn"
          >
            <Plus className="h-4 w-4" />
            Shto Produkt
          </Button>
        </div>
      </div>

      {/* Filters */}
      <Card className="border border-gray-200/60 rounded-3xl shadow-sm bg-white/80 backdrop-blur-md">
        <CardContent className="p-4">
          <div className="flex flex-col md:flex-row gap-4">
            <div className="flex-1 relative">
              <Search className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-gray-400" />
              <Input
                placeholder="Kërko sipas emrit, barkodit ose kategorisë..."
                value={search}
                onChange={(e) => setSearch(e.target.value)}
                className="pl-10"
                data-testid="search-products"
              />
            </div>
            <Select value={categoryFilter} onValueChange={setCategoryFilter}>
              <SelectTrigger className="w-[200px]" data-testid="category-filter">
                <Filter className="h-4 w-4 mr-2" />
                <SelectValue placeholder="Kategoria" />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="all">Të gjitha</SelectItem>
                {categories.map((cat) => (
                  <SelectItem key={cat} value={cat}>{cat}</SelectItem>
                ))}
              </SelectContent>
            </Select>
          </div>
        </CardContent>
      </Card>

      {/* Products Table */}
      <Card className="border border-gray-200/60 rounded-3xl shadow-sm bg-white/80 backdrop-blur-md">
        <CardContent className="p-0">
          {loading ? (
            <div className="flex items-center justify-center py-12">
              <div className="spinner" />
            </div>
          ) : filteredProducts.length === 0 ? (
            <div className="text-center py-12">
              <Package className="h-12 w-12 mx-auto text-gray-300 mb-4" />
              <p className="text-gray-500">Nuk u gjetën produkte</p>
            </div>
          ) : (
            <Table>
              <TableHeader>
                <TableRow className="bg-[#2563EB]/8 hover:bg-[#2563EB]/8 border-b border-[#2563EB]/15">
                  <TableHead className="w-[64px]">Foto</TableHead>
                  <TableHead>Emri</TableHead>
                  <TableHead>Barkodi</TableHead>
                  <TableHead>Kategoria</TableHead>
                  <TableHead className="text-right">Ç. Blerjes</TableHead>
                  <TableHead className="text-right">Ç. Shitjes</TableHead>
                  <TableHead className="text-center">Stoku</TableHead>
                  <TableHead className="text-center">Statusi</TableHead>
                  <TableHead className="text-right">Veprime</TableHead>
                </TableRow>
              </TableHeader>
              <TableBody>
                {filteredProducts.map((product) => {
                  const stockStatus = getStockStatus(product.current_stock);
                  return (
                    <TableRow key={product.id} className="table-row-hover">
                      <TableCell>
                        {product.metadata?.image_url ? (
                          <img
                            src={product.metadata.image_url}
                            alt={product.name || ''}
                            className="h-10 w-10 rounded-lg object-cover border border-gray-200"
                          />
                        ) : (
                          <div className="h-10 w-10 rounded-lg bg-gray-100 flex items-center justify-center text-gray-300">
                            <ImageIcon className="h-5 w-5" />
                          </div>
                        )}
                      </TableCell>
                      <TableCell className="font-medium">
                        <div className="flex items-center gap-2">
                          <span>{product.name || '-'}</span>
                          {product.metadata?.is_package && (
                            <Badge className="bg-[#2563EB]/10 text-[#2563EB] text-xs">Pako</Badge>
                          )}
                        </div>
                      </TableCell>
                      <TableCell className="font-mono text-sm">{product.barcode || '-'}</TableCell>
                      <TableCell>{product.category || '-'}</TableCell>
                      <TableCell className="text-right">
                        {product.purchase_price ? `€${product.purchase_price.toFixed(2)}` : '-'}
                      </TableCell>
                      <TableCell className="text-right font-semibold">
                        {product.sale_price ? `€${product.sale_price.toFixed(2)}` : '-'}
                      </TableCell>
                      <TableCell className="text-center">{product.current_stock || 0}</TableCell>
                      <TableCell className="text-center">
                        <Badge
                          variant={stockStatus.variant}
                          className={
                            stockStatus.variant === 'success' ? 'bg-green-100 text-green-700' :
                            stockStatus.variant === 'warning' ? 'bg-orange-100 text-orange-700' :
                            'bg-red-100 text-red-700'
                          }
                        >
                          {stockStatus.label}
                        </Badge>
                      </TableCell>
                      <TableCell className="text-right">
                        <div className="flex justify-end gap-1">
                          <Button
                            variant="ghost"
                            size="icon"
                            onClick={() => handleEdit(product)}
                            data-testid={`edit-product-${product.id}`}
                          >
                            <Edit2 className="h-4 w-4" />
                          </Button>
                          <Button
                            variant="ghost"
                            size="icon"
                            className="text-red-500 hover:text-red-700"
                            onClick={() => handleDelete(product)}
                            data-testid={`delete-product-${product.id}`}
                          >
                            <Trash2 className="h-4 w-4" />
                          </Button>
                        </div>
                      </TableCell>
                    </TableRow>
                  );
                })}
              </TableBody>
            </Table>
          )}
        </CardContent>
      </Card>

      {/* Add/Edit Product Dialog */}
      <Dialog open={showDialog} onOpenChange={setShowDialog}>
        <DialogContent className="sm:max-w-2xl max-h-[90vh] overflow-y-auto">
          <DialogHeader>
            <DialogTitle>{editingProduct ? 'Modifiko Produktin' : 'Shto Produkt të Ri'}</DialogTitle>
          </DialogHeader>
          <form onSubmit={handleSubmit}>
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4 py-4">
              <div className="space-y-2">
                <Label htmlFor="name">Emri</Label>
                <Input
                  id="name"
                  value={formData.name}
                  onChange={(e) => setFormData({ ...formData, name: e.target.value })}
                  placeholder="Emri i produktit"
                  data-testid="product-name-input"
                />
              </div>

              <div className="space-y-2">
                <Label htmlFor="barcode">Barkodi</Label>
                <Input
                  id="barcode"
                  value={formData.barcode}
                  onChange={(e) => setFormData({ ...formData, barcode: e.target.value })}
                  placeholder="Barkodi"
                  data-testid="product-barcode-input"
                />
              </div>

              <div className="space-y-2">
                <Label htmlFor="purchase_price">Çmimi i Blerjes (€)</Label>
                <Input
                  id="purchase_price"
                  type="number"
                  step="0.01"
                  value={formData.purchase_price}
                  onChange={(e) => setFormData({ ...formData, purchase_price: e.target.value })}
                  placeholder="0.00"
                  data-testid="product-purchase-price-input"
                />
              </div>

              <div className="space-y-2">
                <Label htmlFor="sale_price">Çmimi i Shitjes (€)</Label>
                <Input
                  id="sale_price"
                  type="number"
                  step="0.01"
                  value={formData.sale_price}
                  onChange={(e) => setFormData({ ...formData, sale_price: e.target.value })}
                  placeholder="0.00"
                  data-testid="product-sale-price-input"
                />
              </div>

              <div className="space-y-2">
                <Label htmlFor="category">Kategoria</Label>
                <Input
                  id="category"
                  value={formData.category}
                  onChange={(e) => setFormData({ ...formData, category: e.target.value })}
                  placeholder="p.sh. Ushqimore"
                  data-testid="product-category-input"
                />
              </div>

              <div className="space-y-2">
                <Label htmlFor="subcategory">Nënkategoria</Label>
                <Input
                  id="subcategory"
                  value={formData.subcategory}
                  onChange={(e) => setFormData({ ...formData, subcategory: e.target.value })}
                  placeholder="p.sh. Qumësht"
                />
              </div>

              <div className="space-y-2">
                <Label htmlFor="vat_rate">TVSH (%)</Label>
                <Select
                  value={formData.vat_rate}
                  onValueChange={(value) => setFormData({ ...formData, vat_rate: value })}
                >
                  <SelectTrigger data-testid="product-vat-select">
                    <SelectValue />
                  </SelectTrigger>
                  <SelectContent>
                    <SelectItem value="0">0%</SelectItem>
                    <SelectItem value="8">8%</SelectItem>
                    <SelectItem value="18">18%</SelectItem>
                    <SelectItem value="20">20%</SelectItem>
                  </SelectContent>
                </Select>
              </div>

              <div className="space-y-2">
                <Label htmlFor="unit">Njësia Matëse</Label>
                <Select
                  value={formData.unit}
                  onValueChange={(value) => setFormData({ ...formData, unit: value })}
                >
                  <SelectTrigger>
                    <SelectValue />
                  </SelectTrigger>
                  <SelectContent>
                    <SelectItem value="copë">Copë</SelectItem>
                    <SelectItem value="kg">Kilogram</SelectItem>
                    <SelectItem value="l">Litër</SelectItem>
                    <SelectItem value="m">Metër</SelectItem>
                    <SelectItem value="pako">Pako</SelectItem>
                  </SelectContent>
                </Select>
              </div>

              <div className="space-y-2">
                <Label htmlFor="supplier">Furnitori</Label>
                <Input
                  id="supplier"
                  value={formData.supplier}
                  onChange={(e) => setFormData({ ...formData, supplier: e.target.value })}
                  placeholder="Emri i furnitorit"
                />
              </div>

              <div className="space-y-2">
                <Label htmlFor="expiry_date">Data e Skadencës</Label>
                <Input
                  id="expiry_date"
                  type="date"
                  value={formData.expiry_date}
                  onChange={(e) => setFormData({ ...formData, expiry_date: e.target.value })}
                />
              </div>

              {!editingProduct && (
                <div className="space-y-2">
                  <Label htmlFor="initial_stock">Stoku Fillestar</Label>
                  <Input
                    id="initial_stock"
                    type="number"
                    value={formData.initial_stock}
                    onChange={(e) => setFormData({ ...formData, initial_stock: e.target.value })}
                    placeholder="0"
                    data-testid="product-stock-input"
                  />
                </div>
              )}

              {branches.length > 0 && (
                <div className="space-y-2">
                  <Label htmlFor="branch">Dega</Label>
                  <Select
                    value={formData.branch_id || 'all'}
                    onValueChange={(value) => setFormData({ ...formData, branch_id: value === 'all' ? '' : value })}
                  >
                    <SelectTrigger>
                      <SelectValue placeholder="Zgjidh degën" />
                    </SelectTrigger>
                    <SelectContent>
                      <SelectItem value="all">Të gjitha</SelectItem>
                      {branches.map((branch) => (
                        <SelectItem key={branch.id} value={branch.id}>{branch.name}</SelectItem>
                      ))}
                    </SelectContent>
                  </Select>
                </div>
              )}

              {/* Fotografia e produktit */}
              <div className="space-y-2 md:col-span-2">
                <Label>Fotografia e Produktit</Label>
                <div className="flex items-center gap-4">
                  <div className="h-20 w-20 rounded-2xl border border-gray-200 bg-gray-50 flex items-center justify-center overflow-hidden shrink-0">
                    {formData.image_url ? (
                      <img src={formData.image_url} alt="produkt" className="h-full w-full object-cover" />
                    ) : (
                      <ImageIcon className="h-7 w-7 text-gray-300" />
                    )}
                  </div>
                  <div className="flex flex-col gap-2">
                    <label className="inline-flex items-center gap-2 px-4 h-10 rounded-xl border border-gray-200 bg-white hover:bg-gray-50 cursor-pointer text-sm font-medium text-gray-700 transition-colors">
                      <Upload className="h-4 w-4" />
                      Ngarko foto
                      <input type="file" accept="image/*" className="hidden" onChange={handleImageChange} />
                    </label>
                    {formData.image_url && (
                      <button
                        type="button"
                        onClick={() => setFormData({ ...formData, image_url: '' })}
                        className="inline-flex items-center gap-1 text-sm text-red-500 hover:text-red-700"
                      >
                        <X className="h-4 w-4" />
                        Hiq foton
                      </button>
                    )}
                    <p className="text-xs text-gray-400">PNG, JPG. Maksimumi 2MB.</p>
                  </div>
                </div>
              </div>

              {/* Pako */}
              <div className="space-y-3 md:col-span-2 rounded-2xl border border-gray-200 bg-gray-50/70 p-4">
                <label className="flex items-center gap-3 cursor-pointer">
                  <input
                    type="checkbox"
                    checked={formData.is_package}
                    onChange={(e) => setFormData({ ...formData, is_package: e.target.checked })}
                    className="h-4 w-4 accent-[#2563EB]"
                  />
                  <span className="flex items-center gap-2 text-sm font-medium text-gray-800">
                    <Boxes className="h-4 w-4 text-[#2563EB]" />
                    Ky produkt është pako (përmban disa copë)
                  </span>
                </label>

                {formData.is_package && (
                  <div className="grid grid-cols-1 sm:grid-cols-2 gap-4 pt-1">
                    <div className="space-y-2">
                      <Label htmlFor="units_per_package">Sa copë ka pakoja</Label>
                      <Input
                        id="units_per_package"
                        type="number"
                        step="1"
                        min="1"
                        value={formData.units_per_package}
                        onChange={(e) => setFormData({ ...formData, units_per_package: e.target.value })}
                        placeholder="p.sh. 24"
                      />
                    </div>
                    <div className="space-y-2">
                      <Label>Çmimi i Pakos (€) — automatik</Label>
                      <div className="flex items-center rounded-xl bg-[#2563EB]/10 border border-[#2563EB]/20 px-4 h-10">
                        <span className="text-lg font-bold text-[#2563EB]">€{formData.package_price || '0.00'}</span>
                      </div>
                    </div>
                    <div className="sm:col-span-2">
                      <p className="text-xs text-gray-500">Çmimi i pakos llogaritet automatikisht: <strong>Sa copë × Çmimi i Shitjes</strong>. Shembull: 12 × €4 = €48.</p>
                    </div>
                  </div>
                )}
              </div>
{editingProduct && (
  <div className="space-y-3 md:col-span-2 rounded-2xl border border-amber-200 bg-amber-50/40 p-4">
    <div className="flex items-center gap-2 text-sm font-semibold text-amber-900">
      <Boxes className="h-4 w-4" />
      Modifiko Stokun
    </div>
    <p className="text-xs text-gray-600">Stoku aktual: <strong>{editingProduct.current_stock ?? 0}</strong></p>
    <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
      <div className="space-y-1">
        <Label htmlFor="stock_adjust_qty">Sasia</Label>
        <Input id="stock_adjust_qty" type="number" step="1" min="1" value={stockAdjustQty} onChange={(e) => setStockAdjustQty(e.target.value)} placeholder="p.sh. 10" />
      </div>
      <div className="space-y-1">
        <Label htmlFor="stock_adjust_reason">Arsyeja</Label>
        <Input id="stock_adjust_reason" type="text" value={stockAdjustReason} onChange={(e) => setStockAdjustReason(e.target.value)} placeholder="p.sh. Furnizim, Kthim, Dëmtim" />
      </div>
    </div>
    <div className="flex gap-2 pt-1">
      <Button type="button" onClick={() => handleStockAdjust('in')} disabled={stockAdjustLoading} className="bg-emerald-500 hover:bg-emerald-600 text-white rounded-xl flex-1">
        + Shto në stok
      </Button>
      <Button type="button" onClick={() => handleStockAdjust('out')} disabled={stockAdjustLoading} className="bg-red-500 hover:bg-red-600 text-white rounded-xl flex-1">
        − Hiq nga stoku
      </Button>
    </div>
  </div>
)}
            </div>

            <DialogFooter>
              <Button type="button" variant="outline" onClick={() => setShowDialog(false)}>
                Anulo
              </Button>
              <Button type="submit" className="bg-[#2563EB] hover:bg-[#1D4ED8] rounded-xl shadow-md shadow-[#2563EB]/20" data-testid="save-product-btn">
                {editingProduct ? 'Ruaj Ndryshimet' : 'Shto Produktin'}
              </Button>
            </DialogFooter>
          </form>
        </DialogContent>
      </Dialog>
    </div>
  );
};

export default Products;