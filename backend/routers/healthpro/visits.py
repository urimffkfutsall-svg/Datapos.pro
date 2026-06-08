"""
HealthPRO - Visits Management Router (Home & Community)
"""
from fastapi import APIRouter, HTTPException, Query, Header
from typing import List, Optional
from datetime import datetime, timezone, timedelta
import uuid
import jwt
import os

from database import db
from .models import VisitCreate, VisitUpdate, VisitResponse, VisitType

router = APIRouter(prefix="/healthpro/visits", tags=["HealthPRO Visits"])

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


@router.post("", response_model=VisitResponse)
async def create_visit(visit: VisitCreate, authorization: str = Header(None)):
    """Create a new visit"""
    user = await get_current_hp_user(authorization)
    tenant_id = user.get("tenant_id")
    
    # Verify resident exists
    resident = await db.hp_residents.find_one(
        {"id": visit.resident_id, "tenant_id": tenant_id},
        {"_id": 0, "first_name": 1, "last_name": 1}
    )
    if not resident:
        raise HTTPException(status_code=404, detail="Rezidenti nuk u gjet")
    
    visit_id = str(uuid.uuid4())
    now = datetime.now(timezone.utc).isoformat()
    
    visit_doc = {
        "id": visit_id,
        "tenant_id": tenant_id,
        **visit.model_dump(),
        "is_completed": False,
        "created_at": now,
        "created_by": user.get("sub")
    }
    
    await db.hp_visits.insert_one(visit_doc)
    
    # Get staff names
    staff_names = []
    if visit.staff_ids:
        async for s in db.hp_users.find({"id": {"$in": visit.staff_ids}}, {"_id": 0, "first_name": 1, "last_name": 1}):
            staff_names.append(f"{s.get('first_name', '')} {s.get('last_name', '')}".strip())
    
    return VisitResponse(
        id=visit_id,
        tenant_id=tenant_id,
        is_completed=False,
        created_at=now,
        resident_name=f"{resident.get('first_name', '')} {resident.get('last_name', '')}".strip(),
        staff_names=staff_names,
        **visit.model_dump()
    )


@router.get("", response_model=List[VisitResponse])
async def list_visits(
    resident_id: Optional[str] = Query(None),
    visit_type: Optional[VisitType] = Query(None),
    from_date: Optional[str] = Query(None),
    to_date: Optional[str] = Query(None),
    completed: Optional[bool] = Query(None),
    limit: int = Query(100, ge=1, le=500),
    authorization: str = Header(None)
):
    """List visits"""
    user = await get_current_hp_user(authorization)
    tenant_id = user.get("tenant_id")
    
    query = {"tenant_id": tenant_id}
    if resident_id:
        query["resident_id"] = resident_id
    if visit_type:
        query["visit_type"] = visit_type
    if completed is not None:
        query["is_completed"] = completed
    if from_date:
        query["visit_date"] = {"$gte": from_date}
    if to_date:
        if "visit_date" in query:
            query["visit_date"]["$lte"] = to_date
        else:
            query["visit_date"] = {"$lte": to_date}
    
    cursor = db.hp_visits.find(query, {"_id": 0}).sort("visit_date", -1).limit(limit)
    visits = await cursor.to_list(length=limit)
    
    # Get resident and staff names
    resident_ids = list(set(v.get("resident_id") for v in visits))
    residents = {}
    if resident_ids:
        async for r in db.hp_residents.find({"id": {"$in": resident_ids}}, {"_id": 0, "id": 1, "first_name": 1, "last_name": 1}):
            residents[r["id"]] = f"{r.get('first_name', '')} {r.get('last_name', '')}".strip()
    
    # Get all staff IDs
    all_staff_ids = []
    for v in visits:
        all_staff_ids.extend(v.get("staff_ids", []))
    all_staff_ids = list(set(all_staff_ids))
    staff = {}
    if all_staff_ids:
        async for s in db.hp_users.find({"id": {"$in": all_staff_ids}}, {"_id": 0, "id": 1, "first_name": 1, "last_name": 1}):
            staff[s["id"]] = f"{s.get('first_name', '')} {s.get('last_name', '')}".strip()
    
    return [
        VisitResponse(
            id=v["id"],
            tenant_id=v["tenant_id"],
            resident_id=v.get("resident_id", ""),
            visit_type=v.get("visit_type", VisitType.HOME),
            visit_date=v.get("visit_date", ""),
            visit_time=v.get("visit_time"),
            reason=v.get("reason", ""),
            staff_ids=v.get("staff_ids", []),
            result=v.get("result"),
            notes=v.get("notes"),
            address=v.get("address"),
            is_completed=v.get("is_completed", False),
            created_at=v.get("created_at", ""),
            completed_at=v.get("completed_at"),
            resident_name=residents.get(v.get("resident_id"), ""),
            staff_names=[staff.get(sid, "") for sid in v.get("staff_ids", []) if staff.get(sid)]
        )
        for v in visits
    ]


