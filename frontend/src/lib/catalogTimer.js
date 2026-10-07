export const CATALOG_AUTO_CLOSE_MS = 60_000;

// No persistence: each explicit opening gets a new one-minute deadline.
export function armCatalogAutoClose(close, scheduler = globalThis) {
  const deadline = Date.now() + CATALOG_AUTO_CLOSE_MS;
  const timer = scheduler.setTimeout(close, CATALOG_AUTO_CLOSE_MS);
  const resume = () => { if (Date.now() >= deadline) close(); };
  if (typeof document !== 'undefined') document.addEventListener('visibilitychange', resume);
  if (typeof window !== 'undefined') window.addEventListener('focus', resume);
  return () => {
    scheduler.clearTimeout(timer);
    if (typeof document !== 'undefined') document.removeEventListener('visibilitychange', resume);
    if (typeof window !== 'undefined') window.removeEventListener('focus', resume);
  };
}
