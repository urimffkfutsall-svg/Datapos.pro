"""PhoneSoftware Tenant Management Routes (Super Admin only)"""
from fastapi import APIRouter, HTTPException, Depends
from typing import List
from datetime import datetime, timezone, timedelta
import uuid

from .database import ps_tenants, ps_users, ps_repairs
from .models import (
    PSTenantCreate, PSTenantUpdate, PSTenantResponse,
    PSUserCreate, PSUserResponse, PSUserRole, PSTenantStatus
)
from auth import hash_password, get_current_user, log_audit

router = APIRouter(prefix="/phonesoftware/tenants", tags=["PhoneSoftware Tenants"])


def check_super_admin(current_user: dict):
    """Verify user is super admin"""
    if current_user.get("role") != "super_admin":
        raise HTTPException(status_code=403, detail="Vetëm Super Admin ka akses")


@router.get("", response_model=List[PSTenantResponse])
async def get_all_ps_tenants(current_user: dict = Depends(get_current_user)):
    """Get all PhoneSoftware tenants - Super Admin only"""
    check_super_admin(current_user)
    
    tenants = await ps_tenants.find({}, {"_id": 0}).sort("created_at", -1).to_list(1000)
    
    for tenant in tenants:
        tenant["users_count"] = await ps_users.count_documents({"tenant_id": tenant["id"]})
        tenant["repairs_count"] = await ps_repairs.count_documents({"tenant_id": tenant["id"]})
    
    return tenants


@router.post("", response_model=PSTenantResponse)
async def create_ps_tenant(tenant: PSTenantCreate, current_user: dict = Depends(get_current_user)):
    """Create a new PhoneSoftware tenant - Super Admin only"""
    check_super_admin(current_user)
    
    # Check if name exists
    existing = await ps_tenants.find_one({"name": tenant.name.lower()})
    if existing:
        raise HTTPException(status_code=400, detail="Emri i firmës ekziston tashmë")
    
    # Check if email exists
    existing_email = await ps_tenants.find_one({"email": tenant.email.lower()})
    if existing_email:
        raise HTTPException(status_code=400, detail="Email-i ekziston tashmë")
    
    # Calculate subscription expiration
    subscription_expires = datetime.now(timezone.utc) + timedelta(days=30 * tenant.subscription_months)
    
    tenant_id = str(uuid.uuid4())
    tenant_data = {
        "id": tenant_id,
        "name": tenant.name.lower(),
        "company_name": tenant.company_name,
        "email": tenant.email.lower(),
        "phone": tenant.phone,
        "address": tenant.address,
        "city": tenant.city,
        "logo_url": tenant.logo_url,
        "primary_color": tenant.primary_color,
        "secondary_color": tenant.secondary_color,
        "status": PSTenantStatus.TRIAL if tenant.subscription_months == 1 else PSTenantStatus.ACTIVE,
        "subscription_expires": subscription_expires.isoformat(),
        "created_at": datetime.now(timezone.utc).isoformat(),
        "created_by": current_user["id"]
    }
    
    await ps_tenants.insert_one(tenant_data)
    
    # Create admin user for this tenant
    admin_user = {
        "id": str(uuid.uuid4()),
        "username": tenant.admin_username,
        "password_hash": hash_password(tenant.admin_password),
        "full_name": tenant.admin_full_name,
        "role": PSUserRole.ADMIN,
        "tenant_id": tenant_id,
        "is_active": True,
        "created_at": datetime.now(timezone.utc).isoformat()
    }
    await ps_users.insert_one(admin_user)
    
    await log_audit(current_user["id"], "create", "ps_tenant", tenant_id)
    
    return PSTenantResponse(**tenant_data, users_count=1, repairs_count=0)


@router.get("/{tenant_id}", response_model=PSTenantResponse)
async def get_ps_tenant(tenant_id: str, current_user: dict = Depends(get_current_user)):
    """Get PhoneSoftware tenant details - Super Admin only"""
    check_super_admin(current_user)
    
    tenant = await ps_tenants.find_one({"id": tenant_id}, {"_id": 0})
    if not tenant:
        raise HTTPException(status_code=404, detail="Firma nuk u gjet")
    
    tenant["users_count"] = await ps_users.count_documents({"tenant_id": tenant_id})
    tenant["repairs_count"] = await ps_repairs.count_documents({"tenant_id": tenant_id})
    
    return PSTenantResponse(**tenant)


