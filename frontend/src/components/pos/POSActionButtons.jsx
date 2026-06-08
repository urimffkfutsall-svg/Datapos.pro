import React from 'react';
import { Button } from '../ui/button';
import { 
  FileText, 
  Package, 
  Receipt, 
  Trash2, 
  User, 
  Settings, 
  FileDown, 
  Printer, 
  XCircle,
  Percent
} from 'lucide-react';

export const POSActionButtons = ({
  // Actions
  onShowDocuments,
  onShowProductSearch,
  onPrintNote,
  onDeleteSelectedItem,
  onShowCustomer,
  onShowParams,
  onPrintA4,
  onShowPayment,
  onCloseDrawer,
  onClearCart,
  onToggleVat,
  // State
  cart,
  customerName,
  applyNoVat,
  user
}) => {
  const canToggleVat = user?.role === 'admin' || user?.role === 'manager';
  
  return (
    <div className="w-full lg:w-48 flex flex-row lg:flex-col gap-2">
      {/* Dokumentin - View recent documents/sales - F6 */}
      <Button
        variant="outline"
        className="flex-1 lg:h-14 flex items-center justify-center gap-2"
        onClick={onShowDocuments}
        data-testid="pos-documents-btn"
      >
        <FileText className="h-5 w-5" />
        <span className="hidden lg:inline">Dokumentin</span>
        <span className="text-xs bg-gray-200 px-1.5 py-0.5 rounded ml-1">F6</span>
      </Button>

      {/* Kërko artikullin - Search and add product - F12 */}
      <Button
        variant="outline"
        className="flex-1 lg:h-14 flex items-center justify-center gap-2"
        onClick={onShowProductSearch}
        data-testid="pos-add-product-btn"
      >
        <Package className="h-5 w-5" />
        <span className="hidden lg:inline">Kërko artikullin</span>
        <span className="text-xs bg-gray-200 px-1.5 py-0.5 rounded ml-1">F12</span>
      </Button>

      {/* Shtyp Noten - Print note/receipt */}
      <Button
        variant="outline"
        className="flex-1 lg:h-14 flex items-center justify-center gap-2"
        onClick={onPrintNote}
        data-testid="pos-print-note-btn"
      >
        <Receipt className="h-5 w-5" />
        <span className="hidden lg:inline">Shtyp Noten</span>
      </Button>

      {/* Fshij artikullin - Delete selected item - Delete */}
      <Button
        variant="outline"
        className="flex-1 lg:h-14 flex items-center justify-center gap-2"
        onClick={onDeleteSelectedItem}
        data-testid="pos-delete-btn"
      >
        <Trash2 className="h-5 w-5" />
        <span className="hidden lg:inline">Fshij artikullin</span>
        <span className="text-xs bg-gray-200 px-1.5 py-0.5 rounded ml-1">Del</span>
      </Button>

      {/* Konsumatori - Customer info */}
      <Button
        variant="outline"
        className={`flex-1 lg:h-14 flex items-center justify-center gap-2 ${customerName ? 'border-[#00a79d] text-[#00a79d]' : ''}`}
        onClick={onShowCustomer}
        data-testid="pos-customer-btn"
      >
        <User className="h-5 w-5" />
        <span className="hidden lg:inline">Konsumatori</span>
      </Button>

      {/* Parametrat - Settings/params */}
      <Button
        variant="outline"
        className="flex-1 lg:h-14 flex items-center justify-center gap-2"
        onClick={onShowParams}
        data-testid="pos-params-btn"
      >
        <Settings className="h-5 w-5" />
        <span className="hidden lg:inline">Parametrat</span>
      </Button>

      {/* Printo A4 - Print A4 Invoice - F4 */}
      <Button
        variant="outline"
        className="flex-1 lg:h-14 flex items-center justify-center gap-2 border-blue-500 text-blue-600 hover:bg-blue-50"
        onClick={onPrintA4}
        disabled={cart.length === 0}
        data-testid="pos-print-a4-btn"
      >
        <FileDown className="h-5 w-5" />
        <span className="hidden lg:inline">Printo A4</span>
        <span className="text-xs bg-blue-100 px-1.5 py-0.5 rounded ml-1">F4</span>
      </Button>

      {/* Shtyp - Print and finish (payment) - F2 */}
      <Button
        className="flex-1 lg:h-16 flex items-center justify-center gap-2 bg-green-600 hover:bg-green-700 text-white font-semibold shadow-lg"
        onClick={() => cart.length > 0 && onShowPayment()}
        disabled={cart.length === 0}
        data-testid="pos-print-btn"
      >
        <Printer className="h-5 w-5" />
        <span className="hidden lg:inline">Shtyp</span>
        <span className="text-xs bg-white/20 px-2 py-0.5 rounded ml-1">F2</span>
      </Button>

      {/* Mbyll Arkën - Close drawer */}
      <Button
        variant="outline"
        className="flex-1 lg:h-14 flex items-center justify-center gap-2"
        onClick={onCloseDrawer}
        data-testid="pos-close-drawer-btn"
      >
        <XCircle className="h-5 w-5" />
        <span className="hidden lg:inline">Mbyll Arkën</span>
      </Button>

      {/* Pastro - Clear cart */}
      <Button
        variant="outline"
        className="flex-1 lg:h-14 flex items-center justify-center gap-2 text-red-500 hover:bg-red-50"
        onClick={onClearCart}
        data-testid="pos-clear-btn"
      >
        <Trash2 className="h-5 w-5" />
        <span className="hidden lg:inline">Pastro</span>
      </Button>

      {/* Pa TVSH - Toggle VAT (vetëm admin/manager) */}
      {canToggleVat && (
        <Button
          className={`flex-1 lg:h-14 flex items-center justify-center gap-2 ${applyNoVat ? 'bg-orange-500 hover:bg-orange-600' : 'bg-[#00a79d] hover:bg-[#008f86]'}`}
          onClick={onToggleVat}
          data-testid="pos-no-vat-btn"
        >
          <Percent className="h-5 w-5" />
          <span className="hidden lg:inline">{applyNoVat ? 'Me TVSH' : 'Pa TVSH'}</span>
        </Button>
      )}
    </div>
  );
};

export default POSActionButtons;
