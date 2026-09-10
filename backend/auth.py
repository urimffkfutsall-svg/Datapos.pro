"""Authentication and authorization utilities"""
from fastapi import Depends, HTTPException
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


async def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(security)) -> dict:
    """Get the current authenticated user from JWT token"""
    token = credentials.credentials
    try:
        payload = jwt.decode(token, JWT_SECRET, algorithms=[JWT_ALGORITHM])
        user = await db.users.find_one({"id": payload["sub"]}, {"_id": 0, "password_hash": 0})
        if not user:
            raise HTTPException(status_code=401, detail="Përdoruesi nuk u gjet")
        return user
    except jwt.ExpiredSignatureError:
        raise HTTPException(status_code=401, detail="Token-i ka skaduar")
    except jwt.InvalidTokenError:
        raise HTTPException(status_code=401, detail="Token i pavlefshëm")


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
