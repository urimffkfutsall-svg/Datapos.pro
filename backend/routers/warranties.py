"""
Warranties Router - CRUD operations for warranty documents
"""
from fastapi import APIRouter, Depends, HTTPException, Query
from typing import List, Optional
from datetime import datetime, timezone
from dateutil.relativedelta import relativedelta
import uuid

from database import db
from auth import get_current_user
from models import WarrantyCreate, WarrantyUpdate, WarrantyResponse

router = APIRouter(prefix="/warranties", tags=["Warranties"])


def generate_warranty_number(tenant_id: str) -> str:
    """Generate unique warranty number: GAR-YYYYMMDD-XXXX"""
    date_part = datetime.now(timezone.utc).strftime("%Y%m%d")
    random_part = str(uuid.uuid4())[:4].upper()
    return f"GAR-{date_part}-{random_part}"


def calculate_expiry_date(purchase_date: str, warranty_period: int) -> str:
    """Calculate warranty expiry date"""
    try:
        purchase = datetime.fromisoformat(purchase_date.replace('Z', '+00:00'))
        expiry = purchase + relativedelta(months=warranty_period)
        return expiry.strftime("%Y-%m-%d")
    except:
        return None


@router.post("", response_model=WarrantyResponse)
async def create_warranty(warranty: WarrantyCreate, current_user: dict = Depends(get_current_user)):
    """Create a new warranty document"""
    tenant_id = current_user.get("tenant_id")
    
    # For super_admin without tenant_id, use a default or allow it
    if not tenant_id:
        if current_user.get("role") == "super_admin":
            tenant_id = "super_admin_global"
        else:
            raise HTTPException(status_code=400, detail="Tenant ID required")
    
    warranty_id = str(uuid.uuid4())
    warranty_number = generate_warranty_number(tenant_id)
    now = datetime.now(timezone.utc)
    
    # Calculate expiry date
    expiry_date = None
    if warranty.purchase_date:
        expiry_date = calculate_expiry_date(warranty.purchase_date, warranty.warranty_period)
    
    warranty_doc = {
        "id": warranty_id,
        "warranty_number": warranty_number,
        "customer_name": warranty.customer_name,
        "customer_phone": warranty.customer_phone,
        "customer_address": warranty.customer_address,
        "product_name": warranty.product_name,
        "product_brand": warranty.product_brand,
        "product_model": warranty.product_model,
        "serial_number": warranty.serial_number,
        "imei": warranty.imei,
        "purchase_date": warranty.purchase_date,
        "warranty_period": warranty.warranty_period,
        "expiry_date": expiry_date,
        "product_condition": warranty.product_condition,
        "accessories": warranty.accessories,
        "notes": warranty.notes,
        "created_by": current_user.get("id"),
        "created_by_name": current_user.get("full_name"),
        "created_at": now.isoformat(),
        "tenant_id": tenant_id
    }
    
    await db.warranties.insert_one(warranty_doc)
    
    return WarrantyResponse(
        id=warranty_id,
        warranty_number=warranty_number,
        customer_name=warranty.customer_name,
        customer_phone=warranty.customer_phone,
        customer_address=warranty.customer_address,
        product_name=warranty.product_name,
        product_brand=warranty.product_brand,
        product_model=warranty.product_model,
        serial_number=warranty.serial_number,
        imei=warranty.imei,
        purchase_date=warranty.purchase_date,
        warranty_period=warranty.warranty_period,
        expiry_date=expiry_date,
        product_condition=warranty.product_condition,
        accessories=warranty.accessories,
        notes=warranty.notes,
        created_by=current_user.get("full_name", "Unknown"),
        created_at=now.isoformat(),
        tenant_id=tenant_id
    )


