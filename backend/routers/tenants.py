"""Tenant management routes (Super Admin only)"""
from fastapi import APIRouter, HTTPException, Depends
from typing import List, Optional
from datetime import datetime, timezone
from pydantic import BaseModel
import uuid
import qrcode
import io
import base64

from database import db
from models import (
    TenantCreate, TenantUpdate, TenantResponse, TenantPublicInfo,
    TenantStatus, UserRole
)
from auth import hash_password, get_current_user, log_audit

router = APIRouter(prefix="/tenants", tags=["Tenants"])


def generate_whatsapp_qr(phone: str) -> str:
    """Generate QR code for WhatsApp link as base64 data URL"""
    if not phone:
        return None
    
    # Clean phone number - remove spaces and special chars except +
    clean_phone = ''.join(c for c in phone if c.isdigit() or c == '+')
    if clean_phone.startswith('+'):
        clean_phone = clean_phone[1:]  # Remove + for wa.me link
    
    if not clean_phone:
        return None
    
    # Create WhatsApp link
    whatsapp_url = f"https://wa.me/{clean_phone}"
    
    # Generate QR code
    qr = qrcode.QRCode(
        version=1,
        error_correction=qrcode.constants.ERROR_CORRECT_L,
        box_size=6,
        border=2,
    )
    qr.add_data(whatsapp_url)
    qr.make(fit=True)
    
    # Create image
    img = qr.make_image(fill_color="black", back_color="white")
    
    # Convert to base64
    buffer = io.BytesIO()
    img.save(buffer, format='PNG')
    buffer.seek(0)
    
    img_base64 = base64.b64encode(buffer.getvalue()).decode('utf-8')
    return f"data:image/png;base64,{img_base64}"


# ============ PUBLIC ENDPOINT - No Auth Required ============
@router.get("/by-subdomain/{subdomain}", response_model=TenantPublicInfo)
async def get_tenant_by_subdomain(subdomain: str):
    """Get tenant public info by subdomain - PUBLIC ENDPOINT for subdomain routing"""
    # Clean subdomain - remove www if present
    subdomain = subdomain.lower().strip()
    if subdomain == 'www' or subdomain == 'app':
        raise HTTPException(status_code=404, detail="Firma nuk u gjet")
    
    # Search by name (subdomain is the tenant name)
    tenant = await db.tenants.find_one(
        {"$or": [
            {"name": subdomain},
            {"name": {"$regex": f"^{subdomain}$", "$options": "i"}}
        ]},
        {"_id": 0}
    )
    
    if not tenant:
        raise HTTPException(status_code=404, detail="Firma nuk u gjet")
    
    if tenant.get("status") == "suspended":
        raise HTTPException(status_code=403, detail="Firma është pezulluar")
    
    return TenantPublicInfo(
        id=tenant["id"],
        name=tenant["name"],
        company_name=tenant.get("company_name") or tenant["name"],
        logo_url=tenant.get("logo_url"),
        stamp_url=tenant.get("stamp_url"),
        whatsapp_qr_url=tenant.get("whatsapp_qr_url"),
        primary_color=tenant.get("primary_color", "#00a79d"),
        secondary_color=tenant.get("secondary_color", "#E0F7FA")
    )


@router.get("", response_model=List[TenantResponse])
async def get_all_tenants(current_user: dict = Depends(get_current_user)):
    """Get all tenants - Super Admin only"""
    if current_user.get("role") != UserRole.SUPER_ADMIN and current_user.get("role") != "super_admin":
        raise HTTPException(status_code=403, detail="Vetëm Super Admin mund të shohë të gjitha firmat")
    
    tenants = await db.tenants.find({}, {"_id": 0}).sort("created_at", -1).to_list(1000)
    
    for tenant in tenants:
        tenant["users_count"] = await db.users.count_documents({"tenant_id": tenant["id"]})
        tenant["sales_count"] = await db.sales.count_documents({"tenant_id": tenant["id"]})
    
    return tenants