@router.put("/{tenant_id}", response_model=PSTenantResponse)
async def update_ps_tenant(tenant_id: str, update: PSTenantUpdate, current_user: dict = Depends(get_current_user)):
    """Update PhoneSoftware tenant - Super Admin only"""
    check_super_admin(current_user)
    
    existing = await ps_tenants.find_one({"id": tenant_id})
    if not existing:
        raise HTTPException(status_code=404, detail="Firma nuk u gjet")
    
    update_data = {k: v for k, v in update.model_dump().items() if v is not None}
    
    if update_data:
        await ps_tenants.update_one({"id": tenant_id}, {"$set": update_data})
    
    updated = await ps_tenants.find_one({"id": tenant_id}, {"_id": 0})
    updated["users_count"] = await ps_users.count_documents({"tenant_id": tenant_id})
    updated["repairs_count"] = await ps_repairs.count_documents({"tenant_id": tenant_id})
    
    await log_audit(current_user["id"], "update", "ps_tenant", tenant_id)
    
    return PSTenantResponse(**updated)


@router.delete("/{tenant_id}")
async def delete_ps_tenant(tenant_id: str, current_user: dict = Depends(get_current_user)):
    """Delete PhoneSoftware tenant and all data - Super Admin only"""
    check_super_admin(current_user)
    
    existing = await ps_tenants.find_one({"id": tenant_id})
    if not existing:
        raise HTTPException(status_code=404, detail="Firma nuk u gjet")
    
    from .database import ps_customers, ps_inventory, ps_stock_movements, ps_sales, ps_notifications
    
    # Delete all tenant data
    await ps_users.delete_many({"tenant_id": tenant_id})
    await ps_customers.delete_many({"tenant_id": tenant_id})
    await ps_repairs.delete_many({"tenant_id": tenant_id})
    await ps_inventory.delete_many({"tenant_id": tenant_id})
    await ps_stock_movements.delete_many({"tenant_id": tenant_id})
    await ps_sales.delete_many({"tenant_id": tenant_id})
    await ps_notifications.delete_many({"tenant_id": tenant_id})
    await ps_tenants.delete_one({"id": tenant_id})
    
    await log_audit(current_user["id"], "delete", "ps_tenant", tenant_id)
    
    return {"message": "Firma dhe të gjitha të dhënat u fshinë me sukses"}


# ============ USER MANAGEMENT ============
@router.get("/{tenant_id}/users", response_model=List[PSUserResponse])
async def get_ps_tenant_users(tenant_id: str, current_user: dict = Depends(get_current_user)):
    """Get all users for a PhoneSoftware tenant - Super Admin only"""
    check_super_admin(current_user)
    
    users = await ps_users.find(
        {"tenant_id": tenant_id}, 
        {"_id": 0, "password_hash": 0}
    ).to_list(1000)
    
    return users


@router.post("/{tenant_id}/users", response_model=PSUserResponse)
async def create_ps_tenant_user(tenant_id: str, user_data: PSUserCreate, current_user: dict = Depends(get_current_user)):
    """Create a new user for a PhoneSoftware tenant - Super Admin only"""
    check_super_admin(current_user)
    
    # Verify tenant exists
    tenant = await ps_tenants.find_one({"id": tenant_id})
    if not tenant:
        raise HTTPException(status_code=404, detail="Firma nuk u gjet")
    
    # Check if username exists in this tenant
    existing = await ps_users.find_one({"username": user_data.username, "tenant_id": tenant_id})
    if existing:
        raise HTTPException(status_code=400, detail="Username ekziston tashmë në këtë firmë")
    
    new_user = {
        "id": str(uuid.uuid4()),
        "username": user_data.username,
        "password_hash": hash_password(user_data.password),
        "full_name": user_data.full_name,
        "role": user_data.role,
        "phone": user_data.phone,
        "email": user_data.email,
        "specialization": user_data.specialization,
        "tenant_id": tenant_id,
        "is_active": True,
        "created_at": datetime.now(timezone.utc).isoformat()
    }
    await ps_users.insert_one(new_user)
    
    await log_audit(current_user["id"], "create_ps_user", "ps_user", new_user["id"], {"tenant_id": tenant_id})
    
    # Remove password_hash before returning
    new_user.pop("password_hash", None)
    new_user.pop("_id", None)
    
    return PSUserResponse(**new_user)


@router.delete("/{tenant_id}/users/{user_id}")
async def delete_ps_tenant_user(tenant_id: str, user_id: str, current_user: dict = Depends(get_current_user)):
    """Delete a user from a PhoneSoftware tenant - Super Admin only"""
    check_super_admin(current_user)
    
    result = await ps_users.delete_one({"id": user_id, "tenant_id": tenant_id})
    if result.deleted_count == 0:
        raise HTTPException(status_code=404, detail="Përdoruesi nuk u gjet")
    
    await log_audit(current_user["id"], "delete_ps_user", "ps_user", user_id, {"tenant_id": tenant_id})
    
    return {"message": "Përdoruesi u fshi me sukses"}
