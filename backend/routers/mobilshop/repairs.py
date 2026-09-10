"""Mobilshop Repairs Router - Service Management"""
from fastapi import APIRouter, HTTPException, Depends
from typing import List, Optional
from datetime import datetime, timezone
import uuid

from database import db
from auth import get_current_user
from mobilshop_models import (
    RepairTicketCreate, RepairTicketUpdate, RepairTicketResponse,
    RepairStatus, RepairStatusUpdate, PaymentStatus, PaymentMethod
)

router = APIRouter(prefix="/mobilshop/repairs", tags=["Mobilshop Repairs"])


async def generate_ticket_number(tenant_id: str) -> str:
    """Generate unique ticket number"""
    today = datetime.now(timezone.utc).strftime("%Y%m%d")
    
    # Count today's tickets
    count = await db.mobilshop_repairs.count_documents({
        "tenant_id": tenant_id,
        "created_at": {"$regex": f"^{today[:4]}-{today[4:6]}-{today[6:8]}"}
    })
    
    return f"REP-{today}-{count + 1:04d}"


@router.get("", response_model=List[RepairTicketResponse])
async def get_repairs(
    status: Optional[RepairStatus] = None,
    technician_id: Optional[str] = None,
    customer_id: Optional[str] = None,
    search: Optional[str] = None,
    date_from: Optional[str] = None,
    date_to: Optional[str] = None,
    current_user: dict = Depends(get_current_user)
):
    """Get all repair tickets with optional filters"""
    tenant_id = current_user.get("tenant_id")
    user_role = current_user.get("role")
    
    query = {"tenant_id": tenant_id}
    
    # Technicians can only see their assigned repairs
    if user_role == "technician":
        query["technician_id"] = current_user.get("id")
    elif technician_id:
        query["technician_id"] = technician_id
    
    if status:
        query["status"] = status
    if customer_id:
        query["customer_id"] = customer_id
    if search:
        query["$or"] = [
            {"ticket_number": {"$regex": search, "$options": "i"}},
            {"device_imei": {"$regex": search, "$options": "i"}},
            {"device_brand": {"$regex": search, "$options": "i"}},
            {"device_model": {"$regex": search, "$options": "i"}},
            {"customer_name": {"$regex": search, "$options": "i"}},
            {"customer_phone": {"$regex": search, "$options": "i"}}
        ]
    if date_from:
        query["created_at"] = {"$gte": date_from}
    if date_to:
        if "created_at" in query:
            query["created_at"]["$lte"] = date_to
        else:
            query["created_at"] = {"$lte": date_to}
    
    repairs = await db.mobilshop_repairs.find(query, {"_id": 0}).sort("created_at", -1).to_list(1000)
    
    return repairs


@router.get("/pending")
async def get_pending_repairs(current_user: dict = Depends(get_current_user)):
    """Get count of repairs by status"""
    tenant_id = current_user.get("tenant_id")
    
    statuses = [
        RepairStatus.RECEIVED,
        RepairStatus.DIAGNOSING,
        RepairStatus.WAITING_PARTS,
        RepairStatus.REPAIRING,
        RepairStatus.COMPLETED
    ]
    
    counts = {}
    for status in statuses:
        count = await db.mobilshop_repairs.count_documents({
            "tenant_id": tenant_id,
            "status": status
        })
        counts[status] = count
    
    return counts


@router.get("/by-status/{status}", response_model=List[RepairTicketResponse])
async def get_repairs_by_status(
    status: RepairStatus,
    current_user: dict = Depends(get_current_user)
):
    """Get repairs by specific status"""
    tenant_id = current_user.get("tenant_id")
    
    repairs = await db.mobilshop_repairs.find(
        {"tenant_id": tenant_id, "status": status},
        {"_id": 0}
    ).sort("created_at", -1).to_list(500)
    
    return repairs


@router.get("/{repair_id}", response_model=RepairTicketResponse)
async def get_repair(
    repair_id: str,
    current_user: dict = Depends(get_current_user)
):
    """Get a single repair ticket"""
    tenant_id = current_user.get("tenant_id")
    
    repair = await db.mobilshop_repairs.find_one(
        {"id": repair_id, "tenant_id": tenant_id},
        {"_id": 0}
    )
    
    if not repair:
        raise HTTPException(status_code=404, detail="Riparimi nuk u gjet")
    
    return repair


