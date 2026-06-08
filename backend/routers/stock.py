"""Stock management routes"""
from fastapi import APIRouter, HTTPException, Depends
from typing import List, Optional
from datetime import datetime, timezone

from database import db
from models import (
    StockMovementCreate, StockMovementResponse, StockMovement,
    StockMovementType, UserRole
)
from auth import (
    get_current_user, require_role,
    get_tenant_filter, add_tenant_id, log_audit
)

router = APIRouter(prefix="/stock", tags=["Stock"])


@router.post("/movements", response_model=StockMovementResponse)
async def create_stock_movement(
    movement_data: StockMovementCreate,
    current_user: dict = Depends(require_role([UserRole.ADMIN, UserRole.MANAGER]))
):
    """Create a stock movement"""
    tenant_filter = get_tenant_filter(current_user)
    product = await db.products.find_one({"id": movement_data.product_id, **tenant_filter}, {"_id": 0})
    if not product:
        raise HTTPException(status_code=404, detail="Produkti nuk u gjet")
    
    current_stock = product.get("current_stock", 0)
    if movement_data.movement_type in [StockMovementType.IN]:
        new_stock = current_stock + movement_data.quantity
    else:
        new_stock = current_stock - movement_data.quantity
        if new_stock < 0:
            raise HTTPException(status_code=400, detail="Stoku nuk mund të jetë negativ")
    
    movement = StockMovement(**movement_data.model_dump(), user_id=current_user["id"])
    mov_doc = movement.model_dump()
    mov_doc['created_at'] = mov_doc['created_at'].isoformat()
    mov_doc = add_tenant_id(mov_doc, current_user)
    await db.stock_movements.insert_one(mov_doc)
    
    await db.products.update_one(
        {"id": movement_data.product_id, **tenant_filter},
        {"$set": {"current_stock": new_stock, "updated_at": datetime.now(timezone.utc).isoformat()}}
    )
    
    await log_audit(current_user["id"], "stock_movement", "stock", movement.id, 
                    {"type": movement_data.movement_type, "qty": movement_data.quantity})
    return StockMovementResponse(**mov_doc)


@router.get("/movements", response_model=List[StockMovementResponse])
async def get_stock_movements(
    product_id: Optional[str] = None,
    branch_id: Optional[str] = None,
    movement_type: Optional[StockMovementType] = None,
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
    current_user: dict = Depends(get_current_user)
):
    """Get stock movements"""
    query = get_tenant_filter(current_user)
    if product_id:
        query["product_id"] = product_id
    if branch_id:
        query["branch_id"] = branch_id
    if movement_type:
        query["movement_type"] = movement_type.value
    if start_date:
        query["created_at"] = {"$gte": start_date}
    if end_date:
        query.setdefault("created_at", {})["$lte"] = end_date
    
    movements = await db.stock_movements.find(query, {"_id": 0}).sort("created_at", -1).to_list(10000)
    return [StockMovementResponse(**m) for m in movements]
