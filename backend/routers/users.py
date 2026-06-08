"""User management routes"""
from fastapi import APIRouter, HTTPException, Depends
from typing import List
from datetime import datetime, timezone

from database import db
from models import UserCreate, UserUpdate, UserResponse, User, UserRole
from auth import (
    hash_password, get_current_user, require_role,
    get_tenant_filter, add_tenant_id, log_audit
)

router = APIRouter(prefix="/users", tags=["Users"])


@router.post("", response_model=UserResponse)
async def create_user(user_data: UserCreate, current_user: dict = Depends(require_role([UserRole.ADMIN]))):
    """Create a new user"""
    tenant_filter = get_tenant_filter(current_user)
    
    existing = await db.users.find_one({"username": user_data.username, **tenant_filter})
    if existing:
        raise HTTPException(status_code=400, detail="Username ekziston tashmë")
    
    if user_data.pin:
        existing_pin = await db.users.find_one({"pin": user_data.pin, **tenant_filter})
        if existing_pin:
            raise HTTPException(status_code=400, detail="PIN ekziston tashmë")
    
    user = User(**user_data.model_dump(exclude={"password"}))
    doc = user.model_dump()
    doc['password_hash'] = hash_password(user_data.password)
    doc['created_at'] = doc['created_at'].isoformat()
    doc = add_tenant_id(doc, current_user)
    
    await db.users.insert_one(doc)
    await log_audit(current_user["id"], "create_user", "user", user.id)
    
    return UserResponse(**doc)


@router.get("", response_model=List[UserResponse])
async def get_users(
    role: UserRole = None,
    branch_id: str = None,
    current_user: dict = Depends(require_role([UserRole.ADMIN, UserRole.MANAGER]))
):
    """Get all users"""
    query = get_tenant_filter(current_user)
    if role:
        query["role"] = role.value
    if branch_id:
        query["branch_id"] = branch_id
    
    users = await db.users.find(query, {"_id": 0, "password_hash": 0}).to_list(1000)
    return [UserResponse(**u) for u in users]


@router.get("/{user_id}", response_model=UserResponse)
async def get_user(user_id: str, current_user: dict = Depends(get_current_user)):
    """Get a user by ID"""
    query = {"id": user_id, **get_tenant_filter(current_user)}
    user = await db.users.find_one(query, {"_id": 0, "password_hash": 0})
    if not user:
        raise HTTPException(status_code=404, detail="Përdoruesi nuk u gjet")
    return UserResponse(**user)


@router.put("/{user_id}", response_model=UserResponse)
async def update_user(
    user_id: str,
    user_data: UserUpdate,
    current_user: dict = Depends(require_role([UserRole.ADMIN]))
):
    """Update a user"""
    tenant_filter = get_tenant_filter(current_user)
    update_dict = {k: v for k, v in user_data.model_dump().items() if v is not None}
    
    if "password" in update_dict:
        update_dict["password_hash"] = hash_password(update_dict.pop("password"))
    
    if "pin" in update_dict:
        existing_pin = await db.users.find_one({"pin": update_dict["pin"], "id": {"$ne": user_id}, **tenant_filter})
        if existing_pin:
            raise HTTPException(status_code=400, detail="PIN ekziston tashmë")
    
    if update_dict:
        await db.users.update_one({"id": user_id, **tenant_filter}, {"$set": update_dict})
    
    user = await db.users.find_one({"id": user_id, **tenant_filter}, {"_id": 0, "password_hash": 0})
    if not user:
        raise HTTPException(status_code=404, detail="Përdoruesi nuk u gjet")
    
    await log_audit(current_user["id"], "update_user", "user", user_id, update_dict)
    return UserResponse(**user)


@router.delete("/{user_id}")
async def delete_user(user_id: str, current_user: dict = Depends(require_role([UserRole.ADMIN]))):
    """Delete a user"""
    tenant_filter = get_tenant_filter(current_user)
    result = await db.users.delete_one({"id": user_id, **tenant_filter})
    if result.deleted_count == 0:
        raise HTTPException(status_code=404, detail="Përdoruesi nuk u gjet")
    await log_audit(current_user["id"], "delete_user", "user", user_id)
    return {"message": "Përdoruesi u fshi me sukses"}
