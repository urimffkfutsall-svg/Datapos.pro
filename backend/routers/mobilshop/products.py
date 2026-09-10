"""Mobilshop Products Router - Phones & Accessories Inventory"""
from fastapi import APIRouter, HTTPException, Depends
from typing import List, Optional
from datetime import datetime, timezone
import uuid

from database import db
from auth import get_current_user
from mobilshop_models import (
    MobilshopProductCreate, MobilshopProductUpdate, MobilshopProductResponse,
    ProductType, SupplierCreate, SupplierUpdate, SupplierResponse
)

router = APIRouter(prefix="/mobilshop/products", tags=["Mobilshop Products"])


# ============ SUPPLIERS ============
@router.get("/suppliers", response_model=List[SupplierResponse])
async def get_suppliers(current_user: dict = Depends(get_current_user)):
    """Get all suppliers for the tenant"""
    tenant_id = current_user.get("tenant_id")
    suppliers = await db.mobilshop_suppliers.find(
        {"tenant_id": tenant_id},
        {"_id": 0}
    ).sort("name", 1).to_list(1000)
    return suppliers


@router.post("/suppliers", response_model=SupplierResponse)
async def create_supplier(
    data: SupplierCreate,
    current_user: dict = Depends(get_current_user)
):
    """Create a new supplier"""
    tenant_id = current_user.get("tenant_id")
    
    supplier = {
        "id": str(uuid.uuid4()),
        "tenant_id": tenant_id,
        "name": data.name,
        "contact_person": data.contact_person,
        "phone": data.phone,
        "email": data.email,
        "address": data.address,
        "notes": data.notes,
        "is_active": True,
        "created_at": datetime.now(timezone.utc).isoformat()
    }
    
    await db.mobilshop_suppliers.insert_one(supplier)
    supplier.pop("_id", None)
    return supplier


@router.put("/suppliers/{supplier_id}", response_model=SupplierResponse)
async def update_supplier(
    supplier_id: str,
    data: SupplierUpdate,
    current_user: dict = Depends(get_current_user)
):
    """Update a supplier"""
    tenant_id = current_user.get("tenant_id")
    
    update_data = {k: v for k, v in data.model_dump().items() if v is not None}
    if not update_data:
        raise HTTPException(status_code=400, detail="Asnjë të dhënë për përditësim")
    
    result = await db.mobilshop_suppliers.update_one(
        {"id": supplier_id, "tenant_id": tenant_id},
        {"$set": update_data}
    )
    
    if result.matched_count == 0:
        raise HTTPException(status_code=404, detail="Furnitori nuk u gjet")
    
    supplier = await db.mobilshop_suppliers.find_one(
        {"id": supplier_id, "tenant_id": tenant_id},
        {"_id": 0}
    )
    return supplier


# ============ PRODUCTS ============
@router.get("", response_model=List[MobilshopProductResponse])
async def get_products(
    product_type: Optional[ProductType] = None,
    category: Optional[str] = None,
    brand: Optional[str] = None,
    search: Optional[str] = None,
    low_stock: Optional[bool] = None,
    is_sold: Optional[bool] = None,
    current_user: dict = Depends(get_current_user)
):
    """Get all products with optional filters"""
    tenant_id = current_user.get("tenant_id")
    
    query = {"tenant_id": tenant_id, "is_active": True}
    
    if product_type:
        query["product_type"] = product_type
    if category:
        query["category"] = category
    if brand:
        query["brand"] = {"$regex": brand, "$options": "i"}
    if is_sold is not None:
        query["is_sold"] = is_sold
    if search:
        query["$or"] = [
            {"name": {"$regex": search, "$options": "i"}},
            {"imei": {"$regex": search, "$options": "i"}},
            {"serial_number": {"$regex": search, "$options": "i"}},
            {"barcode": {"$regex": search, "$options": "i"}},
            {"model": {"$regex": search, "$options": "i"}}
        ]
    
    products = await db.mobilshop_products.find(query, {"_id": 0}).sort("created_at", -1).to_list(5000)
    
    # Add supplier names
    for product in products:
        if product.get("supplier_id"):
            supplier = await db.mobilshop_suppliers.find_one(
                {"id": product["supplier_id"]},
                {"_id": 0, "name": 1}
            )
            product["supplier_name"] = supplier["name"] if supplier else None
        else:
            product["supplier_name"] = None
    
    # Filter low stock if requested
    if low_stock:
        products = [p for p in products if p.get("quantity", 0) <= p.get("min_stock", 1)]
    
    return products


