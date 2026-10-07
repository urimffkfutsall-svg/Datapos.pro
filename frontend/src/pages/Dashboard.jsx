import React, { useState, useEffect, useRef, useCallback } from 'react';
import { api, useAuth } from '../App';
import { toast } from 'sonner';
import { getQueue } from '../lib/offline';
import SalesDashboardView from '../components/SalesDashboardView';
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogDescription } from '../components/ui/dialog';
import '../sales-panel.css';

const REVISION = 'sales-panel-v2';
const today = () => { const d = new Date(); return `${d.getFullYear()}-${String(d.getMonth() + 1).padStart(2, '0')}-${String(d.getDate()).padStart(2, '0')}`; };
const backendError = 'Backend-i i ri i shitjeve nuk është publikuar ose nuk përgjigjet. Publikoni backend-in dhe frontend-in e të njëjtit version; resetimi nuk mund të konfirmohet.';

export default function Dashboard() {
  const { user } = useAuth();
  const [anchor, setAnchor] = useState(today);
  const [period, setPeriod] = useState('daily');
  const [page, setPage] = useState(0);
  const [summaries, setSummaries] = useState(null);
  const [report, setReport] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const [action, setAction] = useState(null);
  const [password, setPassword] = useState('');
  const [busy, setBusy] = useState(false);
  const requestId = useRef(0);
  const actionInFlight = useRef(false);
  const canManage = user?.role === 'admin';

  const load = useCallback(async (date = anchor, nextPage = page) => {
    const id = ++requestId.current;
    setLoading(true); setError('');
    try {
      const periods = ['daily', 'monthly', 'yearly'];
      const results = await Promise.all(periods.map(key => api.get('/reports/sales-panel', {
        params: { period: key, anchor: date, offset: key === period ? nextPage * 50 : 0, limit: key === period ? 50 : 1, _fresh: Date.now() }
      })));
      if (results.some(r => r.data?.reporting_revision !== REVISION || r.fromCache)) throw new Error(backendError);
      if (id !== requestId.current) return;
      const next = Object.fromEntries(periods.map((key, i) => [key, results[i].data]));
      setSummaries(next); setReport(next[period]);
    } catch (err) {
      if (id === requestId.current) { setReport(null); setSummaries(null); setError(err.message === backendError ? backendError : (err.response?.status === 404 ? backendError : err.response?.data?.detail || 'Shitjet nuk u ngarkuan. Kontrolloni lidhjen me serverin.')); }
      throw err;
    } finally { if (id === requestId.current) setLoading(false); }
  }, [anchor, page, period]);

  useEffect(() => { load().catch(() => {}); return () => { requestId.current++; }; }, [load]);
  useEffect(() => {
    const refresh = () => { load().catch(() => {}); };
    const storage = e => { if (e.key?.startsWith('datapos_cache:') && e.newValue === null) refresh(); };
    window.addEventListener('datapos-sales-changed', refresh);
    window.addEventListener('storage', storage);
    return () => { window.removeEventListener('datapos-sales-changed', refresh); window.removeEventListener('storage', storage); };
  }, [load]);

  const openReset = kind => { setPassword(''); setAction({ kind }); };
  const submitAction = async event => {
    event.preventDefault();
    if (!action || actionInFlight.current) return;
    if (getQueue().length > 0) { toast.error('Sinkronizoni veprimet offline para resetimit ose fshirjes.'); return; }
    actionInFlight.current = true; setBusy(true);
    let mutationSucceeded = false;
    try {
      if (action.sale) {
        await api.delete(`/sales/${action.sale.id}`);
      } else {
        const response = await api.post('/admin/reset-data', { admin_password: password, reset_type: action.kind });
        if (!response.data?.reset_verified || response.data?.reporting_revision !== REVISION) throw new Error(backendError);
      }
      mutationSucceeded = true;
      setAction(null); setPassword('');
      setPage(0);
      const date = action.sale ? anchor : today();
      setAnchor(date);
      await load(date, 0);
      toast.success(action.sale ? 'Shitja u fshi dhe totalet u përditësuan.' : 'Resetimi u verifikua në databazë. Shitjet e reja pas resetimit llogariten normalisht.');
    } catch (err) {
      toast.error(mutationSucceeded ? 'Veprimi u krye, por totalet nuk u ngarkuan. Rifreskoni; mos e përsërisni veprimin.' : err.message === backendError ? backendError : err.response?.data?.detail || 'Veprimi nuk u konfirmua nga serveri.');
    } finally { actionInFlight.current = false; setBusy(false); }
  };

  const modal = <Dialog open={!!action} onOpenChange={open => { if (!open && !busy) { setAction(null); setPassword(''); } }}>
    <DialogContent className="dp-dialog">
      <DialogHeader><DialogTitle>{action?.sale ? 'Fshij këtë shitje?' : action?.kind === 'monthly' ? 'Reseto shitjet e muajit?' : 'Reseto shitjet e ditës?'}</DialogTitle><DialogDescription>{action?.sale ? `Kuponi ${action.sale.receipt_number} hiqet nga shitjet ditore, mujore, vjetore dhe raportet e printuara.` : 'Shitjet e periudhës aktuale do të hiqen nga llogaritjet në server, jo vetëm në ekran. Ruhet një backup para fshirjes.'}</DialogDescription></DialogHeader>
      <form onSubmit={submitAction} className="dp-form">
        <p className="dp-muted">Stoku nuk rikthehet. Pas resetimit hapeni përsëri arkën. Sinkronizoni të gjitha pajisjet para resetimit.</p>
        {!action?.sale && <label htmlFor="reset-password">Fjalëkalimi i administratorit<input id="reset-password" type="password" autoComplete="current-password" autoFocus required value={password} onChange={e => setPassword(e.target.value)} disabled={busy} /></label>}
        <div className="dp-dialog-actions"><button type="button" className="dp-button dp-secondary" disabled={busy} onClick={() => setAction(null)}>Anulo</button><button type="submit" className="dp-button dp-danger" disabled={busy || (!action?.sale && !password)}>{busy ? 'Duke verifikuar...' : action?.sale ? 'Po, fshije' : 'Konfirmo resetimin'}</button></div>
      </form>
    </DialogContent>
  </Dialog>;
  return <SalesDashboardView summaries={summaries} report={report} period={period} anchor={anchor} page={page} loading={loading} error={error} canManage={canManage} onPeriod={key => { setPeriod(key); setPage(0); }} onDate={date => { setAnchor(date); setPage(0); }} onPage={setPage} onRefresh={() => load().catch(() => {})} onReset={openReset} onDelete={sale => setAction({ sale })} modal={modal} />;
}
