"""PhoneSoftware Customer Management Routes (CRM)"""
from fastapi import APIRouter, HTTPException, Depends, Query
from typing import List, Optional
from datetime import datetime, timezone
import uuid

from .database import ps_customers, ps_repairs, ps_sales
from .models import CustomerCreate, CustomerUpdate, CustomerResponse
from .database import get_ps_current_user

router = APIRouter(prefix="/phonesoftware/customers", tags=["PhoneSoftware Customers"])


@router.get("", response_model=List[CustomerResponse])
async def get_customers(
    search: Optional[str] = None,
    limit: int = Query(default=100, le=500),
    skip: int = 0,
    current_user: dict = Depends(get_ps_current_user)
):
    """Get all customers for the tenant"""
    tenant_id = current_user.get("tenant_id")
    if not tenant_id and current_user.get("role") != "super_admin":
        raise HTTPException(status_code=403, detail="Nuk keni akses")
    
    query = {}
    if tenant_id:
        query["tenant_id"] = tenant_id
    
    if search:
        query["$or"] = [
            {"full_name": {"$regex": search, "$options": "i"}},
            {"phone": {"$regex": search, "$options": "i"}},
            {"email": {"$regex": search, "$options": "i"}}
        ]
    
    customers = await ps_customers.find(query, {"_id": 0}).sort("created_at", -1).skip(skip).limit(limit).to_list(limit)
    
    # Enrich with counts
    for customer in customers:
        customer["total_repairs"] = await ps_repairs.count_documents({"customer_id": customer["id"]})
        customer["total_purchases"] = await ps_sales.count_documents({"customer_id": customer["id"]})
    
    return customers


@router.get("/stats")
async def get_customer_stats(current_user: dict = Depends(get_ps_current_user)):
    """Get customer statistics"""
    tenant_id = current_user.get("tenant_id")
    if not tenant_id and current_user.get("role") != "super_admin":
        raise HTTPException(status_code=403, detail="Nuk keni akses")
    
    query = {"tenant_id": tenant_id} if tenant_id else {}
    
    total_customers = await ps_customers.count_documents(query)
    
    # Get top customers by repair count
    pipeline = [
        {"$match": query},
        {"$lookup": {
            "from": "ps_repairs",
            "localField": "id",
            "foreignField": "customer_id",
            "as": "repairs"
        }},
        {"$addFields": {"repairs_count": {"$size": "$repairs"}}},
        {"$sort": {"repairs_count": -1}},
        {"$limit": 5},
        {"$project": {"_id": 0, "id": 1, "full_name": 1, "phone": 1, "repairs_count": 1}}
    ]
    
    top_customers = await ps_customers.aggregate(pipeline).to_list(5)
    
    return {
        "total_customers": total_customers,
        "top_customers": top_customers
    }


@router.post("", response_model=CustomerResponse)
async def create_customer(customer: CustomerCreate, current_user: dict = Depends(get_ps_current_user)):
    """Create a new customer"""
    tenant_id = current_user.get("tenant_id")
    if not tenant_id:
        raise HTTPException(status_code=403, detail="Nuk keni akses")
    
    # Check if phone exists
    existing = await ps_customers.find_one({"phone": customer.phone, "tenant_id": tenant_id})
    if existing:
        raise HTTPException(status_code=400, detail="Numri i telefonit ekziston tashmë")
    
    customer_data = {
        "id": str(uuid.uuid4()),
        "full_name": customer.full_name,
        "phone": customer.phone,
        "email": customer.email,
        "address": customer.address,
        "notes": customer.notes,
        "tenant_id": tenant_id,
        "created_at": datetime.now(timezone.utc).isoformat()
    }
    
    await ps_customers.insert_one(customer_data)
    
    return CustomerResponse(**customer_data, total_repairs=0, total_purchases=0)


