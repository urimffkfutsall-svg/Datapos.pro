import React, { useState, useRef } from 'react';
import { api } from '../App';
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogDescription } from './ui/dialog';
import '../pos-registration.css';
import { usePaymentViewport } from '../lib/usePaymentViewport';

export default function POSProductRegistration({ barcode, branchId, onClose, onRegistered }) {
  const [data, setData] = useState({ name: '', sale_price: '', purchase_price: '0', vat_rate: '18', category: '', unit: 'copë' });
  const [stage, setStage] = useState('product'), [pin, setPin] = useState(''), [error, setError] = useState(''), [busy, setBusy] = useState(false);
  const locked = useRef(false);
  const viewport = usePaymentViewport(true);
  const change = e => setData(v => ({ ...v, [e.target.name]: e.target.value }));
  const submit = async e => {
    e.preventDefault(); if (locked.current) return;
    setError('');
    if (stage === 'product') { setStage('approval'); return; }
    if (!navigator.onLine) { setPin(''); setError('Regjistrimi kërkon internet dhe verifikim nga administratori.'); return; }
    locked.current = true; setBusy(true);
    // Clear the secret from React state immediately; never persist or queue it.
    const adminPin = pin; setPin('');
    try {
      const result = await api.post('/products/register-with-admin', { admin_pin: adminPin, product: {
        ...data, barcode, sale_price: Number(data.sale_price), purchase_price: Number(data.purchase_price),
        vat_rate: Number(data.vat_rate), initial_stock: 0, branch_id: branchId || null
      }});
      if (result.queued || result.fromCache || result.status === 202) throw new Error('Produkti nuk është konfirmuar nga serveri.');
      onRegistered(result.data);
    } catch (err) {
      const detail = err.response?.data?.detail;
      setError(typeof detail === 'string' ? detail : err.message || 'Regjistrimi dështoi. Provoni përsëri.');
    } finally { locked.current = false; setBusy(false); }
  };
  return <Dialog open onOpenChange={open => { if (!open && !locked.current) { setPin(''); onClose(); } }}>
    <DialogContent className="dp-register-dialog" style={viewport} onEscapeKeyDown={e => busy && e.preventDefault()} onPointerDownOutside={e => e.preventDefault()}>
      <DialogHeader className="dp-register-header">
        <DialogTitle>{stage === 'product' ? 'Regjistro këtë produkt' : 'Miratimi i administratorit'}</DialogTitle>
        <DialogDescription>{stage === 'product' ? 'Barkodi nuk është i regjistruar. Plotësoni të dhënat e produktit.' : 'Produkti ruhet vetëm pas verifikimit të PIN-it të administratorit të firmës.'}</DialogDescription>
      </DialogHeader>
      <div className="dp-register-barcode"><span>Barkodi</span><strong>{barcode}</strong></div>
      <form onSubmit={submit} className="dp-register-form">
        {stage === 'product' ? <>
          <label className="dp-register-wide">Emri i produktit<input name="name" autoFocus required maxLength={200} value={data.name} onChange={change} /></label>
          <label>Çmimi i shitjes (€)<input name="sale_price" type="number" min="0" max="999999999" step="0.01" required value={data.sale_price} onChange={change} /></label>
          <label>Çmimi i blerjes (€)<input name="purchase_price" type="number" min="0" max="999999999" step="0.01" required value={data.purchase_price} onChange={change} /></label>
          <label>TVSH (%)<input name="vat_rate" type="number" min="0" max="100" step="0.01" required value={data.vat_rate} onChange={change} /></label>
          <label>Njësia<input name="unit" maxLength={40} required value={data.unit} onChange={change} /></label>
          <label className="dp-register-wide">Kategoria (opsionale)<input name="category" maxLength={100} value={data.category} onChange={change} /></label>
          <p className="dp-register-note dp-register-wide">Stoku fillon nga 0. Furnizimin e regjistroni nga faqja e produkteve.</p>
        </> : <>
          <div className="dp-register-product dp-register-wide"><strong>{data.name}</strong><span>€{Number(data.sale_price).toFixed(2)}</span></div>
          <label className="dp-register-wide">PIN-i i administratorit<input key="admin-pin" type="password" inputMode="numeric" pattern="[0-9]{4,12}" minLength={4} maxLength={12} autoComplete="off" autoFocus required value={pin} onChange={e => setPin(e.target.value.replace(/\D/g, ''))} disabled={busy} aria-describedby="dp-register-approval-note" /></label>
          <p id="dp-register-approval-note" className="dp-register-note dp-register-wide">Përdorni PIN-in unik të një administratori aktiv të kësaj firme (4–12 shifra). Nuk ndryshon sesioni i arkatarit.</p>
        </>}
        {error && <p role="alert" className="dp-register-error dp-register-wide">{error}</p>}
        <div className="dp-register-actions dp-register-wide">
          <button type="button" disabled={busy} onClick={() => { setPin(''); if (stage === 'approval') { setStage('product'); setError(''); } else onClose(); }}>{stage === 'approval' ? 'Kthehu' : 'Anulo'}</button>
          <button type="submit" disabled={busy} className="dp-register-primary">{busy ? 'Duke verifikuar…' : stage === 'product' ? 'Regjistro produktin' : 'Verifiko PIN-in dhe regjistro'}</button>
        </div>
      </form>
    </DialogContent>
  </Dialog>;
}
