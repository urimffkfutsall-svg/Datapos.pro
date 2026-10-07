import { api } from '../App';

export const SOCIAL_HOSTS = {
  facebook: ['facebook.com', 'www.facebook.com', 'm.facebook.com', 'fb.com', 'www.fb.com'],
  instagram: ['instagram.com', 'www.instagram.com'],
  tiktok: ['tiktok.com', 'www.tiktok.com', 'vm.tiktok.com', 'vt.tiktok.com'],
};
export function safeSocialUrl(value, platform) {
  try {
    const url = new URL(value);
    return url.protocol === 'https:' && SOCIAL_HOSTS[platform]?.includes(url.hostname) && !url.username && !url.password && (!url.port || url.port === '443') ? url.href : '';
  } catch { return ''; }
}
export function partnerLogoUrl(partner) {
  if (!partner?.id || !partner?.logo_url) return '';
  const base = (api.defaults.baseURL || '/api').replace(/\/api\/?$/, '');
  const version = partner.logo_url.includes('?') ? partner.logo_url.slice(partner.logo_url.indexOf('?')) : '';
  return `${base}/api/partners/${encodeURIComponent(partner.id)}/logo${version}`;
}
export function phoneHref(phone) {
  const clean = (phone || '').replace(/[^+\d]/g, '');
  return /\d{3}/.test(clean) ? `tel:${clean}` : undefined;
}
export const emptyPartner = () => ({name: '', kind: 'company', address: '', phone: '', facebook: '', instagram: '', tiktok: '', is_active: true, sort_order: 0, logo_data: null});
export function partnerPayload(draft) {
  const payload = Object.fromEntries(Object.keys(emptyPartner()).map(key => [key, draft[key] ?? emptyPartner()[key]]));
  ['name', 'address', 'phone', 'facebook', 'instagram', 'tiktok'].forEach(key => {payload[key] = String(payload[key]).trim();});
  payload.sort_order = Number(payload.sort_order);
  return payload;
}
