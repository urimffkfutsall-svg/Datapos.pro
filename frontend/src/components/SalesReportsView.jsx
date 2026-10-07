import React from 'react';
export const reportPeriods = { daily: 'Ditës', weekly: 'Javës', monthly: 'Muajit', yearly: 'Vitit' };

export default function SalesReportsView({ anchor, onDate, printing, onPrint, error }) {
  return <main className="dp-sales" data-testid="print-reports-page">
    <header className="dp-page-heading"><div><p className="dp-eyebrow">RAPORTET</p><h1>Printo raportin e shitjeve</h1><p className="dp-muted">Zgjidhni një datë dhe printoni vetëm periudhën që ju nevojitet.</p></div></header>
    {error && <div role="alert" className="dp-error">{error}</div>}
    <section className="dp-box dp-report-filter"><label className="dp-date-label" htmlFor="print-report-date">Data e periudhës<input id="print-report-date" type="date" value={anchor} onChange={e => e.target.value && onDate(e.target.value)} disabled={!!printing} /></label><p className="dp-muted">Java fillon të hënën. Muaji dhe viti përcaktohen nga data e zgjedhur.</p></section>
    <section className="dp-report-grid" aria-label="Raportet për printim">
      {Object.entries(reportPeriods).map(([key,label]) => <article className="dp-report-card" key={key}><span className="dp-report-icon" aria-hidden="true">▤</span><h2>Raporti i {label.toLowerCase()}</h2><p className="dp-muted">Vetëm shitjet e periudhës së zgjedhur, pa shitjet e fshira ose të resetuara.</p><button className="dp-button dp-primary" disabled={!!printing} onClick={() => onPrint(key)} data-testid={`print-${key}`}>{printing === key ? 'Duke përgatitur...' : `Printo raportin e ${label.toLowerCase()}`}</button></article>)}
    </section>
  </main>;
}
