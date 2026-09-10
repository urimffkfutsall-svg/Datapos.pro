/**
 * offline.js
 * ---------------------------------------------------------------------------
 * Modaliteti offline me sinkronizim automatik.
 *
 * Kur nuk ka internet:
 *  - Kerkesat GET kthehen nga cache-i lokal (te dhenat e fundit te shkarkuara).
 *  - Kerkesat POST/PUT/DELETE per veprime shitjeje ruhen ne radhe (queue).
 *
 * Kur lidhja kthehet:
 *  - Radha dergohet automatikisht ne server, sipas rendit kronologjik.
 */

const CACHE_PREFIX = 'datapos_cache:';
const QUEUE_KEY = 'datapos_sync_queue';
const LAST_SYNC_KEY = 'datapos_last_sync';
export const OFFLINE_EVENT = 'datapos-offline-state';

/** Endpoint-et GET qe ruhen ne cache per pune offline. */
export const OFFLINE_CACHEABLE = [
  '/products',
  '/settings/company',
  '/cashier/current',
  '/sales',
  '/users',
  '/branches',
  '/comment-templates',
];

/** Endpoint-et qe mund te pritojne ne radhe kur jemi offline. */
export const OFFLINE_QUEUEABLE = [
  '/sales',
  '/cashier/open',
  '/cashier/close',
  '/warranties',
  '/products',
];

let offlineState = false;
let syncing = false;

/* ------------------------------------------------------------------ */
/* Gjendja e lidhjes                                                   */
/* ------------------------------------------------------------------ */

export const isOffline = () => offlineState || !navigator.onLine;

const emitState = (extra = {}) => {
  try {
    window.dispatchEvent(
      new CustomEvent(OFFLINE_EVENT, {
        detail: {
          offline: isOffline(),
          queued: getQueue().length,
          lastSync: getLastSync(),
          ...extra,
        },
      })
    );
  } catch (e) {
    /* ignore */
  }
};

export const setOfflineState = (value) => {
  const changed = offlineState !== value;
  offlineState = value;
  if (changed) emitState();
};

export const getLastSync = () => {
  try {
    return localStorage.getItem(LAST_SYNC_KEY);
  } catch (e) {
    return null;
  }
};

/* ------------------------------------------------------------------ */
/* Cache per kerkesat GET                                              */
/* ------------------------------------------------------------------ */

const normalize = (url = '') => url.split('?')[0];

export const isCacheable = (url = '') =>
  OFFLINE_CACHEABLE.some((p) => normalize(url).startsWith(p));

export const isQueueable = (url = '') =>
  OFFLINE_QUEUEABLE.some((p) => normalize(url).startsWith(p));

export const writeCache = (url, data) => {
  try {
    localStorage.setItem(
      CACHE_PREFIX + url,
      JSON.stringify({ data, at: new Date().toISOString() })
    );
  } catch (e) {
    /* kuota e mbushur - hesht */
  }
};

export const readCache = (url) => {
  try {
    const raw = localStorage.getItem(CACHE_PREFIX + url);
    if (!raw) return null;
    return JSON.parse(raw);
  } catch (e) {
    return null;
  }
};

export const clearCache = () => {
  try {
    Object.keys(localStorage)
      .filter((k) => k.startsWith(CACHE_PREFIX))
      .forEach((k) => localStorage.removeItem(k));
  } catch (e) {
    /* ignore */
  }
};

/* ------------------------------------------------------------------ */
/* Radha e sinkronizimit                                               */
/* ------------------------------------------------------------------ */

export const getQueue = () => {
  try {
    const raw = localStorage.getItem(QUEUE_KEY);
    return raw ? JSON.parse(raw) : [];
  } catch (e) {
    return [];
  }
};

const saveQueue = (queue) => {
  try {
    localStorage.setItem(QUEUE_KEY, JSON.stringify(queue));
  } catch (e) {
    /* ignore */
  }
};

export const enqueue = (item) => {
  const queue = getQueue();
  const entry = {
    id: 'q-' + Date.now().toString(36) + '-' + Math.random().toString(36).slice(2, 8),
    method: (item.method || 'post').toLowerCase(),
    url: item.url,
    data: item.data ?? null,
    created_at: new Date().toISOString(),
    attempts: 0,
  };
  queue.push(entry);
  saveQueue(queue);
  emitState();
  return entry;
};

export const queueCount = () => getQueue().length;

/**
 * Dergon radhen ne server. Ndalon te gabimi i pare i rrjetit, por i heq
 * elementet qe serveri i refuzon perfundimisht (4xx), qe radha te mos bllokohet.
 */