@router.post("", response_model=RepairTicketResponse)
async def create_repair(
    data: RepairTicketCreate,
    current_user: dict = Depends(get_current_user)
):
    """Create a new repair ticket"""
    tenant_id = current_user.get("tenant_id")
    
    # Verify customer exists
    customer = await db.mobilshop_customers.find_one(
        {"id": data.customer_id, "tenant_id": tenant_id},
        {"_id": 0}
    )
    if not customer:
        raise HTTPException(status_code=404, detail="Klienti nuk u gjet")
    
    # Get technician name if assigned
    technician_name = None
    if data.technician_id:
        technician = await db.users.find_one(
            {"id": data.technician_id, "tenant_id": tenant_id},
            {"_id": 0, "full_name": 1}
        )
        technician_name = technician["full_name"] if technician else None
    
    now = datetime.now(timezone.utc).isoformat()
    ticket_number = await generate_ticket_number(tenant_id)
    
    repair = {
        "id": str(uuid.uuid4()),
        "tenant_id": tenant_id,
        "ticket_number": ticket_number,
        "customer_id": data.customer_id,
        "customer_name": customer["full_name"],
        "customer_phone": customer["phone"],
        "device_brand": data.device_brand,
        "device_model": data.device_model,
        "device_imei": data.device_imei,
        "device_color": data.device_color,
        "device_password": data.device_password,
        "issue_description": data.issue_description,
        "accessories_received": data.accessories_received,
        "status": RepairStatus.RECEIVED,
        "diagnosis": None,
        "parts_used": [],
        "labor_cost": 0,
        "parts_cost": 0,
        "total_cost": 0,
        "estimated_cost": data.estimated_cost,
        "estimated_completion": data.estimated_completion,
        "actual_completion": None,
        "technician_id": data.technician_id,
        "technician_name": technician_name,
        "priority": data.priority,
        "notes": data.notes,
        "payment_status": PaymentStatus.PENDING,
        "payment_method": None,
        "amount_paid": 0,
        "status_history": [
            {
                "status": RepairStatus.RECEIVED,
                "timestamp": now,
                "user_id": current_user.get("id"),
                "user_name": current_user.get("full_name"),
                "notes": "Pajisja u pranua"
            }
        ],
        "created_at": now,
        "updated_at": now,
        "created_by": current_user.get("id")
    }
    
    await db.mobilshop_repairs.insert_one(repair)
    repair.pop("_id", None)
    
    return repair


@router.put("/{repair_id}", response_model=RepairTicketResponse)
async def update_repair(
    repair_id: str,
    data: RepairTicketUpdate,
    current_user: dict = Depends(get_current_user)
):
    """Update a repair ticket"""
    tenant_id = current_user.get("tenant_id")
    
    repair = await db.mobilshop_repairs.find_one(
        {"id": repair_id, "tenant_id": tenant_id}
    )
    if not repair:
        raise HTTPException(status_code=404, detail="Riparimi nuk u gjet")
    
    update_data = {k: v for k, v in data.model_dump().items() if v is not None}
    if not update_data:
        raise HTTPException(status_code=400, detail="Asnjë të dhënë për përditësim")
    
    now = datetime.now(timezone.utc).isoformat()
    update_data["updated_at"] = now
    
    # Calculate total cost if parts or labor updated
    if "labor_cost" in update_data or "parts_cost" in update_data:
        labor = update_data.get("labor_cost", repair.get("labor_cost", 0))
        parts = update_data.get("parts_cost", repair.get("parts_cost", 0))
        update_data["total_cost"] = labor + parts
    
    # Get technician name if assigning
    if data.technician_id:
        technician = await db.users.find_one(
            {"id": data.technician_id, "tenant_id": tenant_id},
            {"_id": 0, "full_name": 1}
        )
        update_data["technician_name"] = technician["full_name"] if technician else None
    
    # Add to status history if status changed
    if data.status and data.status != repair.get("status"):
        status_entry = {
            "status": data.status,
            "timestamp": now,
            "user_id": current_user.get("id"),
            "user_name": current_user.get("full_name"),
            "notes": data.notes or f"Statusi u ndryshua në {data.status}"
        }
        await db.mobilshop_repairs.update_one(
            {"id": repair_id},
            {"$push": {"status_history": status_entry}}
        )
        
        # Set completion date if completed
        if data.status == RepairStatus.COMPLETED:
            update_data["actual_completion"] = now
    
    await db.mobilshop_repairs.update_one(
        {"id": repair_id, "tenant_id": tenant_id},
        {"$set": update_data}
    )
    
    updated_repair = await db.mobilshop_repairs.find_one(
        {"id": repair_id, "tenant_id": tenant_id},
        {"_id": 0}
    )
    
    return updated_repair


