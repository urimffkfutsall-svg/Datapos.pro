import React from 'react';
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
} from '../ui/dialog';
import { Button } from '../ui/button';

export const ParamsDialog = ({
  open,
  onOpenChange,
  cashDrawer,
  user,
  applyNoVat,
  handleNoVat
}) => {
  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent>
        <DialogHeader>
          <DialogTitle>Parametrat e Arkës</DialogTitle>
        </DialogHeader>
        <div className="space-y-4 py-4">
          <div className="p-4 bg-gray-50 rounded-lg">
            <div className="flex justify-between mb-2">
              <span className="text-gray-500">Bilanci Fillestar:</span>
              <span className="font-semibold">€{cashDrawer?.opening_balance?.toFixed(2) || '0.00'}</span>
            </div>
            <div className="flex justify-between mb-2">
              <span className="text-gray-500">Bilanci Aktual:</span>
              <span className="font-semibold">€{cashDrawer?.current_balance?.toFixed(2) || '0.00'}</span>
            </div>
            <div className="flex justify-between">
              <span className="text-gray-500">Bilanci i Pritshëm:</span>
              <span className="font-semibold text-[#00a79d]">€{cashDrawer?.expected_balance?.toFixed(2) || '0.00'}</span>
            </div>
          </div>
          <div className="p-4 bg-gray-50 rounded-lg">
            <div className="flex justify-between mb-2">
              <span className="text-gray-500">Hapur më:</span>
              <span className="font-semibold">{cashDrawer?.opened_at ? new Date(cashDrawer.opened_at).toLocaleString('sq-AL') : '-'}</span>
            </div>
            <div className="flex justify-between">
              <span className="text-gray-500">Arkëtari:</span>
              <span className="font-semibold">{user?.full_name}</span>
            </div>
          </div>
          <div className="flex items-center justify-between p-4 bg-gray-50 rounded-lg">
            <span className="text-gray-500">Pa TVSH:</span>
            <Button
              variant={applyNoVat ? 'default' : 'outline'}
              size="sm"
              onClick={handleNoVat}
              className={applyNoVat ? 'bg-orange-500' : ''}
            >
              {applyNoVat ? 'Aktiv' : 'Joaktiv'}
            </Button>
          </div>
        </div>
      </DialogContent>
    </Dialog>
  );
};

export default ParamsDialog;
