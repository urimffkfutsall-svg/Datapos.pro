"""
HealthPRO - Residents Management Router
"""
from fastapi import APIRouter, HTTPException, Query, Header
from typing import List, Optional
from datetime import datetime, timezone
import uuid
import jwt
import os

from database import db
from .models import (
    ResidentCreate, ResidentUpdate, ResidentResponse, ResidentStatus
)

router = APIRouter(prefix="/healthpro/residents", tags=["HealthPRO Residents"])

SECRET_KEY = os.environ.get("JWT_SECRET", "healthpro-secret-key-2026")
ALGORITHM = "HS256"


async def get_current_hp_user(authorization: str = Header(None)):
    """Extract user from Authorization header"""
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Jo i autorizuar")
    
    token = authorization.replace("Bearer ", "")
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        return payload
    except jwt.ExpiredSignatureError:
        raise HTTPException(status_code=401, detail="Token i skaduar")
    except jwt.InvalidTokenError:
        raise HTTPException(status_code=401, detail="Token i pavlefshëm")


@router.post("", response_model=ResidentResponse)
async def create_resident(
    resident: ResidentCreate,
    authorization: str = Header(None)
):
    """Create a new resident"""
    user = await get_current_hp_user(authorization)
    tenant_id = user.get("tenant_id")
    
    if not tenant_id:
        raise HTTPException(status_code=400, detail="Tenant ID required")
    
    resident_id = str(uuid.uuid4())
    now = datetime.now(timezone.utc).isoformat()
    
    resident_doc = {
        "id": resident_id,
        "tenant_id": tenant_id,
        **resident.model_dump(),
        "status": ResidentStatus.ACTIVE,
        "created_at": now,
        "created_by": user.get("sub")
    }
    
    await db.hp_residents.insert_one(resident_doc)
    
    return ResidentResponse(
        id=resident_id,
        tenant_id=tenant_id,
        status=ResidentStatus.ACTIVE,
        created_at=now,
        **resident.model_dump()
    )


@router.get("", response_model=List[ResidentResponse])
async def list_residents(
    search: Optional[str] = Query(None),
    status: Optional[ResidentStatus] = Query(None),
    limit: int = Query(100, ge=1, le=500),
    skip: int = Query(0, ge=0),
    authorization: str = Header(None)
):
    """List all residents for the tenant"""
    user = await get_current_hp_user(authorization)
    tenant_id = user.get("tenant_id")
    
    query = {"tenant_id": tenant_id}
    
    if status:
        query["status"] = status
    
    if search:
        search_regex = {"$regex": search, "$options": "i"}
        query["$or"] = [
            {"first_name": search_regex},
            {"last_name": search_regex},
            {"personal_id": search_regex},
            {"room_number": search_regex}
        ]
    
    cursor = db.hp_residents.find(query, {"_id": 0}).sort("created_at", -1).skip(skip).limit(limit)
    residents = await cursor.to_list(length=limit)
    
    return [
        ResidentResponse(
            id=r["id"],
            tenant_id=r["tenant_id"],
            first_name=r.get("first_name", ""),
            last_name=r.get("last_name", ""),
            date_of_birth=r.get("date_of_birth"),
            gender=r.get("gender"),
            personal_id=r.get("personal_id"),
            address=r.get("address"),
            phone=r.get("phone"),
            guardian_name=r.get("guardian_name"),
            guardian_phone=r.get("guardian_phone"),
            guardian_relation=r.get("guardian_relation"),
            health_status=r.get("health_status"),
            diagnoses=r.get("diagnoses", []),
            medical_history=r.get("medical_history"),
            allergies=r.get("allergies"),
            blood_type=r.get("blood_type"),
            emergency_contact=r.get("emergency_contact"),
            admission_date=r.get("admission_date"),
            room_number=r.get("room_number"),
            notes=r.get("notes"),
            status=r.get("status", ResidentStatus.ACTIVE),
            created_at=r.get("created_at", ""),
            updated_at=r.get("updated_at")
        )
        for r in residents
    ]


