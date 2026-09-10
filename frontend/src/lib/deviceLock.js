/**
 * deviceLock.js
 * ---------------------------------------------------------------------------
 * Kycja e firmes ne PC (device lock).
 *
 * Pas instalimit te setup.exe, administratori i PARE qe kycet ne kete PC
 * e "kyc" firmen e vet ne kete pajisje. Pas kesaj, ne te njejtin PC nuk mund
 * te kycet asnje firme tjeter e regjistruar ne aplikacion.
 *
 * Ruajtja:
 *  - Ne Electron (setup.exe): ne skedarin device-lock.json ne dosjen e te
 *    dhenave te aplikacionit, qe te mos fshihet me pastrimin e shfletuesit.
 *  - Ne shfletues: ne localStorage (rezerve).
 */

const LOCK_KEY = 'datapos_device_lock';
const DEVICE_ID_KEY = 'datapos_device_id';

const hasElectron = () =>
  typeof window !== 'undefined' && !!window.electronAPI?.getDeviceLock;

/** Identifikues i qendrueshem i pajisjes (per raportim/audit). */
export const getDeviceId = () => {
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
};

/** Lexon kycjen aktuale te pajisjes. Kthen null nese PC-ja nuk eshte e kycur. */
export const getLock = async () => {
  try {
    if (hasElectron()) {
      const lock = await window.electronAPI.getDeviceLock();
      if (lock && lock.tenant_id) return lock;
      return null;
    }
    const raw = localStorage.getItem(LOCK_KEY);
    if (!raw) return null;
    const parsed = JSON.parse(raw);
    return parsed && parsed.tenant_id ? parsed : null;
  } catch (e) {
    return null;
  }
};

/** Version sinkron (vetem localStorage) per render te shpejte ne UI. */
export const getLockSync = () => {
  try {
    const raw = localStorage.getItem(LOCK_KEY);
    if (!raw) return null;
    const parsed = JSON.parse(raw);
    return parsed && parsed.tenant_id ? parsed : null;
  } catch (e) {
    return null;
  }
};

/** Kyc firmen ne kete PC. */
export const setLock = async ({ tenant_id, tenant_name, company_name, username }) => {
  const lock = {
    tenant_id,
    tenant_name: tenant_name || null,
    company_name: company_name || null,
    locked_by: username || null,
    device_id: getDeviceId(),
    locked_at: new Date().toISOString(),
  };
  try {
    localStorage.setItem(LOCK_KEY, JSON.stringify(lock));
    if (hasElectron()) {
      await window.electronAPI.setDeviceLock(lock);
    }
  } catch (e) {
    /* ruajtja deshtoi - vazhdo pa e bllokuar kycjen */
  }
  return lock;
};

/** Heq kycjen (vetem super-administratori duhet te kete kete mundesi). */
export const clearLock = async () => {
  try {
    localStorage.removeItem(LOCK_KEY);
    if (hasElectron()) {
      await window.electronAPI.clearDeviceLock();
    }
    return true;
  } catch (e) {
    return false;
  }
};

/**
 * Kontrollon nese perdoruesi i dhene lejohet ne kete PC.
 *
 * Rregullat:
 *  - super_admin lejohet gjithmone (per mirembajtje).
 *  - Nese PC-ja nuk eshte e kycur, lejohet dhe kycja ruhet.
 *  - Nese PC-ja eshte e kycur, lejohet vetem firma e kycur.
 */
export const checkAndLock = async (userData, tenantInfo = {}) => {
  const role = userData?.role;
  const tenantId = userData?.tenant_id || null;

  if (role === 'super_admin') {
    return { allowed: true, lock: await getLock(), isSuperAdmin: true };
  }

  const lock = await getLock();

  if (!lock) {
    if (!tenantId) return { allowed: true, lock: null };
    const created = await setLock({
      tenant_id: tenantId,
      tenant_name: tenantInfo.name,
      company_name: tenantInfo.company_name,
      username: userData?.username,
    });
    return { allowed: true, lock: created, justLocked: true };
  }

  if (tenantId && lock.tenant_id !== tenantId) {
    const name = lock.company_name || lock.tenant_name || 'firma e kycur';
    return {
      allowed: false,
      lock,
      error:
        'Ky kompjuter është i rezervuar për "' +
        name +
        '". Nuk mund të kyçeni me firmë tjetër në këtë pajisje.',
    };
  }

  return { allowed: true, lock };
};

const deviceLockApi = {
  getDeviceId,
  getLock,
  getLockSync,
  setLock,
  clearLock,
  checkAndLock,
};

export default deviceLockApi;
