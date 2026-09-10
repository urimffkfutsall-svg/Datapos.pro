"""BookPRO Tenant Management Routes (Super Admin Only)"""
from fastapi import APIRouter, HTTPException, Depends
from typing import List
from datetime import datetime, timezone, timedelta
import uuid

from .database import bp_tenants, bp_users, bp_clients, bp_appointments
from .models import (
    BPTenantCreate, BPTenantUpdate, BPTenantResponse, 
    BPTenantStatus, BPUserRole
)
from auth import get_current_user, hash_password
from .auth import verify_bp_token

router = APIRouter(prefix="/bookpro/tenants", tags=["BookPRO Tenants"])


def require_super_admin(current_user: dict = Depends(get_current_user)):
    """Require super admin role"""
    if current_user.get("role") != "super_admin":
        raise HTTPException(status_code=403, detail="Vetëm Super Admin ka qasje")
    return current_user


# Endpoint for salon admins to get their own tenant settings
@router.get("/my-salon", response_model=BPTenantResponse)
async def get_my_salon(current_user: dict = Depends(verify_bp_token)):
    """Get current user's salon/tenant settings"""
    tenant_id = current_user.get("tenant_id")
    if not tenant_id:
        raise HTTPException(status_code=400, detail="Nuk jeni i lidhur me asnjë sallon")
    
    tenant = await bp_tenants.find_one({"id": tenant_id}, {"_id": 0})
    if not tenant:
        raise HTTPException(status_code=404, detail="Salloni nuk u gjet")
    
    users_count = await bp_users.count_documents({"tenant_id": tenant_id})
    appointments_count = await bp_appointments.count_documents({"tenant_id": tenant_id})
    clients_count = await bp_clients.count_documents({"tenant_id": tenant_id})
    
    return BPTenantResponse(
        **tenant,
        users_count=users_count,
        appointments_count=appointments_count,
        clients_count=clients_count
    )


@router.put("/my-salon", response_model=BPTenantResponse)
async def update_my_salon(
    update_data: BPTenantUpdate,
    current_user: dict = Depends(verify_bp_token)
):
    """Update current user's salon/tenant settings"""
    if current_user.get("role") not in ["admin", "super_admin"]:
        raise HTTPException(status_code=403, detail="Vetëm administratori mund të ndryshojë cilësimet")
    
    tenant_id = current_user.get("tenant_id")
    if not tenant_id:
        raise HTTPException(status_code=400, detail="Nuk jeni i lidhur me asnjë sallon")
    
    tenant = await bp_tenants.find_one({"id": tenant_id}, {"_id": 0})
    if not tenant:
        raise HTTPException(status_code=404, detail="Salloni nuk u gjet")
    
    update_dict = {k: v for k, v in update_data.model_dump().items() if v is not None}
    
    if update_dict:
        await bp_tenants.update_one({"id": tenant_id}, {"$set": update_dict})
    
    updated_tenant = await bp_tenants.find_one({"id": tenant_id}, {"_id": 0})
    users_count = await bp_users.count_documents({"tenant_id": tenant_id})
    appointments_count = await bp_appointments.count_documents({"tenant_id": tenant_id})
    clients_count = await bp_clients.count_documents({"tenant_id": tenant_id})
    
    return BPTenantResponse(
        **updated_tenant,
        users_count=users_count,
        appointments_count=appointments_count,
        clients_count=clients_count
    )


@router.post("", response_model=BPTenantResponse)
async def create_tenant(
    tenant_data: BPTenantCreate,
    current_user: dict = Depends(require_super_admin)
):
    """Create a new salon tenant"""
    # Check if name already exists
    existing = await bp_tenants.find_one({"name": tenant_data.name}, {"_id": 0})
    if existing:
        raise HTTPException(status_code=400, detail="Ky emër ekziston tashmë")
    
    # Check if admin username exists
    existing_user = await bp_users.find_one({"username": tenant_data.admin_username}, {"_id": 0})
    if existing_user:
        raise HTTPException(status_code=400, detail="Ky username ekziston tashmë")
    
    tenant_id = str(uuid.uuid4())
    now = datetime.now(timezone.utc)
    subscription_expires = now + timedelta(days=30 * tenant_data.subscription_months)
    
    tenant = {
        "id": tenant_id,
        "name": tenant_data.name,
        "salon_name": tenant_data.salon_name,
        "email": tenant_data.email,
        "phone": tenant_data.phone,
        "address": tenant_data.address,
        "city": tenant_data.city,
        "logo_url": tenant_data.logo_url,
        "primary_color": tenant_data.primary_color,
        "secondary_color": tenant_data.secondary_color,
        "status": BPTenantStatus.ACTIVE.value,
        "subscription_expires": subscription_expires.isoformat(),
        "opening_time": "09:00",
        "closing_time": "19:00",
        "working_days": ["monday", "tuesday", "wednesday", "thursday", "friday", "saturday"],
        "created_at": now.isoformat()
    }
    
    await bp_tenants.insert_one(tenant)
    
    # Create admin user for this tenant
    admin_user = {
        "id": str(uuid.uuid4()),
        "username": tenant_data.admin_username,
        "password_hash": hash_password(tenant_data.admin_password),
        "full_name": tenant_data.admin_full_name,
        "role": BPUserRole.ADMIN.value,
        "phone": tenant_data.phone,
        "email": tenant_data.email,
        "specializations": [],
        "commission_percent": 0,
        "is_active": True,
        "tenant_id": tenant_id,
        "created_at": now.isoformat()
    }
    
    await bp_users.insert_one(admin_user)
    
    return BPTenantResponse(
        **tenant,
        users_count=1,
        appointments_count=0,
        clients_count=0
    )