@router.post("", response_model=TenantResponse)
async def create_tenant(tenant: TenantCreate, current_user: dict = Depends(get_current_user)):
    """Create a new tenant - Super Admin only"""
    if current_user.get("role") != UserRole.SUPER_ADMIN and current_user.get("role") != "super_admin":
        raise HTTPException(status_code=403, detail="Vetëm Super Admin mund të krijojë firma të reja")
    
    existing = await db.tenants.find_one({"name": tenant.name.lower()})
    if existing:
        raise HTTPException(status_code=400, detail="Emri i firmës ekziston tashmë")
    
    existing_email = await db.tenants.find_one({"email": tenant.email.lower()})
    if existing_email:
        raise HTTPException(status_code=400, detail="Email-i ekziston tashmë")
    
    # Generate WhatsApp QR code if phone is provided
    whatsapp_qr = generate_whatsapp_qr(tenant.phone) if tenant.phone else None
    
    tenant_id = str(uuid.uuid4())
    tenant_data = {
        "id": tenant_id,
        "name": tenant.name.lower(),
        "company_name": tenant.company_name,
        "email": tenant.email.lower(),
        "phone": tenant.phone,
        "address": tenant.address,
        "logo_url": tenant.logo_url,
        "whatsapp_qr_url": whatsapp_qr,  # Auto-generated QR code
        "primary_color": tenant.primary_color,
        "secondary_color": tenant.secondary_color,
        "stripe_payment_link": tenant.stripe_payment_link,
        "status": TenantStatus.TRIAL,
        "subscription_expires": None,
        "created_at": datetime.now(timezone.utc).isoformat(),
        "created_by": current_user["id"]
    }
    
    await db.tenants.insert_one(tenant_data)
    
    admin_user = {
        "id": str(uuid.uuid4()),
        "username": tenant.admin_username,
        "password_hash": hash_password(tenant.admin_password),
        "full_name": tenant.admin_full_name,
        "role": UserRole.ADMIN,
        "tenant_id": tenant_id,
        "is_active": True,
        "created_at": datetime.now(timezone.utc).isoformat()
    }
    await db.users.insert_one(admin_user)
    
    await log_audit(current_user["id"], "create", "tenant", tenant_id)
    
    return TenantResponse(**tenant_data, users_count=1, sales_count=0)


@router.get("/{tenant_id}", response_model=TenantResponse)
async def get_tenant(tenant_id: str, current_user: dict = Depends(get_current_user)):
    """Get tenant details - Super Admin only"""
    if current_user.get("role") != UserRole.SUPER_ADMIN and current_user.get("role") != "super_admin":
        raise HTTPException(status_code=403, detail="Vetëm Super Admin mund të shohë detajet e firmës")
    
    tenant = await db.tenants.find_one({"id": tenant_id}, {"_id": 0})
    if not tenant:
        raise HTTPException(status_code=404, detail="Firma nuk u gjet")
    
    tenant["users_count"] = await db.users.count_documents({"tenant_id": tenant_id})
    tenant["sales_count"] = await db.sales.count_documents({"tenant_id": tenant_id})
    
    return TenantResponse(**tenant)


@router.put("/{tenant_id}", response_model=TenantResponse)
async def update_tenant(tenant_id: str, update: TenantUpdate, current_user: dict = Depends(get_current_user)):
    """Update tenant - Super Admin only"""
    if current_user.get("role") != UserRole.SUPER_ADMIN and current_user.get("role") != "super_admin":
        raise HTTPException(status_code=403, detail="Vetëm Super Admin mund të modifikojë firmat")
    
    existing = await db.tenants.find_one({"id": tenant_id})
    if not existing:
        raise HTTPException(status_code=404, detail="Firma nuk u gjet")
    
    update_data = {k: v for k, v in update.model_dump().items() if v is not None}
    
    # Regenerate WhatsApp QR code if phone number changed
    if "phone" in update_data:
        new_qr = generate_whatsapp_qr(update_data["phone"])
        update_data["whatsapp_qr_url"] = new_qr
    
    if update_data:
        await db.tenants.update_one({"id": tenant_id}, {"$set": update_data})
    
    updated = await db.tenants.find_one({"id": tenant_id}, {"_id": 0})
    updated["users_count"] = await db.users.count_documents({"tenant_id": tenant_id})
    updated["sales_count"] = await db.sales.count_documents({"tenant_id": tenant_id})
    
    await log_audit(current_user["id"], "update", "tenant", tenant_id)
    
    return TenantResponse(**updated)


class TenantUserCreate(BaseModel):
    username: str
    password: str
    full_name: str
    role: str = "admin"  # admin or cashier
    pin: Optional[str] = None


@router.get("/{tenant_id}/users")
async def get_tenant_users(tenant_id: str, current_user: dict = Depends(get_current_user)):
    """Get all users for a tenant - Super Admin only"""
    if current_user.get("role") != UserRole.SUPER_ADMIN and current_user.get("role") != "super_admin":
        raise HTTPException(status_code=403, detail="Vetëm Super Admin ka akses")
    
    users = await db.users.find({"tenant_id": tenant_id}, {"_id": 0, "password_hash": 0}).to_list(1000)
    return users


