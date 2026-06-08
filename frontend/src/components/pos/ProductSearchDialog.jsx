import React from 'react';
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
} from '../ui/dialog';
import { Input } from '../ui/input';
import { ScrollArea } from '../ui/scroll-area';
import { Search } from 'lucide-react';

export const ProductSearchDialog = ({
  open,
  onOpenChange,
  dialogSearch,
  setDialogSearch,
  filteredProducts,
  addToCart
}) => {
  return (
    <Dialog open={open} onOpenChange={(isOpen) => {
      onOpenChange(isOpen);
      if (!isOpen) setDialogSearch('');
    }}>
      <DialogContent className="sm:max-w-lg">
        <DialogHeader>
          <DialogTitle>Kërko Artikullin</DialogTitle>
        </DialogHeader>
        <div className="space-y-4">
          <div className="relative">
            <Search className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-gray-400" />
            <Input
              placeholder="Kërko sipas emrit ose barkodit..."
              className="pl-10"
              autoFocus
              value={dialogSearch}
              onChange={(e) => setDialogSearch(e.target.value)}
              onKeyDown={(e) => {
                if (e.key === 'Enter' && filteredProducts.length > 0) {
                  addToCart(filteredProducts[0]);
                  setDialogSearch('');
                }
              }}
            />
          </div>
          <ScrollArea className="h-64">
            <div className="space-y-2">
              {filteredProducts.map((product) => (
                <div
                  key={product.id}
                  className={`p-3 border rounded-lg cursor-pointer transition-colors ${
                    product.current_stock > 0 ? 'hover:bg-[#E0F7FA]' : 'bg-gray-100 opacity-70'
                  }`}
                  onClick={() => {
                    addToCart(product);
                    setDialogSearch('');
                  }}
                >
                  <div className="flex justify-between items-center">
                    <div>
                      <p className="font-medium">{product.name || 'Pa emër'}</p>
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
              {filteredProducts.length === 0 && dialogSearch.trim() && (
                <p className="text-center text-gray-400 py-8">Nuk u gjet asnjë produkt për &quot;{dialogSearch}&quot;</p>
              )}
              {filteredProducts.length === 0 && !dialogSearch.trim() && (
                <p className="text-center text-gray-400 py-8">Shkruani emrin ose barkod-in e produktit</p>
              )}
            </div>
          </ScrollArea>
        </div>
      </DialogContent>
    </Dialog>
  );
};

export default ProductSearchDialog;
