/**
 * OFFLINE MODE + SYNC
 * ---------------------------------------------------------------
 * - Cache i te dhenave GET (produkte, settings, arka, shitjet e fundit)
 *   ne localStorage, qe aplikacioni te punoje edhe pa internet.
 * - Rradhe (queue) per veprimet POST/PUT/DELETE te bera offline.
 * - Kur kthehet interneti, rradha dergohet automatikisht ne server.
 */

import { getDeviceId } from './deviceLock';

const CACHE_PREFIX = 'datapos_cache:';
const QUEUE_KEY = 'datapos_sync_queue';
const LAST_SYNC_KEY = 'datapos_last_sync';

const listeners = new Set();

export const OFFLINE_EVENT = 'datapos-offline-state';

/* ------------------------- helpers ------------------------- */

const safeParse = (raw, fallback) => {
  try {
    return raw ? JSON.parse(raw) : fallback;
  } catch (e) {
    return fallback;
  }
};

const emit = () => {
  const state = getSyncState();
  listeners.forEach((cb) => {
    try {
      cb(state);
    } catch (e) {
      /* ignore */
    }
  });
  if (typeof window !== 'undefined') {
    window.dispatchEvent(new CustomEvent(OFFLINE_EVENT, { detail: state }));
  }
};

export const isOnline = () =>
  typeof navigator === 'undefined' ? true : navigator.onLine !== false;

export function subscribe(cb) {
  listeners.add(cb);
  return () => listeners.delete(cb);
}

/* ------------------------- cache ------------------------- */

const cacheKey = (url) => CACHE_PREFIX + url;

export function readCache(url) {
  const entry = safeParse(localStorage.getItem(cacheKey(url)), null);
  return entry ? entry.data : null;
}

export function readCacheEntry(url) {
  return safeParse(localStorage.getItem(cacheKey(url)), null);
}

export function writeCache(url, data) {
  try {
    localStorage.setItem(
      cacheKey(url),
      JSON.stringify({ data, cachedAt: new Date().toISOString() })
    );
  } catch (e) {
    /* kuota e mbushur - injoro */
  }
}

export function clearCache() {
  try {
    Object.keys(localStorage)
      .filter((k) => k.startsWith(CACHE_PREFIX))
      .forEach((k) => localStorage.removeItem(k));
  } catch (e) {
    /* ignore */
  }
}

/* ------------------------- queue ------------------------- */

export function getQueue() {
  return safeParse(localStorage.getItem(QUEUE_KEY), []);
}

function saveQueue(queue) {
  try {
    localStorage.setItem(QUEUE_KEY, JSON.stringify(queue));
  } catch (e) {
    /* ignore */
  }
  emit();
}

export function getPendingCount() {
  return getQueue().length;
}

export function getLastSync() {
  return localStorage.getItem(LAST_SYNC_KEY);
}

export function getSyncState() {
  return {
    online: isOnline(),
    pending: getPendingCount(),
    lastSync: getLastSync(),
    syncing: syncInProgress,
  };
}

/** Shton nje veprim ne rradhe per t'u derguar kur kthehet interneti. */
export function enqueue({ method, url, data, label }) {
  const queue = getQueue();
  const item = {
    id: 'q-' + Date.now().toString(36) + '-' + Math.random().toString(36).slice(2, 8),
    method: (method || 'post').toLowerCase(),
    url,
    data: data || null,
    label: label || url,
    device_id: getDeviceId(),
    created_at: new Date().toISOString(),
    attempts: 0,
  };
  queue.push(item);
  saveQueue(queue);
  return item;
}

export function removeFromQueue(id) {
  saveQueue(getQueue().filter((q) => q.id !== id));
}

export function clearQueue() {
  saveQueue([]);
}

/* ------------------------- sync ------------------------- */

let syncInProgress = false;
let apiRef = null;

/** Regjistro instancen e axios qe perdoret per sync. */
export function registerApi(api) {
  apiRef = api;
}

/**
 * Dergon ne server te gjitha veprimet e rradhes.
 * Kthen { sent, failed }.
 */
export async function syncNow() {
  if (syncInProgress || !apiRef || !isOnline()) {
    return { sent: 0, failed: 0, skipped: true };
  }
  const queue = getQueue();
  if (queue.length === 0) {
    localStorage.setItem(LAST_SYNC_KEY, new Date().toISOString());
    emit();
    return { sent: 0, failed: 0 };
  }

  syncInProgress = true;
  emit();

  let sent = 0;
  let failed = 0;
  const remaining = [];

  for (const item of queue) {
    try {
      const cfg = { headers: { 'X-Offline-Sync': '1', 'X-Device-Id': item.device_id } };
      if (item.method === 'post') await apiRef.post(item.url, item.data, cfg);
      else if (item.method === 'put') await apiRef.put(item.url, item.data, cfg);
      else if (item.method === 'patch') await apiRef.patch(item.url, item.data, cfg);
      else if (item.method === 'delete') await apiRef.delete(item.url, cfg);
      sent += 1;
    } catch (error) {
      const status = error?.response?.status;
      // 4xx (pervec 401/408/429) = kerkese e pavlefshme -> mos e mbaj pergjithmone
      if (status && status >= 400 && status < 500 && ![401, 408, 429].includes(status)) {
        failed += 1;
      } else {
        remaining.push({ ...item, attempts: (item.attempts || 0) + 1 });
      }
    }
  }

  saveQueue(remaining);
  localStorage.setItem(LAST_SYNC_KEY, new Date().toISOString());
  syncInProgress = false;
  emit();
  return { sent, failed, remaining: remaining.length };
}

let started = false;

/** Nis degjuesit e online/offline dhe sync-un periodik. */
export function startAutoSync(api) {
  if (api) registerApi(api);
  if (started || typeof window === 'undefined') return;
  started = true;

  window.addEventListener('online', () => {
    emit();
    setTimeout(() => syncNow(), 1200);
  });
  window.addEventListener('offline', () => emit());

  // sync periodik çdo 60s nese ka gjera ne pritje
  setInterval(() => {
    if (isOnline() && getPendingCount() > 0) syncNow();
  }, 60000);

  // provo nje sync ne nisje
  setTimeout(() => {
    if (isOnline() && getPendingCount() > 0) syncNow();
  }, 3000);
}

export default {
  isOnline,
  subscribe,
  readCache,
  writeCache,
  clearCache,
  getQueue,
  enqueue,
  removeFromQueue,
  clearQueue,
  getPendingCount,
  getSyncState,
  syncNow,
  startAutoSync,
  registerApi,
};
