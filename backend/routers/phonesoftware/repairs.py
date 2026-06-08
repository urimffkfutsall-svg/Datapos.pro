"""PhoneSoftware Repair Management Routes"""
from fastapi import APIRouter, HTTPException, Depends, Query
from typing import List, Optional
from datetime import datetime, timezone, timedelta
import uuid

from .database import ps_repairs, ps_customers, ps_users, ps_inventory, ps_stock_movements, get_ps_current_user
from .models import (
    RepairCreate, RepairUpdate, RepairResponse, RepairStatus,
    RepairPartUsed, StockMovementType
)

router = APIRouter(prefix="/phonesoftware/repairs", tags=["PhoneSoftware Repairs"])


async def generate_ticket_number(tenant_id: str) -> str:
    """Generate unique ticket number for repairs"""
    today = datetime.now(timezone.utc).strftime("%Y%m%d")
    
    # Count today's repairs for this tenant
    start_of_day = datetime.now(timezone.utc).replace(hour=0, minute=0, second=0, microsecond=0)
    count = await ps_repairs.count_documents({
        "tenant_id": tenant_id,
        "created_at": {"$gte": start_of_day.isoformat()}
    })
    
    return f"REP-{today}-{str(count + 1).zfill(4)}"


@router.get("", response_model=List[RepairResponse])
async def get_repairs(
    status: Optional[RepairStatus] = None,
    customer_id: Optional[str] = None,
    technician_id: Optional[str] = None,
    date_from: Optional[str] = None,
    date_to: Optional[str] = None,
    search: Optional[str] = None,
    limit: int = Query(default=100, le=500),
    skip: int = 0,
    current_user: dict = Depends(get_ps_current_user)
):
    """Get all repairs for the tenant"""
    tenant_id = current_user.get("tenant_id")
    if not tenant_id and current_user.get("role") != "super_admin":
        raise HTTPException(status_code=403, detail="Nuk keni akses")
    
    query = {}
    if tenant_id:
        query["tenant_id"] = tenant_id
    
    if status:
        query["status"] = status
    if customer_id:
        query["customer_id"] = customer_id
    if technician_id:
        query["technician_id"] = technician_id
    if date_from:
        query["created_at"] = {"$gte": date_from}
    if date_to:
        query.setdefault("created_at", {})["$lte"] = date_to
    if search:
        query["$or"] = [
            {"ticket_number": {"$regex": search, "$options": "i"}},
            {"brand": {"$regex": search, "$options": "i"}},
            {"model": {"$regex": search, "$options": "i"}},
            {"imei": {"$regex": search, "$options": "i"}},
            {"problem_description": {"$regex": search, "$options": "i"}}
        ]
    
    repairs = await ps_repairs.find(query, {"_id": 0}).sort("created_at", -1).skip(skip).limit(limit).to_list(limit)
    
    # Enrich with customer and technician names
    for repair in repairs:
        if repair.get("customer_id"):
            customer = await ps_customers.find_one({"id": repair["customer_id"]}, {"_id": 0})
            if customer:
                repair["customer_name"] = customer.get("full_name")
                repair["customer_phone"] = customer.get("phone")
        
        if repair.get("technician_id"):
            technician = await ps_users.find_one({"id": repair["technician_id"]}, {"_id": 0})
            if technician:
                repair["technician_name"] = technician.get("full_name")
    
    return repairs


@router.get("/stats")
async def get_repair_stats(current_user: dict = Depends(get_ps_current_user)):
    """Get repair statistics for dashboard"""
    tenant_id = current_user.get("tenant_id")
    if not tenant_id and current_user.get("role") != "super_admin":
        raise HTTPException(status_code=403, detail="Nuk keni akses")
    
    query = {"tenant_id": tenant_id} if tenant_id else {}
    
    # Status counts
    status_counts = {}
    for status in RepairStatus:
        count = await ps_repairs.count_documents({**query, "status": status.value})
        status_counts[status.value] = count
    
    # Today's repairs
    today = datetime.now(timezone.utc).replace(hour=0, minute=0, second=0, microsecond=0)
    today_count = await ps_repairs.count_documents({
        **query,
        "created_at": {"$gte": today.isoformat()}
    })
    
    # This week's repairs
    week_ago = today - timedelta(days=7)
    week_count = await ps_repairs.count_documents({
        **query,
        "created_at": {"$gte": week_ago.isoformat()}
    })
    
    # Total revenue from completed repairs
    completed_repairs = await ps_repairs.find(
        {**query, "status": {"$in": ["completed", "delivered"]}},
        {"_id": 0, "total_cost": 1}
    ).to_list(10000)
    total_revenue = sum(r.get("total_cost", 0) for r in completed_repairs)
    
    return {
        "status_counts": status_counts,
        "today_count": today_count,
        "week_count": week_count,
        "total_revenue": total_revenue
    }


