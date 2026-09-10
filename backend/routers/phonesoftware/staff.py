"""PhoneSoftware Staff & Technician Management Routes"""
from fastapi import APIRouter, HTTPException, Depends
from typing import List, Optional
from datetime import datetime, timezone, timedelta
import uuid

from .database import ps_users, ps_repairs, get_ps_current_user
from .models import PSUserCreate, PSUserUpdate, PSUserResponse, PSUserRole, RepairStatus
from auth import hash_password

router = APIRouter(prefix="/phonesoftware/staff", tags=["PhoneSoftware Staff"])


def check_admin_access(current_user: dict):
    """Verify user has admin access"""
    if current_user.get("role") not in ["super_admin", "admin", "manager"]:
        raise HTTPException(status_code=403, detail="Nuk keni leje për këtë veprim")


@router.get("", response_model=List[PSUserResponse])
async def get_staff(current_user: dict = Depends(get_ps_current_user)):
    """Get all staff members for the tenant"""
    tenant_id = current_user.get("tenant_id")
    if not tenant_id and current_user.get("role") != "super_admin":
        raise HTTPException(status_code=403, detail="Nuk keni akses")
    
    query = {}
    if tenant_id:
        query["tenant_id"] = tenant_id
    
    staff = await ps_users.find(query, {"_id": 0, "password_hash": 0}).sort("created_at", -1).to_list(100)
    
    # Enrich with repair counts
    for user in staff:
        user["repairs_completed"] = await ps_repairs.count_documents({
            "technician_id": user["id"],
            "status": {"$in": [RepairStatus.COMPLETED.value, RepairStatus.DELIVERED.value]}
        })
    
    return staff


@router.get("/technicians")
async def get_technicians(current_user: dict = Depends(get_ps_current_user)):
    """Get all technicians for assignment"""
    tenant_id = current_user.get("tenant_id")
    if not tenant_id:
        raise HTTPException(status_code=403, detail="Nuk keni akses")
    
    technicians = await ps_users.find(
        {
            "tenant_id": tenant_id,
            "role": {"$in": [PSUserRole.TECHNICIAN.value, PSUserRole.ADMIN.value, PSUserRole.MANAGER.value]},
            "is_active": True
        },
        {"_id": 0, "password_hash": 0}
    ).to_list(50)
    
    return technicians


@router.get("/performance")
async def get_staff_performance(
    period: str = "week",  # day, week, month
    current_user: dict = Depends(get_ps_current_user)
):
    """Get staff performance metrics"""
    tenant_id = current_user.get("tenant_id")
    if not tenant_id and current_user.get("role") != "super_admin":
        raise HTTPException(status_code=403, detail="Nuk keni akses")
    
    # Calculate date range
    now = datetime.now(timezone.utc)
    if period == "day":
        start_date = now.replace(hour=0, minute=0, second=0, microsecond=0)
    elif period == "week":
        start_date = now - timedelta(days=7)
    else:  # month
        start_date = now - timedelta(days=30)
    
    query = {"tenant_id": tenant_id} if tenant_id else {}
    
    staff = await ps_users.find(query, {"_id": 0, "password_hash": 0}).to_list(100)
    
    performance_data = []
    for user in staff:
        # Get completed repairs in period
        completed = await ps_repairs.count_documents({
            "technician_id": user["id"],
            "status": {"$in": [RepairStatus.COMPLETED.value, RepairStatus.DELIVERED.value]},
            "completed_at": {"$gte": start_date.isoformat()}
        })
        
        # Get in-progress repairs
        in_progress = await ps_repairs.count_documents({
            "technician_id": user["id"],
            "status": RepairStatus.IN_PROGRESS.value
        })
        
        # Get total repairs assigned
        total_assigned = await ps_repairs.count_documents({
            "technician_id": user["id"],
            "created_at": {"$gte": start_date.isoformat()}
        })
        
        # Calculate revenue
        completed_repairs = await ps_repairs.find({
            "technician_id": user["id"],
            "status": {"$in": [RepairStatus.COMPLETED.value, RepairStatus.DELIVERED.value]},
            "completed_at": {"$gte": start_date.isoformat()}
        }, {"_id": 0, "total_cost": 1}).to_list(1000)
        
        revenue = sum(r.get("total_cost", 0) for r in completed_repairs)
        
        performance_data.append({
            "user_id": user["id"],
            "full_name": user.get("full_name"),
            "role": user.get("role"),
            "specialization": user.get("specialization"),
            "completed": completed,
            "in_progress": in_progress,
            "total_assigned": total_assigned,
            "revenue": revenue,
            "completion_rate": round(completed / total_assigned * 100, 1) if total_assigned > 0 else 0
        })
    
    # Sort by completed repairs
    performance_data.sort(key=lambda x: x["completed"], reverse=True)
    
    return {
        "period": period,
        "start_date": start_date.isoformat(),
        "staff_performance": performance_data
    }


