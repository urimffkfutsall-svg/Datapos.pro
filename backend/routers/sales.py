"""Sales routes with debt management"""
from fastapi import APIRouter, HTTPException, Depends
from typing import List, Optional
from datetime import datetime, timezone

from database import db
from models import (
    SaleCreate, SaleResponse, Sale, SaleItem,
    StockMovement, StockMovementType,
    CashDrawerStatus, PaymentMethod, UserRole,
    PayDebtRequest
)
from auth import get_current_user, get_tenant_filter, add_tenant_id, log_audit

router = APIRouter(prefix="/sales", tags=["Sales"])


async def generate_receipt_number(branch_id: str = None, tenant_id: str = None) -> str:
    """Generate a unique receipt number"""
    today = datetime.now(timezone.utc).strftime("%Y%m%d")
    prefix = f"RCP-{today}"
    query = {"receipt_number": {"$regex": f"^{prefix}"}}
    if tenant_id:
        query["tenant_id"] = tenant_id
    count = await db.sales.count_documents(query)
    return f"{prefix}-{str(count + 1).zfill(4)}"


@router.post("", response_model=SaleResponse)
async def create_sale(sale_data: SaleCreate, current_user: dict = Depends(get_current_user)):
    """Create a new sale (with optional debt)"""
    tenant_filter = get_tenant_filter(current_user)
    
    drawer = await db.cash_drawers.find_one({
        "user_id": current_user["id"],
        "status": CashDrawerStatus.OPEN.value,
        **tenant_filter
    }, {"_id": 0})
    
    items = []
    subtotal = 0
    total_discount = 0
    total_vat = 0
    
    for item_data in sale_data.items:
        product = await db.products.find_one({"id": item_data.product_id, **tenant_filter}, {"_id": 0})
        if not product:
            raise HTTPException(status_code=404, detail=f"Produkti {item_data.product_id} nuk u gjet")
        
        item_subtotal = item_data.quantity * item_data.unit_price
        item_discount = item_subtotal * (item_data.discount_percent / 100)
        item_after_discount = item_subtotal - item_discount
        item_vat = item_after_discount * (item_data.vat_percent / 100)
        item_total = item_after_discount + item_vat
        
        items.append(SaleItem(
            product_id=item_data.product_id,
            product_name=product.get("name"),
            quantity=item_data.quantity,
            unit_price=item_data.unit_price,
            discount_percent=item_data.discount_percent,
            vat_percent=item_data.vat_percent,
            subtotal=item_subtotal,
            vat_amount=item_vat,
            total=item_total
        ))
        
        subtotal += item_subtotal
        total_discount += item_discount
        total_vat += item_vat
        
        new_stock = product.get("current_stock", 0) - item_data.quantity
        await db.products.update_one(
            {"id": item_data.product_id, **tenant_filter},
            {"$set": {"current_stock": new_stock, "updated_at": datetime.now(timezone.utc).isoformat()}}
        )
        
        movement = StockMovement(
            product_id=item_data.product_id,
            quantity=item_data.quantity,
            movement_type=StockMovementType.SALE,
            reason="Shitje",
            user_id=current_user["id"],
            branch_id=current_user.get("branch_id")
        )
        mov_doc = movement.model_dump()
        mov_doc['created_at'] = mov_doc['created_at'].isoformat()
        mov_doc = add_tenant_id(mov_doc, current_user)
        await db.stock_movements.insert_one(mov_doc)
    
    grand_total = subtotal - total_discount + total_vat
    
    # Handle debt logic
    is_debt = sale_data.is_debt
    remaining_debt = 0
    debtor_name = sale_data.debtor_name
    
    if is_debt:
        # If debt, remaining_debt is specified or defaults to grand_total
        if sale_data.remaining_debt is not None:
            remaining_debt = sale_data.remaining_debt
        else:
            remaining_debt = grand_total
        
        # Validate debtor name for debt sales
        if not debtor_name:
            raise HTTPException(status_code=400, detail="Emri i debitorit është i detyrueshëm për borxh")
    
    change_amount = 0
    if not is_debt and sale_data.payment_method == PaymentMethod.CASH:
        change_amount = (sale_data.cash_amount or 0) - grand_total
    
    receipt_number = await generate_receipt_number(current_user.get("branch_id"), current_user.get("tenant_id"))
    
    sale = Sale(
        receipt_number=receipt_number,
        items=[item.model_dump() for item in items],
        subtotal=round(subtotal, 2),
        total_discount=round(total_discount, 2),
        total_vat=round(total_vat, 2),
        grand_total=round(grand_total, 2),
        payment_method=sale_data.payment_method,
        cash_amount=sale_data.cash_amount or 0,
        bank_amount=sale_data.bank_amount or 0,
        change_amount=round(max(0, change_amount), 2),
        customer_name=sale_data.customer_name or debtor_name,
        notes=sale_data.notes,
        user_id=current_user["id"],
        branch_id=current_user.get("branch_id"),
        cash_drawer_id=drawer["id"] if drawer else None,
        # Debt fields
        is_debt=is_debt,
        debtor_name=debtor_name,
        remaining_debt=round(remaining_debt, 2)
    )
    
    doc = sale.model_dump()
    doc['created_at'] = doc['created_at'].isoformat()
    if doc.get('debt_paid_at'):
        doc['debt_paid_at'] = doc['debt_paid_at'].isoformat()
    doc = add_tenant_id(doc, current_user)
    await db.sales.insert_one(doc)
    
    # Only update cash drawer for non-debt sales
    if drawer and sale_data.cash_amount and not is_debt:
        new_expected = drawer["expected_balance"] + sale_data.cash_amount - change_amount
        await db.cash_drawers.update_one(
            {"id": drawer["id"], **tenant_filter},
            {"$set": {"expected_balance": new_expected}}
        )
    
    await log_audit(current_user["id"], "create_sale", "sale", sale.id, {
        "total": grand_total,
        "is_debt": is_debt,
        "remaining_debt": remaining_debt
    })
    return SaleResponse(**doc)


