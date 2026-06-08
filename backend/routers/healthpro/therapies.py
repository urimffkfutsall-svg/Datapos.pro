"""
HealthPRO - Therapies Management Router
"""
from fastapi import APIRouter, HTTPException, Query, Header
from typing import List, Optional
from datetime import datetime, timezone
import uuid
import jwt
import os

from database import db
from .models import TherapyCreate, TherapyUpdate, TherapyResponse, TherapyType

router = APIRouter(prefix="/healthpro/therapies", tags=["HealthPRO Therapies"])

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


@router.post("", response_model=TherapyResponse)
async def create_therapy(therapy: TherapyCreate, authorization: str = Header(None)):
    """Create a new therapy for a resident"""
    user = await get_current_hp_user(authorization)
    tenant_id = user.get("tenant_id")
    
    # Verify resident exists
    resident = await db.hp_residents.find_one(
        {"id": therapy.resident_id, "tenant_id": tenant_id},
        {"_id": 0, "first_name": 1, "last_name": 1}
    )
    if not resident:
        raise HTTPException(status_code=404, detail="Rezidenti nuk u gjet")
    
    therapy_id = str(uuid.uuid4())
    now = datetime.now(timezone.utc).isoformat()
    
    therapy_doc = {
        "id": therapy_id,
        "tenant_id": tenant_id,
        **therapy.model_dump(),
        "is_active": True,
        "created_at": now,
        "created_by": user.get("sub")
    }
    
    await db.hp_therapies.insert_one(therapy_doc)
    
    return TherapyResponse(
        id=therapy_id,
        tenant_id=tenant_id,
        is_active=True,
        created_at=now,
        resident_name=f"{resident.get('first_name', '')} {resident.get('last_name', '')}".strip(),
        **therapy.model_dump()
    )


@router.get("", response_model=List[TherapyResponse])
async def list_therapies(
    resident_id: Optional[str] = Query(None),
    therapy_type: Optional[TherapyType] = Query(None),
    active_only: bool = Query(True),
    limit: int = Query(100, ge=1, le=500),
    authorization: str = Header(None)
):
    """List therapies"""
    user = await get_current_hp_user(authorization)
    tenant_id = user.get("tenant_id")
    
    query = {"tenant_id": tenant_id}
    if resident_id:
        query["resident_id"] = resident_id
    if therapy_type:
        query["therapy_type"] = therapy_type
    if active_only:
        query["is_active"] = True
    
    cursor = db.hp_therapies.find(query, {"_id": 0}).sort("created_at", -1).limit(limit)
    therapies = await cursor.to_list(length=limit)
    
    # Get resident names
    resident_ids = list(set(t.get("resident_id") for t in therapies))
    residents = {}
    if resident_ids:
        async for r in db.hp_residents.find({"id": {"$in": resident_ids}}, {"_id": 0, "id": 1, "first_name": 1, "last_name": 1}):
            residents[r["id"]] = f"{r.get('first_name', '')} {r.get('last_name', '')}".strip()
    
    return [
        TherapyResponse(
            id=t["id"],
            tenant_id=t["tenant_id"],
            resident_id=t.get("resident_id", ""),
            therapy_type=t.get("therapy_type", TherapyType.MEDICATION),
            name=t.get("name", ""),
            dosage=t.get("dosage"),
            frequency=t.get("frequency"),
            duration=t.get("duration"),
            start_date=t.get("start_date", ""),
            end_date=t.get("end_date"),
            administration_time=t.get("administration_time", []),
            prescribed_by=t.get("prescribed_by"),
            notes=t.get("notes"),
            is_active=t.get("is_active", True),
            created_at=t.get("created_at", ""),
            resident_name=residents.get(t.get("resident_id"), "")
        )
        for t in therapies
    ]


