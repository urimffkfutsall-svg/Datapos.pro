import React, { useRef, useEffect } from 'react';
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
} from '../ui/dialog';
import { Button } from '../ui/button';
import { Input } from '../ui/input';
import { Checkbox } from '../ui/checkbox';
import { 
  Banknote, 
  CreditCard, 
  Delete, 
  Printer, 
  Receipt,
  X
} from 'lucide-react';

export const PaymentDialog = ({
  open,
  onOpenChange,
  cartTotals,
  paymentMethod,
  setPaymentMethod,
  cashAmount,
  setCashAmount,
  changeAmount,
  printReceipt,
  setPrintReceipt,
  directPrintEnabled,
  toggleDirectPrint,
  handlePayment
}) => {
  const cashInputRef = useRef(null);

  // Focus cash input when dialog opens with cash method
  useEffect(() => {
    if (open && paymentMethod === 'cash' && cashInputRef.current) {
      setTimeout(() => cashInputRef.current?.focus(), 100);
    }
  }, [open, paymentMethod]);

  const handleNumpad = (value) => {
    if (value === 'backspace') {
      setCashAmount(prev => prev.slice(0, -1));
    } else if (value === '.' && cashAmount.includes('.')) {
      return;
    } else {
      setCashAmount(prev => prev + value);
    }
  };

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent className="sm:max-w-md">
        <DialogHeader className="flex flex-row items-center justify-between">
          <DialogTitle>Shtyp faturën</DialogTitle>
          <Button variant="ghost" size="icon" onClick={() => onOpenChange(false)}>
            <X className="h-4 w-4" />
          </Button>
        </DialogHeader>
        
        <div className="space-y-4">
          {/* Total */}
          <div className="text-center text-3xl font-bold text-gray-900">
            €{cartTotals.total.toFixed(2)}
          </div>

          {/* Payment Method Tabs */}
          <div className="grid grid-cols-2 gap-2">
            <Button
              variant={paymentMethod === 'cash' ? 'default' : 'outline'}
              className={paymentMethod === 'cash' ? 'bg-[#00a79d] hover:bg-[#008f86]' : ''}
              onClick={() => setPaymentMethod('cash')}
              data-testid="payment-cash-btn"
            >
              <Banknote className="h-4 w-4 mr-2" />
              Cash
            </Button>
            <Button
              variant={paymentMethod === 'bank' ? 'default' : 'outline'}
              className={paymentMethod === 'bank' ? 'bg-[#00a79d] hover:bg-[#008f86]' : ''}
              onClick={() => setPaymentMethod('bank')}
              data-testid="payment-bank-btn"
            >
              <CreditCard className="h-4 w-4 mr-2" />
              Bank
            </Button>
          </div>

          {/* Cash Input */}
          {paymentMethod === 'cash' && (
            <>
              <div className="relative">
                <span className="absolute left-3 top-1/2 -translate-y-1/2 text-[#00a79d] font-bold">€</span>
                <Input
                  ref={cashInputRef}
                  type="text"
                  value={cashAmount}
                  onChange={(e) => setCashAmount(e.target.value)}
                  onKeyDown={(e) => {
                    if (e.key === 'Enter' && parseFloat(cashAmount) >= cartTotals.total) {
                      e.preventDefault();
                      handlePayment();
                    }
                  }}
                  className="pl-8 h-12 text-xl font-semibold"
                  placeholder="Shkruaj shumën e paguar..."
                  autoFocus
                  data-testid="cash-amount-input"
                />
              </div>

              {/* Totals Display */}
              <div className="grid grid-cols-2 gap-4 p-4 bg-gray-50 rounded-lg">
                <div>
                  <p className="text-sm text-gray-500">Total:</p>
                  <p className="text-lg font-bold">€{cartTotals.total.toFixed(2)}</p>
                </div>
                <div>
                  <p className="text-sm text-gray-500">Bank:</p>
                  <p className="text-lg font-bold">€0.00</p>
                </div>
                <div className="col-span-2">
                  <p className="text-sm text-gray-500">Kusuri:</p>
                  <p className={`text-2xl font-bold ${changeAmount >= 0 ? 'text-green-600' : 'text-red-600'}`}>
                    €{changeAmount.toFixed(2)}
                  </p>
                </div>
              </div>

              {/* Numpad */}
              <div className="grid grid-cols-3 gap-2">
                {['7', '8', '9', '4', '5', '6', '1', '2', '3', '.', '0'].map((num) => (
                  <button
                    key={num}
                    className="numpad-btn"
                    onClick={() => handleNumpad(num)}
                  >
                    {num}
                  </button>
                ))}
                <button
                  className="numpad-btn"
                  onClick={() => handleNumpad('backspace')}
                >
                  <Delete className="h-5 w-5 mx-auto" />
                </button>
              </div>
            </>
          )}

          {/* Bank payment - just show total */}
          {paymentMethod === 'bank' && (
            <div className="p-4 bg-gray-50 rounded-lg text-center">
              <p className="text-sm text-gray-500 mb-2">Pagesa me kartë/bank</p>
              <p className="text-2xl font-bold text-[#00a79d]">€{cartTotals.total.toFixed(2)}</p>
            </div>
          )}

          {/* Print Receipt Options */}
          <div className="space-y-2">
            <div className="flex items-center gap-3 p-3 bg-gray-50 rounded-lg">
              <Checkbox
                id="printReceipt"
                checked={printReceipt}
                onCheckedChange={setPrintReceipt}
                className="border-[#00a79d] data-[state=checked]:bg-[#00a79d]"
                data-testid="print-receipt-checkbox"
              />
              <label htmlFor="printReceipt" className="text-sm font-medium cursor-pointer flex-1">
                Shtyp kupon për klientin
              </label>
              <Printer className="h-4 w-4 text-gray-400" />
            </div>
            
            {/* Direct Print Option - only show if printReceipt is checked */}
            {printReceipt && (
              <div className="flex items-center gap-3 p-3 bg-blue-50 rounded-lg border border-blue-100">
                <Checkbox
                  id="directPrint"
                  checked={directPrintEnabled}
                  onCheckedChange={toggleDirectPrint}
                  className="border-blue-500 data-[state=checked]:bg-blue-500"
                  data-testid="direct-print-checkbox"
                />
                <label htmlFor="directPrint" className="text-sm font-medium cursor-pointer flex-1 text-blue-800">
                  Printim direkt (pa parapamje)
                </label>
              </div>
            )}
          </div>

          {/* Confirm Button */}
          <Button
            className="w-full h-12 bg-[#2196F3] hover:bg-[#1976D2]"
            onClick={handlePayment}
            data-testid="confirm-payment-btn"
          >
            <Receipt className="h-4 w-4 mr-2" />
            {printReceipt ? 'Shtyp & Përfundo' : 'Përfundo pa Shtypur'}
          </Button>
        </div>
      </DialogContent>
    </Dialog>
  );
};

export default PaymentDialog;
