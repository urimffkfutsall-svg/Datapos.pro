import React, { forwardRef } from 'react';

// Thermal Receipt Component (80mm width ~ 302px at 96dpi)
const ThermalReceipt = forwardRef(({ sale, companyInfo }, ref) => {
  const company = companyInfo || {};
  
  const formatDate = (dateStr) => {
    const date = new Date(dateStr || new Date());
    return date.toLocaleDateString('sq-AL', {
      day: '2-digit',
      month: '2-digit',
      year: 'numeric'
    });
  };

  const formatTime = (dateStr) => {
    const date = new Date(dateStr || new Date());
    return date.toLocaleTimeString('sq-AL', {
      hour: '2-digit',
      minute: '2-digit'
    });
  };

  return (
    <div 
      ref={ref} 
      className="thermal-receipt bg-white mx-auto"
      style={{ 
        width: '80mm',
        minHeight: '100mm',
        padding: '3mm',
        fontFamily: 'monospace',
        fontSize: '12px',
        lineHeight: '1.3'
      }}
    >
      {/* Header */}
      <div className="text-center border-b border-dashed border-gray-400 pb-2 mb-2">
        {/* Logo if available */}
        {company.logo_url && (
          <div className="mb-2">
            <img 
              src={company.logo_url} 
              alt="Logo" 
              className="mx-auto" 
              style={{ height: '40px', maxWidth: '60mm', objectFit: 'contain' }}
              onError={(e) => e.target.style.display = 'none'}
            />
          </div>
        )}
        <div className="text-lg font-bold">{company.company_name || 'DataPOS'}</div>
        {company.address && <div className="text-xs">{company.address}</div>}
        {company.city && <div className="text-xs">{company.city}</div>}
        {company.phone && <div className="text-xs">Tel: {company.phone}</div>}
      </div>

      {/* Receipt Info */}
      <div className="text-center mb-2">
        <div className="font-bold">KUPON SHITJE</div>
        <div className="text-xs">(Jo Fiskal)</div>
      </div>

      <div className="flex justify-between text-xs mb-2">
        <span>Nr: {sale?.receipt_number || '-'}</span>
        <span>{formatDate(sale?.created_at)}</span>
      </div>
      <div className="flex justify-between text-xs mb-2 border-b border-dashed border-gray-400 pb-2">
        <span>Ora: {formatTime(sale?.created_at)}</span>
        <span>Arkëtar: {sale?.cashier_name || '-'}</span>
      </div>

      {/* Items */}
      <div className="mb-2">
        <div className="flex justify-between text-xs font-bold border-b border-gray-300 pb-1 mb-1">
          <span className="flex-1">Artikulli</span>
          <span className="w-12 text-right">Sasia</span>
          <span className="w-16 text-right">Çmimi</span>
        </div>
        {sale?.items?.map((item, index) => (
          <div key={index} className="mb-1">
            <div className="text-xs truncate">{item.product_name || 'Produkt'}</div>
            <div className="flex justify-between text-xs">
              <span className="flex-1"></span>
              <span className="w-12 text-right">{item.quantity}x</span>
              <span className="w-16 text-right">€{(item.unit_price || 0).toFixed(2)}</span>
            </div>
            {item.discount_percent > 0 && (
              <div className="text-xs text-gray-500 text-right">
                -{item.discount_percent}% zbritje
              </div>
            )}
            <div className="flex justify-between text-xs font-semibold">
              <span></span>
              <span>€{(item.total || (item.quantity * item.unit_price)).toFixed(2)}</span>
            </div>
          </div>
        ))}
      </div>

      {/* Totals */}
      <div className="border-t border-dashed border-gray-400 pt-2 mb-2">
        <div className="flex justify-between text-xs">
          <span>Nëntotali:</span>
          <span>€{(sale?.subtotal || 0).toFixed(2)}</span>
        </div>
        {sale?.total_discount > 0 && (
          <div className="flex justify-between text-xs">
            <span>Zbritja:</span>
            <span>-€{(sale?.total_discount || 0).toFixed(2)}</span>
          </div>
        )}
        {sale?.total_vat > 0 && (
          <div className="flex justify-between text-xs">
            <span>TVSH:</span>
            <span>€{(sale?.total_vat || 0).toFixed(2)}</span>
          </div>
        )}
        <div className="flex justify-between text-base font-bold border-t border-gray-400 pt-1 mt-1">
          <span>TOTAL:</span>
          <span>€{(sale?.grand_total || 0).toFixed(2)}</span>
        </div>
      </div>

      {/* Payment Info */}
      <div className="border-t border-dashed border-gray-400 pt-2 mb-2 text-xs">
        <div className="flex justify-between">
          <span>Pagesa:</span>
          <span>{sale?.payment_method === 'cash' ? 'Cash' : 'Bankë'}</span>
        </div>
        {sale?.payment_method === 'cash' && (
          <>
            <div className="flex justify-between">
              <span>Paguar:</span>
              <span>€{(sale?.cash_amount || 0).toFixed(2)}</span>
            </div>
            <div className="flex justify-between font-bold">
              <span>Kusuri:</span>
              <span>€{(sale?.change_amount || 0).toFixed(2)}</span>
            </div>
          </>
        )}
      </div>

      {/* Footer */}
      <div className="text-center border-t border-dashed border-gray-400 pt-2 text-xs">
        {/* Customer Name if provided */}
        {sale?.customer_name && (
          <div className="mb-2 pb-2 border-b border-dashed border-gray-300">
            <span className="text-gray-600">Klient: </span>
            <span className="font-medium">{sale.customer_name}</span>
          </div>
        )}
        
        <div className="font-semibold">Faleminderit!</div>
        <div className="text-gray-500">Mirë se vini përsëri</div>
        
        <div className="mt-2 text-gray-400 text-xs">
          --------------------------------
        </div>
        
        {company.company_name && (
          <div className="text-gray-400 text-xs mt-1">
            {company.company_name}
          </div>
        )}
      </div>

      {/* Print Styles */}
      <style>{`
        @media print {
          .thermal-receipt {
            width: 80mm !important;
            padding: 2mm !important;
            margin: 0 !important;
          }
          @page {
            size: 80mm auto;
            margin: 0;
          }
        }
      `}</style>
    </div>
  );
});

ThermalReceipt.displayName = 'ThermalReceipt';

export default ThermalReceipt;