@router.get("", response_model=List[BPTenantResponse])
async def get_tenants(current_user: dict = Depends(require_super_admin)):
    """Get all salon tenants"""
    tenants = await bp_tenants.find({}, {"_id": 0}).to_list(1000)
    
    result = []
    for tenant in tenants:
        users_count = await bp_users.count_documents({"tenant_id": tenant["id"]})
        appointments_count = await bp_appointments.count_documents({"tenant_id": tenant["id"]})
        clients_count = await bp_clients.count_documents({"tenant_id": tenant["id"]})
        
        result.append(BPTenantResponse(
            **tenant,
            users_count=users_count,
            appointments_count=appointments_count,
            clients_count=clients_count
        ))
    
    return result


@router.get("/{tenant_id}", response_model=BPTenantResponse)
async def get_tenant(tenant_id: str, current_user: dict = Depends(require_super_admin)):
    """Get a specific tenant"""
    tenant = await bp_tenants.find_one({"id": tenant_id}, {"_id": 0})
    if not tenant:
        raise HTTPException(status_code=404, detail="Salloni nuk u gjet")
    
    users_count = await bp_users.count_documents({"tenant_id": tenant_id})
    appointments_count = await bp_appointments.count_documents({"tenant_id": tenant_id})
    clients_count = await bp_clients.count_documents({"tenant_id": tenant_id})
    
    return BPTenantResponse(
        **tenant,
        users_count=users_count,
        appointments_count=appointments_count,
        clients_count=clients_count
    )


@router.put("/{tenant_id}", response_model=BPTenantResponse)
async def update_tenant(
    tenant_id: str,
    update_data: BPTenantUpdate,
    current_user: dict = Depends(require_super_admin)
):
    """Update a tenant"""
    tenant = await bp_tenants.find_one({"id": tenant_id}, {"_id": 0})
    if not tenant:
        raise HTTPException(status_code=404, detail="Salloni nuk u gjet")
    
    update_dict = {k: v for k, v in update_data.model_dump().items() if v is not None}
    
    if update_dict:
        await bp_tenants.update_one({"id": tenant_id}, {"$set": update_dict})
    
    updated_tenant = await bp_tenants.find_one({"id": tenant_id}, {"_id": 0})
    users_count = await bp_users.count_documents({"tenant_id": tenant_id})
    appointments_count = await bp_appointments.count_documents({"tenant_id": tenant_id})
    clients_count = await bp_clients.count_documents({"tenant_id": tenant_id})
    
    return BPTenantResponse(
        **updated_tenant,
        users_count=users_count,
        appointments_count=appointments_count,
        clients_count=clients_count
    )


@router.delete("/{tenant_id}")
async def delete_tenant(tenant_id: str, current_user: dict = Depends(require_super_admin)):
    """Delete a tenant and all related data"""
    tenant = await bp_tenants.find_one({"id": tenant_id}, {"_id": 0})
    if not tenant:
        raise HTTPException(status_code=404, detail="Salloni nuk u gjet")
    
    # Delete all related data
    await bp_users.delete_many({"tenant_id": tenant_id})
    await bp_clients.delete_many({"tenant_id": tenant_id})
    await bp_appointments.delete_many({"tenant_id": tenant_id})
    await bp_tenants.delete_one({"id": tenant_id})
    
    return {"message": f"Salloni '{tenant['salon_name']}' u fshi me sukses"}


@router.post("/{tenant_id}/extend-subscription")
async def extend_subscription(
    tenant_id: str,
    months: int = 1,
    current_user: dict = Depends(require_super_admin)
):
    """Extend tenant subscription"""
    tenant = await bp_tenants.find_one({"id": tenant_id}, {"_id": 0})
    if not tenant:
        raise HTTPException(status_code=404, detail="Salloni nuk u gjet")
    
    current_expires = tenant.get("subscription_expires")
    if current_expires:
        from dateutil import parser
        expires_date = parser.parse(current_expires)
    else:
        expires_date = datetime.now(timezone.utc)
    
    # If expired, start from now
    if expires_date < datetime.now(timezone.utc):
        expires_date = datetime.now(timezone.utc)
    
    new_expires = expires_date + timedelta(days=30 * months)
    
    await bp_tenants.update_one(
        {"id": tenant_id},
        {"$set": {
            "subscription_expires": new_expires.isoformat(),
            "status": BPTenantStatus.ACTIVE.value
        }}
    )
    
    return {
        "message": f"Abonimi u zgjat me {months} muaj",
        "new_expires": new_expires.isoformat()
    }


