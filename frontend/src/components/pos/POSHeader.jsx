import React, { useRef } from 'react';
import { Input } from '../ui/input';
import { Search, User } from 'lucide-react';

export const POSHeader = ({
  user,
  search,
  setSearch,
  showSearchResults,
  setShowSearchResults,
  mainSearchResults,
  addToCart,
  customerName,
  searchRef
}) => {
  return (
    <div className="flex items-center gap-4 mb-4">
      {/* User info */}
      <div className="flex items-center gap-2 text-sm text-gray-500">
        <User className="h-4 w-4" />
        <span>{user?.full_name}</span>
      </div>
      
      {/* Search input */}
      <div className="flex-1 relative">
        <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 h-4 w-4 text-gray-400" />
        <Input
          ref={searchRef}
          type="text"
          placeholder="Kërko produkt ose skano barkod..."
          value={search}
          onChange={(e) => {
            setSearch(e.target.value);
            setShowSearchResults(e.target.value.trim().length > 0);
          }}
          onFocus={() => search.trim() && setShowSearchResults(true)}
          onBlur={() => setTimeout(() => setShowSearchResults(false), 200)}
          className="pl-10 h-12 border-[#00a79d] focus:ring-[#00a79d]"
          data-testid="pos-search-input"
        />
        
        {/* Live Search Results Dropdown */}
        {showSearchResults && mainSearchResults.length > 0 && (
          <div className="absolute top-full left-0 right-0 mt-1 bg-white border border-gray-200 rounded-lg shadow-lg z-50 max-h-64 overflow-auto">
            {mainSearchResults.map((product) => (
              <div
                key={product.id}
                className={`p-3 cursor-pointer border-b border-gray-100 last:border-b-0 ${
                  product.current_stock > 0 ? 'hover:bg-[#E0F7FA]' : 'bg-gray-50 opacity-70'
                }`}
                onMouseDown={(e) => {
                  e.preventDefault();
                  addToCart(product);
                }}
              >
                <div className="flex justify-between items-center">
                  <div>
                    <p className="font-medium text-gray-900">{product.name || 'Pa emër'}</p>
                    <p className="text-sm text-gray-500">Barkod: {product.barcode || '-'}</p>
                  </div>
                  <div className="text-right">
                    <p className="font-bold text-[#00a79d]">€{(product.sale_price || 0).toFixed(2)}</p>
                    <p className={`text-xs ${product.current_stock > 0 ? 'text-green-600' : 'text-red-500 font-semibold'}`}>
                      {product.current_stock > 0 ? `Stok: ${product.current_stock}` : 'Pa stok!'}
                    </p>
                  </div>
                </div>
              </div>
            ))}
          </div>
        )}
        
        {/* No results message */}
        {showSearchResults && search.trim() && mainSearchResults.length === 0 && (
          <div className="absolute top-full left-0 right-0 mt-1 bg-white border border-gray-200 rounded-lg shadow-lg z-50 p-4 text-center text-gray-500">
            Nuk u gjet asnjë produkt për &quot;{search}&quot;
          </div>
        )}
      </div>
      
      {/* Customer name badge */}
      {customerName && (
        <div className="flex items-center gap-2 px-3 py-1 bg-[#00a79d]/10 rounded-lg">
          <User className="h-4 w-4 text-[#00a79d]" />
          <span className="text-sm font-medium">{customerName}</span>
        </div>
      )}
    </div>
  );
};

export default POSHeader;
