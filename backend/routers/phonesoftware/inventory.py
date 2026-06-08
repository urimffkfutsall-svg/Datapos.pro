"""PhoneSoftware Inventory Management Routes"""
from fastapi import APIRouter, HTTPException, Depends, Query
from typing import List, Optional
from datetime import datetime, timezone
import uuid

from .database import ps_inventory, ps_stock_movements
from .models import (
    InventoryItemCreate, InventoryItemUpdate, InventoryItemResponse,
    InventoryCategory, StockMovementCreate, StockMovementResponse, StockMovementType
)
from .database import get_ps_current_user

router = APIRouter(prefix="/phonesoftware/inventory", tags=["PhoneSoftware Inventory"])


@router.get("", response_model=List[InventoryItemResponse])
async def get_inventory(
    category: Optional[InventoryCategory] = None,
    low_stock_only: bool = False,
    search: Optional[str] = None,
    limit: int = Query(default=100, le=500),
    skip: int = 0,
    current_user: dict = Depends(get_ps_current_user)
):
    """Get all inventory items for the tenant"""
    tenant_id = current_user.get("tenant_id")
    if not tenant_id and current_user.get("role") != "super_admin":
        raise HTTPException(status_code=403, detail="Nuk keni akses")
    
    query = {"is_active": True}
    if tenant_id:
        query["tenant_id"] = tenant_id
    
    if category:
        query["category"] = category
    
    if low_stock_only:
        query["$expr"] = {"$lte": ["$quantity", "$min_stock"]}
    
    if search:
        query["$or"] = [
            {"name": {"$regex": search, "$options": "i"}},
            {"brand": {"$regex": search, "$options": "i"}},
            {"model": {"$regex": search, "$options": "i"}},
            {"barcode": {"$regex": search, "$options": "i"}},
            {"sku": {"$regex": search, "$options": "i"}},
            {"imei": {"$regex": search, "$options": "i"}}
        ]
    
    items = await ps_inventory.find(query, {"_id": 0}).sort("created_at", -1).skip(skip).limit(limit).to_list(limit)
    
    # Add low stock flag
    for item in items:
        item["is_low_stock"] = item.get("quantity", 0) <= item.get("min_stock", 5)
    
    return items


@router.get("/stats")
async def get_inventory_stats(current_user: dict = Depends(get_ps_current_user)):
    """Get inventory statistics"""
    tenant_id = current_user.get("tenant_id")
    if not tenant_id and current_user.get("role") != "super_admin":
        raise HTTPException(status_code=403, detail="Nuk keni akses")
    
    query = {"tenant_id": tenant_id, "is_active": True} if tenant_id else {"is_active": True}
    
    # Category counts
    category_counts = {}
    for cat in InventoryCategory:
        count = await ps_inventory.count_documents({**query, "category": cat.value})
        category_counts[cat.value] = count
    
    # Low stock count
    low_stock_count = await ps_inventory.count_documents({
        **query,
        "$expr": {"$lte": ["$quantity", "$min_stock"]}
    })
    
    # Total items
    total_items = await ps_inventory.count_documents(query)
    
    # Total value
    items = await ps_inventory.find(query, {"_id": 0, "quantity": 1, "purchase_price": 1}).to_list(10000)
    total_value = sum(item.get("quantity", 0) * item.get("purchase_price", 0) for item in items)
    
    return {
        "category_counts": category_counts,
        "low_stock_count": low_stock_count,
        "total_items": total_items,
        "total_value": total_value
    }


@router.get("/low-stock", response_model=List[InventoryItemResponse])
async def get_low_stock_items(current_user: dict = Depends(get_ps_current_user)):
    """Get items with low stock"""
    tenant_id = current_user.get("tenant_id")
    if not tenant_id and current_user.get("role") != "super_admin":
        raise HTTPException(status_code=403, detail="Nuk keni akses")
    
    query = {
        "is_active": True,
        "$expr": {"$lte": ["$quantity", "$min_stock"]}
    }
    if tenant_id:
        query["tenant_id"] = tenant_id
    
    items = await ps_inventory.find(query, {"_id": 0}).sort("quantity", 1).to_list(100)
    
    for item in items:
        item["is_low_stock"] = True
    
    return items