@router.post("", response_model=RepairResponse)
async def create_repair(repair: RepairCreate, current_user: dict = Depends(get_ps_current_user)):
    """Create a new repair ticket"""
    tenant_id = current_user.get("tenant_id")
    if not tenant_id:
        raise HTTPException(status_code=403, detail="Nuk keni akses")
    
    # Get customer info - either from database or manual entry
    customer_name = repair.customer_name
    customer_phone = repair.customer_phone
    customer_id = repair.customer_id
    
    if repair.customer_id:
        customer = await ps_customers.find_one({"id": repair.customer_id, "tenant_id": tenant_id})
        if customer:
            customer_name = customer.get("full_name")
            customer_phone = customer.get("phone")
    
    ticket_number = await generate_ticket_number(tenant_id)
    
    repair_data = {
        "id": str(uuid.uuid4()),
        "ticket_number": ticket_number,
        "customer_id": customer_id,
        "customer_name": customer_name,
        "customer_phone": customer_phone,
        "device_type": repair.device_type or "phone",
        "brand": repair.brand,
        "model": repair.model,
        "imei": repair.imei,
        "serial_number": repair.serial_number,
        "color": repair.color,
        "problem_description": repair.problem_description,
        "customer_notes": repair.customer_notes,
        "status": RepairStatus.RECEIVED,
        "technician_id": None,
        "diagnosis": None,
        "repair_notes": None,
        "parts_used": [],
        "labor_cost": 0,
        "parts_cost": 0,
        "total_cost": 0,
        "estimated_cost": repair.estimated_cost,
        "estimated_completion": repair.estimated_completion,
        "warranty_months": repair.warranty_months,
        "warranty_expires": None,
        "accessories_received": repair.accessories_received or [],
        "tenant_id": tenant_id,
        "created_by": current_user["id"],
        "created_at": datetime.now(timezone.utc).isoformat(),
        "updated_at": datetime.now(timezone.utc).isoformat(),
        "completed_at": None,
        "delivered_at": None
    }
    
    await ps_repairs.insert_one(repair_data)
    
    # Remove _id from MongoDB
    repair_data.pop("_id", None)
    
    return RepairResponse(**repair_data)


@router.get("/{repair_id}", response_model=RepairResponse)
async def get_repair(repair_id: str, current_user: dict = Depends(get_ps_current_user)):
    """Get repair details"""
    tenant_id = current_user.get("tenant_id")
    
    query = {"id": repair_id}
    if tenant_id:
        query["tenant_id"] = tenant_id
    
    repair = await ps_repairs.find_one(query, {"_id": 0})
    if not repair:
        raise HTTPException(status_code=404, detail="Riparimi nuk u gjet")
    
    # Enrich with names
    if repair.get("customer_id"):
        customer = await ps_customers.find_one({"id": repair["customer_id"]}, {"_id": 0})
        if customer:
            repair["customer_name"] = customer.get("full_name")
            repair["customer_phone"] = customer.get("phone")
    
    if repair.get("technician_id"):
        technician = await ps_users.find_one({"id": repair["technician_id"]}, {"_id": 0})
        if technician:
            repair["technician_name"] = technician.get("full_name")
    
    return RepairResponse(**repair)


