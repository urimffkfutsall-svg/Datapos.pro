import React, { useState, useEffect } from 'react';
import { api } from '../App';
import { toast } from 'sonner';
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from './ui/card';
import { Button } from './ui/button';
import { Input } from './ui/input';
import { Switch } from './ui/switch';
import {
  Table, TableBody, TableCell, TableHead, TableHeader, TableRow
} from './ui/table';
import {
  Dialog, DialogContent, DialogHeader, DialogTitle, DialogFooter
} from './ui/dialog';
import {
  Select, SelectTrigger, SelectContent, SelectItem, SelectValue
} from './ui/select';
import { Plus, Pencil, Trash2, Ticket } from 'lucide-react';

const emptyForm = {
  code: '',
  name: '',
  discount_type: 'percent',
  discount_value: 10,
  active: true,
  valid_from: '',
  valid_until: '',
  max_uses: '',
  min_purchase_amount: '',
};

const Label = ({ children }) => (
  <label className="text-sm font-medium text-gray-700 block mb-1">{children}</label>
);

const CouponsTab = () => {
  const [coupons, setCoupons] = useState([]);
  const [loading, setLoading] = useState(false);
  const [dialogOpen, setDialogOpen] = useState(false);
  const [editingId, setEditingId] = useState(null);
  const [form, setForm] = useState(emptyForm);

  const fetchCoupons = async () => {
    setLoading(true);
    try {
      const res = await api.get('/coupons');
      setCoupons(res.data || []);
    } catch (e) {
      console.error(e);
      toast.error('Nuk u ngarkuan kuponet');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => { fetchCoupons(); }, []);

  const openCreate = () => {
    setEditingId(null);
    setForm(emptyForm);
    setDialogOpen(true);
  };

  const openEdit = (c) => {
    setEditingId(c.id);
    setForm({
      code: c.code || '',
      name: c.name || '',
      discount_type: c.discount_type || 'percent',
      discount_value: c.discount_value ?? 0,
      active: c.active !== false,
      valid_from: c.valid_from ? String(c.valid_from).substring(0, 10) : '',
      valid_until: c.valid_until ? String(c.valid_until).substring(0, 10) : '',
      max_uses: c.max_uses ?? '',
      min_purchase_amount: c.min_purchase_amount ?? '',
    });
    setDialogOpen(true);
  };

  const handleSave = async () => {
    if (!form.code.trim() || !form.name.trim()) {
      toast.error('Kodi dhe emri jane te detyrueshem');
      return;
    }
    const val = parseFloat(form.discount_value);
    if (isNaN(val) || val <= 0) {
      toast.error('Vlera e zbritjes duhet me e madhe se 0');
      return;
    }
    if (form.discount_type === 'percent' && val > 100) {
      toast.error('Perqindja s\'mund te kaloje 100');
      return;
    }
    const payload = {
      code: form.code.trim().toUpperCase(),
      name: form.name.trim(),
      discount_type: form.discount_type,
      discount_value: val,
      active: !!form.active,
      valid_from: form.valid_from ? new Date(form.valid_from + 'T00:00:00').toISOString() : null,
      valid_until: form.valid_until ? new Date(form.valid_until + 'T23:59:59').toISOString() : null,
      max_uses: form.max_uses ? parseInt(form.max_uses) : null,
      min_purchase_amount: form.min_purchase_amount ? parseFloat(form.min_purchase_amount) : null,
    };
    try {
      if (editingId) {
        await api.put(`/coupons/${editingId}`, payload);
        toast.success('Kuponi u perditesua');
      } else {
        await api.post('/coupons', payload);
        toast.success('Kuponi u krijua');
      }
      setDialogOpen(false);
      fetchCoupons();
    } catch (e) {
      const msg = e?.response?.data?.detail || 'Gabim gjate ruajtjes';
      toast.error(msg);
    }
  };

  const handleDelete = async (c) => {
    if (!window.confirm(`Fshij kuponin "${c.code}"?`)) return;
    try {
      await api.delete(`/coupons/${c.id}`);
      toast.success('Kuponi u fshi');
      fetchCoupons();
    } catch (e) {
      toast.error(e?.response?.data?.detail || 'Gabim gjate fshirjes');
    }
  };

  const fmtDiscount = (c) => {
    if (c.discount_type === 'percent') return `${c.discount_value}%`;
    return `${Number(c.discount_value).toFixed(2)} EUR`;
  };

  const fmtDate = (s) => {
    if (!s) return '-';
    try { return new Date(s).toLocaleDateString('sq-AL'); } catch { return String(s); }
  };

  return (
    <Card>
      <CardHeader>
        <div className="flex items-center justify-between flex-wrap gap-3">
          <div>
            <CardTitle className="flex items-center gap-2">
              <Ticket className="h-5 w-5 text-[#00a79d]" />
              Kodet e zbritjes
            </CardTitle>
            <CardDescription>
              Krijoni kode kuponi qe arketari mund t'i perdore te arka per te aplikuar zbritje ne shitje.
            </CardDescription>
          </div>
          <Button onClick={openCreate} className="bg-[#00a79d] hover:bg-[#008f86] text-white">
            <Plus className="h-4 w-4 mr-2" />
            Krijo Kupon
          </Button>
        </div>
      </CardHeader>
      <CardContent>
        {loading ? (
          <p className="text-gray-500 text-center py-6">Duke ngarkuar...</p>
        ) : coupons.length === 0 ? (
          <div className="text-center py-10 text-gray-500">
            <Ticket className="h-12 w-12 mx-auto mb-3 text-gray-300" />
            <p>Asnje kupon i krijuar ende.</p>
            <p className="text-sm mt-1">Klikoni "Krijo Kupon" per te shtuar te paren.</p>
          </div>
        ) : (
          <Table>
            <TableHeader>
              <TableRow>
                <TableHead>Kodi</TableHead>
                <TableHead>Emri</TableHead>
                <TableHead>Zbritja</TableHead>
                <TableHead>Statusi</TableHead>
                <TableHead>Vlefshme deri</TableHead>
                <TableHead>Perdor./Limit</TableHead>
                <TableHead className="text-right">Veprime</TableHead>
              </TableRow>
            </TableHeader>
            <TableBody>
              {coupons.map(c => (
                <TableRow key={c.id}>
                  <TableCell className="font-mono font-bold text-[#00a79d]">{c.code}</TableCell>
                  <TableCell>{c.name}</TableCell>
                  <TableCell className="font-semibold">{fmtDiscount(c)}</TableCell>
                  <TableCell>
                    <span className={c.active ? "text-green-600 font-semibold" : "text-gray-400"}>
                      {c.active ? 'Aktiv' : 'Joaktiv'}
                    </span>
                  </TableCell>
                  <TableCell>{fmtDate(c.valid_until)}</TableCell>
                  <TableCell>{c.used_count || 0}{c.max_uses ? `/${c.max_uses}` : ''}</TableCell>
                  <TableCell className="text-right">
                    <Button variant="ghost" size="icon" onClick={() => openEdit(c)} title="Modifiko">
                      <Pencil className="h-4 w-4" />
                    </Button>
                    <Button variant="ghost" size="icon" onClick={() => handleDelete(c)} title="Fshi" className="text-red-500 hover:text-red-700">
                      <Trash2 className="h-4 w-4" />
                    </Button>
                  </TableCell>
                </TableRow>
              ))}
            </TableBody>
          </Table>
        )}
      </CardContent>

      <Dialog open={dialogOpen} onOpenChange={setDialogOpen}>
        <DialogContent className="max-w-md">
          <DialogHeader>
            <DialogTitle>{editingId ? 'Modifiko Kuponin' : 'Krijo Kupon te Ri'}</DialogTitle>
          </DialogHeader>
          <div className="space-y-3 py-2">
            <div>
              <Label>Kodi *</Label>
              <Input
                value={form.code}
                onChange={(e) => setForm({...form, code: e.target.value.toUpperCase()})}
                placeholder="P.sh. ZBRITJE10"
                className="font-mono"
                maxLength={50}
              />
            </div>
            <div>
              <Label>Emri / Pershkrimi *</Label>
              <Input
                value={form.name}
                onChange={(e) => setForm({...form, name: e.target.value})}
                placeholder="P.sh. Zbritje Vere 2026"
              />
            </div>
            <div className="grid grid-cols-2 gap-3">
              <div>
                <Label>Lloji i zbritjes</Label>
                <Select value={form.discount_type} onValueChange={(v) => setForm({...form, discount_type: v})}>
                  <SelectTrigger><SelectValue /></SelectTrigger>
                  <SelectContent>
                    <SelectItem value="percent">% (Perqindje)</SelectItem>
                    <SelectItem value="fixed">EUR (Shume fikse)</SelectItem>
                  </SelectContent>
                </Select>
              </div>
              <div>
                <Label>Vlera *</Label>
                <Input
                  type="number"
                  step="0.01"
                  min="0"
                  value={form.discount_value}
                  onChange={(e) => setForm({...form, discount_value: e.target.value})}
                />
              </div>
            </div>
            <div className="grid grid-cols-2 gap-3">
              <div>
                <Label>Vlefshme nga</Label>
                <Input
                  type="date"
                  value={form.valid_from}
                  onChange={(e) => setForm({...form, valid_from: e.target.value})}
                />
              </div>
              <div>
                <Label>Vlefshme deri</Label>
                <Input
                  type="date"
                  value={form.valid_until}
                  onChange={(e) => setForm({...form, valid_until: e.target.value})}
                />
              </div>
            </div>
            <div className="grid grid-cols-2 gap-3">
              <div>
                <Label>Limiti i perdorimeve</Label>
                <Input
                  type="number"
                  min="1"
                  placeholder="Pa limit"
                  value={form.max_uses}
                  onChange={(e) => setForm({...form, max_uses: e.target.value})}
                />
              </div>
              <div>
                <Label>Shuma min. blerje (EUR)</Label>
                <Input
                  type="number"
                  step="0.01"
                  min="0"
                  placeholder="Pa minimum"
                  value={form.min_purchase_amount}
                  onChange={(e) => setForm({...form, min_purchase_amount: e.target.value})}
                />
              </div>
            </div>
            <div className="flex items-center gap-2 pt-2">
              <Switch
                checked={form.active}
                onCheckedChange={(v) => setForm({...form, active: v})}
              />
              <span className="text-sm font-medium">Aktiv</span>
            </div>
          </div>
          <DialogFooter>
            <Button variant="outline" onClick={() => setDialogOpen(false)}>Anulo</Button>
            <Button onClick={handleSave} className="bg-[#00a79d] hover:bg-[#008f86] text-white">
              {editingId ? 'Ruaj' : 'Krijo'}
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>
    </Card>
  );
};

export default CouponsTab;