@router.post("", response_model=InventoryItemResponse)
async def create_inventory_item(item: InventoryItemCreate, current_user: dict = Depends(get_ps_current_user)):
    """Create a new inventory item"""
    tenant_id = current_user.get("tenant_id")
    if not tenant_id:
        raise HTTPException(status_code=403, detail="Nuk keni akses")
    
    # Check for duplicate barcode or IMEI
    if item.barcode:
        existing = await ps_inventory.find_one({"barcode": item.barcode, "tenant_id": tenant_id})
        if existing:
            raise HTTPException(status_code=400, detail="Barkodi ekziston tashmë")
    
    if item.imei:
        existing = await ps_inventory.find_one({"imei": item.imei, "tenant_id": tenant_id})
        if existing:
            raise HTTPException(status_code=400, detail="IMEI ekziston tashmë")
    
    item_data = {
        "id": str(uuid.uuid4()),
        **item.model_dump(),
        "is_active": True,
        "tenant_id": tenant_id,
        "created_at": datetime.now(timezone.utc).isoformat(),
        "updated_at": datetime.now(timezone.utc).isoformat()
    }
    
    await ps_inventory.insert_one(item_data)
    
    # Log stock movement for initial quantity
    if item.quantity > 0:
        movement = {
            "id": str(uuid.uuid4()),
            "item_id": item_data["id"],
            "item_name": item.name,
            "quantity": item.quantity,
            "movement_type": StockMovementType.IN,
            "reason": "Stok fillestar",
            "unit_cost": item.purchase_price,
            "user_id": current_user["id"],
            "user_name": current_user.get("full_name", ""),
            "tenant_id": tenant_id,
            "created_at": datetime.now(timezone.utc).isoformat()
        }
        await ps_stock_movements.insert_one(movement)
    
    item_data["is_low_stock"] = item.quantity <= item.min_stock
    
    return InventoryItemResponse(**item_data)


@router.get("/{item_id}", response_model=InventoryItemResponse)
async def get_inventory_item(item_id: str, current_user: dict = Depends(get_ps_current_user)):
    """Get inventory item details"""
    tenant_id = current_user.get("tenant_id")
    
    query = {"id": item_id}
    if tenant_id:
        query["tenant_id"] = tenant_id
    
    item = await ps_inventory.find_one(query, {"_id": 0})
    if not item:
        raise HTTPException(status_code=404, detail="Artikulli nuk u gjet")
    
    item["is_low_stock"] = item.get("quantity", 0) <= item.get("min_stock", 5)
    
    return InventoryItemResponse(**item)


@router.put("/{item_id}", response_model=InventoryItemResponse)
async def update_inventory_item(item_id: str, update: InventoryItemUpdate, current_user: dict = Depends(get_ps_current_user)):
    """Update inventory item"""
    tenant_id = current_user.get("tenant_id")
    
    query = {"id": item_id}
    if tenant_id:
        query["tenant_id"] = tenant_id
    
    existing = await ps_inventory.find_one(query)
    if not existing:
        raise HTTPException(status_code=404, detail="Artikulli nuk u gjet")
    
    update_data = {k: v for k, v in update.model_dump().items() if v is not None}
    update_data["updated_at"] = datetime.now(timezone.utc).isoformat()
    
    # Check for quantity change and log movement
    if "quantity" in update_data and update_data["quantity"] != existing.get("quantity"):
        diff = update_data["quantity"] - existing.get("quantity", 0)
        movement = {
            "id": str(uuid.uuid4()),
            "item_id": item_id,
            "item_name": existing.get("name"),
            "quantity": diff,
            "movement_type": StockMovementType.ADJUSTMENT,
            "reason": "Rregullim manual i stokut",
            "user_id": current_user["id"],
            "user_name": current_user.get("full_name", ""),
            "tenant_id": tenant_id,
            "created_at": datetime.now(timezone.utc).isoformat()
        }
        await ps_stock_movements.insert_one(movement)
    
    if update_data:
        await ps_inventory.update_one(query, {"$set": update_data})
    
    updated = await ps_inventory.find_one(query, {"_id": 0})
    updated["is_low_stock"] = updated.get("quantity", 0) <= updated.get("min_stock", 5)
    
    return InventoryItemResponse(**updated)


