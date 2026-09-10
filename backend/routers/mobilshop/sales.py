"""Mobilshop Sales Router - POS & Invoicing"""
from fastapi import APIRouter, HTTPException, Depends
from typing import List, Optional
from datetime import datetime, timezone, timedelta
import uuid

from database import db
from auth import get_current_user
from mobilshop_models import (
    MobilshopSaleCreate, MobilshopSaleResponse, SaleItemResponse,
    PaymentMethod, ProductType
)

router = APIRouter(prefix="/mobilshop/sales", tags=["Mobilshop Sales"])


async def generate_invoice_number(tenant_id: str) -> str:
    """Generate unique invoice number"""
    today = datetime.now(timezone.utc).strftime("%Y%m%d")
    
    count = await db.mobilshop_sales.count_documents({
        "tenant_id": tenant_id,
        "created_at": {"$regex": f"^{today[:4]}-{today[4:6]}-{today[6:8]}"}
    })
    
    return f"INV-{today}-{count + 1:04d}"


@router.get("", response_model=List[MobilshopSaleResponse])
async def get_sales(
    date_from: Optional[str] = None,
    date_to: Optional[str] = None,
    customer_id: Optional[str] = None,
    payment_method: Optional[PaymentMethod] = None,
    current_user: dict = Depends(get_current_user)
):
    """Get all sales with optional filters"""
    tenant_id = current_user.get("tenant_id")
    
    query = {"tenant_id": tenant_id}
    
    if customer_id:
        query["customer_id"] = customer_id
    if payment_method:
        query["payment_method"] = payment_method
    if date_from:
        query["created_at"] = {"$gte": date_from}
    if date_to:
        if "created_at" in query:
            query["created_at"]["$lte"] = date_to + "T23:59:59"
        else:
            query["created_at"] = {"$lte": date_to + "T23:59:59"}
    
    sales = await db.mobilshop_sales.find(query, {"_id": 0}).sort("created_at", -1).to_list(1000)
    return sales


@router.get("/today")
async def get_today_sales(current_user: dict = Depends(get_current_user)):
    """Get today's sales summary"""
    tenant_id = current_user.get("tenant_id")
    today = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    
    sales = await db.mobilshop_sales.find(
        {
            "tenant_id": tenant_id,
            "created_at": {"$regex": f"^{today}"}
        },
        {"_id": 0}
    ).to_list(1000)
    
    total = sum(s.get("grand_total", 0) for s in sales)
    cash = sum(s.get("cash_amount", 0) for s in sales)
    card = sum(s.get("card_amount", 0) for s in sales)
    
    return {
        "date": today,
        "total_sales": len(sales),
        "total_revenue": total,
        "cash_amount": cash,
        "card_amount": card,
        "sales": sales
    }


@router.get("/{sale_id}", response_model=MobilshopSaleResponse)
async def get_sale(
    sale_id: str,
    current_user: dict = Depends(get_current_user)
):
    """Get a single sale/invoice"""
    tenant_id = current_user.get("tenant_id")
    
    sale = await db.mobilshop_sales.find_one(
        {"id": sale_id, "tenant_id": tenant_id},
        {"_id": 0}
    )
    
    if not sale:
        raise HTTPException(status_code=404, detail="Shitja nuk u gjet")
    
    return sale


