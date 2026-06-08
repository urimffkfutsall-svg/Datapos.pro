"""Product management routes"""
from fastapi import APIRouter, HTTPException, Depends
from typing import List, Optional
from datetime import datetime, timezone

from database import db
from models import (
    ProductCreate, ProductUpdate, ProductResponse, Product,
    StockMovement, StockMovementType, StockMovementResponse,
    UserRole
)
from auth import (
    get_current_user, require_role,
    get_tenant_filter, add_tenant_id, log_audit
)

router = APIRouter(prefix="/products", tags=["Products"])


@router.post("", response_model=ProductResponse)
async def create_product(
    product_data: ProductCreate,
    current_user: dict = Depends(require_role([UserRole.ADMIN, UserRole.MANAGER]))
):
    """Create a new product"""
    product = Product(**product_data.model_dump())
    product.current_stock = product_data.initial_stock or 0
    doc = product.model_dump()
    doc['created_at'] = doc['created_at'].isoformat()
    doc['updated_at'] = doc['updated_at'].isoformat()
    doc = add_tenant_id(doc, current_user)
    await db.products.insert_one(doc)
    
    if product_data.initial_stock and product_data.initial_stock > 0:
        movement = StockMovement(
            product_id=product.id,
            quantity=product_data.initial_stock,
            movement_type=StockMovementType.IN,
            reason="Stok fillestar",
            user_id=current_user["id"],
            branch_id=product_data.branch_id
        )
        mov_doc = movement.model_dump()
        mov_doc['created_at'] = mov_doc['created_at'].isoformat()
        mov_doc = add_tenant_id(mov_doc, current_user)
        await db.stock_movements.insert_one(mov_doc)
    
    await log_audit(current_user["id"], "create_product", "product", product.id)
    return ProductResponse(**doc)


@router.get("", response_model=List[ProductResponse])
async def get_products(
    branch_id: Optional[str] = None,
    category: Optional[str] = None,
    search: Optional[str] = None,
    low_stock: Optional[bool] = None,
    current_user: dict = Depends(get_current_user)
):
    """Get all products"""
    query = get_tenant_filter(current_user)
    if branch_id:
        query["branch_id"] = branch_id
    if category:
        query["category"] = category
    if search:
        query["$or"] = [
            {"name": {"$regex": search, "$options": "i"}},
            {"barcode": {"$regex": search, "$options": "i"}}
        ]
    if low_stock:
        query["current_stock"] = {"$lt": 10}
    
    products = await db.products.find(query, {"_id": 0}).to_list(10000)
    return [ProductResponse(**p) for p in products]


@router.get("/{product_id}", response_model=ProductResponse)
async def get_product(product_id: str, current_user: dict = Depends(get_current_user)):
    """Get a product by ID"""
    query = {"id": product_id, **get_tenant_filter(current_user)}
    product = await db.products.find_one(query, {"_id": 0})
    if not product:
        raise HTTPException(status_code=404, detail="Produkti nuk u gjet")
    return ProductResponse(**product)


@router.get("/barcode/{barcode}", response_model=ProductResponse)
async def get_product_by_barcode(barcode: str, current_user: dict = Depends(get_current_user)):
    """Get a product by barcode"""
    query = {"barcode": barcode, **get_tenant_filter(current_user)}
    product = await db.products.find_one(query, {"_id": 0})
    if not product:
        raise HTTPException(status_code=404, detail="Produkti nuk u gjet")
    return ProductResponse(**product)


@router.put("/{product_id}", response_model=ProductResponse)
async def update_product(
    product_id: str,
    product_data: ProductUpdate,
    current_user: dict = Depends(require_role([UserRole.ADMIN, UserRole.MANAGER]))
):
    """Update a product"""
    tenant_filter = get_tenant_filter(current_user)
    update_dict = {k: v for k, v in product_data.model_dump().items() if v is not None}
    update_dict["updated_at"] = datetime.now(timezone.utc).isoformat()
    
    await db.products.update_one({"id": product_id, **tenant_filter}, {"$set": update_dict})
    product = await db.products.find_one({"id": product_id, **tenant_filter}, {"_id": 0})
    if not product:
        raise HTTPException(status_code=404, detail="Produkti nuk u gjet")
    
    await log_audit(current_user["id"], "update_product", "product", product_id)
    return ProductResponse(**product)


@router.delete("/{product_id}")
async def delete_product(product_id: str, current_user: dict = Depends(require_role([UserRole.ADMIN]))):
    """Delete a product"""
    tenant_filter = get_tenant_filter(current_user)
    result = await db.products.delete_one({"id": product_id, **tenant_filter})
    if result.deleted_count == 0:
        raise HTTPException(status_code=404, detail="Produkti nuk u gjet")
    await log_audit(current_user["id"], "delete_product", "product", product_id)
    return {"message": "Produkti u fshi me sukses"}
