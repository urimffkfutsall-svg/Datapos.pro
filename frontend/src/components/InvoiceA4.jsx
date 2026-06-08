import React, { forwardRef } from 'react';

// Invoice A4 Component for printing
const InvoiceA4 = forwardRef(({ sale, companyInfo }, ref) => {
  const defaultCompany = {
    company_name: 'DataPOS',
    address: '',
    city: '',
    phone: '',
    email: '',
    nui: '',
    nf: '',
    logo_url: '',
  };

  const company = companyInfo && companyInfo.company_name ? companyInfo : defaultCompany;
  const buyer = sale?.buyer_info || {};
  
  // Format date
  const formatDate = (dateStr) => {
    const date = new Date(dateStr);
    return date.toLocaleDateString('sq-AL', {
      day: '2-digit',
      month: '2-digit', 
      year: 'numeric',
      hour: '2-digit',
      minute: '2-digit'
    });
  };

  return (
    <div ref={ref} className="invoice-a4 bg-white p-8 w-[210mm] min-h-[297mm] mx-auto" style={{ fontFamily: 'Arial, sans-serif' }}>
      {/* Header */}
      <div className="flex justify-between items-start border-b-2 border-gray-800 pb-4 mb-6">
        {/* Company Logo & Info */}
        <div className="flex-1">
          <div className="flex items-center gap-2 mb-2">
            {/* Show company logo if available, otherwise show default icon */}
            {company.logo_url ? (
              <img 
                src={company.logo_url} 
                alt="Logo" 
                className="h-10 w-auto object-contain"
                onError={(e) => e.target.style.display = 'none'}
              />
            ) : (
              <div className="bg-[#00a79d] p-2 rounded-lg">
                <svg className="w-6 h-6 text-white" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                  <rect x="5" y="2" width="14" height="20" rx="2" ry="2"/>
                  <line x1="12" y1="18" x2="12" y2="18"/>
                </svg>
              </div>
            )}
            <span className="text-2xl font-bold">
              <span className="text-[#00a79d]">{company.company_name || 'DataPOS'}</span>
            </span>
          </div>
          {company.address && <p className="text-sm text-gray-600">{company.address}{company.city ? `, ${company.city}` : ''}</p>}
          {company.phone && <p className="text-sm text-gray-600">Tel: {company.phone}</p>}
          {company.email && <p className="text-sm text-gray-600">Email: {company.email}</p>}
        </div>

        {/* Invoice Info */}
        <div className="text-right">
          <h1 className="text-2xl font-bold text-gray-800 mb-2">FATURË</h1>
          <p className="text-sm"><span className="font-semibold">Nr. Faturës:</span> {sale?.receipt_number || '-'}</p>
          <p className="text-sm"><span className="font-semibold">Data:</span> {sale?.created_at ? formatDate(sale.created_at) : '-'}</p>
        </div>
      </div>

      {/* Company Details */}
      <div className="grid grid-cols-2 gap-8 mb-6">
        <div className="bg-gray-50 p-4 rounded">
          <h3 className="font-bold text-gray-800 mb-2 text-sm uppercase">Shitësi</h3>
          <p className="font-semibold">{company.company_name || 'DataPOS'}</p>
          {company.nui && <p className="text-sm text-gray-600">NUI: {company.nui}</p>}
          {company.nf && <p className="text-sm text-gray-600">NF: {company.nf}</p>}
          {company.vat_number && <p className="text-sm text-gray-600">TVSH: {company.vat_number}</p>}
          {company.address && <p className="text-sm text-gray-600">{company.address}</p>}
          {company.city && <p className="text-sm text-gray-600">{company.city} {company.postal_code}</p>}
        </div>
        <div className="bg-gray-50 p-4 rounded">
          <h3 className="font-bold text-gray-800 mb-2 text-sm uppercase">Blerësi</h3>
          {buyer.name || sale?.customer_name ? (
            <>
              <p className="font-semibold">{buyer.name || sale?.customer_name}</p>
              {buyer.nui && <p className="text-sm text-gray-600">NUI: {buyer.nui}</p>}
              {buyer.nf && <p className="text-sm text-gray-600">NF: {buyer.nf}</p>}
              {buyer.address && <p className="text-sm text-gray-600">{buyer.address}</p>}
              {buyer.phone && <p className="text-sm text-gray-600">Tel: {buyer.phone}</p>}
            </>
          ) : (
            <p className="text-gray-500 italic">Konsumator i përgjithshëm</p>
          )}
          {sale?.notes && <p className="text-sm text-gray-600 mt-1">{sale.notes}</p>}
        </div>
      </div>

      {/* Items Table */}
      <table className="w-full mb-6 border-collapse">
        <thead>
          <tr className="bg-gray-800 text-white">
            <th className="py-3 px-4 text-left text-sm font-semibold">Nr.</th>
            <th className="py-3 px-4 text-left text-sm font-semibold">Përshkrimi</th>
            <th className="py-3 px-4 text-center text-sm font-semibold">Sasia</th>
            <th className="py-3 px-4 text-right text-sm font-semibold">Çmimi</th>
            <th className="py-3 px-4 text-center text-sm font-semibold">Zbritja %</th>
            <th className="py-3 px-4 text-center text-sm font-semibold">TVSH %</th>
            <th className="py-3 px-4 text-right text-sm font-semibold">Totali</th>
          </tr>
        </thead>
        <tbody>
          {sale?.items?.map((item, index) => (
            <tr key={index} className={index % 2 === 0 ? 'bg-white' : 'bg-gray-50'}>
              <td className="py-3 px-4 text-sm border-b border-gray-200">{index + 1}</td>
              <td className="py-3 px-4 text-sm border-b border-gray-200 font-medium">{item.product_name || 'Produkt'}</td>
              <td className="py-3 px-4 text-sm border-b border-gray-200 text-center">{item.quantity}</td>
              <td className="py-3 px-4 text-sm border-b border-gray-200 text-right">€{(item.unit_price || 0).toFixed(2)}</td>
              <td className="py-3 px-4 text-sm border-b border-gray-200 text-center">{item.discount_percent || 0}%</td>
              <td className="py-3 px-4 text-sm border-b border-gray-200 text-center">{item.vat_percent || 0}%</td>
              <td className="py-3 px-4 text-sm border-b border-gray-200 text-right font-semibold">€{(item.total || 0).toFixed(2)}</td>
            </tr>
          ))}
        </tbody>
      </table>

      {/* Totals and Stamp Section */}
      <div className="flex justify-between items-end mb-8">
        {/* Digital Stamp - Vula Digjitale */}
        <div className="flex flex-col items-center">
          {company.stamp_url && (
            <div className="text-center">
              <img 
                src={company.stamp_url} 
                alt="Vula Digjitale" 
                className="max-w-[150px] max-h-[150px] object-contain opacity-90"
                style={{ mixBlendMode: 'multiply' }}
                onError={(e) => e.target.style.display = 'none'}
              />
              <p className="text-xs text-gray-500 mt-1">Vula Digjitale</p>
            </div>
          )}
        </div>

        {/* Totals */}
        <div className="w-72">
          <div className="flex justify-between py-2 border-b border-gray-200">
            <span className="text-gray-600">Nëntotali:</span>
            <span className="font-semibold">€{(sale?.subtotal || 0).toFixed(2)}</span>
          </div>
          <div className="flex justify-between py-2 border-b border-gray-200">
            <span className="text-gray-600">Zbritja:</span>
            <span className="font-semibold text-red-600">-€{(sale?.total_discount || 0).toFixed(2)}</span>
          </div>
          <div className="flex justify-between py-2 border-b border-gray-200">
            <span className="text-gray-600">TVSH:</span>
            <span className="font-semibold">€{(sale?.total_vat || 0).toFixed(2)}</span>
          </div>
          <div className="flex justify-between py-3 bg-gray-800 text-white px-4 rounded mt-2">
            <span className="font-bold text-lg">TOTALI:</span>
            <span className="font-bold text-lg">€{(sale?.grand_total || 0).toFixed(2)}</span>
          </div>
        </div>
      </div>

      {/* Payment Info */}
      <div className="bg-[#E0F7FA] p-4 rounded mb-8">
        <h3 className="font-bold text-gray-800 mb-2 text-sm uppercase">Informacioni i Pagesës</h3>
        <div className="grid grid-cols-3 gap-4 text-sm">
          <div>
            <span className="text-gray-600">Metoda:</span>
            <span className="font-semibold ml-2">
              {sale?.payment_method === 'cash' ? 'Cash' : sale?.payment_method === 'bank' ? 'Bankë' : 'E përzier'}
            </span>
          </div>
          {sale?.payment_method === 'cash' && (
            <>
              <div>
                <span className="text-gray-600">Paguar:</span>
                <span className="font-semibold ml-2">€{(sale?.cash_amount || 0).toFixed(2)}</span>
              </div>
              <div>
                <span className="text-gray-600">Kusuri:</span>
                <span className="font-semibold ml-2">€{(sale?.change_amount || 0).toFixed(2)}</span>
              </div>
            </>
          )}
          {sale?.payment_method === 'bank' && (
            <div>
              <span className="text-gray-600">Paguar me kartë:</span>
              <span className="font-semibold ml-2">€{(sale?.bank_amount || 0).toFixed(2)}</span>
            </div>
          )}
        </div>
      </div>

      {/* Footer */}
      <div className="border-t-2 border-gray-800 pt-4 mt-auto">
        <div className="text-center text-sm text-gray-600">
          <p className="font-semibold mb-1">Faleminderit për blerjen tuaj!</p>
          {company.phone && <p>Për çdo pyetje kontaktoni: {company.phone}</p>}
          <p className="text-xs mt-2 text-gray-400">Kjo faturë është gjeneruar automatikisht nga sistemi DataPOS</p>
        </div>
      </div>

      {/* Print Styles */}
      <style>{`
        @media print {
          .invoice-a4 {
            width: 210mm !important;
            min-height: 297mm !important;
            padding: 15mm !important;
            margin: 0 !important;
            box-shadow: none !important;
          }
          
          @page {
            size: A4;
            margin: 0;
          }
        }
      `}</style>
    </div>
  );
});

InvoiceA4.displayName = 'InvoiceA4';

export default InvoiceA4;
