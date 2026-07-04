import React, { useState, useEffect } from 'react';
import { api } from '../App';
import { toast } from 'sonner';
import { Card, CardContent, CardHeader, CardTitle } from '../components/ui/card';
import { Button } from '../components/ui/button';
import { Input } from '../components/ui/input';
import { Label } from '../components/ui/label';
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
import { Calendar } from '../components/ui/calendar';
import {
  Popover,
  PopoverContent,
  PopoverTrigger,
} from '../components/ui/popover';
import {
  BarChart3,
  Download,
  FileSpreadsheet,
  FileText,
  Calendar as CalendarIcon,
  TrendingUp,
  DollarSign,
  Package,
  Users
} from 'lucide-react';
import { LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, BarChart, Bar, PieChart, Pie, Cell } from 'recharts';
import { format } from 'date-fns';
import { sq } from 'date-fns/locale';

const Reports = () => {
  const [activeTab, setActiveTab] = useState('sales');
  const [branches, setBranches] = useState([]);
  const [selectedBranch, setSelectedBranch] = useState('all');
  const [dateRange, setDateRange] = useState({
    from: new Date(new Date().setDate(new Date().getDate() - 30)),
    to: new Date()
  });
  const [salesReport, setSalesReport] = useState(null);
  const [profitReport, setProfitReport] = useState(null);
  const [stockReport, setStockReport] = useState(null);
  const [cashierReport, setCashierReport] = useState([]);
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    loadBranches();
  }, []);

  useEffect(() => {
    loadReport();
  }, [activeTab, selectedBranch, dateRange]);

  const loadBranches = async () => {
    try {
      const response = await api.get('/branches');
      setBranches(response.data);
    } catch (error) {
      console.error('Error loading branches:', error);
    }
  };

  const loadReport = async () => {
    setLoading(true);
    try {
      const startDate = format(dateRange.from, 'yyyy-MM-dd');
      const endDate = format(dateRange.to, 'yyyy-MM-dd');
      const branchParam = selectedBranch !== 'all' ? `&branch_id=${selectedBranch}` : '';

      if (activeTab === 'sales') {
        const response = await api.get(`/reports/sales?start_date=${startDate}&end_date=${endDate}${branchParam}`);
        setSalesReport(response.data);
      } else if (activeTab === 'profit') {
        const response = await api.get(`/reports/profit-loss?start_date=${startDate}&end_date=${endDate}${branchParam}`);
        setProfitReport(response.data);
      } else if (activeTab === 'stock') {
        const response = await api.get(`/reports/stock?${branchParam.slice(1)}`);
        setStockReport(response.data);
      } else if (activeTab === 'cashier') {
        const response = await api.get(`/reports/cashier-performance?start_date=${startDate}&end_date=${endDate}${branchParam}`);
        setCashierReport(response.data);
      }
    } catch (error) {
      console.error('Error loading report:', error);
      toast.error('Gabim gjatë ngarkimit të raportit');
    } finally {
      setLoading(false);
    }
  };

  const exportReport = async (type) => {
    try {
      const startDate = format(dateRange.from, 'yyyy-MM-dd');
      const endDate = format(dateRange.to, 'yyyy-MM-dd');
      const branchParam = selectedBranch !== 'all' ? `&branch_id=${selectedBranch}` : '';
      
      const url = `/reports/export/${type}?report_type=${activeTab}&start_date=${startDate}&end_date=${endDate}${branchParam}`;
      
      const response = await api.get(url, { responseType: 'blob' });
      const blob = new Blob([response.data]);
      const link = document.createElement('a');
      link.href = URL.createObjectURL(blob);
      link.download = `raport_${activeTab}_${format(new Date(), 'yyyyMMdd')}.${type === 'pdf' ? 'pdf' : 'xlsx'}`;
      link.click();
      
      toast.success('Raporti u eksportua me sukses');
    } catch (error) {
      toast.error('Gabim gjatë eksportimit');
    }
  };

  // Quick date range presets
  const setQuickDateRange = (preset) => {
    const today = new Date();
    let from, to = today;
    
    switch (preset) {
      case 'today':
        from = today;
        break;
      case 'yesterday':
        from = new Date(today.setDate(today.getDate() - 1));
        to = from;
        break;
      case 'week':
        from = new Date(today.setDate(today.getDate() - 7));
        to = new Date();
        break;
      case 'month':
        from = new Date(today.setMonth(today.getMonth() - 1));
        to = new Date();
        break;
      case 'quarter':
        from = new Date(today.setMonth(today.getMonth() - 3));
        to = new Date();
        break;
      case 'year':
        from = new Date(today.setFullYear(today.getFullYear() - 1));
        to = new Date();
        break;
      default:
        from = new Date(new Date().setDate(new Date().getDate() - 30));
    }
    
    setDateRange({ from, to });
  };

  const COLORS = ['#2563EB', '#2563EB', '#10B981', '#F59E0B', '#8B5CF6'];

  return (
    <div className="space-y-6 animate-fade-in" data-testid="reports-page">
      {/* Header */}
      <div className="flex flex-col md:flex-row md:items-center md:justify-between gap-4">
        <div>
          <h1 className="text-2xl font-bold text-gray-900">Raportet</h1>
          <p className="text-gray-500">Analizoni performancën e biznesit</p>
        </div>
        <div className="flex gap-2">
          {/* Quick Export Dropdown */}
          <Popover>
            <PopoverTrigger asChild>
              <Button variant="outline" className="gap-2">
                <Download className="h-4 w-4" />
                Eksporto
              </Button>
            </PopoverTrigger>
            <PopoverContent className="w-56 p-2" align="end">
              <div className="space-y-1">
                <p className="text-xs font-medium text-gray-500 px-2 py-1">Eksporto PDF</p>
                <Button 
                  variant="ghost" 
                  className="w-full justify-start text-sm h-8"
                  onClick={() => exportReport('pdf')}
                >
                  <FileText className="h-4 w-4 mr-2 text-red-500" />
                  Periudha Aktuale
                </Button>
                <p className="text-xs font-medium text-gray-500 px-2 py-1 mt-2">Eksporto Excel</p>
                <Button 
                  variant="ghost" 
                  className="w-full justify-start text-sm h-8"
                  onClick={() => exportReport('excel')}
                >
                  <FileSpreadsheet className="h-4 w-4 mr-2 text-green-600" />
                  Periudha Aktuale
                </Button>
              </div>
            </PopoverContent>
          </Popover>
          
          <Button
            variant="outline"
            className="gap-2"
            onClick={() => exportReport('pdf')}
            data-testid="export-pdf-btn"
          >
            <FileText className="h-4 w-4" />
            PDF
          </Button>
          <Button
            variant="outline"
            className="gap-2"
            onClick={() => exportReport('excel')}
            data-testid="export-excel-btn"
          >
            <FileSpreadsheet className="h-4 w-4" />
            Excel
          </Button>
        </div>
      </div>

      {/* Quick Date Range Presets */}
      <div className="flex flex-wrap gap-2">
        <Button 
          variant="outline" 
          size="sm" 
          onClick={() => setQuickDateRange('today')}
          className="text-xs"
        >
          Sot
        </Button>
        <Button 
          variant="outline" 
          size="sm" 
          onClick={() => setQuickDateRange('yesterday')}
          className="text-xs"
        >
          Dje
        </Button>
        <Button 
          variant="outline" 
          size="sm" 
          onClick={() => setQuickDateRange('week')}
          className="text-xs"
        >
          7 ditët e fundit
        </Button>
        <Button 
          variant="outline" 
          size="sm" 
          onClick={() => setQuickDateRange('month')}
          className="text-xs"
        >
          30 ditët e fundit
        </Button>
        <Button 
          variant="outline" 
          size="sm" 
          onClick={() => setQuickDateRange('quarter')}
          className="text-xs"
        >
          3 muajt e fundit
        </Button>
        <Button 
          variant="outline" 
          size="sm" 
          onClick={() => setQuickDateRange('year')}
          className="text-xs"
        >
          1 vit
        </Button>
      </div>

      {/* Filters */}
      <Card className="border border-gray-200/60 rounded-3xl shadow-sm bg-white/80 backdrop-blur-md">
        <CardContent className="p-4">
          <div className="flex flex-wrap gap-4 items-end">
            <div className="space-y-2">
              <Label>Periudha</Label>
              <Popover>
                <PopoverTrigger asChild>
                  <Button variant="outline" className="w-[280px] justify-start gap-2">
                    <CalendarIcon className="h-4 w-4" />
                    {dateRange.from && dateRange.to ? (
                      <>
                        {format(dateRange.from, 'dd MMM', { locale: sq })} - {format(dateRange.to, 'dd MMM yyyy', { locale: sq })}
                      </>
                    ) : (
                      'Zgjidh periudhën'
                    )}
                  </Button>
                </PopoverTrigger>
                <PopoverContent className="w-auto p-0" align="start">
                  <Calendar
                    mode="range"
                    selected={dateRange}
                    onSelect={(range) => range && setDateRange(range)}
                    numberOfMonths={2}
                  />
                </PopoverContent>
              </Popover>
            </div>

            {branches.length > 0 && (
              <div className="space-y-2">
                <Label>Dega</Label>
                <Select value={selectedBranch} onValueChange={setSelectedBranch}>
                  <SelectTrigger className="w-[200px]" data-testid="report-branch-filter">
                    <SelectValue />
                  </SelectTrigger>
                  <SelectContent>
                    <SelectItem value="all">Të gjitha degët</SelectItem>
                    {branches.map((branch) => (
                      <SelectItem key={branch.id} value={branch.id}>{branch.name}</SelectItem>
                    ))}
                  </SelectContent>
                </Select>
              </div>
            )}
          </div>
        </CardContent>
      </Card>

      {/* Tabs */}
      <Tabs value={activeTab} onValueChange={setActiveTab}>
        <TabsList>
          <TabsTrigger value="sales" data-testid="sales-report-tab">
            <DollarSign className="h-4 w-4 mr-2" />
            Shitjet
          </TabsTrigger>
          <TabsTrigger value="profit" data-testid="profit-report-tab">
            <TrendingUp className="h-4 w-4 mr-2" />
            Fitimi
          </TabsTrigger>
          <TabsTrigger value="stock" data-testid="stock-report-tab">
            <Package className="h-4 w-4 mr-2" />
            Stoku
          </TabsTrigger>
          <TabsTrigger value="cashier" data-testid="cashier-report-tab">
            <Users className="h-4 w-4 mr-2" />
            Performanca
          </TabsTrigger>
        </TabsList>

        {/* Sales Report */}
        <TabsContent value="sales" className="space-y-6">
          {loading ? (
            <div className="flex items-center justify-center py-12">
              <div className="spinner" />
            </div>
          ) : salesReport && (
            <>
              {/* Summary Cards */}
              <div className="grid grid-cols-1 sm:grid-cols-4 gap-4">
                <Card className="border border-gray-200/60 rounded-3xl shadow-sm bg-white/80 backdrop-blur-md">
                  <CardContent className="p-6">
                    <p className="text-sm text-gray-500">Të Ardhura Totale</p>
                    <p className="text-2xl font-bold text-[#2563EB]">
                      €{salesReport.summary.total_revenue.toFixed(2)}
                    </p>
                  </CardContent>
                </Card>
                <Card className="border border-gray-200/60 rounded-3xl shadow-sm bg-white/80 backdrop-blur-md">
                  <CardContent className="p-6">
                    <p className="text-sm text-gray-500">Transaksione</p>
                    <p className="text-2xl font-bold">{salesReport.summary.total_transactions}</p>
                  </CardContent>
                </Card>
                <Card className="border border-gray-200/60 rounded-3xl shadow-sm bg-white/80 backdrop-blur-md">
                  <CardContent className="p-6">
                    <p className="text-sm text-gray-500">TVSH Total</p>
                    <p className="text-2xl font-bold text-[#2563EB]">
                      €{salesReport.summary.total_vat.toFixed(2)}
                    </p>
                  </CardContent>
                </Card>
                <Card className="border border-gray-200/60 rounded-3xl shadow-sm bg-white/80 backdrop-blur-md">
                  <CardContent className="p-6">
                    <p className="text-sm text-gray-500">Zbritje</p>
                    <p className="text-2xl font-bold text-orange-500">
                      €{salesReport.summary.total_discount.toFixed(2)}
                    </p>
                  </CardContent>
                </Card>
              </div>

              {/* Chart */}
              <Card className="border border-gray-200/60 rounded-3xl shadow-sm bg-white/80 backdrop-blur-md">
                <CardHeader>
                  <CardTitle>Trendi i Shitjeve</CardTitle>
                </CardHeader>
                <CardContent>
                  <div className="h-80">
                    <ResponsiveContainer width="100%" height="100%">
                      <LineChart data={salesReport.daily_breakdown}>
                        <CartesianGrid strokeDasharray="3 3" stroke="#E2E8F0" />
                        <XAxis dataKey="date" stroke="#64748B" fontSize={12} />
                        <YAxis stroke="#64748B" fontSize={12} />
                        <Tooltip
                          contentStyle={{
                            backgroundColor: 'white',
                            border: '1px solid #E2E8F0',
                            borderRadius: '8px',
                          }}
                          formatter={(value) => [`€${value.toFixed(2)}`, 'Shitjet']}
                        />
                        <Line
                          type="monotone"
                          dataKey="total"
                          stroke="#2563EB"
                          strokeWidth={3}
                          dot={{ fill: '#2563EB' }}
                        />
                      </LineChart>
                    </ResponsiveContainer>
                  </div>
                </CardContent>
              </Card>

              {/* Daily Breakdown Table */}
              <Card className="border border-gray-200/60 rounded-3xl shadow-sm bg-white/80 backdrop-blur-md">
                <CardHeader>
                  <CardTitle>Detajet Ditore</CardTitle>
                </CardHeader>
                <CardContent className="p-0">
                  <Table>
                    <TableHeader>
                      <TableRow className="bg-[#2563EB]/8 hover:bg-[#2563EB]/8 border-b border-[#2563EB]/15">
                        <TableHead>Data</TableHead>
                        <TableHead className="text-right">Transaksione</TableHead>
                        <TableHead className="text-right">Totali</TableHead>
                      </TableRow>
                    </TableHeader>
                    <TableBody>
                      {salesReport.daily_breakdown.map((day) => (
                        <TableRow key={day.date} className="table-row-hover">
                          <TableCell>{format(new Date(day.date), 'dd MMMM yyyy', { locale: sq })}</TableCell>
                          <TableCell className="text-right">{day.count}</TableCell>
                          <TableCell className="text-right font-semibold">€{day.total.toFixed(2)}</TableCell>
                        </TableRow>
                      ))}
                    </TableBody>
                  </Table>
                </CardContent>
              </Card>
            </>
          )}
        </TabsContent>

        {/* Profit/Loss Report */}
        <TabsContent value="profit" className="space-y-6">
          {loading ? (
            <div className="flex items-center justify-center py-12">
              <div className="spinner" />
            </div>
          ) : profitReport && (
            <>
              {/* Summary Cards */}
              <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
                <Card className="border border-gray-200/60 rounded-3xl shadow-sm bg-white/80 backdrop-blur-md">
                  <CardContent className="p-6">
                    <p className="text-sm text-gray-500">Të Ardhura</p>
                    <p className="text-2xl font-bold text-blue-600">
                      €{profitReport.summary.total_revenue.toFixed(2)}
                    </p>
                  </CardContent>
                </Card>
                <Card className="border border-gray-200/60 rounded-3xl shadow-sm bg-white/80 backdrop-blur-md">
                  <CardContent className="p-6">
                    <p className="text-sm text-gray-500">Kosto</p>
                    <p className="text-2xl font-bold text-orange-500">
                      €{profitReport.summary.total_cost.toFixed(2)}
                    </p>
                  </CardContent>
                </Card>
                <Card className="border border-gray-200/60 rounded-3xl shadow-sm bg-white/80 backdrop-blur-md">
                  <CardContent className="p-6">
                    <p className="text-sm text-gray-500">Fitimi Bruto</p>
                    <p className={`text-2xl font-bold ${profitReport.summary.gross_profit >= 0 ? 'text-green-600' : 'text-red-600'}`}>
                      €{profitReport.summary.gross_profit.toFixed(2)}
                    </p>
                  </CardContent>
                </Card>
                <Card className="border border-gray-200/60 rounded-3xl shadow-sm bg-white/80 backdrop-blur-md">
                  <CardContent className="p-6">
                    <p className="text-sm text-gray-500">Marzhi i Fitimit</p>
                    <p className={`text-2xl font-bold ${profitReport.summary.profit_margin >= 0 ? 'text-green-600' : 'text-red-600'}`}>
                      {profitReport.summary.profit_margin.toFixed(1)}%
                    </p>
                  </CardContent>
                </Card>
              </div>

              {/* Additional Info */}
              <div className="grid grid-cols-1 sm:grid-cols-3 gap-4">
                <Card className="border border-gray-200/60 rounded-2xl shadow-sm bg-gray-50/70">
                  <CardContent className="p-4">
                    <div className="flex justify-between items-center">
                      <span className="text-sm text-gray-600">TVSH</span>
                      <span className="font-semibold">€{profitReport.summary.total_vat.toFixed(2)}</span>
                    </div>
                  </CardContent>
                </Card>
                <Card className="border border-gray-200/60 rounded-2xl shadow-sm bg-gray-50/70">
                  <CardContent className="p-4">
                    <div className="flex justify-between items-center">
                      <span className="text-sm text-gray-600">Fitimi Neto</span>
                      <span className={`font-semibold ${profitReport.summary.net_profit >= 0 ? 'text-green-600' : 'text-red-600'}`}>
                        €{profitReport.summary.net_profit.toFixed(2)}
                      </span>
                    </div>
                  </CardContent>
                </Card>
                <Card className="border border-gray-200/60 rounded-2xl shadow-sm bg-gray-50/70">
                  <CardContent className="p-4">
                    <div className="flex justify-between items-center">
                      <span className="text-sm text-gray-600">Transaksione</span>
                      <span className="font-semibold">{profitReport.summary.total_transactions}</span>
                    </div>
                  </CardContent>
                </Card>
              </div>

              {/* Chart */}
              <Card className="border border-gray-200/60 rounded-3xl shadow-sm bg-white/80 backdrop-blur-md">
                <CardHeader>
                  <CardTitle>Trendi i Fitimit</CardTitle>
                </CardHeader>
                <CardContent>
                  <div className="h-80">
                    <ResponsiveContainer width="100%" height="100%">
                      <BarChart data={profitReport.daily_breakdown}>
                        <CartesianGrid strokeDasharray="3 3" stroke="#E2E8F0" />
                        <XAxis dataKey="date" stroke="#64748B" fontSize={12} />
                        <YAxis stroke="#64748B" fontSize={12} />
                        <Tooltip
                          contentStyle={{
                            backgroundColor: 'white',
                            border: '1px solid #E2E8F0',
                            borderRadius: '8px',
                          }}
                          formatter={(value, name) => [
                            `€${value.toFixed(2)}`,
                            name === 'revenue' ? 'Të ardhura' : name === 'cost' ? 'Kosto' : 'Fitimi'
                          ]}
                        />
                        <Bar dataKey="revenue" fill="#3B82F6" name="revenue" />
                        <Bar dataKey="cost" fill="#F97316" name="cost" />
                        <Bar dataKey="profit" fill="#10B981" name="profit" />
                      </BarChart>
                    </ResponsiveContainer>
                  </div>
                </CardContent>
              </Card>

              {/* Daily Breakdown Table */}
              <Card className="border border-gray-200/60 rounded-3xl shadow-sm bg-white/80 backdrop-blur-md">
                <CardHeader>
                  <CardTitle>Detajet Ditore</CardTitle>
                </CardHeader>
                <CardContent className="p-0">
                  <Table>
                    <TableHeader>
                      <TableRow className="bg-[#2563EB]/8 hover:bg-[#2563EB]/8 border-b border-[#2563EB]/15">
                        <TableHead>Data</TableHead>
                        <TableHead className="text-right">Të Ardhura</TableHead>
                        <TableHead className="text-right">Kosto</TableHead>
                        <TableHead className="text-right">Fitimi</TableHead>
                      </TableRow>
                    </TableHeader>
                    <TableBody>
                      {profitReport.daily_breakdown.map((day) => (
                        <TableRow key={day.date} className="table-row-hover">
                          <TableCell>{format(new Date(day.date), 'dd MMMM yyyy', { locale: sq })}</TableCell>
                          <TableCell className="text-right text-blue-600">€{day.revenue.toFixed(2)}</TableCell>
                          <TableCell className="text-right text-orange-500">€{day.cost.toFixed(2)}</TableCell>
                          <TableCell className={`text-right font-semibold ${day.profit >= 0 ? 'text-green-600' : 'text-red-600'}`}>
                            €{day.profit.toFixed(2)}
                          </TableCell>
                        </TableRow>
                      ))}
                    </TableBody>
                  </Table>
                </CardContent>
              </Card>
            </>
          )}
        </TabsContent>

        {/* Stock Report */}
        <TabsContent value="stock" className="space-y-6">
          {loading ? (
            <div className="flex items-center justify-center py-12">
              <div className="spinner" />
            </div>
          ) : stockReport && (
            <>
              {/* Summary Cards */}
              <div className="grid grid-cols-1 sm:grid-cols-4 gap-4">
                <Card className="border border-gray-200/60 rounded-3xl shadow-sm bg-white/80 backdrop-blur-md">
                  <CardContent className="p-6">
                    <p className="text-sm text-gray-500">Total Produkte</p>
                    <p className="text-2xl font-bold">{stockReport.summary.total_products}</p>
                  </CardContent>
                </Card>
                <Card className="border border-gray-200/60 rounded-3xl shadow-sm bg-white/80 backdrop-blur-md">
                  <CardContent className="p-6">
                    <p className="text-sm text-gray-500">Artikuj në Stok</p>
                    <p className="text-2xl font-bold text-[#2563EB]">{stockReport.summary.total_items}</p>
                  </CardContent>
                </Card>
                <Card className="border border-gray-200/60 rounded-3xl shadow-sm bg-white/80 backdrop-blur-md">
                  <CardContent className="p-6">
                    <p className="text-sm text-gray-500">Vlera e Stokut</p>
                    <p className="text-2xl font-bold text-green-600">€{stockReport.summary.total_value.toFixed(2)}</p>
                  </CardContent>
                </Card>
                <Card className="border border-gray-200/60 rounded-3xl shadow-sm bg-white/80 backdrop-blur-md">
                  <CardContent className="p-6">
                    <p className="text-sm text-gray-500">Stok i Ulët / Pa Stok</p>
                    <p className="text-2xl font-bold text-orange-500">
                      {stockReport.summary.low_stock_count} / {stockReport.summary.out_of_stock_count}
                    </p>
                  </CardContent>
                </Card>
              </div>

              {/* Low Stock Table */}
              <Card className="border border-gray-200/60 rounded-3xl shadow-sm bg-white/80 backdrop-blur-md">
                <CardHeader>
                  <CardTitle className="text-orange-500">Produkte me Stok të Ulët</CardTitle>
                </CardHeader>
                <CardContent className="p-0">
                  <Table>
                    <TableHeader>
                      <TableRow className="bg-[#2563EB]/8 hover:bg-[#2563EB]/8 border-b border-[#2563EB]/15">
                        <TableHead>Produkti</TableHead>
                        <TableHead>Barkodi</TableHead>
                        <TableHead className="text-center">Stoku</TableHead>
                        <TableHead className="text-right">Çmimi</TableHead>
                      </TableRow>
                    </TableHeader>
                    <TableBody>
                      {stockReport.low_stock_products.map((product) => (
                        <TableRow key={product.id} className="table-row-hover">
                          <TableCell className="font-medium">{product.name || '-'}</TableCell>
                          <TableCell className="font-mono text-sm">{product.barcode || '-'}</TableCell>
                          <TableCell className="text-center font-bold text-orange-500">
                            {product.current_stock}
                          </TableCell>
                          <TableCell className="text-right">
                            €{(product.sale_price || 0).toFixed(2)}
                          </TableCell>
                        </TableRow>
                      ))}
                    </TableBody>
                  </Table>
                </CardContent>
              </Card>
            </>
          )}
        </TabsContent>

        {/* Cashier Performance Report */}
        <TabsContent value="cashier" className="space-y-6">
          {loading ? (
            <div className="flex items-center justify-center py-12">
              <div className="spinner" />
            </div>
          ) : (
            <>
              {/* Chart */}
              <Card className="border border-gray-200/60 rounded-3xl shadow-sm bg-white/80 backdrop-blur-md">
                <CardHeader>
                  <CardTitle>Performanca e Arkëtarëve</CardTitle>
                </CardHeader>
                <CardContent>
                  <div className="h-80">
                    <ResponsiveContainer width="100%" height="100%">
                      <BarChart data={cashierReport} layout="vertical">
                        <CartesianGrid strokeDasharray="3 3" stroke="#E2E8F0" />
                        <XAxis type="number" stroke="#64748B" fontSize={12} />
                        <YAxis dataKey="user_name" type="category" stroke="#64748B" fontSize={12} width={100} />
                        <Tooltip
                          contentStyle={{
                            backgroundColor: 'white',
                            border: '1px solid #E2E8F0',
                            borderRadius: '8px',
                          }}
                          formatter={(value) => [`€${value.toFixed(2)}`, 'Shitjet']}
                        />
                        <Bar dataKey="total_sales" fill="#2563EB" radius={[0, 4, 4, 0]} />
                      </BarChart>
                    </ResponsiveContainer>
                  </div>
                </CardContent>
              </Card>

              {/* Table */}
              <Card className="border border-gray-200/60 rounded-3xl shadow-sm bg-white/80 backdrop-blur-md">
                <CardHeader>
                  <CardTitle>Detajet</CardTitle>
                </CardHeader>
                <CardContent className="p-0">
                  <Table>
                    <TableHeader>
                      <TableRow className="bg-[#2563EB]/8 hover:bg-[#2563EB]/8 border-b border-[#2563EB]/15">
                        <TableHead>Arkëtari</TableHead>
                        <TableHead className="text-right">Transaksione</TableHead>
                        <TableHead className="text-right">Artikuj</TableHead>
                        <TableHead className="text-right">Shitjet Totale</TableHead>
                      </TableRow>
                    </TableHeader>
                    <TableBody>
                      {cashierReport.map((cashier, index) => (
                        <TableRow key={cashier.user_id} className="table-row-hover">
                          <TableCell className="font-medium">
                            <div className="flex items-center gap-2">
                              <span className="text-sm text-gray-400">#{index + 1}</span>
                              {cashier.user_name}
                            </div>
                          </TableCell>
                          <TableCell className="text-right">{cashier.total_transactions}</TableCell>
                          <TableCell className="text-right">{cashier.total_items}</TableCell>
                          <TableCell className="text-right font-bold text-[#2563EB]">
                            €{cashier.total_sales.toFixed(2)}
                          </TableCell>
                        </TableRow>
                      ))}
                    </TableBody>
                  </Table>
                </CardContent>
              </Card>
            </>
          )}
        </TabsContent>
      </Tabs>
    </div>
  );
};

export default Reports;
