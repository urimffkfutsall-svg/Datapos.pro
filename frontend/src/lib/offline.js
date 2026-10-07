/**
 * offline.js
 * ---------------------------------------------------------------------------
 * Modaliteti offline me sinkronizim automatik.
 *
 * Kur nuk ka internet:
 *  - Kerkesat GET kthehen nga cache-i lokal (te dhenat e fundit te shkarkuara).
 *  - Kerkesat POST/PUT per veprime shitjeje ruhen ne radhe (queue).
 *
 * Kur lidhja kthehet:
 *  - Radha dergohet automatikisht ne server, sipas rendit kronologjik.
 */

const CACHE_PREFIX = 'datapos_cache:';
const QUEUE_KEY = 'datapos_sync_queue';
const LAST_SYNC_KEY = 'datapos_last_sync';
export const sessionOwner = () => {
  try { const user = JSON.parse(localStorage.getItem('t3next_user') || 'null'); return user?.id ? (user.tenant_id || user.tenant?.id || 'legacy') + ':' + user.id : null; }
  catch { return null; }
};
export const blockedCount = () => {const owner=sessionOwner();return getQueue().filter(item=>owner&&item.owner===owner&&item.status==='blocked').length;};
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
          queued: queueCount(),
          blocked: blockedCount(),
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
      JSON.stringify({ data, owner: sessionOwner(), at: new Date().toISOString() })
    );
  } catch (e) {
    /* kuota e mbushur - hesht */
  }
};

export const readCache = (url) => {
  try {
    const raw = localStorage.getItem(CACHE_PREFIX + url);
    if (!raw) return null;
    const cached = JSON.parse(raw);
    return cached.owner && cached.owner === sessionOwner() ? cached : null;
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
  localStorage.setItem(QUEUE_KEY, JSON.stringify(queue));
};
const updateQueueItem = (id, changes) => saveQueue(getQueue().map(item=>item.id===id?{...item,...changes}:item));
const removeQueueItem = id => saveQueue(getQueue().filter(item=>item.id!==id));

export const enqueue = item => {
  const owner = sessionOwner();
  if (!owner) throw new Error('Sesioni mungon. Shitja nuk u ruajt offline.');
  const queue = getQueue();
  const key = item.data?.request_id;
  const prior = key && queue.find(row=>row.owner===owner&&row.data?.request_id===key);
  if (prior) {
    if (JSON.stringify(prior.data)!==JSON.stringify(item.data)) throw new Error('Kërkesa offline ka të dhëna të ndryshme. Verifikoni shitjen.');
    return prior;
  }
  const entry = {id:'q-'+Date.now().toString(36)+'-'+Math.random().toString(36).slice(2,10),
    method:(item.method||'post').toLowerCase(),url:item.url,data:item.data??null,
    owner,status:'pending',created_at:new Date().toISOString(),attempts:0};
  queue.push(entry);
  saveQueue(queue); // quota/full storage must reject instead of pretending the sale was saved
  emitState();
  return entry;
};
export const queueCount = () => {const owner=sessionOwner();return getQueue().filter(item=>owner&&item.owner===owner).length;};

/** Never discard a rejected sale. Keep its payload and error for manual review. */
export const flushQueue = async api => {
  if (syncing || !api) return {sent:0,failed:0};
  const owner=sessionOwner();
  if (!owner) return {sent:0,failed:0};
  const candidates=getQueue().filter(item=>item.owner===owner&&item.status!=='blocked');
  if (!candidates.length) {emitState();return {sent:0,failed:0};}
  syncing=true;emitState({syncing:true});let sent=0,failed=0;
  try {
    for(const candidate of candidates){
      if(sessionOwner()!==owner) break; // never replay another cashier's queue after a session switch
      const item=getQueue().find(row=>row.id===candidate.id);
      if(!item)continue;
      const key=item.data?.request_id||item.id;
      if(item.method==='post'&&normalize(item.url)==='/sales'&&!item.data?.request_id){
        item.data={...item.data,request_id:key};updateQueueItem(item.id,{data:item.data});
      }
      try{
        const response=await api.request({method:item.method,url:item.url,data:item.data,
          headers:{'X-Offline-Sync':'1',...(normalize(item.url)==='/sales'?{'Idempotency-Key':key}:{})}});
        if(response?.queued||response?.data?.queued)throw new Error('Shitja nuk u konfirmua në server.');
        removeQueueItem(item.id);sent++;
      }catch(error){
        const status=error?.response?.status;
        const detail=error?.response?.data?.detail;
        const changes={attempts:(item.attempts||0)+1,last_error:typeof detail==='string'?detail.slice(0,400):'Sinkronizimi nuk u konfirmua.',last_status:status||null};
        if([401,403,408,429].includes(status)){
          updateQueueItem(item.id,{...changes,status:'pending'});failed++;break;
        }
        if(status>=400&&status<500){
          updateQueueItem(item.id,{...changes,status:'blocked'});failed++;break;
        }
        updateQueueItem(item.id,{...changes,status:'pending'});failed++;break;
      }
    }
    if(sent)localStorage.setItem(LAST_SYNC_KEY,new Date().toISOString());
  }finally{
    syncing=false;emitState({syncing:false,sent,failed});
    if(sent)window.dispatchEvent(new Event('datapos-sales-changed'));
  }
  return {sent,failed};
};
export const retryBlocked = async api => {
  const owner=sessionOwner();
  saveQueue(getQueue().map(item=>item.owner===owner&&item.status==='blocked'?{...item,status:'pending'}:item));
  emitState();return flushQueue(api);
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
      if ((method === 'post' && url === '/admin/reset-data') ||
          (method === 'delete' && normalize(url).startsWith('/sales/'))) {
        clearCache();
        window.dispatchEvent(new Event('datapos-sales-changed'));
      }
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
        const cached = normalize(url).startsWith('/reports') ? null : readCache(url);
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
      if (method !== 'delete' && isQueueable(url) && config.headers?.['X-Offline-Sync'] !== '1') {
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
  blockedCount,
  retryBlocked,
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