@router.get("/phones", response_model=List[MobilshopProductResponse])
async def get_phones(
    brand: Optional[str] = None,
    is_sold: Optional[bool] = False,
    current_user: dict = Depends(get_current_user)
):
    """Get all phones (with IMEI tracking)"""
    tenant_id = current_user.get("tenant_id")
    
    query = {
        "tenant_id": tenant_id,
        "product_type": ProductType.PHONE,
        "is_active": True,
        "is_sold": is_sold
    }
    
    if brand:
        query["brand"] = {"$regex": brand, "$options": "i"}
    
    products = await db.mobilshop_products.find(query, {"_id": 0}).sort("created_at", -1).to_list(5000)
    return products


@router.get("/accessories", response_model=List[MobilshopProductResponse])
async def get_accessories(
    category: Optional[str] = None,
    current_user: dict = Depends(get_current_user)
):
    """Get all accessories (quantity-based)"""
    tenant_id = current_user.get("tenant_id")
    
    query = {
        "tenant_id": tenant_id,
        "product_type": ProductType.ACCESSORY,
        "is_active": True
    }
    
    if category:
        query["category"] = category
    
    products = await db.mobilshop_products.find(query, {"_id": 0}).sort("created_at", -1).to_list(5000)
    return products


@router.get("/low-stock", response_model=List[MobilshopProductResponse])
async def get_low_stock(current_user: dict = Depends(get_current_user)):
    """Get products with low stock"""
    tenant_id = current_user.get("tenant_id")
    
    # Get all active products
    products = await db.mobilshop_products.find(
        {"tenant_id": tenant_id, "is_active": True, "is_sold": False},
        {"_id": 0}
    ).to_list(5000)
    
    # Filter low stock
    low_stock = [p for p in products if p.get("quantity", 0) <= p.get("min_stock", 1)]
    return low_stock


@router.get("/search/{query}")
async def search_products(
    query: str,
    current_user: dict = Depends(get_current_user)
):
    """Search products by IMEI, barcode, name, or model"""
    tenant_id = current_user.get("tenant_id")
    
    products = await db.mobilshop_products.find(
        {
            "tenant_id": tenant_id,
            "is_active": True,
            "$or": [
                {"imei": {"$regex": query, "$options": "i"}},
                {"serial_number": {"$regex": query, "$options": "i"}},
                {"barcode": {"$regex": query, "$options": "i"}},
                {"name": {"$regex": query, "$options": "i"}},
                {"model": {"$regex": query, "$options": "i"}}
            ]
        },
        {"_id": 0}
    ).to_list(100)
    
    return products


@router.get("/{product_id}", response_model=MobilshopProductResponse)
async def get_product(
    product_id: str,
    current_user: dict = Depends(get_current_user)
):
    """Get a single product by ID"""
    tenant_id = current_user.get("tenant_id")
    
    product = await db.mobilshop_products.find_one(
        {"id": product_id, "tenant_id": tenant_id},
        {"_id": 0}
    )
    
    if not product:
        raise HTTPException(status_code=404, detail="Produkti nuk u gjet")
    
    # Add supplier name
    if product.get("supplier_id"):
        supplier = await db.mobilshop_suppliers.find_one(
            {"id": product["supplier_id"]},
            {"_id": 0, "name": 1}
        )
        product["supplier_name"] = supplier["name"] if supplier else None
    
    return product


