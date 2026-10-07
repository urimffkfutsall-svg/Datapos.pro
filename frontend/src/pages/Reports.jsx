import React, { useState, useRef } from 'react';
import { api } from '../App';
import SalesReportsView from '../components/SalesReportsView';
import { buildSalesPrintHtml, printSalesHtml } from '../lib/salesPrint';
import '../sales-panel.css';
const today = () => { const d = new Date(); return `${d.getFullYear()}-${String(d.getMonth()+1).padStart(2,'0')}-${String(d.getDate()).padStart(2,'0')}`; };
export default function Reports() {
  const [anchor, setAnchor] = useState(today);
  const [printing, setPrinting] = useState(null);
  const [error, setError] = useState('');
  const printInFlight = useRef(false);
  const print = async period => {
    if (printInFlight.current) return;
    printInFlight.current = true; setPrinting(period); setError('');
    try {
      const response = await api.get('/reports/sales-print', { params: { period, anchor, _fresh: Date.now() } });
      if (response.data?.reporting_revision !== 'sales-panel-v2' || response.fromCache) throw new Error('Publikoni backend-in e ri. Raporti nuk mund të printohet nga një version i vjetër.');
      await printSalesHtml(buildSalesPrintHtml(response.data));
    } catch (err) { setError(err.response?.status === 404 ? 'Backend-i i raporteve nuk është përditësuar. Publikoni backend-in dhe frontend-in bashkë.' : err.response?.data?.detail || err.message || 'Raporti nuk u përgatit. Kontrolloni lidhjen.'); }
    finally { printInFlight.current = false; setPrinting(null); }
  };
  return <SalesReportsView anchor={anchor} onDate={setAnchor} printing={printing} onPrint={print} error={error} />;
}
