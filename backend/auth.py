"""Authentication and authorization utilities"""
import re
from fastapi import Depends, HTTPException, Request
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from datetime import datetime, timezone, timedelta
from typing import List
import jwt
import os
import bcrypt

from database import db
from models import UserRole, AuditLog

# JWT Config
JWT_SECRET = os.environ.get('JWT_SECRET', 't3next_pos_secret_key')
JWT_ALGORITHM = os.environ.get('JWT_ALGORITHM', 'HS256')
JWT_EXPIRATION_HOURS = int(os.environ.get('JWT_EXPIRATION_HOURS', 24))

# Security
security = HTTPBearer()


def hash_password(password: str) -> str:
    """Hash a password using bcrypt directly"""
    salt = bcrypt.gensalt()
    return bcrypt.hashpw(password.encode('utf-8'), salt).decode('utf-8')


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verify a password against a hash"""
    try:
        return bcrypt.checkpw(plain_password.encode('utf-8'), hashed_password.encode('utf-8'))
    except Exception:
        return False


def create_token(user_id: str, username: str, role: str, tenant_id: str = None) -> str:
    """Create a JWT token for a user"""
    payload = {
        "sub": user_id,
        "username": username,
        "role": role,
        "exp": datetime.now(timezone.utc) + timedelta(hours=JWT_EXPIRATION_HOURS)
    }
    if tenant_id:
        payload["tenant_id"] = tenant_id
    return jwt.encode(payload, JWT_SECRET, algorithm=JWT_ALGORITHM)


# Subdomain i nje firme reale, p.sh. "nlagje.datapos.pro" -> "nlagje"
_TENANT_HOST_RE = re.compile(r'^([a-z0-9-]+)\.datapos\.pro$', re.IGNORECASE)


def extract_subdomain(host: str):
    """Nxjerr subdomain-in e firmes nga Host header. None = domain kryesor."""
    if not host:
        return None
    host = host.split(':')[0].strip().lower()
    match = _TENANT_HOST_RE.match(host)
    if not match:
        return None
    sub = match.group(1)
    if sub in ('www', 'app'):
        return None
    return sub


async def _host_tenant_id(request: Request):
    """Tenant-i i kerkuar nga domain-i i kerkeses (None per domain-in kryesor)."""
    if request is None:
        return None
    host = request.headers.get('x-forwarded-host') or request.headers.get('host')
    sub = extract_subdomain(host)
    if not sub:
        return None
    tenant = await db.tenants.find_one(
        {"name": {"$regex": f"^{re.escape(sub)}$", "$options": "i"}}, {"_id": 0}
    )
    if not tenant:
        raise HTTPException(status_code=404, detail="Firma nuk u gjet për këtë domain")
    return tenant.get("id")


async def get_current_user(
    request: Request,
    credentials: HTTPAuthorizationCredentials = Depends(security),
) -> dict:
    """Get the current authenticated user from JWT token.

    Zbaton izolimin e firmave: nje token i leshuar per firmen A nuk mund te
    perdoret ne subdomain-in e firmes B, dhe ne domain-in kryesor pranohet
    vetem super-administratori.
    """
    token = credentials.credentials
    try:
        payload = jwt.decode(token, JWT_SECRET, algorithms=[JWT_ALGORITHM])
        user = await db.users.find_one({"id": payload["sub"]}, {"_id": 0, "password_hash": 0})
        if not user:
            raise HTTPException(status_code=401, detail="Përdoruesi nuk u gjet")
    except jwt.ExpiredSignatureError:
        raise HTTPException(status_code=401, detail="Token-i ka skaduar")
    except jwt.InvalidTokenError:
        raise HTTPException(status_code=401, detail="Token i pavlefshëm")

    is_super = user.get("role") == "super_admin"
    host_tenant = await _host_tenant_id(request)

    if not is_super:
        if host_tenant is None:
            # Domain kryesor -> vetem super_admin
            raise HTTPException(
                status_code=403,
                detail="Përdorni adresën e firmës suaj (p.sh. firma.datapos.pro)",
            )
        if user.get("tenant_id") != host_tenant:
            # Token i nje firme tjeter -> ndalohet ne kete subdomain
            raise HTTPException(
                status_code=403,
                detail="Nuk keni qasje në këtë firmë",
            )

    return user


def require_role(allowed_roles: List[UserRole]):
    """Dependency to require specific roles for an endpoint"""
    async def role_checker(current_user: dict = Depends(get_current_user)):
        if current_user["role"] not in [r.value for r in allowed_roles]:
            raise HTTPException(status_code=403, detail="Nuk keni leje për këtë veprim")
        return current_user
    return role_checker


def get_tenant_filter(current_user: dict) -> dict:
    """Get tenant filter for queries - returns empty dict for super_admin"""
    if current_user.get("role") == UserRole.SUPER_ADMIN or current_user.get("role") == "super_admin":
        return {}
    tenant_id = current_user.get("tenant_id")
    if not tenant_id:
        return {}
    return {"tenant_id": tenant_id}


def add_tenant_id(data: dict, current_user: dict) -> dict:
    """Add tenant_id to data for create operations"""
    tenant_id = current_user.get("tenant_id")
    if tenant_id:
        data["tenant_id"] = tenant_id
    return data


async def log_audit(user_id: str, action: str, entity_type: str, entity_id: str, details: dict = None):
    """Log an audit event"""
    audit = AuditLog(user_id=user_id, action=action, entity_type=entity_type, entity_id=entity_id, details=details)
    doc = audit.model_dump()
    doc['created_at'] = doc['created_at'].isoformat()
    await db.audit_logs.insert_one(doc)