export const flushQueue = async (api) => {
  if (syncing || !api) return { sent: 0, failed: 0 };
  const queue = getQueue();
  if (!queue.length) return { sent: 0, failed: 0 };

  syncing = true;
  emitState({ syncing: true });

  let sent = 0;
  let failed = 0;
  const remaining = [...queue];

  while (remaining.length) {
    const item = remaining[0];
    try {
      await api.request({
        method: item.method,
        url: item.url,
        data: item.data,
        headers: { 'X-Offline-Sync': '1' },
      });
      remaining.shift();
      sent += 1;
      saveQueue(remaining);
    } catch (error) {
      const status = error?.response?.status;
      if (status && status >= 400 && status < 500) {
        // Refuzim perfundimtar - hiqe nga radha
        remaining.shift();
        failed += 1;
        saveQueue(remaining);
        continue;
      }
      // Problem rrjeti/serveri - provo perseri me vone
      item.attempts = (item.attempts || 0) + 1;
      saveQueue(remaining);
      break;
    }
  }

  try {
    localStorage.setItem(LAST_SYNC_KEY, new Date().toISOString());
  } catch (e) {
    /* ignore */
  }

  syncing = false;
  emitState({ syncing: false, sent, failed });
  return { sent, failed };
};

/* ------------------------------------------------------------------ */
/* Sinkronizimi automatik                                              */
/* ------------------------------------------------------------------ */

let autoSyncTimer = null;

/**
 * Nis mbikeqyrjen e lidhjes dhe sinkronizimin automatik.
 * Kthen funksionin per ndalim.
 */
export const startAutoSync = (api, intervalMs = 30000) => {
  const onOnline = async () => {
    setOfflineState(false);
    await flushQueue(api);
  };
  const onOffline = () => setOfflineState(true);

  window.addEventListener('online', onOnline);
  window.addEventListener('offline', onOffline);

  if (window.electronAPI?.onNetworkStatus) {
    window.electronAPI.onNetworkStatus((status) => {
      if (status?.online) onOnline();
      else onOffline();
    });
  }

  if (autoSyncTimer) clearInterval(autoSyncTimer);
  autoSyncTimer = setInterval(() => {
    if (navigator.onLine && getQueue().length) flushQueue(api);
  }, intervalMs);

  setOfflineState(!navigator.onLine);
  if (navigator.onLine) flushQueue(api);

  return () => {
    window.removeEventListener('online', onOnline);
    window.removeEventListener('offline', onOffline);
    if (autoSyncTimer) clearInterval(autoSyncTimer);
    autoSyncTimer = null;
  };
};

/* ------------------------------------------------------------------ */
/* Interceptorat e axios                                              */
/* ------------------------------------------------------------------ */

const isNetworkError = (error) =>
  !error?.response ||
  error.code === 'ERR_NETWORK' ||
  error.code === 'ECONNABORTED' ||
  error.message === 'Network Error';

/**
 * Lidh interceptorat offline me instancen e axios.
 * - Pergjigjet GET te suksesshme ruhen ne cache.
 * - Gabimet e rrjetit kthehen nga cache-i, ose ruhen ne radhe.
 */
export const attachInterceptors = (api) => {
  api.interceptors.response.use(
    (response) => {
      const method = (response.config?.method || 'get').toLowerCase();
      const url = response.config?.url || '';
      if (method === 'get' && isCacheable(url)) {
        writeCache(url, response.data);
      }
      setOfflineState(false);
      return response;
    },
    async (error) => {
      const config = error?.config || {};
      const method = (config.method || 'get').toLowerCase();
      const url = config.url || '';

      if (!isNetworkError(error)) return Promise.reject(error);

      setOfflineState(true);

      // GET -> kthe te dhenat e ruajtura
      if (method === 'get') {
        const cached = readCache(url);
        if (cached) {
          return Promise.resolve({
            data: cached.data,
            status: 200,
            statusText: 'OK (offline)',
            headers: {},
            config,
            fromCache: true,
            cachedAt: cached.at,
          });
        }
        return Promise.reject(error);
      }

      // Shkrimet e lejuara -> ruaji ne radhe
      if (isQueueable(url) && config.headers?.['X-Offline-Sync'] !== '1') {
        let data = config.data;
        if (typeof data === 'string') {
          try {
            data = JSON.parse(data);
          } catch (e) {
            /* mbaje si string */
          }
        }
        const entry = enqueue({ method, url, data });
        return Promise.resolve({
          data: { ...(data || {}), id: entry.id, offline: true, queued: true },
          status: 202,
          statusText: 'Queued (offline)',
          headers: {},
          config,
          queued: true,
        });
      }

      return Promise.reject(error);
    }
  );

  return api;
};

const offlineApi = {
  OFFLINE_EVENT,
  isOffline,
  setOfflineState,
  getQueue,
  queueCount,
  enqueue,
  flushQueue,
  startAutoSync,
  attachInterceptors,
  readCache,
  writeCache,
  clearCache,
  getLastSync,
};

export default offlineApi;
