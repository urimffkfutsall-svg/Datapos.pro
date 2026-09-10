"""BookPRO Clients/CRM Management Routes"""
from fastapi import APIRouter, HTTPException, Depends
from typing import List, Optional
from datetime import datetime, timezone
import uuid

from .database import bp_clients, bp_appointments
from .models import BPClientCreate, BPClientUpdate, BPClientResponse
from .auth import verify_bp_token

router = APIRouter(prefix="/bookpro/clients", tags=["BookPRO Clients"])


def get_tenant_filter(user: dict) -> dict:
    """Get tenant filter for queries"""
    if user.get("role") == "super_admin":
        return {}
    return {"tenant_id": user.get("tenant_id")}


@router.post("", response_model=BPClientResponse)
async def create_client(
    client_data: BPClientCreate,
    current_user: dict = Depends(verify_bp_token)
):
    """Create a new client"""
    tenant_id = current_user.get("tenant_id")
    if not tenant_id and current_user.get("role") != "super_admin":
        raise HTTPException(status_code=400, detail="Tenant ID mungon")
    
    # Check if phone already exists for this tenant
    existing = await bp_clients.find_one({
        "phone": client_data.phone,
        "tenant_id": tenant_id
    }, {"_id": 0})
    
    if existing:
        raise HTTPException(status_code=400, detail="Ky numër telefoni ekziston tashmë")
    
    now = datetime.now(timezone.utc)
    
    client = {
        "id": str(uuid.uuid4()),
        "full_name": client_data.full_name,
        "phone": client_data.phone,
        "email": client_data.email,
        "gender": client_data.gender,
        "birthdate": client_data.birthdate,
        "address": client_data.address,
        "notes": client_data.notes,
        "preferences": client_data.preferences,
        "referral_source": client_data.referral_source,
        "tenant_id": tenant_id,
        "created_at": now.isoformat(),
        "last_visit": None,
        "total_visits": 0,
        "total_spent": 0,
        "loyalty_points": 0
    }
    
    await bp_clients.insert_one(client)
    
    return BPClientResponse(**client)


@router.get("", response_model=List[BPClientResponse])
async def get_clients(
    search: Optional[str] = None,
    limit: int = 100,
    current_user: dict = Depends(verify_bp_token)
):
    """Get all clients for the tenant"""
    query = get_tenant_filter(current_user)
    
    if search:
        query["$or"] = [
            {"full_name": {"$regex": search, "$options": "i"}},
            {"phone": {"$regex": search, "$options": "i"}},
            {"email": {"$regex": search, "$options": "i"}}
        ]
    
    clients = await bp_clients.find(query, {"_id": 0}).sort("created_at", -1).to_list(limit)
    
    return [BPClientResponse(**c) for c in clients]


@router.get("/{client_id}", response_model=BPClientResponse)
async def get_client(client_id: str, current_user: dict = Depends(verify_bp_token)):
    """Get a specific client"""
    query = {"id": client_id, **get_tenant_filter(current_user)}
    client = await bp_clients.find_one(query, {"_id": 0})
    
    if not client:
        raise HTTPException(status_code=404, detail="Klienti nuk u gjet")
    
    return BPClientResponse(**client)


@router.get("/{client_id}/history")
async def get_client_history(client_id: str, current_user: dict = Depends(verify_bp_token)):
    """Get client appointment history"""
    query = {"id": client_id, **get_tenant_filter(current_user)}
    client = await bp_clients.find_one(query, {"_id": 0})
    
    if not client:
        raise HTTPException(status_code=404, detail="Klienti nuk u gjet")
    
    appointments = await bp_appointments.find({
        "client_id": client_id,
        **get_tenant_filter(current_user)
    }, {"_id": 0}).sort("appointment_date", -1).to_list(100)
    
    return {
        "client": client,
        "appointments": appointments,
        "total_visits": client.get("total_visits", 0),
        "total_spent": client.get("total_spent", 0)
    }


@router.put("/{client_id}", response_model=BPClientResponse)
async def update_client(
    client_id: str,
    update_data: BPClientUpdate,
    current_user: dict = Depends(verify_bp_token)
):
    """Update a client"""
    query = {"id": client_id, **get_tenant_filter(current_user)}
    client = await bp_clients.find_one(query, {"_id": 0})
    
    if not client:
        raise HTTPException(status_code=404, detail="Klienti nuk u gjet")
    
    update_dict = {k: v for k, v in update_data.model_dump().items() if v is not None}
    
    if update_dict:
        await bp_clients.update_one({"id": client_id}, {"$set": update_dict})
    
    updated = await bp_clients.find_one({"id": client_id}, {"_id": 0})
    return BPClientResponse(**updated)


@router.delete("/{client_id}")
async def delete_client(client_id: str, current_user: dict = Depends(verify_bp_token)):
    """Delete a client"""
    if current_user.get("role") not in ["admin", "super_admin"]:
        raise HTTPException(status_code=403, detail="Vetëm administratori mund të fshijë klientët")
    
    query = {"id": client_id, **get_tenant_filter(current_user)}
    client = await bp_clients.find_one(query, {"_id": 0})
    
    if not client:
        raise HTTPException(status_code=404, detail="Klienti nuk u gjet")
    
    await bp_clients.delete_one({"id": client_id})
    
    return {"message": "Klienti u fshi me sukses"}