@router.get("/{resident_id}", response_model=ResidentResponse)
async def get_resident(resident_id: str, authorization: str = Header(None)):
    """Get a specific resident"""
    user = await get_current_hp_user(authorization)
    tenant_id = user.get("tenant_id")
    
    resident = await db.hp_residents.find_one(
        {"id": resident_id, "tenant_id": tenant_id},
        {"_id": 0}
    )
    
    if not resident:
        raise HTTPException(status_code=404, detail="Rezidenti nuk u gjet")
    
    return ResidentResponse(
        id=resident["id"],
        tenant_id=resident["tenant_id"],
        first_name=resident.get("first_name", ""),
        last_name=resident.get("last_name", ""),
        date_of_birth=resident.get("date_of_birth"),
        gender=resident.get("gender"),
        personal_id=resident.get("personal_id"),
        address=resident.get("address"),
        phone=resident.get("phone"),
        guardian_name=resident.get("guardian_name"),
        guardian_phone=resident.get("guardian_phone"),
        guardian_relation=resident.get("guardian_relation"),
        health_status=resident.get("health_status"),
        diagnoses=resident.get("diagnoses", []),
        medical_history=resident.get("medical_history"),
        allergies=resident.get("allergies"),
        blood_type=resident.get("blood_type"),
        emergency_contact=resident.get("emergency_contact"),
        admission_date=resident.get("admission_date"),
        room_number=resident.get("room_number"),
        notes=resident.get("notes"),
        status=resident.get("status", ResidentStatus.ACTIVE),
        created_at=resident.get("created_at", ""),
        updated_at=resident.get("updated_at")
    )


@router.put("/{resident_id}", response_model=ResidentResponse)
async def update_resident(
    resident_id: str,
    update: ResidentUpdate,
    authorization: str = Header(None)
):
    """Update a resident"""
    user = await get_current_hp_user(authorization)
    tenant_id = user.get("tenant_id")
    
    # Check if resident exists
    existing = await db.hp_residents.find_one(
        {"id": resident_id, "tenant_id": tenant_id}
    )
    if not existing:
        raise HTTPException(status_code=404, detail="Rezidenti nuk u gjet")
    
    update_data = {k: v for k, v in update.model_dump().items() if v is not None}
    update_data["updated_at"] = datetime.now(timezone.utc).isoformat()
    
    await db.hp_residents.update_one(
        {"id": resident_id, "tenant_id": tenant_id},
        {"$set": update_data}
    )
    
    # Return updated resident
    updated = await db.hp_residents.find_one(
        {"id": resident_id, "tenant_id": tenant_id},
        {"_id": 0}
    )
    
    return ResidentResponse(
        id=updated["id"],
        tenant_id=updated["tenant_id"],
        first_name=updated.get("first_name", ""),
        last_name=updated.get("last_name", ""),
        date_of_birth=updated.get("date_of_birth"),
        gender=updated.get("gender"),
        personal_id=updated.get("personal_id"),
        address=updated.get("address"),
        phone=updated.get("phone"),
        guardian_name=updated.get("guardian_name"),
        guardian_phone=updated.get("guardian_phone"),
        guardian_relation=updated.get("guardian_relation"),
        health_status=updated.get("health_status"),
        diagnoses=updated.get("diagnoses", []),
        medical_history=updated.get("medical_history"),
        allergies=updated.get("allergies"),
        blood_type=updated.get("blood_type"),
        emergency_contact=updated.get("emergency_contact"),
        admission_date=updated.get("admission_date"),
        room_number=updated.get("room_number"),
        notes=updated.get("notes"),
        status=updated.get("status", ResidentStatus.ACTIVE),
        created_at=updated.get("created_at", ""),
        updated_at=updated.get("updated_at")
    )


@router.delete("/{resident_id}")
async def delete_resident(resident_id: str, authorization: str = Header(None)):
    """Delete (deactivate) a resident"""
    user = await get_current_hp_user(authorization)
    tenant_id = user.get("tenant_id")
    
    # Check user role
    if user.get("role") not in ["admin", "super_admin"]:
        raise HTTPException(status_code=403, detail="Vetëm administratori mund të fshijë")
    
    result = await db.hp_residents.update_one(
        {"id": resident_id, "tenant_id": tenant_id},
        {"$set": {"status": ResidentStatus.INACTIVE, "updated_at": datetime.now(timezone.utc).isoformat()}}
    )
    
    if result.modified_count == 0:
        raise HTTPException(status_code=404, detail="Rezidenti nuk u gjet")
    
    return {"message": "Rezidenti u çaktivizua me sukses"}


@router.get("/stats/summary")
async def get_residents_stats(authorization: str = Header(None)):
    """Get residents statistics"""
    user = await get_current_hp_user(authorization)
    tenant_id = user.get("tenant_id")
    
    total = await db.hp_residents.count_documents({"tenant_id": tenant_id})
    active = await db.hp_residents.count_documents({"tenant_id": tenant_id, "status": "active"})
    inactive = await db.hp_residents.count_documents({"tenant_id": tenant_id, "status": "inactive"})
    
    # Gender distribution
    male = await db.hp_residents.count_documents({"tenant_id": tenant_id, "gender": "male", "status": "active"})
    female = await db.hp_residents.count_documents({"tenant_id": tenant_id, "gender": "female", "status": "active"})
    
    return {
        "total": total,
        "active": active,
        "inactive": inactive,
        "male": male,
        "female": female
    }
