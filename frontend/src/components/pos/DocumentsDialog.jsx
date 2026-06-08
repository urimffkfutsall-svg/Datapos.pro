import React from 'react';
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
} from '../ui/dialog';
import { Button } from '../ui/button';
import { ScrollArea } from '../ui/scroll-area';
import { FileDown } from 'lucide-react';

export const DocumentsDialog = ({
  open,
  onOpenChange,
  recentSales,
  handleViewSaleA4
}) => {
  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent className="sm:max-w-lg">
        <DialogHeader>
          <DialogTitle>Dokumentet e Fundit</DialogTitle>
        </DialogHeader>
        <ScrollArea className="h-80">
          <div className="space-y-2">
            {recentSales.map((sale) => (
              <div 
                key={sale.id} 
                className="p-3 border rounded-lg hover:bg-gray-50 cursor-pointer" 
                onClick={() => handleViewSaleA4(sale.id)}
              >
                <div className="flex justify-between items-center">
                  <div>
                    <p className="font-medium">{sale.receipt_number}</p>
                    <p className="text-sm text-gray-500">
                      {new Date(sale.created_at).toLocaleString('sq-AL')}
                    </p>
                  </div>
                  <div className="flex items-center gap-3">
                    <div className="text-right">
                      <p className="font-bold text-[#00a79d]">€{sale.grand_total?.toFixed(2)}</p>
                      <p className="text-xs text-gray-400 capitalize">{sale.payment_method}</p>
                    </div>
                    <Button
                      variant="ghost"
                      size="icon"
                      className="h-8 w-8 text-blue-600"
                      onClick={(e) => { e.stopPropagation(); handleViewSaleA4(sale.id); }}
                      title="Printo A4"
                    >
                      <FileDown className="h-4 w-4" />
                    </Button>
                  </div>
                </div>
              </div>
            ))}
            {recentSales.length === 0 && (
              <p className="text-center text-gray-400 py-8">Nuk ka dokumente</p>
            )}
          </div>
        </ScrollArea>
      </DialogContent>
    </Dialog>
  );
};

export default DocumentsDialog;