@router.post("", response_model=PSUserResponse)
async def create_staff_member(user_data: PSUserCreate, current_user: dict = Depends(get_ps_current_user)):
    """Create a new staff member"""
    tenant_id = current_user.get("tenant_id")
    if not tenant_id:
        raise HTTPException(status_code=403, detail="Nuk keni akses")
    
    check_admin_access(current_user)
    
    # Check if username exists
    existing = await ps_users.find_one({"username": user_data.username, "tenant_id": tenant_id})
    if existing:
        raise HTTPException(status_code=400, detail="Username ekziston tashmë")
    
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
    
    # Remove sensitive data
    new_user.pop("password_hash", None)
    new_user.pop("_id", None)
    
    return PSUserResponse(**new_user, repairs_completed=0)


@router.get("/{user_id}", response_model=PSUserResponse)
async def get_staff_member(user_id: str, current_user: dict = Depends(get_ps_current_user)):
    """Get staff member details"""
    tenant_id = current_user.get("tenant_id")
    
    query = {"id": user_id}
    if tenant_id:
        query["tenant_id"] = tenant_id
    
    user = await ps_users.find_one(query, {"_id": 0, "password_hash": 0})
    if not user:
        raise HTTPException(status_code=404, detail="Përdoruesi nuk u gjet")
    
    user["repairs_completed"] = await ps_repairs.count_documents({
        "technician_id": user_id,
        "status": {"$in": [RepairStatus.COMPLETED.value, RepairStatus.DELIVERED.value]}
    })
    
    return PSUserResponse(**user)


@router.put("/{user_id}", response_model=PSUserResponse)
async def update_staff_member(user_id: str, update: PSUserUpdate, current_user: dict = Depends(get_ps_current_user)):
    """Update staff member"""
    tenant_id = current_user.get("tenant_id")
    
    check_admin_access(current_user)
    
    query = {"id": user_id}
    if tenant_id:
        query["tenant_id"] = tenant_id
    
    existing = await ps_users.find_one(query)
    if not existing:
        raise HTTPException(status_code=404, detail="Përdoruesi nuk u gjet")
    
    update_data = {k: v for k, v in update.model_dump().items() if v is not None}
    
    # Handle password update
    if update.password:
        update_data["password_hash"] = hash_password(update.password)
        del update_data["password"]
    
    if update_data:
        await ps_users.update_one(query, {"$set": update_data})
    
    updated = await ps_users.find_one(query, {"_id": 0, "password_hash": 0})
    updated["repairs_completed"] = await ps_repairs.count_documents({
        "technician_id": user_id,
        "status": {"$in": [RepairStatus.COMPLETED.value, RepairStatus.DELIVERED.value]}
    })
    
    return PSUserResponse(**updated)


@router.delete("/{user_id}")
async def delete_staff_member(user_id: str, current_user: dict = Depends(get_ps_current_user)):
    """Delete (deactivate) staff member"""
    tenant_id = current_user.get("tenant_id")
    
    check_admin_access(current_user)
    
    # Can't delete yourself
    if user_id == current_user["id"]:
        raise HTTPException(status_code=400, detail="Nuk mund të fshini veten")
    
    query = {"id": user_id}
    if tenant_id:
        query["tenant_id"] = tenant_id
    
    result = await ps_users.update_one(query, {"$set": {"is_active": False}})
    
    if result.modified_count == 0:
        raise HTTPException(status_code=404, detail="Përdoruesi nuk u gjet")
    
    return {"message": "Përdoruesi u çaktivizua me sukses"}


@router.get("/{user_id}/repairs")
async def get_staff_repairs(
    user_id: str,
    status: Optional[RepairStatus] = None,
    current_user: dict = Depends(get_ps_current_user)
):
    """Get repairs assigned to a staff member"""
    tenant_id = current_user.get("tenant_id")
    
    query = {"technician_id": user_id}
    if tenant_id:
        query["tenant_id"] = tenant_id
    if status:
        query["status"] = status.value
    
    repairs = await ps_repairs.find(query, {"_id": 0}).sort("created_at", -1).to_list(100)
    
    return repairs
