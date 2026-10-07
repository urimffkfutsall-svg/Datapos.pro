"""Tenant routing across separate frontend/API hosts.
Routing hints select a tenant; they NEVER authenticate a user. auth.get_current_user
still verifies the JWT and compares the user's tenant_id with the resolved tenant.
"""
import re
from urllib.parse import urlsplit
from fastapi import HTTPException

HOST_RE = re.compile(r'^([a-z0-9-]{1,63})\.datapos\.pro$', re.I)
SUB_RE = re.compile(r'^[a-z0-9-]{1,63}$', re.I)
RESERVED = {'www', 'app', 'api'}

def subdomain_from_host(host):
    host = (host or '').split(':')[0].strip().lower().rstrip('.')
    match = HOST_RE.fullmatch(host)
    return match.group(1) if match and match.group(1) not in RESERVED else None


def request_tenant_subdomain(request):
    if request is None:
        return None
    headers = request.headers
    forwarded = subdomain_from_host(headers.get('x-forwarded-host'))
    host = subdomain_from_host(headers.get('host'))
    # Proxies/clients can merge repeated headers into a comma-separated value.
    # Accept only identical valid slugs; never silently choose between tenants.
    raw_hint = headers.get('x-tenant-subdomain') or ''
    hint_values = [value.strip().lower() for value in raw_hint.split(',')] if raw_hint.strip() else []
    if any(not SUB_RE.fullmatch(value) or value in RESERVED for value in hint_values):
        raise HTTPException(status_code=400, detail='Subdomain-i i firmës është i pavlefshëm')
    unique_hints = set(hint_values)
    if len(unique_hints) > 1:
        raise HTTPException(status_code=403, detail='Kërkesa përmban firma të ndryshme')
    hint = next(iter(unique_hints), None)
    origin_sub = None
    origin = headers.get('origin')
    if origin and origin != 'null':
        try:
            parsed = urlsplit(origin)
            if parsed.scheme in ('https', 'http'):
                origin_sub = subdomain_from_host(parsed.hostname)
        except ValueError:
            pass
    candidates = {value for value in (forwarded, host, hint, origin_sub) if value}
    if len(candidates) > 1:
        raise HTTPException(status_code=403, detail='Adresa e firmës nuk përputhet me kërkesën')
    return next(iter(candidates), None)