@router.patch("/{repair_id}/status", response_model=RepairTicketResponse)
async def update_repair_status(
    repair_id: str,
    data: RepairStatusUpdate,
    current_user: dict = Depends(get_current_user)
):
    """Quick status update for a repair"""
    tenant_id = current_user.get("tenant_id")
    
    repair = await db.mobilshop_repairs.find_one(
        {"id": repair_id, "tenant_id": tenant_id}
    )
    if not repair:
        raise HTTPException(status_code=404, detail="Riparimi nuk u gjet")
    
    now = datetime.now(timezone.utc).isoformat()
    
    # Status flow names in Albanian
    status_names = {
        RepairStatus.RECEIVED: "Pranuar",
        RepairStatus.DIAGNOSING: "Në Diagnozë",
        RepairStatus.WAITING_PARTS: "Në Pritje të Pjesëve",
        RepairStatus.REPAIRING: "Në Riparim",
        RepairStatus.COMPLETED: "Përfunduar",
        RepairStatus.DELIVERED: "Dorëzuar",
        RepairStatus.CANCELLED: "Anuluar"
    }
    
    status_entry = {
        "status": data.status,
        "timestamp": now,
        "user_id": current_user.get("id"),
        "user_name": current_user.get("full_name"),
        "notes": data.notes or f"Statusi u ndryshua në {status_names.get(data.status, data.status)}"
    }
    
    update_data = {
        "status": data.status,
        "updated_at": now
    }
    
    if data.status == RepairStatus.COMPLETED:
        update_data["actual_completion"] = now
    
    await db.mobilshop_repairs.update_one(
        {"id": repair_id, "tenant_id": tenant_id},
        {
            "$set": update_data,
            "$push": {"status_history": status_entry}
        }
    )
    
    updated_repair = await db.mobilshop_repairs.find_one(
        {"id": repair_id, "tenant_id": tenant_id},
        {"_id": 0}
    )
    
    return updated_repair


@router.post("/{repair_id}/payment")
async def record_payment(
    repair_id: str,
    amount: float,
    payment_method: PaymentMethod,
    current_user: dict = Depends(get_current_user)
):
    """Record a payment for a repair"""
    tenant_id = current_user.get("tenant_id")
    
    repair = await db.mobilshop_repairs.find_one(
        {"id": repair_id, "tenant_id": tenant_id}
    )
    if not repair:
        raise HTTPException(status_code=404, detail="Riparimi nuk u gjet")
    
    new_amount_paid = repair.get("amount_paid", 0) + amount
    total_cost = repair.get("total_cost", 0)
    
    if new_amount_paid >= total_cost:
        payment_status = PaymentStatus.PAID
    elif new_amount_paid > 0:
        payment_status = PaymentStatus.PARTIAL
    else:
        payment_status = PaymentStatus.PENDING
    
    await db.mobilshop_repairs.update_one(
        {"id": repair_id, "tenant_id": tenant_id},
        {
            "$set": {
                "amount_paid": new_amount_paid,
                "payment_status": payment_status,
                "payment_method": payment_method,
                "updated_at": datetime.now(timezone.utc).isoformat()
            }
        }
    )
    
    return {
        "amount_paid": new_amount_paid,
        "total_cost": total_cost,
        "remaining": max(0, total_cost - new_amount_paid),
        "payment_status": payment_status
    }


@router.get("/customer/{customer_id}/devices")
async def get_customer_devices(
    customer_id: str,
    current_user: dict = Depends(get_current_user)
):
    """Get all devices a customer has brought for repair"""
    tenant_id = current_user.get("tenant_id")
    
    repairs = await db.mobilshop_repairs.find(
        {"customer_id": customer_id, "tenant_id": tenant_id},
        {"_id": 0, "device_brand": 1, "device_model": 1, "device_imei": 1, "created_at": 1, "status": 1}
    ).sort("created_at", -1).to_list(100)
    
    # Get unique devices
    devices = {}
    for r in repairs:
        key = f"{r['device_brand']}_{r['device_model']}_{r.get('device_imei', '')}"
        if key not in devices:
            devices[key] = {
                "brand": r["device_brand"],
                "model": r["device_model"],
                "imei": r.get("device_imei"),
                "repair_count": 1,
                "last_repair": r["created_at"]
            }
        else:
            devices[key]["repair_count"] += 1
    
    return list(devices.values())
