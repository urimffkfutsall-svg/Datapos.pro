"""BookPRO Authentication Routes"""
from fastapi import APIRouter, HTTPException, Depends
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from datetime import datetime, timezone
from dateutil import parser as date_parser

from .database import bp_tenants, bp_users
from .models import BPLoginRequest, BPTokenResponse, BPUserResponse, BPUserRole
from auth import hash_password, verify_password, create_token, get_current_user

router = APIRouter(prefix="/bookpro/auth", tags=["BookPRO Auth"])


@router.post("/login", response_model=BPTokenResponse)
async def bp_login(request: BPLoginRequest):
    """Login to BookPRO"""
    # First check if super admin
    from database import db
    super_admin = await db.users.find_one(
        {"username": request.username, "role": "super_admin"}, 
        {"_id": 0}
    )
    
    if super_admin:
        if not verify_password(request.password, super_admin.get("password_hash", "")):
            raise HTTPException(status_code=401, detail="Kredencialet e gabuara")
        
        token = create_token(
            user_id=super_admin["id"],
            username=super_admin["username"],
            role="super_admin",
            tenant_id=None
        )
        
        created_at = super_admin.get("created_at")
        if isinstance(created_at, datetime):
            created_at = created_at.isoformat()
        
        return BPTokenResponse(
            access_token=token,
            user=BPUserResponse(
                id=super_admin["id"],
                username=super_admin["username"],
                full_name=super_admin.get("full_name", "Super Administrator"),
                role=BPUserRole.SUPER_ADMIN,
                is_active=True,
                tenant_id=None,
                created_at=created_at or datetime.now(timezone.utc).isoformat()
            )
        )
    
    # Check BookPRO users
    user = await bp_users.find_one({"username": request.username}, {"_id": 0})
    
    if not user:
        raise HTTPException(status_code=401, detail="Kredencialet e gabuara")
    
    if not user.get("is_active", True):
        raise HTTPException(status_code=401, detail="Llogaria është e çaktivizuar")
    
    if not verify_password(request.password, user.get("password_hash", "")):
        raise HTTPException(status_code=401, detail="Kredencialet e gabuara")
    
    tenant_id = user.get("tenant_id")
    
    # Check tenant status and subscription
    if tenant_id:
        tenant = await bp_tenants.find_one({"id": tenant_id}, {"_id": 0})
        if tenant:
            if tenant.get("status") == "suspended":
                raise HTTPException(
                    status_code=403, 
                    detail="Salloni juaj është pezulluar. Kontaktoni administratorin."
                )
            
            subscription_expires = tenant.get("subscription_expires")
            if subscription_expires:
                try:
                    if isinstance(subscription_expires, str):
                        expires_date = date_parser.parse(subscription_expires)
                    else:
                        expires_date = subscription_expires
                    
                    if expires_date.tzinfo is None:
                        expires_date = expires_date.replace(tzinfo=timezone.utc)
                    
                    now = datetime.now(timezone.utc)
                    if expires_date < now:
                        days_expired = (now - expires_date).days
                        raise HTTPException(
                            status_code=402,
                            detail=f"SUBSCRIPTION_EXPIRED|{days_expired}"
                        )
                except HTTPException:
                    raise
                except Exception:
                    pass
    
    token = create_token(
        user_id=user["id"],
        username=user["username"],
        role=user["role"],
        tenant_id=tenant_id
    )
    
    created_at = user.get("created_at")
    if isinstance(created_at, datetime):
        created_at = created_at.isoformat()
    
    return BPTokenResponse(
        access_token=token,
        user=BPUserResponse(
            id=user["id"],
            username=user["username"],
            full_name=user.get("full_name", ""),
            role=user["role"],
            phone=user.get("phone"),
            email=user.get("email"),
            specializations=user.get("specializations", []),
            bio=user.get("bio"),
            photo_url=user.get("photo_url"),
            commission_percent=user.get("commission_percent", 0),
            is_active=user.get("is_active", True),
            tenant_id=user.get("tenant_id"),
            created_at=created_at or ""
        )
    )


@router.get("/me", response_model=BPUserResponse)
async def get_bp_me(current_user: dict = Depends(get_current_user)):
    """Get current BookPRO user info"""
    created_at = current_user.get("created_at")
    if isinstance(created_at, datetime):
        created_at = created_at.isoformat()
    
    return BPUserResponse(
        id=current_user["id"],
        username=current_user["username"],
        full_name=current_user.get("full_name", ""),
        role=current_user.get("role", "stylist"),
        phone=current_user.get("phone"),
        email=current_user.get("email"),
        specializations=current_user.get("specializations", []),
        bio=current_user.get("bio"),
        photo_url=current_user.get("photo_url"),
        commission_percent=current_user.get("commission_percent", 0),
        is_active=current_user.get("is_active", True),
        tenant_id=current_user.get("tenant_id"),
        created_at=created_at or ""
    )


async def get_bp_current_user(current_user: dict = Depends(get_current_user)):
    """Get current BookPRO user - checks bp_users collection"""
    if current_user.get("role") == "super_admin":
        return current_user
    
    # For BookPRO users, we need to check bp_users collection
    # The current_user from get_current_user might return None for BP users
    # because they're not in the main users collection
    user = await bp_users.find_one({"id": current_user["id"]}, {"_id": 0, "password_hash": 0})
    if user:
        return user
    
    # If not found in bp_users, the current_user from main users might be valid for super_admin
    return current_user


async def verify_bp_token(credentials: HTTPAuthorizationCredentials = Depends(HTTPBearer())) -> dict:
    """Verify JWT token and get BookPRO user - checks bp_users first, then pos_users for super_admin"""
    import jwt
    import os
    
    JWT_SECRET = os.environ.get('JWT_SECRET', 't3next_pos_secret_key')
    JWT_ALGORITHM = os.environ.get('JWT_ALGORITHM', 'HS256')
    
    token = credentials.credentials
    try:
        payload = jwt.decode(token, JWT_SECRET, algorithms=[JWT_ALGORITHM])
        user_id = payload.get("sub")
        
        # First check BookPRO users
        user = await bp_users.find_one({"id": user_id}, {"_id": 0, "password_hash": 0})
        
        if not user:
            # Check POS users (for super_admin)
            from database import db
            user = await db.users.find_one({"id": user_id, "role": "super_admin"}, {"_id": 0, "password_hash": 0})
        
        if not user:
            raise HTTPException(status_code=401, detail="Përdoruesi nuk u gjet")
        
        return user
    except jwt.ExpiredSignatureError:
        raise HTTPException(status_code=401, detail="Token-i ka skaduar")
    except jwt.InvalidTokenError:
        raise HTTPException(status_code=401, detail="Token i pavlefshëm")
