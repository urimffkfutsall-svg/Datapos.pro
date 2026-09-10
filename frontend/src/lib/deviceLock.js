/**
 * DEVICE LOCK (Kyçja e firmes ne nje PC)
 * ---------------------------------------------------------------
 * Pas instalimit te setup.exe, firma (tenant) e administratorit te PARE
 * qe kyçet ne ate kompjuter "bllokohet" per ate PC. Asnje perdorues i nje
 * firme tjeter nuk mund te kyçet me ne ate pajisje.
 *
 * Ruajtja behet ne dy nivele:
 *  1. Electron (desktop): ne skedarin device-lock.json ne userData -> mbetet
 *     edhe nese pastrohet cache-i i shfletuesit.
 *  2. localStorage: fallback per web / nese IPC nuk eshte i disponueshem.
 */

const LOCK_KEY = 'datapos_device_lock';
const DEVICE_ID_KEY = 'datapos_device_id';

const hasElectronLock = () =>
  typeof window !== 'undefined' &&
  window.electronAPI &&
  typeof window.electronAPI.getDeviceLock === 'function';

function readLocal() {
  try {
    const raw = localStorage.getItem(LOCK_KEY);
    return raw ? JSON.parse(raw) : null;
  } catch (e) {
    return null;
  }
}

function writeLocal(lock) {
  try {
    localStorage.setItem(LOCK_KEY, JSON.stringify(lock));
  } catch (e) {
    /* ignore */
  }
}

/** ID unike e pajisjes (perdoret edhe per sync-un e shitjeve offline). */
export function getDeviceId() {
  try {
    let id = localStorage.getItem(DEVICE_ID_KEY);
    if (!id) {
      id =
        'dev-' +
        Date.now().toString(36) +
        '-' +
        Math.random().toString(36).slice(2, 10);
      localStorage.setItem(DEVICE_ID_KEY, id);
    }
    return id;
  } catch (e) {
    return 'dev-unknown';
  }
}

/** Kthen kyçjen aktuale te pajisjes ose null nese PC-ja nuk eshte e kyçur ende. */
export async function getDeviceLock() {
  if (hasElectronLock()) {
    try {
      const lock = await window.electronAPI.getDeviceLock();
      if (lock && lock.tenant_id) {
        writeLocal(lock); // mbaj sinkron edhe kopjen lokale
        return lock;
      }
      return null;
    } catch (e) {
      /* bie ne fallback */
    }
  }
  return readLocal();
}

/** Version sinkron (vetem localStorage) per render te shpejte te UI-se. */
export function getDeviceLockSync() {
  return readLocal();
}

/** Kyç pajisjen per nje firme te caktuar. Behet vetem njehere. */
export async function setDeviceLock({ tenantId, companyName, username }) {
  if (!tenantId) return null;
  const lock = {
    tenant_id: tenantId,
    company_name: companyName || '',
    locked_by: username || '',
    locked_at: new Date().toISOString(),
    device_id: getDeviceId(),
  };
  writeLocal(lock);
  if (hasElectronLock() && typeof window.electronAPI.setDeviceLock === 'function') {
    try {
      await window.electronAPI.setDeviceLock(lock);
    } catch (e) {
      /* ignore */
    }
  }
  return lock;
}

/**
 * Kontrollon nese perdoruesi lejohet te kyçet ne kete PC.
 * Kthen { allowed: true } ose { allowed: false, message }.
 * super_admin lejohet gjithmone (per mirembajtje/suport).
 */
export async function checkDeviceAllowed(userData) {
  if (!userData) return { allowed: true };
  if (userData.role === 'super_admin') return { allowed: true };

  const lock = await getDeviceLock();
  if (!lock || !lock.tenant_id) return { allowed: true, needsLock: true };

  const userTenant = userData.tenant_id || null;
  if (!userTenant) return { allowed: true };

  if (String(userTenant) !== String(lock.tenant_id)) {
    return {
      allowed: false,
      message:
        'Ky kompjuter është i regjistruar për firmën "' +
        (lock.company_name || lock.tenant_id) +
        '". Nuk lejohet kyçja me një firmë tjetër në këtë pajisje.',
      lock,
    };
  }
  return { allowed: true, lock };
}

/** Hiq kyçjen — vetem super_admin duhet ta therrase kete. */
export async function clearDeviceLock() {
  try {
    localStorage.removeItem(LOCK_KEY);
  } catch (e) {
    /* ignore */
  }
  if (hasElectronLock() && typeof window.electronAPI.clearDeviceLock === 'function') {
    try {
      await window.electronAPI.clearDeviceLock();
    } catch (e) {
      /* ignore */
    }
  }
}

export default {
  getDeviceId,
  getDeviceLock,
  getDeviceLockSync,
  setDeviceLock,
  checkDeviceAllowed,
  clearDeviceLock,
};