@router.post("", response_model=MobilshopSaleResponse)
async def create_sale(
    data: MobilshopSaleCreate,
    current_user: dict = Depends(get_current_user)
):
    """Create a new sale/invoice"""
    tenant_id = current_user.get("tenant_id")
    
    # Get customer info if provided
    customer_name = None
    customer_phone = None
    if data.customer_id:
        customer = await db.mobilshop_customers.find_one(
            {"id": data.customer_id, "tenant_id": tenant_id},
            {"_id": 0}
        )
        if customer:
            customer_name = customer["full_name"]
            customer_phone = customer["phone"]
    
    # Process items
    items = []
    subtotal = 0
    
    for item in data.items:
        product = await db.mobilshop_products.find_one(
            {"id": item.product_id, "tenant_id": tenant_id},
            {"_id": 0}
        )
        
        if not product:
            raise HTTPException(status_code=404, detail=f"Produkti {item.product_id} nuk u gjet")
        
        # Check stock for accessories
        if product["product_type"] == ProductType.ACCESSORY:
            if product.get("quantity", 0) < item.quantity:
                raise HTTPException(
                    status_code=400, 
                    detail=f"Stoku i pamjaftueshëm për {product['name']}"
                )
        else:
            # For phones, check if already sold
            if product.get("is_sold"):
                raise HTTPException(
                    status_code=400,
                    detail=f"Telefoni {product['name']} është shitur tashmë"
                )
        
        item_subtotal = item.unit_price * item.quantity
        item_discount = (item_subtotal * item.discount_percent / 100) + item.discount_amount
        item_total = item_subtotal - item_discount
        
        items.append({
            "product_id": item.product_id,
            "product_name": product["name"],
            "product_type": product["product_type"],
            "imei": product.get("imei"),
            "quantity": item.quantity,
            "unit_price": item.unit_price,
            "discount_percent": item.discount_percent,
            "discount_amount": item.discount_amount,
            "subtotal": item_subtotal,
            "total": item_total
        })
        
        subtotal += item_subtotal
        
        # Update inventory
        if product["product_type"] == ProductType.ACCESSORY:
            await db.mobilshop_products.update_one(
                {"id": item.product_id},
                {"$inc": {"quantity": -item.quantity}}
            )
        else:
            # Mark phone as sold
            await db.mobilshop_products.update_one(
                {"id": item.product_id},
                {"$set": {"is_sold": True, "sold_at": datetime.now(timezone.utc).isoformat()}}
            )
    
    # Calculate totals
    total_discount = (subtotal * data.discount_percent / 100) + data.discount_amount
    grand_total = subtotal - total_discount
    
    # Calculate change
    total_paid = data.cash_amount + data.card_amount
    change_amount = max(0, total_paid - grand_total)
    
    now = datetime.now(timezone.utc).isoformat()
    invoice_number = await generate_invoice_number(tenant_id)
    
    # Get user info
    user = await db.users.find_one({"id": current_user.get("id")}, {"_id": 0, "full_name": 1})
    user_name = user["full_name"] if user else "Unknown"
    
    sale = {
        "id": str(uuid.uuid4()),
        "tenant_id": tenant_id,
        "invoice_number": invoice_number,
        "customer_id": data.customer_id,
        "customer_name": customer_name,
        "customer_phone": customer_phone,
        "items": items,
        "subtotal": subtotal,
        "discount_percent": data.discount_percent,
        "discount_amount": data.discount_amount,
        "total_discount": total_discount,
        "grand_total": grand_total,
        "payment_method": data.payment_method,
        "cash_amount": data.cash_amount,
        "card_amount": data.card_amount,
        "change_amount": change_amount,
        "notes": data.notes,
        "warranty_terms": data.warranty_terms,
        "user_id": current_user.get("id"),
        "user_name": user_name,
        "created_at": now
    }
    
    await db.mobilshop_sales.insert_one(sale)
    sale.pop("_id", None)
    
    # Update customer loyalty points (1 point per euro spent)
    if data.customer_id:
        points = int(grand_total)
        await db.mobilshop_customers.update_one(
            {"id": data.customer_id},
            {"$inc": {"loyalty_points": points}}
        )
    
    return sale


@router.get("/invoice/{invoice_number}")
async def get_by_invoice_number(
    invoice_number: str,
    current_user: dict = Depends(get_current_user)
):
    """Get sale by invoice number"""
    tenant_id = current_user.get("tenant_id")
    
    sale = await db.mobilshop_sales.find_one(
        {"invoice_number": invoice_number, "tenant_id": tenant_id},
        {"_id": 0}
    )
    
    if not sale:
        raise HTTPException(status_code=404, detail="Fatura nuk u gjet")
    
    return sale


@router.delete("/{sale_id}")
async def void_sale(
    sale_id: str,
    reason: str = "Anulim",
    current_user: dict = Depends(get_current_user)
):
    """Void/cancel a sale and restore inventory"""
    tenant_id = current_user.get("tenant_id")
    user_role = current_user.get("role")
    
    if user_role not in ["admin", "manager"]:
        raise HTTPException(status_code=403, detail="Vetëm admin/manager mund të anulojë shitje")
    
    sale = await db.mobilshop_sales.find_one(
        {"id": sale_id, "tenant_id": tenant_id}
    )
    
    if not sale:
        raise HTTPException(status_code=404, detail="Shitja nuk u gjet")
    
    # Restore inventory
    for item in sale.get("items", []):
        product = await db.mobilshop_products.find_one({"id": item["product_id"]})
        if product:
            if product["product_type"] == ProductType.ACCESSORY:
                await db.mobilshop_products.update_one(
                    {"id": item["product_id"]},
                    {"$inc": {"quantity": item["quantity"]}}
                )
            else:
                await db.mobilshop_products.update_one(
                    {"id": item["product_id"]},
                    {"$set": {"is_sold": False, "sold_at": None}}
                )
    
    # Mark sale as voided
    await db.mobilshop_sales.update_one(
        {"id": sale_id},
        {
            "$set": {
                "voided": True,
                "voided_at": datetime.now(timezone.utc).isoformat(),
                "voided_by": current_user.get("id"),
                "void_reason": reason
            }
        }
    )
    
    return {"message": "Shitja u anulua me sukses"}
