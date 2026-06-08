import React from 'react';
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
  DialogFooter,
} from '../ui/dialog';
import { Button } from '../ui/button';
import { Input } from '../ui/input';
import { Label } from '../ui/label';
import { FileDown } from 'lucide-react';

export const BuyerFormDialog = ({
  open,
  onOpenChange,
  buyerInfo,
  setBuyerInfo,
  onProceed
}) => {
  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent className="sm:max-w-md">
        <DialogHeader>
          <DialogTitle>Të Dhënat e Blerësit</DialogTitle>
        </DialogHeader>
        <div className="space-y-4 py-4">
          <div className="space-y-2">
            <Label>Emri i Blerësit / Kompanisë</Label>
            <Input
              value={buyerInfo.name}
              onChange={(e) => setBuyerInfo({ ...buyerInfo, name: e.target.value })}
              placeholder="Emri i plotë ose emri i kompanisë"
            />
          </div>
          <div className="space-y-2">
            <Label>Adresa</Label>
            <Input
              value={buyerInfo.address}
              onChange={(e) => setBuyerInfo({ ...buyerInfo, address: e.target.value })}
              placeholder="Adresa e blerësit"
            />
          </div>
          <div className="space-y-2">
            <Label>Telefoni</Label>
            <Input
              value={buyerInfo.phone}
              onChange={(e) => setBuyerInfo({ ...buyerInfo, phone: e.target.value })}
              placeholder="+383 XX XXX XXX"
            />
          </div>
          <div className="grid grid-cols-2 gap-4">
            <div className="space-y-2">
              <Label>NUI</Label>
              <Input
                value={buyerInfo.nui}
                onChange={(e) => setBuyerInfo({ ...buyerInfo, nui: e.target.value })}
                placeholder="Numri Unik"
              />
            </div>
            <div className="space-y-2">
              <Label>NF</Label>
              <Input
                value={buyerInfo.nf}
                onChange={(e) => setBuyerInfo({ ...buyerInfo, nf: e.target.value })}
                placeholder="Numri Fiskal"
              />
            </div>
          </div>
        </div>
        <DialogFooter className="gap-2">
          <Button variant="outline" onClick={() => onOpenChange(false)}>
            Anulo
          </Button>
          <Button 
            onClick={onProceed}
            className="bg-[#00a79d] hover:bg-[#008f86]"
          >
            <FileDown className="h-4 w-4 mr-2" />
            Vazhdo me Faturën
          </Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  );
};

export default BuyerFormDialog;