@router.get("", response_model=List[WarrantyResponse])
async def list_warranties(
    search: Optional[str] = Query(None, description="Search by customer name, product, serial, or IMEI"),
    limit: int = Query(50, ge=1, le=200),
    skip: int = Query(0, ge=0),
    current_user: dict = Depends(get_current_user)
):
    """List warranty documents for the tenant"""
    tenant_id = current_user.get("tenant_id")
    
    # For super_admin without tenant_id
    if not tenant_id:
        if current_user.get("role") == "super_admin":
            tenant_id = "super_admin_global"
        else:
            raise HTTPException(status_code=400, detail="Tenant ID required")
    
    query = {"tenant_id": tenant_id}
    
    # Add search filter
    if search:
        search_regex = {"$regex": search, "$options": "i"}
        query["$or"] = [
            {"customer_name": search_regex},
            {"customer_phone": search_regex},
            {"product_name": search_regex},
            {"product_brand": search_regex},
            {"serial_number": search_regex},
            {"imei": search_regex},
            {"warranty_number": search_regex}
        ]
    
    cursor = db.warranties.find(query, {"_id": 0}).sort("created_at", -1).skip(skip).limit(limit)
    warranties = await cursor.to_list(length=limit)
    
    return [
        WarrantyResponse(
            id=w["id"],
            warranty_number=w.get("warranty_number", ""),
            customer_name=w.get("customer_name"),
            customer_phone=w.get("customer_phone"),
            customer_address=w.get("customer_address"),
            product_name=w.get("product_name"),
            product_brand=w.get("product_brand"),
            product_model=w.get("product_model"),
            serial_number=w.get("serial_number"),
            imei=w.get("imei"),
            purchase_date=w.get("purchase_date"),
            warranty_period=w.get("warranty_period", 12),
            expiry_date=w.get("expiry_date"),
            product_condition=w.get("product_condition", "I ri"),
            accessories=w.get("accessories"),
            notes=w.get("notes"),
            created_by=w.get("created_by_name", "Unknown"),
            created_at=w.get("created_at", ""),
            tenant_id=w.get("tenant_id", "")
        )
        for w in warranties
    ]


@router.get("/{warranty_id}", response_model=WarrantyResponse)
async def get_warranty(warranty_id: str, current_user: dict = Depends(get_current_user)):
    """Get a specific warranty document"""
    tenant_id = current_user.get("tenant_id")
    if not tenant_id and current_user.get("role") == "super_admin":
        tenant_id = "super_admin_global"
    
    warranty = await db.warranties.find_one(
        {"id": warranty_id, "tenant_id": tenant_id},
        {"_id": 0}
    )
    
    if not warranty:
        raise HTTPException(status_code=404, detail="Warranty not found")
    
    return WarrantyResponse(
        id=warranty["id"],
        warranty_number=warranty.get("warranty_number", ""),
        customer_name=warranty.get("customer_name"),
        customer_phone=warranty.get("customer_phone"),
        customer_address=warranty.get("customer_address"),
        product_name=warranty.get("product_name"),
        product_brand=warranty.get("product_brand"),
        product_model=warranty.get("product_model"),
        serial_number=warranty.get("serial_number"),
        imei=warranty.get("imei"),
        purchase_date=warranty.get("purchase_date"),
        warranty_period=warranty.get("warranty_period", 12),
        expiry_date=warranty.get("expiry_date"),
        product_condition=warranty.get("product_condition", "I ri"),
        accessories=warranty.get("accessories"),
        notes=warranty.get("notes"),
        created_by=warranty.get("created_by_name", "Unknown"),
        created_at=warranty.get("created_at", ""),
        tenant_id=warranty.get("tenant_id", "")
    )


@router.delete("/{warranty_id}")
async def delete_warranty(warranty_id: str, current_user: dict = Depends(get_current_user)):
    """Delete a warranty document"""
    tenant_id = current_user.get("tenant_id")
    if not tenant_id and current_user.get("role") == "super_admin":
        tenant_id = "super_admin_global"
    
    # Only admins can delete
    if current_user.get("role") not in ["admin", "super_admin", "manager"]:
        raise HTTPException(status_code=403, detail="Only admins can delete warranties")
    
    result = await db.warranties.delete_one({"id": warranty_id, "tenant_id": tenant_id})
    
    if result.deleted_count == 0:
        raise HTTPException(status_code=404, detail="Warranty not found")
    
    return {"message": "Warranty deleted successfully"}


@router.get("/stats/summary")
async def get_warranty_stats(current_user: dict = Depends(get_current_user)):
    """Get warranty statistics for the tenant"""
    tenant_id = current_user.get("tenant_id")
    if not tenant_id:
        if current_user.get("role") == "super_admin":
            tenant_id = "super_admin_global"
        else:
            raise HTTPException(status_code=400, detail="Tenant ID required")
    
    today = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    
    # Total warranties
    total = await db.warranties.count_documents({"tenant_id": tenant_id})
    
    # Active warranties (not expired)
    active = await db.warranties.count_documents({
        "tenant_id": tenant_id,
        "expiry_date": {"$gte": today}
    })
    
    # Expired warranties
    expired = await db.warranties.count_documents({
        "tenant_id": tenant_id,
        "expiry_date": {"$lt": today}
    })
    
    # This month warranties
    month_start = datetime.now(timezone.utc).replace(day=1).strftime("%Y-%m-%d")
    this_month = await db.warranties.count_documents({
        "tenant_id": tenant_id,
        "created_at": {"$gte": month_start}
    })
    
    return {
        "total": total,
        "active": active,
        "expired": expired,
        "this_month": this_month
    }