@router.delete("/{item_id}")
async def delete_inventory_item(item_id: str, current_user: dict = Depends(get_ps_current_user)):
    """Delete (deactivate) inventory item"""
    tenant_id = current_user.get("tenant_id")
    
    # Only admin/manager can delete
    if current_user.get("role") not in ["super_admin", "admin", "manager"]:
        raise HTTPException(status_code=403, detail="Nuk keni leje për këtë veprim")
    
    query = {"id": item_id}
    if tenant_id:
        query["tenant_id"] = tenant_id
    
    result = await ps_inventory.update_one(
        query,
        {"$set": {"is_active": False, "updated_at": datetime.now(timezone.utc).isoformat()}}
    )
    
    if result.modified_count == 0:
        raise HTTPException(status_code=404, detail="Artikulli nuk u gjet")
    
    return {"message": "Artikulli u çaktivizua me sukses"}


@router.post("/{item_id}/adjust-stock")
async def adjust_stock(
    item_id: str,
    quantity: int,
    movement_type: StockMovementType,
    reason: Optional[str] = None,
    current_user: dict = Depends(get_ps_current_user)
):
    """Manually adjust stock for an item"""
    tenant_id = current_user.get("tenant_id")
    
    query = {"id": item_id}
    if tenant_id:
        query["tenant_id"] = tenant_id
    
    item = await ps_inventory.find_one(query)
    if not item:
        raise HTTPException(status_code=404, detail="Artikulli nuk u gjet")
    
    # Calculate new quantity
    current_qty = item.get("quantity", 0)
    if movement_type == StockMovementType.IN:
        new_qty = current_qty + quantity
    elif movement_type == StockMovementType.OUT:
        new_qty = current_qty - quantity
        if new_qty < 0:
            raise HTTPException(status_code=400, detail="Stoku nuk mund të jetë negativ")
    else:
        new_qty = quantity  # Direct adjustment
    
    # Update inventory
    await ps_inventory.update_one(
        query,
        {"$set": {"quantity": new_qty, "updated_at": datetime.now(timezone.utc).isoformat()}}
    )
    
    # Log movement
    movement = {
        "id": str(uuid.uuid4()),
        "item_id": item_id,
        "item_name": item.get("name"),
        "quantity": quantity if movement_type == StockMovementType.IN else -quantity,
        "movement_type": movement_type,
        "reason": reason,
        "user_id": current_user["id"],
        "user_name": current_user.get("full_name", ""),
        "tenant_id": tenant_id,
        "created_at": datetime.now(timezone.utc).isoformat()
    }
    await ps_stock_movements.insert_one(movement)
    
    return {"message": "Stoku u rregullua me sukses", "new_quantity": new_qty}


@router.get("/{item_id}/movements", response_model=List[StockMovementResponse])
async def get_item_movements(item_id: str, current_user: dict = Depends(get_ps_current_user)):
    """Get stock movements for an item"""
    tenant_id = current_user.get("tenant_id")
    
    query = {"item_id": item_id}
    if tenant_id:
        query["tenant_id"] = tenant_id
    
    movements = await ps_stock_movements.find(query, {"_id": 0}).sort("created_at", -1).to_list(100)
    
    return movements


@router.get("/barcode/{barcode}")
async def get_by_barcode(barcode: str, current_user: dict = Depends(get_ps_current_user)):
    """Get inventory item by barcode"""
    tenant_id = current_user.get("tenant_id")
    
    query = {"barcode": barcode, "is_active": True}
    if tenant_id:
        query["tenant_id"] = tenant_id
    
    item = await ps_inventory.find_one(query, {"_id": 0})
    if not item:
        raise HTTPException(status_code=404, detail="Artikulli nuk u gjet")
    
    item["is_low_stock"] = item.get("quantity", 0) <= item.get("min_stock", 5)
    
    return item


@router.get("/spare-parts/available")
async def get_available_spare_parts(current_user: dict = Depends(get_ps_current_user)):
    """Get available spare parts for repairs"""
    tenant_id = current_user.get("tenant_id")
    if not tenant_id:
        raise HTTPException(status_code=403, detail="Nuk keni akses")
    
    parts = await ps_inventory.find(
        {
            "tenant_id": tenant_id,
            "category": InventoryCategory.SPARE_PART,
            "is_active": True,
            "quantity": {"$gt": 0}
        },
        {"_id": 0}
    ).sort("name", 1).to_list(500)
    
    return parts
