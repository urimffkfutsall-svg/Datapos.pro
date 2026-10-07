export const escapeHtml = value => String(value ?? '').replace(/[&<>"']/g, char => ({ '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;' }[char]));
const labels = { daily: 'ditës', weekly: 'javës', monthly: 'muajit', yearly: 'vitit' };
export function buildSalesPrintHtml(data) {
  const esc = escapeHtml;
  const rows = data.sales.map((sale, i) => `<tr><td>${i + 1}</td><td>${esc(sale.receipt_number)}</td><td>${esc(new Date(sale.created_at).toLocaleString('sq-AL', { timeZone: data.timezone }))}</td><td>${esc(sale.is_debt ? 'Borxh' : sale.payment_method === 'cash' ? 'Cash' : 'Bank')}</td><td class="amount">€${Number(sale.grand_total || 0).toFixed(2)}</td></tr>`).join('');
  return `<!doctype html><html lang="sq"><head><meta charset="utf-8"><title>Raporti i ${labels[data.period]}</title><style>
    @page{size:A4;margin:16mm}*{box-sizing:border-box}body{font:11pt/1.45 Arial,sans-serif;color:#242424;margin:0}h1{font-size:22pt;margin:0 0 6pt}h2{font-size:16pt;margin:0 0 8pt}.muted{color:#555}.heading{border-bottom:2px solid #0e4b49;padding-bottom:14pt;margin-bottom:20pt}.total{font-size:18pt;font-weight:bold;margin:0 0 16pt}table{border-collapse:collapse;width:100%;font-size:10pt}thead{display:table-header-group}tr{break-inside:avoid}th,td{padding:8pt;border-bottom:1px solid #ddd;text-align:left;overflow-wrap:anywhere}th{background:#f4f6f5}.amount{text-align:right;white-space:nowrap}footer{margin-top:18pt;font-size:9pt;color:#555}
    </style></head><body><header class="heading"><h1>${esc(data.company_name || 'DataPOS')}</h1><h2>Raporti i shitjeve të ${labels[data.period]}</h2><div class="muted">${esc(data.start_date)} — ${esc(data.end_date)} · ${esc(data.timezone)}</div></header><p class="total">Totali: €${Number(data.total || 0).toFixed(2)}</p><table><thead><tr><th>#</th><th>Kuponi</th><th>Data / ora</th><th>Pagesa</th><th class="amount">Shuma</th></tr></thead><tbody>${rows || '<tr><td colspan="5">Nuk ka shitje në këtë periudhë.</td></tr>'}</tbody></table><footer>Gjeneruar: ${esc(new Date().toLocaleString('sq-AL'))}. Shitjet e fshira ose të resetuara nuk përfshihen.</footer></body></html>`;
}

export async function printSalesHtml(html) {
  const frame = document.createElement('iframe');
  frame.title = 'Raporti i shitjeve për printim';
  frame.style.cssText = 'position:fixed;left:-10000px;top:0;width:800px;height:1000px;border:0;';
  document.body.appendChild(frame);
  try {
    await new Promise((resolve, reject) => {
      frame.onload = resolve;
      frame.onerror = () => reject(new Error('Raporti nuk u hap për printim.'));
      frame.srcdoc = html;
    });
    if (frame.contentDocument?.fonts?.ready) await frame.contentDocument.fonts.ready;
    frame.contentWindow.focus();
    frame.contentWindow.addEventListener('afterprint', () => frame.remove(), { once: true });
    frame.contentWindow.print();
    setTimeout(() => frame.remove(), 120000);
  } catch (err) { frame.remove(); throw err; }
}