@router.get("", response_model=List[SaleResponse])
async def get_sales(
    branch_id: Optional[str] = None,
    user_id: Optional[str] = None,
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
    is_debt: Optional[bool] = None,
    limit: int = 100,
    current_user: dict = Depends(get_current_user)
):
    """Get sales with optional debt filter"""
    query = get_tenant_filter(current_user)
    if branch_id:
        query["branch_id"] = branch_id
    if user_id:
        query["user_id"] = user_id
    if start_date:
        query["created_at"] = {"$gte": start_date}
    if end_date:
        query.setdefault("created_at", {})["$lte"] = end_date
    if is_debt is not None:
        query["is_debt"] = is_debt
    
    sales = await db.sales.find(query, {"_id": 0}).sort("created_at", -1).to_list(limit)
    return [SaleResponse(**s) for s in sales]


@router.get("/debts", response_model=List[SaleResponse])
async def get_debts(
    status: Optional[str] = "unpaid",
    debtor_name: Optional[str] = None,
    limit: int = 100,
    current_user: dict = Depends(get_current_user)
):
    """Get all debt sales (admin only)"""
    if current_user.get("role") not in ["admin", "manager", "super_admin"]:
        raise HTTPException(status_code=403, detail="Vetëm administratori mund të shohë borxhet")
    
    query = {**get_tenant_filter(current_user), "is_debt": True}
    
    if status == "unpaid":
        query["remaining_debt"] = {"$gt": 0}
    elif status == "paid":
        query["remaining_debt"] = 0
    
    if debtor_name:
        query["debtor_name"] = {"$regex": debtor_name, "$options": "i"}
    
    debts = await db.sales.find(query, {"_id": 0}).sort("created_at", -1).to_list(limit)
    return [SaleResponse(**d) for d in debts]


