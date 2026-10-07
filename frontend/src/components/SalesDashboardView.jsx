import React from 'react';
import { saleProductLines } from '../lib/saleProducts';

export const money = value => `€${Number(value || 0).toFixed(2)}`;
export const periodLabels = { daily: 'Ditore', monthly: 'Mujore', yearly: 'Vjetore' };

export default function SalesDashboardView({ summaries, report, period, anchor, page, loading, error, canManage, onPeriod, onDate, onPage, onRefresh, onReset, onDelete, modal }) {
  return (
    <main className="dp-sales" data-testid="sales-dashboard">
      <header className="dp-page-heading">
        <div><p className="dp-eyebrow">PANELI I FIRMËS</p><h1>Shitjet</h1><p className="dp-muted">Vetëm shitjet reale të ditës, muajit dhe vitit.</p></div>
        <button className="dp-button dp-secondary" onClick={onRefresh} disabled={loading}>Rifresko</button>
      </header>
      {error && <div role="alert" className="dp-error">{error}</div>}
      <section className="dp-summary-grid" aria-label="Përmbledhja e shitjeve">
        {Object.entries(periodLabels).map(([key, label]) => (
          <button key={key} className={`dp-summary ${period === key ? 'dp-selected' : ''}`} onClick={() => onPeriod(key)} aria-pressed={period === key}>
            <span className="dp-muted">Shitjet {label.toLowerCase()}</span>
            <strong>{summaries ? money(summaries[key]?.total) : '—'}</strong>
            <span className="dp-summary-date">{summaries?.[key] ? `${summaries[key].start_date} — ${summaries[key].end_date}` : 'Duke ngarkuar...'}</span>
          </button>
        ))}
      </section>
      <section className="dp-box">
        <header className="dp-section-heading">
          <div><h2>Shitjet {periodLabels[period].toLowerCase()}</h2><p className="dp-muted">{report ? `${report.start_date} — ${report.end_date}` : 'Zgjidhni periudhën'}</p></div>
          <label className="dp-date-label" htmlFor="sales-date">Data e periudhës<input id="sales-date" type="date" value={anchor} onChange={e => e.target.value && onDate(e.target.value)} /></label>
        </header>
        {loading ? <div className="dp-empty" role="status">Duke ngarkuar shitjet nga serveri...</div> : report && report.sales.length ? (
          <div className="dp-sale-list">
            {report.sales.map(sale => (
              <article key={sale.id} className="dp-sale-row">
                <div className="dp-sale-info"><div className="dp-sale-products">{saleProductLines(sale).map((line, index) => <strong key={index}>{line}</strong>)}</div><span className="dp-muted">{new Date(sale.created_at).toLocaleString('sq-AL', { timeZone: report.timezone })} · {sale.is_debt ? 'Borxh' : sale.payment_method === 'cash' ? 'Cash' : 'Bank'}</span></div>
                <span className="dp-sale-total">{money(sale.grand_total)}</span>
                {canManage && period === 'daily' && <button className="dp-button dp-danger-outline" onClick={() => onDelete(sale)} data-testid={`delete-sale-${sale.id}`}>Fshij këtë shitje</button>}
              </article>
            ))}
          </div>
        ) : <div className="dp-empty">{error ? 'Të dhënat nuk mund të ngarkohen.' : 'Nuk ka shitje në këtë periudhë.'}</div>}
        {report && !loading && <footer className="dp-list-footer"><span className="dp-muted">Totali i periudhës: <strong>{money(report.total)}</strong></span><div className="dp-pagination"><button className="dp-button dp-secondary" disabled={page === 0} onClick={() => onPage(page - 1)}>Mbrapa</button><span>Faqja {page + 1}</span><button className="dp-button dp-secondary" disabled={(page + 1) * 50 >= report.sales_count} onClick={() => onPage(page + 1)}>Tjetra</button></div></footer>}
      </section>
      {canManage && <section className="dp-reset-box"><div><h2>Resetimi i shitjeve</h2><p className="dp-muted">Për firmën tuaj. Resetimi zbatohet për ditën ose muajin aktual.</p></div><div className="dp-reset-actions"><button className="dp-button dp-warning" disabled={loading || !!error} onClick={() => onReset('daily')}>Reseto ditën</button><button className="dp-button dp-warning" disabled={loading || !!error} onClick={() => onReset('monthly')}>Reseto muajin</button></div></section>}
      {modal}
    </main>
  );
}
