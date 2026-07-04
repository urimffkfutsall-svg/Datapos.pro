import React, { useState, useEffect } from 'react';
import { api } from '../App';
import { toast } from 'sonner';
import { Card, CardContent, CardHeader, CardTitle } from '../components/ui/card';
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
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from '../components/ui/table';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '../components/ui/tabs';
import { Badge } from '../components/ui/badge';
import {
  Plus,
  Minus,
  ArrowDownCircle,
  ArrowUpCircle,
  Package,
  AlertTriangle,
  Search,
  RefreshCw
} from 'lucide-react';

const Stock = () => {
  const [products, setProducts] = useState([]);
  const [movements, setMovements] = useState([]);
  const [loading, setLoading] = useState(true);
  const [search, setSearch] = useState('');
  const [showMovementDialog, setShowMovementDialog] = useState(false);
  const [movementData, setMovementData] = useState({
    product_id: '',
    quantity: '',
    movement_type: 'in',
    reason: ''
  });

  useEffect(() => {
    loadData();
  }, []);

  const loadData = async () => {
    try {
      setLoading(true);
      const [productsRes, movementsRes] = await Promise.all([
        api.get('/products'),
        api.get('/stock/movements')
      ]);
      setProducts(productsRes.data);
      setMovements(movementsRes.data);
    } catch (error) {
      console.error('Error loading stock data:', error);
      toast.error('Gabim gjatë ngarkimit të të dhënave');
    } finally {
      setLoading(false);
    }
  };

  const handleMovement = async (e) => {
    e.preventDefault();
    try {
      await api.post('/stock/movements', {
        ...movementData,
        quantity: parseFloat(movementData.quantity)
      });
      toast.success('Lëvizja e stokut u regjistrua');
      setShowMovementDialog(false);
      setMovementData({ product_id: '', quantity: '', movement_type: 'in', reason: '' });
      loadData();
    } catch (error) {
      toast.error(error.response?.data?.detail || 'Gabim gjatë regjistrimit');
    }
  };

  const filteredProducts = products.filter(p =>
    p.name?.toLowerCase().includes(search.toLowerCase()) ||
    p.barcode?.includes(search)
  );

  const lowStockProducts = products.filter(p => p.current_stock < 10);
  const outOfStockProducts = products.filter(p => p.current_stock <= 0);

  const getStockBadge = (stock) => {
    if (stock <= 0) return <Badge className="bg-red-100 text-red-700">Pa stok</Badge>;
    if (stock < 10) return <Badge className="bg-orange-100 text-orange-700">I ulët</Badge>;
    if (stock < 50) return <Badge className="bg-yellow-100 text-yellow-700">Mesatar</Badge>;
    return <Badge className="bg-green-100 text-green-700">Mirë</Badge>;
  };

  return (
    <div className="space-y-6 animate-fade-in" data-testid="stock-page">
      {/* Header */}
      <div className="flex flex-col md:flex-row md:items-center md:justify-between gap-4">
        <div>
          <h1 className="text-2xl font-bold text-gray-900">Menaxhimi i Stokut</h1>
          <p className="text-gray-500">Kontrollo dhe menaxho stokun e produkteve</p>
        </div>
        <div className="flex gap-2">
          <Button variant="outline" onClick={loadData} className="gap-2">
            <RefreshCw className="h-4 w-4" />
            Rifresko
          </Button>
          <Button
            className="bg-[#2563EB] hover:bg-[#1D4ED8] gap-2 rounded-xl shadow-md shadow-[#2563EB]/20"
            onClick={() => setShowMovementDialog(true)}
            data-testid="add-movement-btn"
          >
            <Plus className="h-4 w-4" />
            Lëvizje Stoku
          </Button>
        </div>
      </div>

      {/* Stats Cards */}
      <div className="grid grid-cols-1 sm:grid-cols-3 gap-4">
        <Card className="border border-gray-200/60 rounded-3xl shadow-sm bg-white/80 backdrop-blur-md">
          <CardContent className="p-6">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm text-gray-500">Total Produktet</p>
                <p className="text-3xl font-bold mt-1">{products.length}</p>
              </div>
              <div className="h-12 w-12 rounded-2xl bg-blue-100 flex items-center justify-center">
                <Package className="h-6 w-6 text-blue-600" />
              </div>
            </div>
          </CardContent>
        </Card>

        <Card className="border border-gray-200/60 rounded-3xl shadow-sm bg-white/80 backdrop-blur-md">
          <CardContent className="p-6">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm text-gray-500">Stok i Ulët</p>
                <p className="text-3xl font-bold mt-1 text-orange-500">{lowStockProducts.length}</p>
              </div>
              <div className="h-12 w-12 rounded-2xl bg-orange-100 flex items-center justify-center">
                <AlertTriangle className="h-6 w-6 text-orange-500" />
              </div>
            </div>
          </CardContent>
        </Card>

        <Card className="border border-gray-200/60 rounded-3xl shadow-sm bg-white/80 backdrop-blur-md">
          <CardContent className="p-6">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm text-gray-500">Pa Stok</p>
                <p className="text-3xl font-bold mt-1 text-red-500">{outOfStockProducts.length}</p>
              </div>
              <div className="h-12 w-12 rounded-2xl bg-red-100 flex items-center justify-center">
                <Package className="h-6 w-6 text-red-500" />
              </div>
            </div>
          </CardContent>
        </Card>
      </div>

      {/* Tabs */}
      <Tabs defaultValue="levels" className="space-y-4">
        <TabsList>
          <TabsTrigger value="levels" data-testid="stock-levels-tab">Nivelet e Stokut</TabsTrigger>
          <TabsTrigger value="movements" data-testid="stock-movements-tab">Historia e Lëvizjeve</TabsTrigger>
          <TabsTrigger value="alerts" data-testid="stock-alerts-tab">
            Alarme ({lowStockProducts.length})
          </TabsTrigger>
        </TabsList>

        {/* Stock Levels Tab */}
        <TabsContent value="levels">
          <Card className="border border-gray-200/60 rounded-3xl shadow-sm bg-white/80 backdrop-blur-md">
            <CardHeader className="pb-4">
              <div className="flex items-center gap-4">
                <div className="flex-1 relative">
                  <Search className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-gray-400" />
                  <Input
                    placeholder="Kërko produkt..."
                    value={search}
                    onChange={(e) => setSearch(e.target.value)}
                    className="pl-10"
                    data-testid="search-stock"
                  />
                </div>
              </div>
            </CardHeader>
            <CardContent className="p-0">
              {loading ? (
                <div className="flex items-center justify-center py-12">
                  <div className="spinner" />
                </div>
              ) : (
                <Table>
                  <TableHeader>
                    <TableRow className="bg-[#2563EB]/8 hover:bg-[#2563EB]/8 border-b border-[#2563EB]/15">
                      <TableHead>Produkti</TableHead>
                      <TableHead>Barkodi</TableHead>
                      <TableHead>Kategoria</TableHead>
                      <TableHead className="text-center">Stoku Aktual</TableHead>
                      <TableHead className="text-center">Statusi</TableHead>
                      <TableHead className="text-right">Vlera</TableHead>
                    </TableRow>
                  </TableHeader>
                  <TableBody>
                    {filteredProducts.map((product) => (
                      <TableRow key={product.id} className="table-row-hover">
                        <TableCell className="font-medium">{product.name || '-'}</TableCell>
                        <TableCell className="font-mono text-sm">{product.barcode || '-'}</TableCell>
                        <TableCell>{product.category || '-'}</TableCell>
                        <TableCell className="text-center font-semibold">
                          {product.current_stock} {product.unit || ''}
                        </TableCell>
                        <TableCell className="text-center">
                          {getStockBadge(product.current_stock)}
                        </TableCell>
                        <TableCell className="text-right">
                          €{((product.current_stock || 0) * (product.purchase_price || 0)).toFixed(2)}
                        </TableCell>
                      </TableRow>
                    ))}
                  </TableBody>
                </Table>
              )}
            </CardContent>
          </Card>
        </TabsContent>

        {/* Movements Tab */}
        <TabsContent value="movements">
          <Card className="border border-gray-200/60 rounded-3xl shadow-sm bg-white/80 backdrop-blur-md">
            <CardContent className="p-0">
              <Table>
                <TableHeader>
                  <TableRow className="bg-[#2563EB]/8 hover:bg-[#2563EB]/8 border-b border-[#2563EB]/15">
                    <TableHead>Data</TableHead>
                    <TableHead>Produkti</TableHead>
                    <TableHead>Lloji</TableHead>
                    <TableHead className="text-center">Sasia</TableHead>
                    <TableHead>Arsyeja</TableHead>
                  </TableRow>
                </TableHeader>
                <TableBody>
                  {movements.slice(0, 50).map((movement) => {
                    const product = products.find(p => p.id === movement.product_id);
                    return (
                      <TableRow key={movement.id} className="table-row-hover">
                        <TableCell className="text-sm">
                          {new Date(movement.created_at).toLocaleString('sq-AL')}
                        </TableCell>
                        <TableCell className="font-medium">
                          {product?.name || movement.product_id}
                        </TableCell>
                        <TableCell>
                          {movement.movement_type === 'in' ? (
                            <span className="flex items-center gap-1 text-green-600">
                              <ArrowDownCircle className="h-4 w-4" />
                              Hyrje
                            </span>
                          ) : movement.movement_type === 'sale' ? (
                            <span className="flex items-center gap-1 text-blue-600">
                              <ArrowUpCircle className="h-4 w-4" />
                              Shitje
                            </span>
                          ) : (
                            <span className="flex items-center gap-1 text-red-600">
                              <ArrowUpCircle className="h-4 w-4" />
                              Dalje
                            </span>
                          )}
                        </TableCell>
                        <TableCell className="text-center font-semibold">
                          {movement.quantity}
                        </TableCell>
                        <TableCell className="text-gray-500">{movement.reason || '-'}</TableCell>
                      </TableRow>
                    );
                  })}
                </TableBody>
              </Table>
            </CardContent>
          </Card>
        </TabsContent>

        {/* Alerts Tab */}
        <TabsContent value="alerts">
          <Card className="border border-gray-200/60 rounded-3xl shadow-sm bg-white/80 backdrop-blur-md">
            <CardHeader>
              <CardTitle className="text-lg flex items-center gap-2">
                <AlertTriangle className="h-5 w-5 text-orange-500" />
                Produktet me Stok të Ulët
              </CardTitle>
            </CardHeader>
            <CardContent className="p-0">
              <Table>
                <TableHeader>
                  <TableRow className="bg-[#2563EB]/8 hover:bg-[#2563EB]/8 border-b border-[#2563EB]/15">
                    <TableHead>Produkti</TableHead>
                    <TableHead>Barkodi</TableHead>
                    <TableHead className="text-center">Stoku</TableHead>
                    <TableHead className="text-center">Statusi</TableHead>
                    <TableHead className="text-right">Veprim</TableHead>
                  </TableRow>
                </TableHeader>
                <TableBody>
                  {lowStockProducts.map((product) => (
                    <TableRow key={product.id} className="table-row-hover">
                      <TableCell className="font-medium">{product.name || '-'}</TableCell>
                      <TableCell className="font-mono text-sm">{product.barcode || '-'}</TableCell>
                      <TableCell className="text-center font-semibold">
                        {product.current_stock}
                      </TableCell>
                      <TableCell className="text-center">
                        {getStockBadge(product.current_stock)}
                      </TableCell>
                      <TableCell className="text-right">
                        <Button
                          size="sm"
                          variant="outline"
                          onClick={() => {
                            setMovementData({
                              product_id: product.id,
                              quantity: '',
                              movement_type: 'in',
                              reason: 'Rimbushje stoku'
                            });
                            setShowMovementDialog(true);
                          }}
                        >
                          <Plus className="h-4 w-4 mr-1" />
                          Shto Stok
                        </Button>
                      </TableCell>
                    </TableRow>
                  ))}
                  {lowStockProducts.length === 0 && (
                    <TableRow>
                      <TableCell colSpan={5} className="text-center py-12 text-gray-400">
                        Nuk ka produkte me stok të ulët
                      </TableCell>
                    </TableRow>
                  )}
                </TableBody>
              </Table>
            </CardContent>
          </Card>
        </TabsContent>
      </Tabs>

      {/* Movement Dialog */}
      <Dialog open={showMovementDialog} onOpenChange={setShowMovementDialog}>
        <DialogContent>
          <DialogHeader>
            <DialogTitle>Regjistro Lëvizje Stoku</DialogTitle>
          </DialogHeader>
          <form onSubmit={handleMovement}>
            <div className="space-y-4 py-4">
              <div className="space-y-2">
                <Label>Produkti</Label>
                <Select
                  value={movementData.product_id}
                  onValueChange={(value) => setMovementData({ ...movementData, product_id: value })}
                >
                  <SelectTrigger data-testid="movement-product-select">
                    <SelectValue placeholder="Zgjidh produktin" />
                  </SelectTrigger>
                  <SelectContent>
                    {products.map((product) => (
                      <SelectItem key={product.id} value={product.id}>
                        {product.name || product.barcode || product.id}
                      </SelectItem>
                    ))}
                  </SelectContent>
                </Select>
              </div>

              <div className="space-y-2">
                <Label>Lloji i Lëvizjes</Label>
                <Select
                  value={movementData.movement_type}
                  onValueChange={(value) => setMovementData({ ...movementData, movement_type: value })}
                >
                  <SelectTrigger data-testid="movement-type-select">
                    <SelectValue />
                  </SelectTrigger>
                  <SelectContent>
                    <SelectItem value="in">
                      <span className="flex items-center gap-2">
                        <ArrowDownCircle className="h-4 w-4 text-green-600" />
                        Hyrje (IN)
                      </span>
                    </SelectItem>
                    <SelectItem value="out">
                      <span className="flex items-center gap-2">
                        <ArrowUpCircle className="h-4 w-4 text-red-600" />
                        Dalje (OUT)
                      </span>
                    </SelectItem>
                    <SelectItem value="adjustment">
                      <span className="flex items-center gap-2">
                        <RefreshCw className="h-4 w-4 text-blue-600" />
                        Rregullim
                      </span>
                    </SelectItem>
                  </SelectContent>
                </Select>
              </div>

              <div className="space-y-2">
                <Label>Sasia</Label>
                <Input
                  type="number"
                  min="0"
                  step="0.01"
                  value={movementData.quantity}
                  onChange={(e) => setMovementData({ ...movementData, quantity: e.target.value })}
                  placeholder="0"
                  required
                  data-testid="movement-quantity-input"
                />
              </div>

              <div className="space-y-2">
                <Label>Arsyeja</Label>
                <Textarea
                  value={movementData.reason}
                  onChange={(e) => setMovementData({ ...movementData, reason: e.target.value })}
                  placeholder="Shkruani arsyen e lëvizjes..."
                  data-testid="movement-reason-input"
                />
              </div>
            </div>

            <DialogFooter>
              <Button type="button" variant="outline" onClick={() => setShowMovementDialog(false)}>
                Anulo
              </Button>
              <Button
                type="submit"
                className="bg-[#2563EB] hover:bg-[#1D4ED8] rounded-xl shadow-md shadow-[#2563EB]/20"
                data-testid="save-movement-btn"
              >
                Regjistro
              </Button>
            </DialogFooter>
          </form>
        </DialogContent>
      </Dialog>
    </div>
  );
};

export default Stock;
