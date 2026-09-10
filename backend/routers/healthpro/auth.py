"""
HealthPRO - Authentication Router
"""
from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel
from datetime import datetime, timezone, timedelta
from typing import Optional
import uuid
import hashlib
import jwt
import os
import re

from database import db

router = APIRouter(prefix="/healthpro/auth", tags=["HealthPRO Auth"])

SECRET_KEY = os.environ.get("JWT_SECRET", "healthpro-secret-key-2026")
ALGORITHM = "HS256"

def hash_password(password: str) -> str:
    return hashlib.sha256(password.encode()).hexdigest()

def create_token(user_data: dict) -> str:
    expire = datetime.now(timezone.utc) + timedelta(hours=24)
    to_encode = {**user_data, "exp": expire}
    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)

def slugify(text: str) -> str:
    text = text.lower().strip()
    text = re.sub(r'[^\w\s-]', '', text)
    text = re.sub(r'[\s_-]+', '-', text)
    return text


class LoginRequest(BaseModel):
    username: str
    password: str

class RegisterRequest(BaseModel):
    name: str
    institute_type: str = "nursing_home"
    address: Optional[str] = None
    phone: Optional[str] = None
    email: Optional[str] = None
    admin_name: str
    admin_username: str
    admin_password: str


@router.post("/login")
async def login(request: LoginRequest):
    """Login to HealthPRO"""
    # Check in hp_users collection
    user = await db.hp_users.find_one(
        {"username": request.username},
        {"_id": 0}
    )
    
    if not user:
        raise HTTPException(status_code=401, detail="Kredencialet e gabuara")
    
    if user.get("password") != hash_password(request.password):
        raise HTTPException(status_code=401, detail="Kredencialet e gabuara")
    
    if not user.get("is_active", True):
        raise HTTPException(status_code=401, detail="Llogaria është çaktivizuar")
    
    # Get tenant info
    tenant = await db.hp_tenants.find_one(
        {"id": user.get("tenant_id")},
        {"_id": 0}
    )
    
    token_data = {
        "sub": user["id"],
        "username": user["username"],
        "role": user.get("role", "staff"),
        "tenant_id": user.get("tenant_id"),
        "full_name": f"{user.get('first_name', '')} {user.get('last_name', '')}".strip()
    }
    
    token = create_token(token_data)
    
    return {
        "access_token": token,
        "token_type": "bearer",
        "user": {
            "id": user["id"],
            "username": user["username"],
            "full_name": token_data["full_name"],
            "role": user.get("role", "staff"),
            "tenant_id": user.get("tenant_id"),
            "tenant_name": tenant.get("name") if tenant else None
        }
    }


@router.post("/register")
async def register(request: RegisterRequest):
    """Register a new HealthPRO institute"""
    # Check if username exists
    existing = await db.hp_users.find_one({"username": request.admin_username})
    if existing:
        raise HTTPException(status_code=400, detail="Username tashmë ekziston")
    
    # Create tenant
    tenant_id = str(uuid.uuid4())
    slug = slugify(request.name)
    
    # Ensure unique slug
    existing_slug = await db.hp_tenants.find_one({"slug": slug})
    if existing_slug:
        slug = f"{slug}-{str(uuid.uuid4())[:4]}"
    
    now = datetime.now(timezone.utc).isoformat()
    
    tenant_doc = {
        "id": tenant_id,
        "name": request.name,
        "slug": slug,
        "institute_type": request.institute_type,
        "address": request.address,
        "phone": request.phone,
        "email": request.email,
        "is_active": True,
        "created_at": now,
        "settings": {
            "systematic_checkup_interval": 6,  # months
            "auto_generate_checkups": True
        }
    }
    
    await db.hp_tenants.insert_one(tenant_doc)
    
    # Create admin user
    admin_id = str(uuid.uuid4())
    admin_doc = {
        "id": admin_id,
        "tenant_id": tenant_id,
        "username": request.admin_username,
        "password": hash_password(request.admin_password),
        "first_name": request.admin_name.split()[0] if request.admin_name else "Admin",
        "last_name": " ".join(request.admin_name.split()[1:]) if len(request.admin_name.split()) > 1 else "",
        "role": "admin",
        "is_active": True,
        "created_at": now
    }
    
    await db.hp_users.insert_one(admin_doc)
    
    return {
        "message": "Instituti u regjistrua me sukses!",
        "tenant_id": tenant_id,
        "tenant_name": request.name
    }


@router.get("/me")
async def get_current_user_info(token: str):
    """Get current user info from token"""
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        user_id = payload.get("sub")
        
        user = await db.hp_users.find_one({"id": user_id}, {"_id": 0, "password": 0})
        if not user:
            raise HTTPException(status_code=404, detail="User not found")
        
        tenant = await db.hp_tenants.find_one({"id": user.get("tenant_id")}, {"_id": 0})
        
        return {
            "user": user,
            "tenant": tenant
        }
    except jwt.ExpiredSignatureError:
        raise HTTPException(status_code=401, detail="Token expired")
    except jwt.InvalidTokenError:
        raise HTTPException(status_code=401, detail="Invalid token")