@router.put("/{repair_id}", response_model=RepairResponse)
async def update_repair(repair_id: str, update: RepairUpdate, current_user: dict = Depends(get_ps_current_user)):
    """Update repair ticket"""
    tenant_id = current_user.get("tenant_id")
    
    query = {"id": repair_id}
    if tenant_id:
        query["tenant_id"] = tenant_id
    
    existing = await ps_repairs.find_one(query)
    if not existing:
        raise HTTPException(status_code=404, detail="Riparimi nuk u gjet")
    
    update_data = {k: v for k, v in update.model_dump().items() if v is not None}
    update_data["updated_at"] = datetime.now(timezone.utc).isoformat()
    
    # Handle parts usage
    if update.parts_used:
        parts_cost = 0
        for part in update.parts_used:
            parts_cost += part.total_cost
            
            # Deduct from inventory
            await ps_inventory.update_one(
                {"id": part.part_id, "tenant_id": tenant_id},
                {"$inc": {"quantity": -part.quantity}}
            )
            
            # Log stock movement
            movement = {
                "id": str(uuid.uuid4()),
                "item_id": part.part_id,
                "item_name": part.part_name,
                "quantity": -part.quantity,
                "movement_type": StockMovementType.REPAIR_USE,
                "reference_id": repair_id,
                "reason": f"Përdorur në riparim {existing['ticket_number']}",
                "unit_cost": part.unit_cost,
                "user_id": current_user["id"],
                "user_name": current_user.get("full_name", ""),
                "tenant_id": tenant_id,
                "created_at": datetime.now(timezone.utc).isoformat()
            }
            await ps_stock_movements.insert_one(movement)
        
        update_data["parts_cost"] = parts_cost
        update_data["parts_used"] = [p.model_dump() for p in update.parts_used]
    
    # Calculate total cost
    labor_cost = update_data.get("labor_cost", existing.get("labor_cost", 0))
    parts_cost = update_data.get("parts_cost", existing.get("parts_cost", 0))
    update_data["total_cost"] = labor_cost + parts_cost
    
    # Handle status changes
    if update.status:
        if update.status == RepairStatus.COMPLETED and not existing.get("completed_at"):
            update_data["completed_at"] = datetime.now(timezone.utc).isoformat()
            # Set warranty expiration
            warranty_months = update_data.get("warranty_months", existing.get("warranty_months", 1))
            warranty_expires = datetime.now(timezone.utc) + timedelta(days=30 * warranty_months)
            update_data["warranty_expires"] = warranty_expires.isoformat()
        
        elif update.status == RepairStatus.DELIVERED and not existing.get("delivered_at"):
            update_data["delivered_at"] = datetime.now(timezone.utc).isoformat()
    
    await ps_repairs.update_one(query, {"$set": update_data})
    
    updated = await ps_repairs.find_one(query, {"_id": 0})
    
    # Enrich with names
    if updated.get("customer_id"):
        customer = await ps_customers.find_one({"id": updated["customer_id"]}, {"_id": 0})
        if customer:
            updated["customer_name"] = customer.get("full_name")
            updated["customer_phone"] = customer.get("phone")
    
    if updated.get("technician_id"):
        technician = await ps_users.find_one({"id": updated["technician_id"]}, {"_id": 0})
        if technician:
            updated["technician_name"] = technician.get("full_name")
    
    return RepairResponse(**updated)


@router.delete("/{repair_id}")
async def delete_repair(repair_id: str, current_user: dict = Depends(get_ps_current_user)):
    """Delete repair ticket"""
    tenant_id = current_user.get("tenant_id")
    
    # Only admin/manager can delete
    if current_user.get("role") not in ["super_admin", "admin", "manager"]:
        raise HTTPException(status_code=403, detail="Nuk keni leje për këtë veprim")
    
    query = {"id": repair_id}
    if tenant_id:
        query["tenant_id"] = tenant_id
    
    result = await ps_repairs.delete_one(query)
    if result.deleted_count == 0:
        raise HTTPException(status_code=404, detail="Riparimi nuk u gjet")
    
    return {"message": "Riparimi u fshi me sukses"}


@router.post("/{repair_id}/assign")
async def assign_technician(repair_id: str, technician_id: str, current_user: dict = Depends(get_ps_current_user)):
    """Assign a technician to a repair"""
    tenant_id = current_user.get("tenant_id")
    
    query = {"id": repair_id}
    if tenant_id:
        query["tenant_id"] = tenant_id
    
    existing = await ps_repairs.find_one(query)
    if not existing:
        raise HTTPException(status_code=404, detail="Riparimi nuk u gjet")
    
    # Verify technician exists
    technician = await ps_users.find_one({"id": technician_id, "tenant_id": tenant_id})
    if not technician:
        raise HTTPException(status_code=404, detail="Tekniku nuk u gjet")
    
    await ps_repairs.update_one(
        query,
        {
            "$set": {
                "technician_id": technician_id,
                "status": RepairStatus.IN_PROGRESS if existing["status"] == RepairStatus.RECEIVED.value else existing["status"],
                "updated_at": datetime.now(timezone.utc).isoformat()
            }
        }
    )
    
    return {"message": f"Riparimi u caktua tek {technician['full_name']}"}


@router.get("/history/device/{imei}")
async def get_device_history(imei: str, current_user: dict = Depends(get_ps_current_user)):
    """Get repair history for a device by IMEI"""
    tenant_id = current_user.get("tenant_id")
    
    query = {"imei": imei}
    if tenant_id:
        query["tenant_id"] = tenant_id
    
    repairs = await ps_repairs.find(query, {"_id": 0}).sort("created_at", -1).to_list(100)
    
    return repairs


@router.get("/history/customer/{customer_id}")
async def get_customer_repair_history(customer_id: str, current_user: dict = Depends(get_ps_current_user)):
    """Get repair history for a customer"""
    tenant_id = current_user.get("tenant_id")
    
    query = {"customer_id": customer_id}
    if tenant_id:
        query["tenant_id"] = tenant_id
    
    repairs = await ps_repairs.find(query, {"_id": 0}).sort("created_at", -1).to_list(100)
    
    return repairs
