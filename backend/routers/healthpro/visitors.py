"""
HealthPRO - Visitor User Management Router
Menaxhimi i përdoruesve vizitorë (read-only access)
"""
from fastapi import APIRouter, HTTPException, Query, Header
from typing import List, Optional
from datetime import datetime, timezone
import uuid
import hashlib
import jwt
import os

from database import db
from .models import VisitorUserCreate, VisitorUserResponse, EmployeeRole

router = APIRouter(prefix="/healthpro/visitors", tags=["HealthPRO Visitors"])

SECRET_KEY = os.environ.get("JWT_SECRET", "healthpro-secret-key-2026")
ALGORITHM = "HS256"


def hash_password(password: str) -> str:
    return hashlib.sha256(password.encode()).hexdigest()


async def get_current_hp_user(authorization: str = Header(None)):
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Jo i autorizuar")
    token = authorization.replace("Bearer ", "")
    try:
        return jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
    except:
        raise HTTPException(status_code=401, detail="Token i pavlefshëm")


@router.post("", response_model=VisitorUserResponse)
async def create_visitor_user(visitor: VisitorUserCreate, authorization: str = Header(None)):
    """Krijo një përdorues vizitor (read-only)"""
    user = await get_current_hp_user(authorization)
    tenant_id = user.get("tenant_id")
    
    # Vetëm admin mund të krijojë vizitorë
    if user.get("role") not in ["admin", "super_admin"]:
        raise HTTPException(status_code=403, detail="Vetëm administratori mund të krijojë vizitorë")
    
    # Kontrollo nëse username ekziston
    existing = await db.hp_users.find_one({"username": visitor.username})
    if existing:
        raise HTTPException(status_code=400, detail="Username tashmë ekziston")
    
    visitor_id = str(uuid.uuid4())
    now = datetime.now(timezone.utc).isoformat()
    
    # Ndaj emrin e plotë në emër dhe mbiemër
    name_parts = visitor.full_name.split()
    first_name = name_parts[0] if name_parts else ""
    last_name = " ".join(name_parts[1:]) if len(name_parts) > 1 else ""
    
    visitor_doc = {
        "id": visitor_id,
        "tenant_id": tenant_id,
        "username": visitor.username,
        "password": hash_password(visitor.password),
        "first_name": first_name,
        "last_name": last_name,
        "email": visitor.email,
        "role": EmployeeRole.VISITOR.value,  # Read-only role
        "notes": visitor.notes,
        "is_active": True,
        "status": "active",
        "created_at": now,
        "created_by": user.get("sub")
    }
    
    await db.hp_users.insert_one(visitor_doc)
    
    return VisitorUserResponse(
        id=visitor_id,
        tenant_id=tenant_id,
        username=visitor.username,
        full_name=visitor.full_name,
        email=visitor.email,
        notes=visitor.notes,
        role=EmployeeRole.VISITOR.value,
        is_active=True,
        created_at=now
    )


@router.get("", response_model=List[VisitorUserResponse])
async def list_visitor_users(
    search: Optional[str] = Query(None),
    is_active: Optional[bool] = Query(None),
    limit: int = Query(100, ge=1, le=500),
    authorization: str = Header(None)
):
    """Lista e të gjithë vizitorëve"""
    user = await get_current_hp_user(authorization)
    tenant_id = user.get("tenant_id")
    
    query = {"tenant_id": tenant_id, "role": EmployeeRole.VISITOR.value}
    
    if is_active is not None:
        query["is_active"] = is_active
    
    if search:
        search_regex = {"$regex": search, "$options": "i"}
        query["$or"] = [
            {"first_name": search_regex},
            {"last_name": search_regex},
            {"username": search_regex},
            {"email": search_regex}
        ]
    
    cursor = db.hp_users.find(query, {"_id": 0, "password": 0}).sort("created_at", -1).limit(limit)
    visitors = await cursor.to_list(length=limit)
    
    return [
        VisitorUserResponse(
            id=v["id"],
            tenant_id=v["tenant_id"],
            username=v.get("username", ""),
            full_name=f"{v.get('first_name', '')} {v.get('last_name', '')}".strip(),
            email=v.get("email"),
            notes=v.get("notes"),
            role=v.get("role", "visitor"),
            is_active=v.get("is_active", True),
            created_at=v.get("created_at", "")
        )
        for v in visitors
    ]


