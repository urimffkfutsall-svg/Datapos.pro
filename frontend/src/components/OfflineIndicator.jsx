import React, { useEffect, useState } from 'react';
import { WifiOff, RefreshCw, CheckCircle2 } from 'lucide-react';
import offline, { OFFLINE_EVENT } from '../lib/offline';

/**
 * OfflineIndicator
 * ---------------------------------------------------------------------------
 * Shirit i vogel qe shfaqet vetem kur:
 *  - nuk ka internet, ose
 *  - kemi veprime ne pritje per sinkronizim.
 *
 * Perdoruesi vazhdon punen normalisht; sinkronizimi behet vetvetiu.
 */
const OfflineIndicator = ({ api }) => {
  const [state, setState] = useState({
    offline: !navigator.onLine,
    queued: offline.queueCount(),
    syncing: false,
    justSynced: false,
  });

  useEffect(() => {
    const handler = (event) => {
      const detail = event.detail || {};
      setState((prev) => ({
        offline: detail.offline ?? prev.offline,
        queued: detail.queued ?? prev.queued,
        syncing: detail.syncing ?? false,
        justSynced: (detail.sent || 0) > 0,
      }));
      if ((detail.sent || 0) > 0) {
        setTimeout(
          () => setState((prev) => ({ ...prev, justSynced: false })),
          4000
        );
      }
    };
    window.addEventListener(OFFLINE_EVENT, handler);
    return () => window.removeEventListener(OFFLINE_EVENT, handler);
  }, []);

  const { offline: isOff, queued, syncing, justSynced } = state;

  if (!isOff && !queued && !syncing && !justSynced) return null;

  const base =
    'fixed bottom-4 left-4 z-[9999] flex items-center gap-2 rounded-lg px-3 py-2 text-sm font-medium shadow-lg';

  if (isOff) {
    return (
      <div
        data-testid="offline-indicator"
        className={base + ' bg-amber-500 text-white'}
      >
        <WifiOff size={16} />
        <span>
          Pa internet &mdash; puna vazhdon
          {queued > 0 ? ` (${queued} n\u00eb pritje)` : ''}
        </span>
      </div>
    );
  }

  if (syncing || queued > 0) {
    return (
      <div
        data-testid="offline-indicator"
        className={base + ' bg-teal-700 text-white'}
      >
        <RefreshCw size={16} className="animate-spin" />
        <span>Sinkronizimi{queued > 0 ? ` (${queued})` : ''}…</span>
      </div>
    );
  }

  return (
    <div
      data-testid="offline-indicator"
      className={base + ' bg-emerald-600 text-white'}
    >
      <CheckCircle2 size={16} />
      <span>Të dhënat u sinkronizuan</span>
    </div>
  );
};

export default OfflineIndicator;
