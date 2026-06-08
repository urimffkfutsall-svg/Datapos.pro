import React, { useState, useEffect } from 'react';
import { api } from '../App';
import { toast } from 'sonner';
import { Card, CardContent, CardHeader, CardTitle } from '../components/ui/card';
import { Button } from '../components/ui/button';
import { Input } from '../components/ui/input';
import { Label } from '../components/ui/label';
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
import { ScrollArea } from '../components/ui/scroll-area';
import {
  CreditCard,
  Search,
  DollarSign,
  CheckCircle,
  Clock,
  User,
  Calendar,
  FileText,
  Printer,
  AlertTriangle,
  TrendingUp
} from 'lucide-react';

const Debts = () => {
  const [debts, setDebts] = useState([]);
  const [summary, setSummary] = useState(null);
  const [loading, setLoading] = useState(true);
  const [search, setSearch] = useState('');
  const [statusFilter, setStatusFilter] = useState('unpaid');
  const [showPayDialog, setShowPayDialog] = useState(false);
  const [selectedDebt, setSelectedDebt] = useState(null);
  const [paymentAmount, setPaymentAmount] = useState('');
  const [paymentNotes, setPaymentNotes] = useState('');

  useEffect(() => {
    loadData();
  }, [statusFilter]);

  const loadData = async () => {
    try {
      setLoading(true);
      const [debtsRes, summaryRes] = await Promise.all([
        api.get(`/sales/debts?status=${statusFilter}`),
        api.get('/sales/debts/summary')
      ]);
      setDebts(debtsRes.data);
      setSummary(summaryRes.data);
    } catch (error) {
      console.error('Error loading debts:', error);
      toast.error('Gabim gjatë ngarkimit të borxheve');
    } finally {
      setLoading(false);
    }
  };

  const handlePayDebt = async () => {
    if (!selectedDebt || !paymentAmount) return;

    const amount = parseFloat(paymentAmount);
    if (isNaN(amount) || amount <= 0) {
      toast.error('Ju lutem shkruani një shumë të vlefshme');
      return;
    }

    if (amount > selectedDebt.remaining_debt) {
      toast.error(`Shuma tejkalon borxhin e mbetur (€${selectedDebt.remaining_debt.toFixed(2)})`);
      return;
    }

    try {
      const response = await api.post(`/sales/debts/${selectedDebt.id}/pay`, {
        amount: amount,
        notes: paymentNotes || null
      });

      if (response.data.fully_paid) {
        toast.success(`Borxhi u shlye plotësisht për ${selectedDebt.debtor_name}!`);
      } else {
        toast.success(`Pagesa u regjistrua. Borxhi i mbetur: €${response.data.remaining_debt.toFixed(2)}`);
      }

      setShowPayDialog(false);
      setSelectedDebt(null);
      setPaymentAmount('');
      setPaymentNotes('');
      loadData();
    } catch (error) {
      toast.error(error.response?.data?.detail || 'Gabim gjatë regjistrimit të pagesës');
    }
  };

  const openPayDialog = (debt) => {
    setSelectedDebt(debt);
    setPaymentAmount(debt.remaining_debt.toFixed(2));
    setPaymentNotes('');
    setShowPayDialog(true);
  };

  const filteredDebts = debts.filter(debt => {
    if (!search) return true;
    return (
      debt.debtor_name?.toLowerCase().includes(search.toLowerCase()) ||
      debt.receipt_number?.toLowerCase().includes(search.toLowerCase())
    );
  });

  const printDebtReport = () => {
    const printWindow = window.open('', '_blank');
    const companyName = 'DataPOS';
    
    printWindow.document.write(`
      <!DOCTYPE html>
      <html>
        <head>
          <title>Raporti i Borxheve</title>
          <style>
            body { font-family: Arial, sans-serif; padding: 20px; }
            h1 { text-align: center; color: #333; }
            .summary { display: flex; justify-content: space-around; margin: 20px 0; padding: 15px; background: #f5f5f5; border-radius: 8px; }
            .summary-item { text-align: center; }
            .summary-item .value { font-size: 24px; font-weight: bold; color: #ea580c; }
            table { width: 100%; border-collapse: collapse; margin-top: 20px; }
            th, td { border: 1px solid #ddd; padding: 10px; text-align: left; }
            th { background: #f8f8f8; }
            .status-unpaid { color: #ea580c; font-weight: bold; }
            .status-paid { color: #16a34a; }
            .footer { margin-top: 30px; text-align: center; font-size: 12px; color: #666; }
          </style>
        </head>
        <body>
          <h1>${companyName} - Raporti i Borxheve</h1>
          <p style="text-align:center;">Data: ${new Date().toLocaleDateString('sq-AL')} - ${new Date().toLocaleTimeString('sq-AL')}</p>
          
          <div class="summary">
            <div class="summary-item">
              <div>Total Borxhe</div>
              <div class="value">€${summary?.total_debt?.toFixed(2) || '0.00'}</div>
            </div>
            <div class="summary-item">
              <div>Paguar</div>
              <div class="value" style="color:#16a34a">€${summary?.total_paid?.toFixed(2) || '0.00'}</div>
            </div>
            <div class="summary-item">
              <div>Pa Paguar</div>
              <div class="value">€${summary?.outstanding?.toFixed(2) || '0.00'}</div>
            </div>
            <div class="summary-item">
              <div>Numri i Borxheve</div>
              <div class="value">${summary?.debt_count || 0}</div>
            </div>
          </div>

          <h2>Lista e Borxheve ${statusFilter === 'unpaid' ? '(Pa Paguar)' : statusFilter === 'paid' ? '(Paguar)' : ''}</h2>
          <table>
            <thead>
              <tr>
                <th>Nr. Faturës</th>
                <th>Debitori</th>
                <th>Data</th>
                <th>Total</th>
                <th>Mbetur</th>
                <th>Statusi</th>
              </tr>
            </thead>
            <tbody>
              ${filteredDebts.map(debt => `
                <tr>
                  <td>${debt.receipt_number}</td>
                  <td>${debt.debtor_name || 'N/A'}</td>
                  <td>${new Date(debt.created_at).toLocaleDateString('sq-AL')}</td>
                  <td>€${debt.grand_total?.toFixed(2)}</td>
                  <td>€${debt.remaining_debt?.toFixed(2)}</td>
                  <td class="${debt.remaining_debt > 0 ? 'status-unpaid' : 'status-paid'}">
                    ${debt.remaining_debt > 0 ? 'Pa paguar' : 'Paguar'}
                  </td>
                </tr>
              `).join('')}
            </tbody>
          </table>

          <div class="footer">
            <p>Ky raport u gjenerua automatikisht nga ${companyName}</p>
          </div>
        </body>
      </html>
    `);
    printWindow.document.close();
    printWindow.print();
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-orange-500"></div>
      </div>
    );
  }

  return (
    <div className="space-y-6 animate-fade-in" data-testid="debts-page">
      {/* Header */}
      <div className="flex flex-col sm:flex-row justify-between items-start sm:items-center gap-4">
        <div>
          <h1 className="text-2xl font-bold text-gray-900">Menaxhimi i Borxheve</h1>
          <p className="text-gray-500">Shikoni dhe mbyllni borxhet e klientëve</p>
        </div>
        <Button
          onClick={printDebtReport}
          variant="outline"
          className="gap-2"
          data-testid="print-debt-report-btn"
        >
          <Printer className="h-4 w-4" />
          Printo Raportin
        </Button>
      </div>

      {/* Summary Cards */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
        <Card className="border border-orange-200 bg-orange-50 rounded-3xl shadow-sm">
          <CardContent className="pt-6">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm text-orange-600">Total Borxhe</p>
                <p className="text-2xl font-bold text-orange-700">€{summary?.total_debt?.toFixed(2) || '0.00'}</p>
              </div>
              <DollarSign className="h-8 w-8 text-orange-400" />
            </div>
          </CardContent>
        </Card>

        <Card className="border border-green-200 bg-green-50 rounded-3xl shadow-sm">
          <CardContent className="pt-6">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm text-green-600">Paguar</p>
                <p className="text-2xl font-bold text-green-700">€{summary?.total_paid?.toFixed(2) || '0.00'}</p>
              </div>
              <CheckCircle className="h-8 w-8 text-green-400" />
            </div>
          </CardContent>
        </Card>

        <Card className="border border-red-200 bg-red-50 rounded-3xl shadow-sm">
          <CardContent className="pt-6">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm text-red-600">Pa Paguar</p>
                <p className="text-2xl font-bold text-red-700">€{summary?.outstanding?.toFixed(2) || '0.00'}</p>
              </div>
              <AlertTriangle className="h-8 w-8 text-red-400" />
            </div>
          </CardContent>
        </Card>

        <Card className="border border-gray-200/60 rounded-3xl shadow-sm bg-white/80 backdrop-blur-md">
          <CardContent className="pt-6">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm text-gray-500">Numri i Borxheve</p>
                <p className="text-2xl font-bold text-gray-700">
                  {summary?.unpaid_count || 0} / {summary?.debt_count || 0}
                </p>
              </div>
              <TrendingUp className="h-8 w-8 text-gray-400" />
            </div>
          </CardContent>
        </Card>
      </div>

      {/* Filters */}
      <Card className="border border-gray-200/60 rounded-3xl shadow-sm bg-white/80 backdrop-blur-md">
        <CardContent className="pt-6">
          <div className="flex flex-col sm:flex-row gap-4">
            <div className="flex-1 relative">
              <Search className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-gray-400" />
              <Input
                placeholder="Kërko debitorin ose nr. faturës..."
                value={search}
                onChange={(e) => setSearch(e.target.value)}
                className="pl-10"
                data-testid="debt-search-input"
              />
            </div>
            <div className="flex gap-2">
              <Button
                variant={statusFilter === 'unpaid' ? 'default' : 'outline'}
                onClick={() => setStatusFilter('unpaid')}
                className={statusFilter === 'unpaid' ? 'bg-orange-500 hover:bg-orange-600' : ''}
                data-testid="filter-unpaid-btn"
              >
                <Clock className="h-4 w-4 mr-2" />
                Pa Paguar
              </Button>
              <Button
                variant={statusFilter === 'paid' ? 'default' : 'outline'}
                onClick={() => setStatusFilter('paid')}
                className={statusFilter === 'paid' ? 'bg-green-500 hover:bg-green-600' : ''}
                data-testid="filter-paid-btn"
              >
                <CheckCircle className="h-4 w-4 mr-2" />
                Paguar
              </Button>
              <Button
                variant={statusFilter === 'all' ? 'default' : 'outline'}
                onClick={() => setStatusFilter('all')}
                data-testid="filter-all-btn"
              >
                Të Gjitha
              </Button>
            </div>
          </div>
        </CardContent>
      </Card>

      {/* Debts Table */}
      <Card className="border border-gray-200/60 rounded-3xl shadow-sm bg-white/80 backdrop-blur-md">
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <CreditCard className="h-5 w-5 text-orange-500" />
            Lista e Borxheve
          </CardTitle>
        </CardHeader>
        <CardContent>
          <ScrollArea className="h-[500px]">
            <Table>
              <TableHeader>
                <TableRow>
                  <TableHead>Nr. Faturës</TableHead>
                  <TableHead>Debitori</TableHead>
                  <TableHead>Data</TableHead>
                  <TableHead className="text-right">Total</TableHead>
                  <TableHead className="text-right">Mbetur</TableHead>
                  <TableHead>Statusi</TableHead>
                  <TableHead className="text-right">Veprime</TableHead>
                </TableRow>
              </TableHeader>
              <TableBody>
                {filteredDebts.length === 0 ? (
                  <TableRow>
                    <TableCell colSpan={7} className="text-center py-8 text-gray-500">
                      {search ? 'Nuk u gjet asnjë borxh' : 'Nuk ka borxhe për të shfaqur'}
                    </TableCell>
                  </TableRow>
                ) : (
                  filteredDebts.map((debt) => (
                    <TableRow key={debt.id} className="hover:bg-gray-50">
                      <TableCell className="font-mono text-sm">{debt.receipt_number}</TableCell>
                      <TableCell>
                        <div className="flex items-center gap-2">
                          <User className="h-4 w-4 text-gray-400" />
                          <span className="font-medium">{debt.debtor_name || 'N/A'}</span>
                        </div>
                      </TableCell>
                      <TableCell>
                        <div className="flex items-center gap-2 text-gray-500">
                          <Calendar className="h-4 w-4" />
                          {new Date(debt.created_at).toLocaleDateString('sq-AL')}
                        </div>
                      </TableCell>
                      <TableCell className="text-right font-medium">
                        €{debt.grand_total?.toFixed(2)}
                      </TableCell>
                      <TableCell className="text-right">
                        <span className={`font-bold ${debt.remaining_debt > 0 ? 'text-orange-600' : 'text-green-600'}`}>
                          €{debt.remaining_debt?.toFixed(2)}
                        </span>
                      </TableCell>
                      <TableCell>
                        {debt.remaining_debt > 0 ? (
                          <span className="inline-flex items-center gap-1 px-2 py-1 bg-orange-100 text-orange-700 rounded-full text-xs font-medium">
                            <Clock className="h-3 w-3" />
                            Pa paguar
                          </span>
                        ) : (
                          <span className="inline-flex items-center gap-1 px-2 py-1 bg-green-100 text-green-700 rounded-full text-xs font-medium">
                            <CheckCircle className="h-3 w-3" />
                            Paguar
                          </span>
                        )}
                      </TableCell>
                      <TableCell className="text-right">
                        {debt.remaining_debt > 0 && (
                          <Button
                            size="sm"
                            onClick={() => openPayDialog(debt)}
                            className="bg-green-500 hover:bg-green-600"
                            data-testid={`pay-debt-${debt.id}-btn`}
                          >
                            <DollarSign className="h-4 w-4 mr-1" />
                            Paguaj
                          </Button>
                        )}
                      </TableCell>
                    </TableRow>
                  ))
                )}
              </TableBody>
            </Table>
          </ScrollArea>
        </CardContent>
      </Card>

      {/* Pay Debt Dialog */}
      <Dialog open={showPayDialog} onOpenChange={setShowPayDialog}>
        <DialogContent className="sm:max-w-md">
          <DialogHeader>
            <DialogTitle className="flex items-center gap-2">
              <DollarSign className="h-5 w-5 text-green-500" />
              Paguaj Borxhin
            </DialogTitle>
          </DialogHeader>
          
          {selectedDebt && (
            <div className="space-y-4">
              {/* Debt Info */}
              <div className="p-4 bg-gray-50 rounded-lg space-y-2">
                <div className="flex justify-between">
                  <span className="text-gray-500">Debitori:</span>
                  <span className="font-medium">{selectedDebt.debtor_name}</span>
                </div>
                <div className="flex justify-between">
                  <span className="text-gray-500">Nr. Faturës:</span>
                  <span className="font-mono text-sm">{selectedDebt.receipt_number}</span>
                </div>
                <div className="flex justify-between">
                  <span className="text-gray-500">Total Faturë:</span>
                  <span className="font-medium">€{selectedDebt.grand_total?.toFixed(2)}</span>
                </div>
                <div className="flex justify-between border-t pt-2 mt-2">
                  <span className="text-gray-700 font-medium">Borxhi i Mbetur:</span>
                  <span className="text-lg font-bold text-orange-600">€{selectedDebt.remaining_debt?.toFixed(2)}</span>
                </div>
              </div>

              {/* Payment Amount */}
              <div>
                <Label htmlFor="paymentAmount">Shuma e Pagesës (€)</Label>
                <Input
                  id="paymentAmount"
                  type="number"
                  step="0.01"
                  min="0.01"
                  max={selectedDebt.remaining_debt}
                  value={paymentAmount}
                  onChange={(e) => setPaymentAmount(e.target.value)}
                  className="mt-1"
                  autoFocus
                  data-testid="payment-amount-input"
                />
              </div>

              {/* Payment Notes */}
              <div>
                <Label htmlFor="paymentNotes">Shënim (opsional)</Label>
                <Input
                  id="paymentNotes"
                  type="text"
                  value={paymentNotes}
                  onChange={(e) => setPaymentNotes(e.target.value)}
                  placeholder="P.sh. Pagesa me cash"
                  className="mt-1"
                  data-testid="payment-notes-input"
                />
              </div>

              {/* Quick Amount Buttons */}
              <div className="flex gap-2 flex-wrap">
                <Button
                  type="button"
                  variant="outline"
                  size="sm"
                  onClick={() => setPaymentAmount(selectedDebt.remaining_debt.toFixed(2))}
                >
                  Paguaj Plotë (€{selectedDebt.remaining_debt?.toFixed(2)})
                </Button>
                {selectedDebt.remaining_debt >= 50 && (
                  <Button
                    type="button"
                    variant="outline"
                    size="sm"
                    onClick={() => setPaymentAmount('50.00')}
                  >
                    €50
                  </Button>
                )}
                {selectedDebt.remaining_debt >= 100 && (
                  <Button
                    type="button"
                    variant="outline"
                    size="sm"
                    onClick={() => setPaymentAmount('100.00')}
                  >
                    €100
                  </Button>
                )}
              </div>
            </div>
          )}

          <DialogFooter className="gap-2">
            <Button
              variant="outline"
              onClick={() => setShowPayDialog(false)}
            >
              Anulo
            </Button>
            <Button
              onClick={handlePayDebt}
              className="bg-green-500 hover:bg-green-600"
              disabled={!paymentAmount || parseFloat(paymentAmount) <= 0}
              data-testid="confirm-pay-debt-btn"
            >
              <CheckCircle className="h-4 w-4 mr-2" />
              Konfirmo Pagesën
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>
    </div>
  );
};

export default Debts;
