export function apiErrorMessage(error, fallback = 'Kërkesa dështoi') {
  const detail = error?.response?.data?.detail;
  if (typeof detail === 'string' && detail) return detail;
  if (Array.isArray(detail)) {
    return detail.map(item => `${(item.loc || []).filter(part => part !== 'body').join('.')}: ${item.msg || 'Vlerë e pavlefshme'}`).join('; ');
  }
  if (!error?.response) return 'Nuk u arrit serveri. Kontrolloni lidhjen; veprimi nuk është konfirmuar.';
  return `${fallback} (${error.response.status})`;
}
