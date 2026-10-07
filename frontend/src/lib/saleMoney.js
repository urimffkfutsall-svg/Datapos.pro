// Exact rational decimal inputs; round each line to cents (HALF_UP), like the server.
function fraction(value) {
  const text = String(value ?? 0).trim();
  if (!Number.isFinite(Number(text))) return [0n, 1n];
  const match = text.match(/^([+-]?)(\d*)(?:\.(\d*))?(?:e([+-]?\d+))?$/i);
  if (!match) return [0n, 1n];
  const places = (match[3] || '').length - Number(match[4] || 0);
  if (Math.abs(places) > 24) return [0n, 1n];
  let n = BigInt((match[2] || '0') + (match[3] || '')) * (match[1] === '-' ? -1n : 1n);
  return places >= 0 ? [n, 10n ** BigInt(places)] : [n * 10n ** BigInt(-places), 1n];
}
const halfUp = (n, d) => n < 0n ? -halfUp(-n, d) : (2n * n + d) / (2n * d);
export const toCents = value => { const [n,d] = fraction(value); return Number(halfUp(n * 100n,d)); };
export function calculateSaleLine(item) {
  const [qn,qd] = fraction(item.quantity), [pn,pd] = fraction(item.unit_price);
  const [dn,dd] = fraction(item.discount_percent), [vn,vd] = fraction(item.vat_percent);
  const sub = halfUp(qn * pn * 100n, qd * pd);
  const discount = halfUp(sub * dn, dd * 100n);
  const vat = halfUp((sub - discount) * vn, vd * 100n);
  return {subtotal:Number(sub)/100,discount:Number(discount)/100,vat:Number(vat)/100,total:Number(sub-discount+vat)/100};
}
export function sumSaleLines(cart) {
  const cents = cart.reduce((a,item) => {const line=calculateSaleLine(item);for(const key of Object.keys(a))a[key]+=toCents(line[key]);return a;}, {subtotal:0,discount:0,vat:0,total:0});
  return Object.fromEntries(Object.entries(cents).map(([key,value])=>[key,value/100]));
}
