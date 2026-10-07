export function saleProductLines(sale) {
  const items = Array.isArray(sale?.items) ? sale.items : [];
  if (!items.length) return ['Shitje pa artikuj të regjistruar'];
  return items.map(item => {
    const name = String(item.product_name || item.name || 'Produkt pa emër').trim() || 'Produkt pa emër';
    const quantity = Number(item.quantity);
    return Number.isFinite(quantity) && quantity > 0 ? `${name} × ${quantity}` : name;
  });
}
export const saleProductsTitle = sale => saleProductLines(sale).join(', ');
