import React, { useEffect, useState } from 'react';
import { Wifi, WifiOff, RefreshCw, CloudUpload, Check } from 'lucide-react';
import offline, { OFFLINE_EVENT } from '../lib/offline';

/**
 * Treguesi i statusit online/offline dhe i sinkronizimit.
 * Shfaqet fiks poshte-djathtas ne te gjitha faqet.
 */
const OfflineIndicator = () => {
  const [state, setState] = useState(offline.getSyncState());
  const [busy, setBusy] = useState(false);

  useEffect(() => {
    const update = () => setState(offline.getSyncState());
    const unsub = offline.subscribe(update);
    window.addEventListener(OFFLINE_EVENT, update);
    window.addEventListener('online', update);
    window.addEventListener('offline', update);
    const t = setInterval(update, 5000);
    return () => {
      unsub();
      window.removeEventListener(OFFLINE_EVENT, update);
      window.removeEventListener('online', update);
      window.removeEventListener('offline', update);
      clearInterval(t);
    };
  }, []);

  const handleSync = async () => {
    setBusy(true);
    await offline.syncNow();
    setBusy(false);
    setState(offline.getSyncState());
  };

  const { online, pending, syncing } = state;

  // Kur jemi online dhe s'ka asgje ne pritje -> tregues i vogel diskret
  if (online && pending === 0) {
    return (
      <div className="fixed bottom-3 right-3 z-[9998] flex items-center gap-1.5 px-2.5 py-1.5 rounded-full bg-white/90 backdrop-blur border border-[#0E4B49]/15 shadow-sm text-[11px] font-semibold text-[#0E4B49]">
        <Check className="h-3.5 w-3.5" />
        <span>{'T\u00eb gjitha t\u00eb sinkronizuara'}</span>
      </div>
    );
  }

  return (
    <div
      className={`fixed bottom-3 right-3 z-[9998] flex items-center gap-2 px-3 py-2 rounded-xl shadow-lg border text-xs font-semibold ${
        online
          ? 'bg-amber-50 border-amber-300 text-amber-800'
          : 'bg-red-50 border-red-300 text-red-700'
      }`}
      data-testid="offline-indicator"
    >
      {online ? <Wifi className="h-4 w-4" /> : <WifiOff className="h-4 w-4" />}
      <div className="leading-tight">
        <div>{online ? 'Online' : 'Pa internet — modaliteti offline'}</div>
        {pending > 0 && (
          <div className="font-normal opacity-80">
            {pending} {'veprime presin sinkronizim'}
          </div>
        )}
      </div>
      {online && pending > 0 && (
        <button
          type="button"
          onClick={handleSync}
          disabled={busy || syncing}
          className="ml-1 flex items-center gap-1 px-2 py-1 rounded-lg bg-[#0E4B49] text-white disabled:opacity-60"
          title="Sinkronizo tani"
        >
          {busy || syncing ? (
            <RefreshCw className="h-3.5 w-3.5 animate-spin" />
          ) : (
            <CloudUpload className="h-3.5 w-3.5" />
          )}
          <span>Sinkronizo</span>
        </button>
      )}
    </div>
  );
};

export default OfflineIndicator;