@router.get("/debts/summary")
async def get_debt_summary(
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
    current_user: dict = Depends(get_current_user)
):
    """Get debt summary for reporting"""
    if current_user.get("role") not in ["admin", "manager", "super_admin"]:
        raise HTTPException(status_code=403, detail="Vetëm administratori mund të shohë përmbledhjen e borxheve")
    
    query = {**get_tenant_filter(current_user), "is_debt": True}
    
    if start_date:
        query["created_at"] = {"$gte": start_date}
    if end_date:
        query.setdefault("created_at", {})["$lte"] = end_date
    
    debts = await db.sales.find(query, {"_id": 0}).to_list(1000)
    
    total_debt = sum(d.get("grand_total", 0) for d in debts)
    total_paid = sum(d.get("grand_total", 0) - d.get("remaining_debt", 0) for d in debts)
    outstanding = sum(d.get("remaining_debt", 0) for d in debts)
    
    return {
        "total_debt": round(total_debt, 2),
        "total_paid": round(total_paid, 2),
        "outstanding": round(outstanding, 2),
        "debt_count": len(debts),
        "unpaid_count": len([d for d in debts if d.get("remaining_debt", 0) > 0])
    }


@router.post("/debts/{sale_id}/pay")
async def pay_debt(
    sale_id: str,
    payment: PayDebtRequest,
    current_user: dict = Depends(get_current_user)
):
    """Pay off a debt (admin only)"""
    if current_user.get("role") not in ["admin", "manager", "super_admin"]:
        raise HTTPException(status_code=403, detail="Vetëm administratori mund të mbyllë borxhet")
    
    tenant_filter = get_tenant_filter(current_user)
    query = {"id": sale_id, "is_debt": True, **tenant_filter}
    
    sale = await db.sales.find_one(query, {"_id": 0})
    if not sale:
        raise HTTPException(status_code=404, detail="Borxhi nuk u gjet")
    
    current_remaining = sale.get("remaining_debt", 0)
    if current_remaining <= 0:
        raise HTTPException(status_code=400, detail="Ky borxh është i paguar tashmë")
    
    if payment.amount <= 0:
        raise HTTPException(status_code=400, detail="Shuma e pagesës duhet të jetë pozitive")
    
    if payment.amount > current_remaining:
        raise HTTPException(status_code=400, detail=f"Shuma e pagesës ({payment.amount}€) tejkalon borxhin e mbetur ({current_remaining}€)")
    
    new_remaining = round(current_remaining - payment.amount, 2)
    
    update_data = {
        "remaining_debt": new_remaining,
        "debt_paid_by": current_user["id"]
    }
    
    if new_remaining == 0:
        update_data["debt_paid_at"] = datetime.now(timezone.utc).isoformat()
    
    # Add payment note
    existing_notes = sale.get("notes") or ""
    payment_note = f"\n[{datetime.now(timezone.utc).strftime('%d.%m.%Y %H:%M')}] Pagesa: {payment.amount}€"
    if payment.notes:
        payment_note += f" - {payment.notes}"
    update_data["notes"] = existing_notes + payment_note
    
    await db.sales.update_one(
        {"id": sale_id, **tenant_filter},
        {"$set": update_data}
    )
    
    await log_audit(current_user["id"], "pay_debt", "sale", sale_id, {
        "amount": payment.amount,
        "new_remaining": new_remaining
    })
    
    return {
        "success": True,
        "message": f"Pagesa u regjistrua me sukses",
        "paid_amount": payment.amount,
        "remaining_debt": new_remaining,
        "fully_paid": new_remaining == 0
    }


@router.get("/{sale_id}", response_model=SaleResponse)
async def get_sale(sale_id: str, current_user: dict = Depends(get_current_user)):
    """Get a sale by ID"""
    query = {"id": sale_id, **get_tenant_filter(current_user)}
    sale = await db.sales.find_one(query, {"_id": 0})
    if not sale:
        raise HTTPException(status_code=404, detail="Shitja nuk u gjet")
    return SaleResponse(**sale)
