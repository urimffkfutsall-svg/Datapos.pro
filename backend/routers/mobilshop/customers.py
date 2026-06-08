"""Mobilshop Customers Router - CRM"""
from fastapi import APIRouter, HTTPException, Depends
from typing import List, Optional
from datetime import datetime, timezone
import uuid

from database import db
from auth import get_current_user
from mobilshop_models import CustomerCreate, CustomerUpdate, CustomerResponse

router = APIRouter(prefix="/mobilshop/customers", tags=["Mobilshop Customers"])


@router.get("", response_model=List[CustomerResponse])
async def get_customers(
    search: Optional[str] = None,
    current_user: dict = Depends(get_current_user)
):
    """Get all customers with optional search"""
    tenant_id = current_user.get("tenant_id")
    
    query = {"tenant_id": tenant_id, "is_active": True}
    
    if search:
        query["$or"] = [
            {"full_name": {"$regex": search, "$options": "i"}},
            {"phone": {"$regex": search, "$options": "i"}},
            {"email": {"$regex": search, "$options": "i"}},
            {"id_number": {"$regex": search, "$options": "i"}}
        ]
    
    customers = await db.mobilshop_customers.find(query, {"_id": 0}).sort("full_name", 1).to_list(5000)
    
    # Add purchase and repair stats
    for customer in customers:
        # Total purchases
        sales = await db.mobilshop_sales.find(
            {"customer_id": customer["id"], "tenant_id": tenant_id}
        ).to_list(10000)
        customer["total_purchases"] = sum(s.get("grand_total", 0) for s in sales)
        
        # Total repairs
        repairs = await db.mobilshop_repairs.count_documents(
            {"customer_id": customer["id"], "tenant_id": tenant_id}
        )
        customer["total_repairs"] = repairs
    
    return customers


@router.get("/search/{query}")
async def search_customers(
    query: str,
    current_user: dict = Depends(get_current_user)
):
    """Quick search customers by name or phone"""
    tenant_id = current_user.get("tenant_id")
    
    customers = await db.mobilshop_customers.find(
        {
            "tenant_id": tenant_id,
            "is_active": True,
            "$or": [
                {"full_name": {"$regex": query, "$options": "i"}},
                {"phone": {"$regex": query, "$options": "i"}}
            ]
        },
        {"_id": 0}
    ).limit(20).to_list(20)
    
    return customers


@router.get("/{customer_id}", response_model=CustomerResponse)
async def get_customer(
    customer_id: str,
    current_user: dict = Depends(get_current_user)
):
    """Get a single customer with full details"""
    tenant_id = current_user.get("tenant_id")
    
    customer = await db.mobilshop_customers.find_one(
        {"id": customer_id, "tenant_id": tenant_id},
        {"_id": 0}
    )
    
    if not customer:
        raise HTTPException(status_code=404, detail="Klienti nuk u gjet")
    
    # Add stats
    sales = await db.mobilshop_sales.find(
        {"customer_id": customer_id, "tenant_id": tenant_id}
    ).to_list(10000)
    customer["total_purchases"] = sum(s.get("grand_total", 0) for s in sales)
    
    repairs = await db.mobilshop_repairs.count_documents(
        {"customer_id": customer_id, "tenant_id": tenant_id}
    )
    customer["total_repairs"] = repairs
    
    return customer


@router.get("/{customer_id}/history")
async def get_customer_history(
    customer_id: str,
    current_user: dict = Depends(get_current_user)
):
    """Get customer's purchase and repair history"""
    tenant_id = current_user.get("tenant_id")
    
    customer = await db.mobilshop_customers.find_one(
        {"id": customer_id, "tenant_id": tenant_id},
        {"_id": 0}
    )
    
    if not customer:
        raise HTTPException(status_code=404, detail="Klienti nuk u gjet")
    
    # Get purchases
    purchases = await db.mobilshop_sales.find(
        {"customer_id": customer_id, "tenant_id": tenant_id},
        {"_id": 0}
    ).sort("created_at", -1).to_list(100)
    
    # Get repairs
    repairs = await db.mobilshop_repairs.find(
        {"customer_id": customer_id, "tenant_id": tenant_id},
        {"_id": 0}
    ).sort("created_at", -1).to_list(100)
    
    return {
        "customer": customer,
        "purchases": purchases,
        "repairs": repairs,
        "total_spent": sum(p.get("grand_total", 0) for p in purchases),
        "total_repairs": len(repairs)
    }


