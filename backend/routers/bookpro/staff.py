"""BookPRO Staff Management Routes"""
from fastapi import APIRouter, HTTPException, Depends
from typing import List, Optional
from datetime import datetime, timezone
import uuid

from .database import bp_users, bp_appointments, bp_working_hours
from .models import (
    BPUserCreate, BPUserUpdate, BPUserResponse, BPUserRole,
    WorkingHoursCreate, WorkingHoursResponse, DayOfWeek
)
from .auth import verify_bp_token
from auth import hash_password

router = APIRouter(prefix="/bookpro/staff", tags=["BookPRO Staff"])


def get_tenant_filter(user: dict) -> dict:
    """Get tenant filter for queries"""
    if user.get("role") == "super_admin":
        return {}
    return {"tenant_id": user.get("tenant_id")}


@router.post("", response_model=BPUserResponse)
async def create_staff(
    staff_data: BPUserCreate,
    current_user: dict = Depends(verify_bp_token)
):
    """Create a new staff member"""
    if current_user.get("role") not in ["admin", "super_admin"]:
        raise HTTPException(status_code=403, detail="Vetëm administratori mund të shtojë staf")
    
    tenant_id = current_user.get("tenant_id")
    if not tenant_id and current_user.get("role") != "super_admin":
        raise HTTPException(status_code=400, detail="Tenant ID mungon")
    
    # Check if username exists
    existing = await bp_users.find_one({"username": staff_data.username}, {"_id": 0})
    if existing:
        raise HTTPException(status_code=400, detail="Ky username ekziston tashmë")
    
    now = datetime.now(timezone.utc)
    
    user = {
        "id": str(uuid.uuid4()),
        "username": staff_data.username,
        "password_hash": hash_password(staff_data.password),
        "full_name": staff_data.full_name,
        "role": staff_data.role.value,
        "phone": staff_data.phone,
        "email": staff_data.email,
        "specializations": staff_data.specializations or [],
        "bio": staff_data.bio,
        "photo_url": staff_data.photo_url,
        "commission_percent": staff_data.commission_percent,
        "is_active": True,
        "tenant_id": tenant_id,
        "created_at": now.isoformat()
    }
    
    await bp_users.insert_one(user)
    
    # Create default working hours (Mon-Sat 09:00-18:00)
    default_days = ["monday", "tuesday", "wednesday", "thursday", "friday", "saturday"]
    for day in default_days:
        working_hour = {
            "id": str(uuid.uuid4()),
            "user_id": user["id"],
            "day_of_week": day,
            "start_time": "09:00",
            "end_time": "18:00",
            "is_working": True,
            "tenant_id": tenant_id
        }
        await bp_working_hours.insert_one(working_hour)
    
    return BPUserResponse(**user)


@router.get("", response_model=List[BPUserResponse])
async def get_staff(
    active_only: bool = True,
    role: Optional[BPUserRole] = None,
    current_user: dict = Depends(verify_bp_token)
):
    """Get all staff members for the tenant"""
    query = get_tenant_filter(current_user)
    
    if active_only:
        query["is_active"] = True
    if role:
        query["role"] = role.value
    
    users = await bp_users.find(query, {"_id": 0, "password_hash": 0}).to_list(100)
    
    result = []
    for user in users:
        appointments_count = await bp_appointments.count_documents({
            "stylist_id": user["id"],
            "status": "completed"
        })
        
        # Calculate total revenue from completed appointments
        completed = await bp_appointments.find({
            "stylist_id": user["id"],
            "status": "completed"
        }, {"_id": 0, "total_price": 1}).to_list(1000)
        
        total_revenue = sum(a.get("total_price", 0) for a in completed)
        
        result.append(BPUserResponse(
            **user,
            appointments_count=appointments_count,
            total_revenue=total_revenue
        ))
    
    return result


@router.get("/{staff_id}", response_model=BPUserResponse)
async def get_staff_member(staff_id: str, current_user: dict = Depends(verify_bp_token)):
    """Get a specific staff member"""
    query = {"id": staff_id, **get_tenant_filter(current_user)}
    user = await bp_users.find_one(query, {"_id": 0, "password_hash": 0})
    
    if not user:
        raise HTTPException(status_code=404, detail="Stafi nuk u gjet")
    
    return BPUserResponse(**user)


@router.put("/{staff_id}", response_model=BPUserResponse)
async def update_staff(
    staff_id: str,
    update_data: BPUserUpdate,
    current_user: dict = Depends(verify_bp_token)
):
    """Update a staff member"""
    if current_user.get("role") not in ["admin", "super_admin"]:
        raise HTTPException(status_code=403, detail="Vetëm administratori mund të modifikojë stafin")
    
    query = {"id": staff_id, **get_tenant_filter(current_user)}
    user = await bp_users.find_one(query, {"_id": 0})
    
    if not user:
        raise HTTPException(status_code=404, detail="Stafi nuk u gjet")
    
    update_dict = {}
    for k, v in update_data.model_dump().items():
        if v is not None:
            if k == "password":
                update_dict["password_hash"] = hash_password(v)
            elif k == "role":
                update_dict[k] = v.value
            else:
                update_dict[k] = v
    
    if update_dict:
        await bp_users.update_one({"id": staff_id}, {"$set": update_dict})
    
    updated = await bp_users.find_one({"id": staff_id}, {"_id": 0, "password_hash": 0})
    return BPUserResponse(**updated)


@router.delete("/{staff_id}")
async def delete_staff(staff_id: str, current_user: dict = Depends(verify_bp_token)):
    """Deactivate a staff member"""
    if current_user.get("role") not in ["admin", "super_admin"]:
        raise HTTPException(status_code=403, detail="Vetëm administratori mund të fshijë stafin")
    
    query = {"id": staff_id, **get_tenant_filter(current_user)}
    user = await bp_users.find_one(query, {"_id": 0})
    
    if not user:
        raise HTTPException(status_code=404, detail="Stafi nuk u gjet")
    
    # Soft delete
    await bp_users.update_one({"id": staff_id}, {"$set": {"is_active": False}})
    
    return {"message": "Stafi u çaktivizua me sukses"}


# Working Hours Routes
@router.get("/{staff_id}/hours", response_model=List[WorkingHoursResponse])
async def get_staff_hours(staff_id: str, current_user: dict = Depends(verify_bp_token)):
    """Get working hours for a staff member"""
    hours = await bp_working_hours.find({
        "user_id": staff_id,
        **get_tenant_filter(current_user)
    }, {"_id": 0}).to_list(7)
    
    return [WorkingHoursResponse(**h) for h in hours]


@router.put("/{staff_id}/hours")
async def update_staff_hours(
    staff_id: str,
    hours: List[WorkingHoursCreate],
    current_user: dict = Depends(verify_bp_token)
):
    """Update working hours for a staff member"""
    if current_user.get("role") not in ["admin", "super_admin"]:
        raise HTTPException(status_code=403, detail="Vetëm administratori mund të ndryshojë oraret")
    
    tenant_filter = get_tenant_filter(current_user)
    
    # Delete existing hours
    await bp_working_hours.delete_many({"user_id": staff_id, **tenant_filter})
    
    # Insert new hours
    for hour in hours:
        working_hour = {
            "id": str(uuid.uuid4()),
            "user_id": staff_id,
            "day_of_week": hour.day_of_week.value,
            "start_time": hour.start_time,
            "end_time": hour.end_time,
            "is_working": hour.is_working,
            "tenant_id": current_user.get("tenant_id")
        }
        await bp_working_hours.insert_one(working_hour)
    
    return {"message": "Oraret u përditësuan me sukses"}
