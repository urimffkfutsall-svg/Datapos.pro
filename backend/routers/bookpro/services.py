"""BookPRO Services Management Routes"""
from fastapi import APIRouter, HTTPException, Depends
from typing import List, Optional
from datetime import datetime, timezone
import uuid

from .database import bp_services, bp_tenants, bp_appointments
from .models import (
    BPServiceCreate, BPServiceUpdate, BPServiceResponse, ServiceCategory
)
from .auth import verify_bp_token

router = APIRouter(prefix="/bookpro/services", tags=["BookPRO Services"])


def get_tenant_filter(user: dict) -> dict:
    """Get tenant filter for queries"""
    if user.get("role") == "super_admin":
        return {}
    return {"tenant_id": user.get("tenant_id")}


@router.post("", response_model=BPServiceResponse)
async def create_service(
    service_data: BPServiceCreate,
    current_user: dict = Depends(verify_bp_token)
):
    """Create a new service"""
    if current_user.get("role") not in ["admin", "super_admin"]:
        raise HTTPException(status_code=403, detail="Vetëm administratori mund të shtojë shërbime")
    
    tenant_id = current_user.get("tenant_id")
    if not tenant_id and current_user.get("role") != "super_admin":
        raise HTTPException(status_code=400, detail="Tenant ID mungon")
    
    now = datetime.now(timezone.utc)
    
    service = {
        "id": str(uuid.uuid4()),
        "name": service_data.name,
        "category": service_data.category.value,
        "description": service_data.description,
        "duration_minutes": service_data.duration_minutes,
        "price": service_data.price,
        "deposit_required": service_data.deposit_required,
        "assigned_staff": service_data.assigned_staff or [],
        "is_popular": service_data.is_popular,
        "is_active": True,
        "tenant_id": tenant_id,
        "created_at": now.isoformat()
    }
    
    await bp_services.insert_one(service)
    
    return BPServiceResponse(**service)


@router.get("", response_model=List[BPServiceResponse])
async def get_services(
    category: Optional[ServiceCategory] = None,
    active_only: bool = True,
    current_user: dict = Depends(verify_bp_token)
):
    """Get all services for the tenant"""
    query = get_tenant_filter(current_user)
    
    if category:
        query["category"] = category.value
    if active_only:
        query["is_active"] = True
    
    services = await bp_services.find(query, {"_id": 0}).to_list(500)
    
    result = []
    for service in services:
        bookings_count = await bp_appointments.count_documents({
            "tenant_id": service.get("tenant_id"),
            "services.service_id": service["id"]
        })
        result.append(BPServiceResponse(**service, bookings_count=bookings_count))
    
    return result


@router.get("/{service_id}", response_model=BPServiceResponse)
async def get_service(service_id: str, current_user: dict = Depends(verify_bp_token)):
    """Get a specific service"""
    query = {"id": service_id, **get_tenant_filter(current_user)}
    service = await bp_services.find_one(query, {"_id": 0})
    
    if not service:
        raise HTTPException(status_code=404, detail="Shërbimi nuk u gjet")
    
    return BPServiceResponse(**service)


@router.put("/{service_id}", response_model=BPServiceResponse)
async def update_service(
    service_id: str,
    update_data: BPServiceUpdate,
    current_user: dict = Depends(verify_bp_token)
):
    """Update a service"""
    if current_user.get("role") not in ["admin", "super_admin"]:
        raise HTTPException(status_code=403, detail="Vetëm administratori mund të modifikojë shërbimet")
    
    query = {"id": service_id, **get_tenant_filter(current_user)}
    service = await bp_services.find_one(query, {"_id": 0})
    
    if not service:
        raise HTTPException(status_code=404, detail="Shërbimi nuk u gjet")
    
    update_dict = {}
    for k, v in update_data.model_dump().items():
        if v is not None:
            if k == "category" and v:
                update_dict[k] = v.value
            else:
                update_dict[k] = v
    
    if update_dict:
        await bp_services.update_one({"id": service_id}, {"$set": update_dict})
    
    updated = await bp_services.find_one({"id": service_id}, {"_id": 0})
    return BPServiceResponse(**updated)


@router.delete("/{service_id}")
async def delete_service(service_id: str, current_user: dict = Depends(verify_bp_token)):
    """Delete (deactivate) a service"""
    if current_user.get("role") not in ["admin", "super_admin"]:
        raise HTTPException(status_code=403, detail="Vetëm administratori mund të fshijë shërbimet")
    
    query = {"id": service_id, **get_tenant_filter(current_user)}
    service = await bp_services.find_one(query, {"_id": 0})
    
    if not service:
        raise HTTPException(status_code=404, detail="Shërbimi nuk u gjet")
    
    # Soft delete
    await bp_services.update_one({"id": service_id}, {"$set": {"is_active": False}})
    
    return {"message": "Shërbimi u çaktivizua me sukses"}