@router.get("/my-salon", response_model=BPTenantResponse)
async def get_my_salon(current_user: dict = Depends(verify_bp_token)):
    """Get the current user's salon info"""
    tenant_id = current_user.get("tenant_id")
    if not tenant_id:
        raise HTTPException(status_code=404, detail="Nuk jeni i lidhur me ndonjë sallon")
    
    tenant = await bp_tenants.find_one({"id": tenant_id}, {"_id": 0})
    if not tenant:
        raise HTTPException(status_code=404, detail="Salloni nuk u gjet")
    
    users_count = await bp_users.count_documents({"tenant_id": tenant_id})
    appointments_count = await bp_appointments.count_documents({"tenant_id": tenant_id})
    clients_count = await bp_clients.count_documents({"tenant_id": tenant_id})
    
    return BPTenantResponse(
        **tenant,
        users_count=users_count,
        appointments_count=appointments_count,
        clients_count=clients_count
    )


@router.put("/my-salon")
async def update_my_salon(update_data: dict, current_user: dict = Depends(verify_bp_token)):
    """Update the current user's salon info"""
    tenant_id = current_user.get("tenant_id")
    if not tenant_id:
        raise HTTPException(status_code=404, detail="Nuk jeni i lidhur me ndonjë sallon")
    
    # Only allow certain fields to be updated by salon admin
    allowed_fields = [
        "name", "salon_name", "email", "phone", "address", "city",
        "opening_time", "closing_time", "working_days", "nui", "nf",
        "logo_url", "instagram", "facebook"
    ]
    
    update_dict = {k: v for k, v in update_data.items() if k in allowed_fields and v is not None}
    
    # Validate slug if being updated
    if "name" in update_dict:
        slug = update_dict["name"]
        # Check if slug is unique
        existing = await bp_tenants.find_one({"name": slug, "id": {"$ne": tenant_id}})
        if existing:
            raise HTTPException(status_code=400, detail="Ky identifikues tashmë ekziston")
    
    if update_dict:
        await bp_tenants.update_one({"id": tenant_id}, {"$set": update_dict})
    
    return {"message": "Cilësimet u ruajtën me sukses"}


@router.get("/{tenant_id}/users")
async def get_tenant_users(tenant_id: str, current_user: dict = Depends(require_super_admin)):
    """Get all users for a specific tenant"""
    tenant = await bp_tenants.find_one({"id": tenant_id}, {"_id": 0})
    if not tenant:
        raise HTTPException(status_code=404, detail="Salloni nuk u gjet")
    
    users = await bp_users.find(
        {"tenant_id": tenant_id},
        {"_id": 0, "password_hash": 0}
    ).to_list(100)
    
    return users


@router.post("/{tenant_id}/users")
async def create_tenant_user(tenant_id: str, user_data: dict, current_user: dict = Depends(require_super_admin)):
    """Create a new user for a specific tenant"""
    tenant = await bp_tenants.find_one({"id": tenant_id}, {"_id": 0})
    if not tenant:
        raise HTTPException(status_code=404, detail="Salloni nuk u gjet")
    
    # Validate required fields
    if not user_data.get("username") or not user_data.get("password") or not user_data.get("full_name"):
        raise HTTPException(status_code=400, detail="Username, fjalëkalimi dhe emri janë të detyrueshëm")
    
    # Check if username exists
    existing = await bp_users.find_one({"username": user_data["username"]})
    if existing:
        raise HTTPException(status_code=400, detail="Ky username tashmë ekziston")
    
    # Create user
    new_user = {
        "id": str(uuid.uuid4()),
        "username": user_data["username"],
        "password_hash": hash_password(user_data["password"]),
        "full_name": user_data["full_name"],
        "role": user_data.get("role", "stylist"),
        "phone": user_data.get("phone"),
        "email": user_data.get("email"),
        "specializations": [],
        "commission_percent": 0,
        "is_active": True,
        "tenant_id": tenant_id,
        "created_at": datetime.now(timezone.utc).isoformat()
    }
    
    await bp_users.insert_one(new_user)
    
    # Return without password_hash
    del new_user["password_hash"]
    new_user.pop("_id", None)
    
    return new_user


@router.delete("/{tenant_id}/users/{user_id}")
async def delete_tenant_user(tenant_id: str, user_id: str, current_user: dict = Depends(require_super_admin)):
    """Delete a user from a tenant"""
    user = await bp_users.find_one({"id": user_id, "tenant_id": tenant_id})
    if not user:
        raise HTTPException(status_code=404, detail="Përdoruesi nuk u gjet")
    
    # Don't allow deleting the last admin
    admin_count = await bp_users.count_documents({"tenant_id": tenant_id, "role": "admin"})
    if user.get("role") == "admin" and admin_count <= 1:
        raise HTTPException(status_code=400, detail="Nuk mund të fshini administratorin e fundit")
    
    await bp_users.delete_one({"id": user_id})
    
    return {"message": "Përdoruesi u fshi me sukses"}
