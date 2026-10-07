export const AUTH_EXPIRED_EVENT = 'datapos-auth-expired';
export function clearSession(storage) {
  storage.removeItem('t3next_token');
  storage.removeItem('t3next_user');
}
export function restoreSession(storage, now = Date.now(), decode = atob) {
  const token = storage.getItem('t3next_token');
  const saved = storage.getItem('t3next_user');
  if (!token || !saved) { clearSession(storage); return null; }
  try {
    const user = JSON.parse(saved);
    const part = token.split('.')[1].replace(/-/g, '+').replace(/_/g, '/');
    const payload = JSON.parse(decode(part.padEnd(Math.ceil(part.length / 4) * 4, '=')));
    if (!user?.id || !payload.exp || payload.exp * 1000 <= now) { clearSession(storage); return null; }
    // This only restores UI state. Every backend request still verifies the JWT.
    return user;
  } catch { clearSession(storage); return null; }
}
export function shouldExpireSession(error) {
  const status = error.response?.status;
  const detail = error.response?.data?.detail;
  const url = (error.config?.url || '').split('?')[0];
  if (status === 401) {
    if (url.endsWith('/auth/login')) return false;
    // Old backend versions used 401 for a wrong reset/confirmation password.
    if (url.startsWith('/admin/') && detail === 'Fjalëkalimi i gabuar') return false;
    return true;
  }
  return status === 403 && ['Not authenticated', 'Invalid authentication credentials'].includes(detail);
}