@router.put("/{visit_id}", response_model=VisitResponse)
async def update_visit(visit_id: str, update: VisitUpdate, authorization: str = Header(None)):
    """Update a visit"""
    user = await get_current_hp_user(authorization)
    tenant_id = user.get("tenant_id")
    
    existing = await db.hp_visits.find_one({"id": visit_id, "tenant_id": tenant_id})
    if not existing:
        raise HTTPException(status_code=404, detail="Vizita nuk u gjet")
    
    update_data = {k: v for k, v in update.model_dump().items() if v is not None}
    
    if update_data.get("is_completed"):
        update_data["completed_at"] = datetime.now(timezone.utc).isoformat()
    
    await db.hp_visits.update_one(
        {"id": visit_id, "tenant_id": tenant_id},
        {"$set": update_data}
    )
    
    updated = await db.hp_visits.find_one({"id": visit_id}, {"_id": 0})
    resident = await db.hp_residents.find_one({"id": updated.get("resident_id")}, {"_id": 0, "first_name": 1, "last_name": 1})
    
    staff_names = []
    if updated.get("staff_ids"):
        async for s in db.hp_users.find({"id": {"$in": updated.get("staff_ids", [])}}, {"_id": 0, "first_name": 1, "last_name": 1}):
            staff_names.append(f"{s.get('first_name', '')} {s.get('last_name', '')}".strip())
    
    return VisitResponse(
        id=updated["id"],
        tenant_id=updated["tenant_id"],
        resident_id=updated.get("resident_id", ""),
        visit_type=updated.get("visit_type", VisitType.HOME),
        visit_date=updated.get("visit_date", ""),
        visit_time=updated.get("visit_time"),
        reason=updated.get("reason", ""),
        staff_ids=updated.get("staff_ids", []),
        result=updated.get("result"),
        notes=updated.get("notes"),
        address=updated.get("address"),
        is_completed=updated.get("is_completed", False),
        created_at=updated.get("created_at", ""),
        completed_at=updated.get("completed_at"),
        resident_name=f"{resident.get('first_name', '')} {resident.get('last_name', '')}".strip() if resident else "",
        staff_names=staff_names
    )


@router.delete("/{visit_id}")
async def delete_visit(visit_id: str, authorization: str = Header(None)):
    """Delete a visit"""
    user = await get_current_hp_user(authorization)
    tenant_id = user.get("tenant_id")
    
    result = await db.hp_visits.delete_one({"id": visit_id, "tenant_id": tenant_id})
    if result.deleted_count == 0:
        raise HTTPException(status_code=404, detail="Vizita nuk u gjet")
    
    return {"message": "Vizita u fshi me sukses"}


@router.get("/stats")
async def get_visit_stats(
    period: str = Query("month", regex="^(week|month|year)$"),
    authorization: str = Header(None)
):
    """Get visit statistics"""
    user = await get_current_hp_user(authorization)
    tenant_id = user.get("tenant_id")
    
    now = datetime.now(timezone.utc)
    if period == "week":
        start_date = (now - timedelta(days=7)).strftime("%Y-%m-%d")
    elif period == "month":
        start_date = (now - timedelta(days=30)).strftime("%Y-%m-%d")
    else:
        start_date = (now - timedelta(days=365)).strftime("%Y-%m-%d")
    
    total = await db.hp_visits.count_documents({
        "tenant_id": tenant_id,
        "visit_date": {"$gte": start_date}
    })
    
    home_visits = await db.hp_visits.count_documents({
        "tenant_id": tenant_id,
        "visit_date": {"$gte": start_date},
        "visit_type": "home"
    })
    
    community_visits = await db.hp_visits.count_documents({
        "tenant_id": tenant_id,
        "visit_date": {"$gte": start_date},
        "visit_type": "community"
    })
    
    completed = await db.hp_visits.count_documents({
        "tenant_id": tenant_id,
        "visit_date": {"$gte": start_date},
        "is_completed": True
    })
    
    return {
        "period": period,
        "total": total,
        "home_visits": home_visits,
        "community_visits": community_visits,
        "completed": completed,
        "pending": total - completed
    }
