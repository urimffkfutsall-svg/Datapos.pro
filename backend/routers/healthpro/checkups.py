"""
HealthPRO - Medical Checkups Management Router
"""
from fastapi import APIRouter, HTTPException, Query, Header
from typing import List, Optional
from datetime import datetime, timezone
from dateutil.relativedelta import relativedelta
import uuid
import jwt
import os

from database import db
from .models import (
    CheckupCreate, CheckupUpdate, CheckupResponse, CheckupStatus, CheckupType
)

router = APIRouter(prefix="/healthpro/checkups", tags=["HealthPRO Checkups"])

SECRET_KEY = os.environ.get("JWT_SECRET", "healthpro-secret-key-2026")
ALGORITHM = "HS256"


async def get_current_hp_user(authorization: str = Header(None)):
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Jo i autorizuar")
    token = authorization.replace("Bearer ", "")
    try:
        return jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
    except:
        raise HTTPException(status_code=401, detail="Token i pavlefshëm")


@router.post("", response_model=CheckupResponse)
async def create_checkup(checkup: CheckupCreate, authorization: str = Header(None)):
    """Create a new medical checkup"""
    user = await get_current_hp_user(authorization)
    tenant_id = user.get("tenant_id")
    
    # Verify resident exists
    resident = await db.hp_residents.find_one(
        {"id": checkup.resident_id, "tenant_id": tenant_id},
        {"_id": 0, "first_name": 1, "last_name": 1}
    )
    if not resident:
        raise HTTPException(status_code=404, detail="Rezidenti nuk u gjet")
    
    checkup_id = str(uuid.uuid4())
    now = datetime.now(timezone.utc).isoformat()
    
    checkup_doc = {
        "id": checkup_id,
        "tenant_id": tenant_id,
        **checkup.model_dump(),
        "status": CheckupStatus.PLANNED,
        "created_at": now,
        "created_by": user.get("sub")
    }
    
    await db.hp_checkups.insert_one(checkup_doc)
    
    return CheckupResponse(
        id=checkup_id,
        tenant_id=tenant_id,
        status=CheckupStatus.PLANNED,
        created_at=now,
        resident_name=f"{resident.get('first_name', '')} {resident.get('last_name', '')}".strip(),
        **checkup.model_dump()
    )


@router.get("", response_model=List[CheckupResponse])
async def list_checkups(
    resident_id: Optional[str] = Query(None),
    status: Optional[CheckupStatus] = Query(None),
    checkup_type: Optional[CheckupType] = Query(None),
    from_date: Optional[str] = Query(None),
    to_date: Optional[str] = Query(None),
    limit: int = Query(100, ge=1, le=500),
    authorization: str = Header(None)
):
    """List all checkups"""
    user = await get_current_hp_user(authorization)
    tenant_id = user.get("tenant_id")
    
    query = {"tenant_id": tenant_id}
    
    if resident_id:
        query["resident_id"] = resident_id
    if status:
        query["status"] = status
    if checkup_type:
        query["checkup_type"] = checkup_type
    if from_date:
        query["scheduled_date"] = {"$gte": from_date}
    if to_date:
        if "scheduled_date" in query:
            query["scheduled_date"]["$lte"] = to_date
        else:
            query["scheduled_date"] = {"$lte": to_date}
    
    cursor = db.hp_checkups.find(query, {"_id": 0}).sort("scheduled_date", -1).limit(limit)
    checkups = await cursor.to_list(length=limit)
    
    # Get resident names
    resident_ids = list(set(c.get("resident_id") for c in checkups if c.get("resident_id")))
    residents = {}
    if resident_ids:
        res_cursor = db.hp_residents.find({"id": {"$in": resident_ids}}, {"_id": 0, "id": 1, "first_name": 1, "last_name": 1})
        async for r in res_cursor:
            residents[r["id"]] = f"{r.get('first_name', '')} {r.get('last_name', '')}".strip()
    
    return [
        CheckupResponse(
            id=c["id"],
            tenant_id=c["tenant_id"],
            resident_id=c.get("resident_id", ""),
            checkup_type=c.get("checkup_type", CheckupType.GENERAL),
            scheduled_date=c.get("scheduled_date", ""),
            scheduled_time=c.get("scheduled_time"),
            institution=c.get("institution"),
            doctor_name=c.get("doctor_name"),
            notes=c.get("notes"),
            results=c.get("results"),
            recommendations=c.get("recommendations"),
            is_systematic=c.get("is_systematic", False),
            status=c.get("status", CheckupStatus.PLANNED),
            created_at=c.get("created_at", ""),
            completed_at=c.get("completed_at"),
            resident_name=residents.get(c.get("resident_id"), "")
        )
        for c in checkups
    ]