@router.get("/{customer_id}", response_model=CustomerResponse)
async def get_customer(customer_id: str, current_user: dict = Depends(get_ps_current_user)):
    """Get customer details"""
    tenant_id = current_user.get("tenant_id")
    
    query = {"id": customer_id}
    if tenant_id:
        query["tenant_id"] = tenant_id
    
    customer = await ps_customers.find_one(query, {"_id": 0})
    if not customer:
        raise HTTPException(status_code=404, detail="Klienti nuk u gjet")
    
    customer["total_repairs"] = await ps_repairs.count_documents({"customer_id": customer_id})
    customer["total_purchases"] = await ps_sales.count_documents({"customer_id": customer_id})
    
    return CustomerResponse(**customer)


@router.put("/{customer_id}", response_model=CustomerResponse)
async def update_customer(customer_id: str, update: CustomerUpdate, current_user: dict = Depends(get_ps_current_user)):
    """Update customer"""
    tenant_id = current_user.get("tenant_id")
    
    query = {"id": customer_id}
    if tenant_id:
        query["tenant_id"] = tenant_id
    
    existing = await ps_customers.find_one(query)
    if not existing:
        raise HTTPException(status_code=404, detail="Klienti nuk u gjet")
    
    # Check if phone is being changed and already exists
    if update.phone and update.phone != existing.get("phone"):
        phone_exists = await ps_customers.find_one({
            "phone": update.phone,
            "tenant_id": tenant_id,
            "id": {"$ne": customer_id}
        })
        if phone_exists:
            raise HTTPException(status_code=400, detail="Numri i telefonit ekziston tashmë")
    
    update_data = {k: v for k, v in update.model_dump().items() if v is not None}
    
    if update_data:
        await ps_customers.update_one(query, {"$set": update_data})
    
    updated = await ps_customers.find_one(query, {"_id": 0})
    updated["total_repairs"] = await ps_repairs.count_documents({"customer_id": customer_id})
    updated["total_purchases"] = await ps_sales.count_documents({"customer_id": customer_id})
    
    return CustomerResponse(**updated)


@router.delete("/{customer_id}")
async def delete_customer(customer_id: str, current_user: dict = Depends(get_ps_current_user)):
    """Delete customer"""
    tenant_id = current_user.get("tenant_id")
    
    # Only admin/manager can delete
    if current_user.get("role") not in ["super_admin", "admin", "manager"]:
        raise HTTPException(status_code=403, detail="Nuk keni leje për këtë veprim")
    
    query = {"id": customer_id}
    if tenant_id:
        query["tenant_id"] = tenant_id
    
    # Check if customer has repairs
    repairs_count = await ps_repairs.count_documents({"customer_id": customer_id})
    if repairs_count > 0:
        raise HTTPException(
            status_code=400, 
            detail=f"Klienti ka {repairs_count} riparime. Nuk mund të fshihet."
        )
    
    result = await ps_customers.delete_one(query)
    if result.deleted_count == 0:
        raise HTTPException(status_code=404, detail="Klienti nuk u gjet")
    
    return {"message": "Klienti u fshi me sukses"}


@router.get("/{customer_id}/history")
async def get_customer_history(customer_id: str, current_user: dict = Depends(get_ps_current_user)):
    """Get full customer history - repairs and purchases"""
    tenant_id = current_user.get("tenant_id")
    
    query = {"id": customer_id}
    if tenant_id:
        query["tenant_id"] = tenant_id
    
    customer = await ps_customers.find_one(query, {"_id": 0})
    if not customer:
        raise HTTPException(status_code=404, detail="Klienti nuk u gjet")
    
    repairs = await ps_repairs.find(
        {"customer_id": customer_id},
        {"_id": 0}
    ).sort("created_at", -1).to_list(100)
    
    sales = await ps_sales.find(
        {"customer_id": customer_id},
        {"_id": 0}
    ).sort("created_at", -1).to_list(100)
    
    return {
        "customer": customer,
        "repairs": repairs,
        "purchases": sales
    }


@router.get("/search/phone/{phone}")
async def search_by_phone(phone: str, current_user: dict = Depends(get_ps_current_user)):
    """Quick search customer by phone number"""
    tenant_id = current_user.get("tenant_id")
    
    query = {"phone": {"$regex": phone}}
    if tenant_id:
        query["tenant_id"] = tenant_id
    
    customers = await ps_customers.find(query, {"_id": 0}).limit(10).to_list(10)
    
    return customers
