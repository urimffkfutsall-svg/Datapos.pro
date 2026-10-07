// Persist before sending: a timeout/refresh must not turn the same sale into a new request.
const PREFIX = 'datapos_sale_attempt:';
const storageFor = storage => storage || localStorage;
const slotFor = user => {
  if (!user?.id) throw new Error('Sesioni mungon. Kyçuni përsëri para shitjes.');
  return PREFIX + (user.tenant_id || user.tenant?.id || 'legacy') + ':' + user.id;
};
export function prepareSaleAttempt(payload, user, storage, context) {
  const s = storageFor(storage), slot = slotFor(user);
  const fingerprint = JSON.stringify(payload);
  const saved = s.getItem(slot);
  if (saved) {
    const prior = JSON.parse(saved);
    if (prior.fingerprint !== fingerprint) {
      throw new Error('Ka një shitje të pakonfirmuar me shportë tjetër. Verifikoni shitjen para se të ndryshoni pagesën ose produktet.');
    }
    return prior;
  }
  const key = globalThis.crypto?.randomUUID?.() || 'sale-' + Date.now().toString(36) + '-' + Math.random().toString(36).slice(2) + '-' + Math.random().toString(36).slice(2);
  const attempt = { key, fingerprint, payload, context, created_at: new Date().toISOString() };
  s.setItem(slot, JSON.stringify(attempt)); // storage failure must stop the sale, not silently lose protection
  return attempt;
}
export function completeSaleAttempt(user, storage) { storageFor(storage).removeItem(slotFor(user)); }
export function releaseRejectedSaleAttempt(error, user, storage) {
  if ([400,404,422].includes(error?.response?.status)) completeSaleAttempt(user, storage);
}
export function pendingSaleAttempt(user, storage) {
  try { return JSON.parse(storageFor(storage).getItem(slotFor(user)) || 'null'); }
  catch { return null; }
}