@router.get("/{visitor_id}", response_model=VisitorUserResponse)
async def get_visitor_user(visitor_id: str, authorization: str = Header(None)):
    """Merr detajet e një vizitori"""
    user = await get_current_hp_user(authorization)
    tenant_id = user.get("tenant_id")
    
    visitor = await db.hp_users.find_one(
        {"id": visitor_id, "tenant_id": tenant_id, "role": EmployeeRole.VISITOR.value},
        {"_id": 0, "password": 0}
    )
    
    if not visitor:
        raise HTTPException(status_code=404, detail="Vizitori nuk u gjet")
    
    return VisitorUserResponse(
        id=visitor["id"],
        tenant_id=visitor["tenant_id"],
        username=visitor.get("username", ""),
        full_name=f"{visitor.get('first_name', '')} {visitor.get('last_name', '')}".strip(),
        email=visitor.get("email"),
        notes=visitor.get("notes"),
        role=visitor.get("role", "visitor"),
        is_active=visitor.get("is_active", True),
        created_at=visitor.get("created_at", "")
    )


@router.put("/{visitor_id}/toggle-status")
async def toggle_visitor_status(visitor_id: str, authorization: str = Header(None)):
    """Aktivizo/Çaktivizo një vizitor"""
    user = await get_current_hp_user(authorization)
    tenant_id = user.get("tenant_id")
    
    if user.get("role") not in ["admin", "super_admin"]:
        raise HTTPException(status_code=403, detail="Vetëm administratori mund të ndryshojë statusin")
    
    visitor = await db.hp_users.find_one(
        {"id": visitor_id, "tenant_id": tenant_id, "role": EmployeeRole.VISITOR.value},
        {"_id": 0}
    )
    
    if not visitor:
        raise HTTPException(status_code=404, detail="Vizitori nuk u gjet")
    
    new_status = not visitor.get("is_active", True)
    
    await db.hp_users.update_one(
        {"id": visitor_id, "tenant_id": tenant_id},
        {"$set": {"is_active": new_status, "status": "active" if new_status else "inactive"}}
    )
    
    return {
        "message": f"Vizitori u {'aktivizua' if new_status else 'çaktivizua'} me sukses",
        "is_active": new_status
    }


@router.delete("/{visitor_id}")
async def delete_visitor_user(visitor_id: str, authorization: str = Header(None)):
    """Fshi një vizitor përgjithmonë"""
    user = await get_current_hp_user(authorization)
    tenant_id = user.get("tenant_id")
    
    if user.get("role") not in ["admin", "super_admin"]:
        raise HTTPException(status_code=403, detail="Vetëm administratori mund të fshijë")
    
    result = await db.hp_users.delete_one(
        {"id": visitor_id, "tenant_id": tenant_id, "role": EmployeeRole.VISITOR.value}
    )
    
    if result.deleted_count == 0:
        raise HTTPException(status_code=404, detail="Vizitori nuk u gjet")
    
    return {"message": "Vizitori u fshi me sukses"}


@router.put("/{visitor_id}/reset-password")
async def reset_visitor_password(
    visitor_id: str,
    new_password: str = Query(..., min_length=4),
    authorization: str = Header(None)
):
    """Rivendos fjalëkalimin e një vizitori"""
    user = await get_current_hp_user(authorization)
    tenant_id = user.get("tenant_id")
    
    if user.get("role") not in ["admin", "super_admin"]:
        raise HTTPException(status_code=403, detail="Vetëm administratori mund të rivendosë fjalëkalimin")
    
    result = await db.hp_users.update_one(
        {"id": visitor_id, "tenant_id": tenant_id, "role": EmployeeRole.VISITOR.value},
        {"$set": {"password": hash_password(new_password)}}
    )
    
    if result.modified_count == 0:
        raise HTTPException(status_code=404, detail="Vizitori nuk u gjet")
    
    return {"message": "Fjalëkalimi u rivendos me sukses"}