@router.put("/{checkup_id}", response_model=CheckupResponse)
async def update_checkup(checkup_id: str, update: CheckupUpdate, authorization: str = Header(None)):
    """Update a checkup"""
    user = await get_current_hp_user(authorization)
    tenant_id = user.get("tenant_id")
    
    existing = await db.hp_checkups.find_one({"id": checkup_id, "tenant_id": tenant_id})
    if not existing:
        raise HTTPException(status_code=404, detail="Kontrolla nuk u gjet")
    
    update_data = {k: v for k, v in update.model_dump().items() if v is not None}
    
    # If status changed to completed, set completed_at
    if update_data.get("status") == CheckupStatus.COMPLETED:
        update_data["completed_at"] = datetime.now(timezone.utc).isoformat()
    
    await db.hp_checkups.update_one(
        {"id": checkup_id, "tenant_id": tenant_id},
        {"$set": update_data}
    )
    
    updated = await db.hp_checkups.find_one({"id": checkup_id}, {"_id": 0})
    
    # Get resident name
    resident = await db.hp_residents.find_one(
        {"id": updated.get("resident_id")},
        {"_id": 0, "first_name": 1, "last_name": 1}
    )
    
    return CheckupResponse(
        id=updated["id"],
        tenant_id=updated["tenant_id"],
        resident_id=updated.get("resident_id", ""),
        checkup_type=updated.get("checkup_type", CheckupType.GENERAL),
        scheduled_date=updated.get("scheduled_date", ""),
        scheduled_time=updated.get("scheduled_time"),
        institution=updated.get("institution"),
        doctor_name=updated.get("doctor_name"),
        notes=updated.get("notes"),
        results=updated.get("results"),
        recommendations=updated.get("recommendations"),
        is_systematic=updated.get("is_systematic", False),
        status=updated.get("status", CheckupStatus.PLANNED),
        created_at=updated.get("created_at", ""),
        completed_at=updated.get("completed_at"),
        resident_name=f"{resident.get('first_name', '')} {resident.get('last_name', '')}".strip() if resident else ""
    )


@router.delete("/{checkup_id}")
async def delete_checkup(checkup_id: str, authorization: str = Header(None)):
    """Delete a checkup"""
    user = await get_current_hp_user(authorization)
    tenant_id = user.get("tenant_id")
    
    result = await db.hp_checkups.delete_one({"id": checkup_id, "tenant_id": tenant_id})
    if result.deleted_count == 0:
        raise HTTPException(status_code=404, detail="Kontrolla nuk u gjet")
    
    return {"message": "Kontrolla u fshi me sukses"}


@router.post("/generate-systematic")
async def generate_systematic_checkups(authorization: str = Header(None)):
    """Generate systematic checkups for all active residents (every 6 months)"""
    user = await get_current_hp_user(authorization)
    tenant_id = user.get("tenant_id")
    
    if user.get("role") not in ["admin", "super_admin"]:
        raise HTTPException(status_code=403, detail="Vetëm administratori mund të gjenerojë kontrolla sistematike")
    
    # Get all active residents
    residents = await db.hp_residents.find(
        {"tenant_id": tenant_id, "status": "active"},
        {"_id": 0, "id": 1, "first_name": 1, "last_name": 1}
    ).to_list(length=1000)
    
    now = datetime.now(timezone.utc)
    next_checkup_date = (now + relativedelta(months=6)).strftime("%Y-%m-%d")
    created_count = 0
    
    for resident in residents:
        # Check if there's already a planned systematic checkup
        existing = await db.hp_checkups.find_one({
            "resident_id": resident["id"],
            "tenant_id": tenant_id,
            "is_systematic": True,
            "status": CheckupStatus.PLANNED
        })
        
        if not existing:
            checkup_doc = {
                "id": str(uuid.uuid4()),
                "tenant_id": tenant_id,
                "resident_id": resident["id"],
                "checkup_type": CheckupType.GENERAL,
                "scheduled_date": next_checkup_date,
                "is_systematic": True,
                "status": CheckupStatus.PLANNED,
                "notes": "Kontrollë sistematike 6-mujore (e gjeneruar automatikisht)",
                "created_at": now.isoformat()
            }
            await db.hp_checkups.insert_one(checkup_doc)
            created_count += 1
    
    return {
        "message": f"U gjeneruan {created_count} kontrolla sistematike",
        "next_checkup_date": next_checkup_date
    }


@router.get("/upcoming")
async def get_upcoming_checkups(days: int = Query(30, ge=1, le=90), authorization: str = Header(None)):
    """Get upcoming checkups for the next X days"""
    user = await get_current_hp_user(authorization)
    tenant_id = user.get("tenant_id")
    
    today = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    end_date = (datetime.now(timezone.utc) + relativedelta(days=days)).strftime("%Y-%m-%d")
    
    checkups = await db.hp_checkups.find({
        "tenant_id": tenant_id,
        "status": CheckupStatus.PLANNED,
        "scheduled_date": {"$gte": today, "$lte": end_date}
    }, {"_id": 0}).sort("scheduled_date", 1).to_list(length=100)
    
    # Get resident names
    resident_ids = list(set(c.get("resident_id") for c in checkups))
    residents = {}
    if resident_ids:
        async for r in db.hp_residents.find({"id": {"$in": resident_ids}}, {"_id": 0, "id": 1, "first_name": 1, "last_name": 1}):
            residents[r["id"]] = f"{r.get('first_name', '')} {r.get('last_name', '')}".strip()
    
    return [
        {
            **c,
            "resident_name": residents.get(c.get("resident_id"), "")
        }
        for c in checkups
    ]