@router.post("", response_model=MobilshopProductResponse)
async def create_product(
    data: MobilshopProductCreate,
    current_user: dict = Depends(get_current_user)
):
    """Create a new product"""
    tenant_id = current_user.get("tenant_id")
    
    # Check for duplicate IMEI
    if data.imei:
        existing = await db.mobilshop_products.find_one(
            {"imei": data.imei, "tenant_id": tenant_id}
        )
        if existing:
            raise HTTPException(status_code=400, detail=f"IMEI {data.imei} ekziston tashmë")
    
    now = datetime.now(timezone.utc).isoformat()
    
    product = {
        "id": str(uuid.uuid4()),
        "tenant_id": tenant_id,
        "name": data.name,
        "product_type": data.product_type,
        "brand": data.brand,
        "model": data.model,
        "sku": data.sku or str(uuid.uuid4())[:8].upper(),
        "barcode": data.barcode,
        "imei": data.imei,
        "serial_number": data.serial_number,
        "purchase_price": data.purchase_price,
        "sale_price": data.sale_price,
        "category": data.category,
        "color": data.color,
        "storage": data.storage,
        "condition": data.condition,
        "warranty_months": data.warranty_months,
        "supplier_id": data.supplier_id,
        "location": data.location,
        "quantity": data.quantity,
        "min_stock": data.min_stock,
        "description": data.description,
        "specifications": data.specifications,
        "is_active": True,
        "is_sold": False,
        "created_at": now,
        "updated_at": now,
        "created_by": current_user.get("id")
    }
    
    await db.mobilshop_products.insert_one(product)
    product.pop("_id", None)
    product["supplier_name"] = None
    
    return product


@router.put("/{product_id}", response_model=MobilshopProductResponse)
async def update_product(
    product_id: str,
    data: MobilshopProductUpdate,
    current_user: dict = Depends(get_current_user)
):
    """Update a product"""
    tenant_id = current_user.get("tenant_id")
    
    update_data = {k: v for k, v in data.model_dump().items() if v is not None}
    if not update_data:
        raise HTTPException(status_code=400, detail="Asnjë të dhënë për përditësim")
    
    update_data["updated_at"] = datetime.now(timezone.utc).isoformat()
    
    # Check IMEI uniqueness if updating
    if data.imei:
        existing = await db.mobilshop_products.find_one(
            {"imei": data.imei, "tenant_id": tenant_id, "id": {"$ne": product_id}}
        )
        if existing:
            raise HTTPException(status_code=400, detail=f"IMEI {data.imei} ekziston tashmë")
    
    result = await db.mobilshop_products.update_one(
        {"id": product_id, "tenant_id": tenant_id},
        {"$set": update_data}
    )
    
    if result.matched_count == 0:
        raise HTTPException(status_code=404, detail="Produkti nuk u gjet")
    
    product = await db.mobilshop_products.find_one(
        {"id": product_id, "tenant_id": tenant_id},
        {"_id": 0}
    )
    
    # Add supplier name
    if product.get("supplier_id"):
        supplier = await db.mobilshop_suppliers.find_one(
            {"id": product["supplier_id"]},
            {"_id": 0, "name": 1}
        )
        product["supplier_name"] = supplier["name"] if supplier else None
    
    return product


@router.delete("/{product_id}")
async def delete_product(
    product_id: str,
    current_user: dict = Depends(get_current_user)
):
    """Soft delete a product"""
    tenant_id = current_user.get("tenant_id")
    
    result = await db.mobilshop_products.update_one(
        {"id": product_id, "tenant_id": tenant_id},
        {"$set": {"is_active": False, "updated_at": datetime.now(timezone.utc).isoformat()}}
    )
    
    if result.matched_count == 0:
        raise HTTPException(status_code=404, detail="Produkti nuk u gjet")
    
    return {"message": "Produkti u fshi me sukses"}


@router.get("/categories/list")
async def get_categories(current_user: dict = Depends(get_current_user)):
    """Get all unique categories"""
    tenant_id = current_user.get("tenant_id")
    
    categories = await db.mobilshop_products.distinct(
        "category",
        {"tenant_id": tenant_id, "is_active": True}
    )
    
    return [c for c in categories if c]


@router.get("/brands/list")
async def get_brands(current_user: dict = Depends(get_current_user)):
    """Get all unique brands"""
    tenant_id = current_user.get("tenant_id")
    
    brands = await db.mobilshop_products.distinct(
        "brand",
        {"tenant_id": tenant_id, "is_active": True}
    )
    
    return [b for b in brands if b]
