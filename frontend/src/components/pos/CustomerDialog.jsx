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
import { Textarea } from '../ui/textarea';

export const CustomerDialog = ({
  open,
  onOpenChange,
  customerName,
  setCustomerName,
  customerNote,
  setCustomerNote
}) => {
  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent>
        <DialogHeader>
          <DialogTitle>Informacioni i Konsumatorit</DialogTitle>
        </DialogHeader>
        <div className="space-y-4 py-4">
          <div className="space-y-2">
            <Label>Emri i Konsumatorit</Label>
            <Input
              value={customerName}
              onChange={(e) => setCustomerName(e.target.value)}
              placeholder="Emri (opsional)"
              data-testid="customer-name-input"
            />
          </div>
          <div className="space-y-2">
            <Label>Shënime</Label>
            <Textarea
              value={customerNote}
              onChange={(e) => setCustomerNote(e.target.value)}
              placeholder="Shënime shtesë..."
              data-testid="customer-note-input"
            />
          </div>
        </div>
        <DialogFooter>
          <Button variant="outline" onClick={() => { setCustomerName(''); setCustomerNote(''); }}>
            Pastro
          </Button>
          <Button onClick={() => onOpenChange(false)} className="bg-[#00a79d] hover:bg-[#008f86]">
            Ruaj
          </Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  );
};

export default CustomerDialog;