@router.post("", response_model=CustomerResponse)
async def create_customer(
    data: CustomerCreate,
    current_user: dict = Depends(get_current_user)
):
    """Create a new customer"""
    tenant_id = current_user.get("tenant_id")
    
    # Check for duplicate phone
    existing = await db.mobilshop_customers.find_one(
        {"phone": data.phone, "tenant_id": tenant_id, "is_active": True}
    )
    if existing:
        raise HTTPException(status_code=400, detail="Ky numër telefoni ekziston tashmë")
    
    customer = {
        "id": str(uuid.uuid4()),
        "tenant_id": tenant_id,
        "full_name": data.full_name,
        "phone": data.phone,
        "email": data.email,
        "address": data.address,
        "city": data.city,
        "id_number": data.id_number,
        "notes": data.notes,
        "loyalty_points": data.loyalty_points,
        "is_active": True,
        "created_at": datetime.now(timezone.utc).isoformat(),
        "created_by": current_user.get("id")
    }
    
    await db.mobilshop_customers.insert_one(customer)
    customer.pop("_id", None)
    customer["total_purchases"] = 0
    customer["total_repairs"] = 0
    
    return customer


@router.put("/{customer_id}", response_model=CustomerResponse)
async def update_customer(
    customer_id: str,
    data: CustomerUpdate,
    current_user: dict = Depends(get_current_user)
):
    """Update a customer"""
    tenant_id = current_user.get("tenant_id")
    
    update_data = {k: v for k, v in data.model_dump().items() if v is not None}
    if not update_data:
        raise HTTPException(status_code=400, detail="Asnjë të dhënë për përditësim")
    
    # Check phone uniqueness if updating
    if data.phone:
        existing = await db.mobilshop_customers.find_one(
            {"phone": data.phone, "tenant_id": tenant_id, "id": {"$ne": customer_id}, "is_active": True}
        )
        if existing:
            raise HTTPException(status_code=400, detail="Ky numër telefoni ekziston tashmë")
    
    result = await db.mobilshop_customers.update_one(
        {"id": customer_id, "tenant_id": tenant_id},
        {"$set": update_data}
    )
    
    if result.matched_count == 0:
        raise HTTPException(status_code=404, detail="Klienti nuk u gjet")
    
    customer = await db.mobilshop_customers.find_one(
        {"id": customer_id, "tenant_id": tenant_id},
        {"_id": 0}
    )
    
    # Add stats
    sales = await db.mobilshop_sales.find(
        {"customer_id": customer_id, "tenant_id": tenant_id}
    ).to_list(10000)
    customer["total_purchases"] = sum(s.get("grand_total", 0) for s in sales)
    customer["total_repairs"] = await db.mobilshop_repairs.count_documents(
        {"customer_id": customer_id, "tenant_id": tenant_id}
    )
    
    return customer


@router.delete("/{customer_id}")
async def delete_customer(
    customer_id: str,
    current_user: dict = Depends(get_current_user)
):
    """Soft delete a customer"""
    tenant_id = current_user.get("tenant_id")
    
    result = await db.mobilshop_customers.update_one(
        {"id": customer_id, "tenant_id": tenant_id},
        {"$set": {"is_active": False}}
    )
    
    if result.matched_count == 0:
        raise HTTPException(status_code=404, detail="Klienti nuk u gjet")
    
    return {"message": "Klienti u fshi me sukses"}


@router.post("/{customer_id}/loyalty-points")
async def add_loyalty_points(
    customer_id: str,
    points: int,
    current_user: dict = Depends(get_current_user)
):
    """Add loyalty points to a customer"""
    tenant_id = current_user.get("tenant_id")
    
    result = await db.mobilshop_customers.update_one(
        {"id": customer_id, "tenant_id": tenant_id},
        {"$inc": {"loyalty_points": points}}
    )
    
    if result.matched_count == 0:
        raise HTTPException(status_code=404, detail="Klienti nuk u gjet")
    
    customer = await db.mobilshop_customers.find_one(
        {"id": customer_id, "tenant_id": tenant_id},
        {"_id": 0, "loyalty_points": 1}
    )
    
    return {"loyalty_points": customer["loyalty_points"]}
