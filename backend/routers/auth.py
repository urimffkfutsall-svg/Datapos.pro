"""Authentication routes"""
from fastapi import APIRouter, HTTPException, Depends
from datetime import datetime, timezone
from dateutil import parser as date_parser

from database import db
from models import LoginRequest, TokenResponse, UserResponse, UserRole, TenantPublicInfo
from auth import hash_password, verify_password, create_token, get_current_user

router = APIRouter(prefix="/auth", tags=["Authentication"])


@router.post("/login", response_model=TokenResponse)
async def login(request: LoginRequest):
    """Login with username/password or PIN"""
    user = await db.users.find_one({"username": request.username}, {"_id": 0})
    
    if not user:
        user = await db.users.find_one({"pin": request.username}, {"_id": 0})
    
    if not user:
        raise HTTPException(status_code=401, detail="Kredencialet e gabuara")
    
    if not user.get("is_active", True):
        raise HTTPException(status_code=401, detail="Llogaria është e çaktivizuar")
    
    if user.get("pin") == request.password:
        pass
    elif not verify_password(request.password, user.get("password_hash", "")):
        raise HTTPException(status_code=401, detail="Kredencialet e gabuara")
    
    tenant_id = user.get("tenant_id")
    
    if tenant_id and user.get("role") != UserRole.SUPER_ADMIN and user.get("role") != "super_admin":
        tenant = await db.tenants.find_one({"id": tenant_id}, {"_id": 0})
        if tenant:
            # Check if tenant is suspended
            if tenant.get("status") == "suspended":
                raise HTTPException(status_code=403, detail="Firma juaj është pezulluar. Kontaktoni administratorin.")
            
            # Check subscription expiration
            subscription_expires = tenant.get("subscription_expires")
            if subscription_expires:
                try:
                    # Parse the expiration date
                    if isinstance(subscription_expires, str):
                        expires_date = date_parser.parse(subscription_expires)
                    else:
                        expires_date = subscription_expires
                    
                    # Make sure it's timezone aware
                    if expires_date.tzinfo is None:
                        expires_date = expires_date.replace(tzinfo=timezone.utc)
                    
                    # Check if subscription has expired
                    now = datetime.now(timezone.utc)
                    if expires_date < now:
                        # Calculate days expired
                        days_expired = (now - expires_date).days
                        raise HTTPException(
                            status_code=402,  # 402 Payment Required
                            detail=f"SUBSCRIPTION_EXPIRED|{days_expired}"
                        )
                except HTTPException:
                    raise
                except Exception:
                    # If date parsing fails, allow login but log the issue
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
    
    return TokenResponse(
        access_token=token,
        user=UserResponse(
            id=user["id"],
            username=user["username"],
            full_name=user.get("full_name", ""),
            role=user["role"],
            branch_id=user.get("branch_id"),
            is_active=user.get("is_active", True),
            created_at=created_at or datetime.now(timezone.utc).isoformat(),
            pin=user.get("pin"),
            tenant_id=user.get("tenant_id")
        )
    )


@router.get("/me", response_model=UserResponse)
async def get_me(current_user: dict = Depends(get_current_user)):
    """Get current user info"""
    created_at = current_user.get("created_at")
    if isinstance(created_at, datetime):
        created_at = created_at.isoformat()
    
    return UserResponse(
        id=current_user["id"],
        username=current_user["username"],
        full_name=current_user.get("full_name", ""),
        role=current_user["role"],
        branch_id=current_user.get("branch_id"),
        is_active=current_user.get("is_active", True),
        created_at=created_at or "",
        pin=current_user.get("pin"),
        tenant_id=current_user.get("tenant_id")
    )