@router.put("/{therapy_id}", response_model=TherapyResponse)
async def update_therapy(therapy_id: str, update: TherapyUpdate, authorization: str = Header(None)):
    """Update a therapy"""
    user = await get_current_hp_user(authorization)
    tenant_id = user.get("tenant_id")
    
    existing = await db.hp_therapies.find_one({"id": therapy_id, "tenant_id": tenant_id})
    if not existing:
        raise HTTPException(status_code=404, detail="Terapia nuk u gjet")
    
    update_data = {k: v for k, v in update.model_dump().items() if v is not None}
    
    await db.hp_therapies.update_one(
        {"id": therapy_id, "tenant_id": tenant_id},
        {"$set": update_data}
    )
    
    updated = await db.hp_therapies.find_one({"id": therapy_id}, {"_id": 0})
    resident = await db.hp_residents.find_one({"id": updated.get("resident_id")}, {"_id": 0, "first_name": 1, "last_name": 1})
    
    return TherapyResponse(
        id=updated["id"],
        tenant_id=updated["tenant_id"],
        resident_id=updated.get("resident_id", ""),
        therapy_type=updated.get("therapy_type", TherapyType.MEDICATION),
        name=updated.get("name", ""),
        dosage=updated.get("dosage"),
        frequency=updated.get("frequency"),
        duration=updated.get("duration"),
        start_date=updated.get("start_date", ""),
        end_date=updated.get("end_date"),
        administration_time=updated.get("administration_time", []),
        prescribed_by=updated.get("prescribed_by"),
        notes=updated.get("notes"),
        is_active=updated.get("is_active", True),
        created_at=updated.get("created_at", ""),
        resident_name=f"{resident.get('first_name', '')} {resident.get('last_name', '')}".strip() if resident else ""
    )


@router.delete("/{therapy_id}")
async def delete_therapy(therapy_id: str, authorization: str = Header(None)):
    """Deactivate a therapy"""
    user = await get_current_hp_user(authorization)
    tenant_id = user.get("tenant_id")
    
    result = await db.hp_therapies.update_one(
        {"id": therapy_id, "tenant_id": tenant_id},
        {"$set": {"is_active": False}}
    )
    
    if result.modified_count == 0:
        raise HTTPException(status_code=404, detail="Terapia nuk u gjet")
    
    return {"message": "Terapia u çaktivizua me sukses"}


@router.get("/daily-schedule")
async def get_daily_therapy_schedule(
    date: Optional[str] = Query(None),
    authorization: str = Header(None)
):
    """Get daily therapy administration schedule"""
    user = await get_current_hp_user(authorization)
    tenant_id = user.get("tenant_id")
    
    if not date:
        date = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    
    # Get all active therapies
    therapies = await db.hp_therapies.find({
        "tenant_id": tenant_id,
        "is_active": True,
        "start_date": {"$lte": date},
        "$or": [
            {"end_date": None},
            {"end_date": {"$gte": date}}
        ]
    }, {"_id": 0}).to_list(length=500)
    
    # Get resident names
    resident_ids = list(set(t.get("resident_id") for t in therapies))
    residents = {}
    if resident_ids:
        async for r in db.hp_residents.find({"id": {"$in": resident_ids}}, {"_id": 0, "id": 1, "first_name": 1, "last_name": 1, "room_number": 1}):
            residents[r["id"]] = {
                "name": f"{r.get('first_name', '')} {r.get('last_name', '')}".strip(),
                "room": r.get("room_number", "")
            }
    
    # Organize by time
    schedule = {}
    for t in therapies:
        for time in t.get("administration_time", []):
            if time not in schedule:
                schedule[time] = []
            resident_info = residents.get(t.get("resident_id"), {})
            schedule[time].append({
                "therapy_id": t["id"],
                "resident_id": t.get("resident_id"),
                "resident_name": resident_info.get("name", ""),
                "room_number": resident_info.get("room", ""),
                "therapy_name": t.get("name"),
                "dosage": t.get("dosage"),
                "therapy_type": t.get("therapy_type")
            })
    
    # Sort by time
    sorted_schedule = dict(sorted(schedule.items()))
    
    return {"date": date, "schedule": sorted_schedule}