@router.post("/{tenant_id}/users")
async def create_tenant_user(tenant_id: str, user_data: TenantUserCreate, current_user: dict = Depends(get_current_user)):
    """Create a new user for a tenant - Super Admin only"""
    if current_user.get("role") != UserRole.SUPER_ADMIN and current_user.get("role") != "super_admin":
        raise HTTPException(status_code=403, detail="Vetëm Super Admin ka akses")
    
    # Verify tenant exists
    tenant = await db.tenants.find_one({"id": tenant_id})
    if not tenant:
        raise HTTPException(status_code=404, detail="Firma nuk u gjet")
    
    # Check if username exists
    existing = await db.users.find_one({"username": user_data.username, "tenant_id": tenant_id})
    if existing:
        raise HTTPException(status_code=400, detail="Username ekziston tashmë në këtë firmë")
    
    # Check PIN if provided
    if user_data.pin:
        existing_pin = await db.users.find_one({"pin": user_data.pin, "tenant_id": tenant_id})
        if existing_pin:
            raise HTTPException(status_code=400, detail="PIN ekziston tashmë në këtë firmë")
    
    # Determine role
    role = UserRole.ADMIN if user_data.role == "admin" else UserRole.CASHIER
    
    new_user = {
        "id": str(uuid.uuid4()),
        "username": user_data.username,
        "password_hash": hash_password(user_data.password),
        "full_name": user_data.full_name,
        "role": role,
        "tenant_id": tenant_id,
        "pin": user_data.pin,
        "is_active": True,
        "created_at": datetime.now(timezone.utc).isoformat()
    }
    await db.users.insert_one(new_user)
    
    await log_audit(current_user["id"], "create_tenant_user", "user", new_user["id"], {"tenant_id": tenant_id})
    
    # Return without password_hash and _id
    new_user.pop("password_hash", None)
    new_user.pop("_id", None)
    return {"message": "Përdoruesi u krijua me sukses", "user": new_user}


@router.delete("/{tenant_id}/users/{user_id}")
async def delete_tenant_user(tenant_id: str, user_id: str, current_user: dict = Depends(get_current_user)):
    """Delete a user from a tenant - Super Admin only"""
    if current_user.get("role") != UserRole.SUPER_ADMIN and current_user.get("role") != "super_admin":
        raise HTTPException(status_code=403, detail="Vetëm Super Admin ka akses")
    
    result = await db.users.delete_one({"id": user_id, "tenant_id": tenant_id})
    if result.deleted_count == 0:
        raise HTTPException(status_code=404, detail="Përdoruesi nuk u gjet")
    
    await log_audit(current_user["id"], "delete_tenant_user", "user", user_id, {"tenant_id": tenant_id})
    
    return {"message": "Përdoruesi u fshi me sukses"}


@router.delete("/{tenant_id}")
async def delete_tenant(tenant_id: str, current_user: dict = Depends(get_current_user)):
    """Delete tenant and all associated data - Super Admin only"""
    if current_user.get("role") != UserRole.SUPER_ADMIN and current_user.get("role") != "super_admin":
        raise HTTPException(status_code=403, detail="Vetëm Super Admin mund të fshijë firmat")
    
    existing = await db.tenants.find_one({"id": tenant_id})
    if not existing:
        raise HTTPException(status_code=404, detail="Firma nuk u gjet")
    
    # Delete all tenant data
    await db.users.delete_many({"tenant_id": tenant_id})
    await db.products.delete_many({"tenant_id": tenant_id})
    await db.sales.delete_many({"tenant_id": tenant_id})
    await db.branches.delete_many({"tenant_id": tenant_id})
    await db.cash_drawers.delete_many({"tenant_id": tenant_id})
    await db.stock_movements.delete_many({"tenant_id": tenant_id})
    await db.settings.delete_many({"tenant_id": tenant_id})
    await db.tenants.delete_one({"id": tenant_id})
    
    await log_audit(current_user["id"], "delete", "tenant", tenant_id)
    
    return {"message": "Firma dhe të gjitha të dhënat u fshinë me sukses"}


@router.get("/public/{tenant_name}", response_model=TenantPublicInfo)
async def get_tenant_public_info(tenant_name: str):
    """Get public tenant info for branding (no auth required)"""
    tenant = await db.tenants.find_one({"name": tenant_name.lower()}, {"_id": 0})
    if not tenant:
        raise HTTPException(status_code=404, detail="Firma nuk u gjet")
    
    return TenantPublicInfo(
        id=tenant["id"],
        name=tenant["name"],
        company_name=tenant["company_name"],
        logo_url=tenant.get("logo_url"),
        whatsapp_qr_url=tenant.get("whatsapp_qr_url"),
        primary_color=tenant["primary_color"],
        secondary_color=tenant["secondary_color"]
    )


@router.post("/{tenant_id}/regenerate-qr")
async def regenerate_whatsapp_qr(tenant_id: str, current_user: dict = Depends(get_current_user)):
    """Regenerate WhatsApp QR code for a tenant - Super Admin only"""
    if current_user.get("role") != UserRole.SUPER_ADMIN and current_user.get("role") != "super_admin":
        raise HTTPException(status_code=403, detail="Vetëm Super Admin ka akses")
    
    tenant = await db.tenants.find_one({"id": tenant_id})
    if not tenant:
        raise HTTPException(status_code=404, detail="Firma nuk u gjet")
    
    phone = tenant.get("phone")
    if not phone:
        raise HTTPException(status_code=400, detail="Firma nuk ka numër telefoni")
    
    qr_url = generate_whatsapp_qr(phone)
    await db.tenants.update_one({"id": tenant_id}, {"$set": {"whatsapp_qr_url": qr_url}})
    
    return {"message": "QR code u ri-gjenerua me sukses", "whatsapp_qr_url": qr_url}
