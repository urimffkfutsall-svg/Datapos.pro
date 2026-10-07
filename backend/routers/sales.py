"""Sales routes with debt management"""
from fastapi import APIRouter, HTTPException, Depends, Header
from typing import List, Optional
from datetime import datetime, timezone

from database import db
from sale_service import save_sale, SaleError
from report_dates import date_filter, period_query
from auth import require_role
from models import (
    SaleCreate, SaleResponse, Sale, SaleItem,
    StockMovement, StockMovementType,
    CashDrawerStatus, PaymentMethod, UserRole,
    PayDebtRequest
)
from auth import get_current_user, get_tenant_filter, add_tenant_id, log_audit

router = APIRouter(prefix="/sales", tags=["Sales"])


@router.post("", response_model=SaleResponse)
async def create_sale(sale_data: SaleCreate, current_user: dict = Depends(get_current_user),
                      idempotency_key: Optional[str] = Header(None, alias="Idempotency-Key")):
    try:
        doc = await save_sale(db, sale_data.model_dump(mode="json"), current_user,
                              get_tenant_filter(current_user), idempotency_key)
        return SaleResponse(**doc)
    except SaleError as error:
        raise HTTPException(status_code=error.status, detail=error.detail) from error


@router.get("/readiness")
async def sale_readiness(current_user: dict = Depends(get_current_user)):
    """Authenticated pre-deployment check; never exposes connection strings."""
    hello = await db.command("hello")
    capable = bool(hello.get("setName") or hello.get("msg") == "isdbgrid") and hello.get("logicalSessionTimeoutMinutes") is not None and hello.get("maxWireVersion", 0) >= 9
    return {"transaction_capable": capable, "idempotent_sales": True, "money_version": "cents-v1"}


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
    if start_date or end_date:
        query.update(period_query({}, date_filter(start_date, end_date)))
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
    
    if start_date or end_date:
        query.update(period_query({}, date_filter(start_date, end_date)))
    
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


@router.delete("/{sale_id}")
async def delete_sale(sale_id: str, current_user: dict = Depends(require_role([UserRole.ADMIN]))):
    """Remove a sale from reports, keeping an audit/archive; not a stock return."""
    tenant_filter = get_tenant_filter(current_user)
    if not tenant_filter.get("tenant_id"):
        raise HTTPException(status_code=403, detail="Zgjidhni firmën për këtë veprim")
    query = {"id": sale_id, **tenant_filter}
    sale = await db.sales.find_one(query, {"_id": 0})
    if not sale:
        raise HTTPException(status_code=404, detail="Shitja nuk u gjet")
    archive = {**sale, "deleted_at": datetime.now(timezone.utc).isoformat(),
               "deleted_by": current_user["id"]}
    await db.deleted_sales.update_one(query, {"$setOnInsert": archive}, upsert=True)
    result = await db.sales.delete_one(query)
    if result.deleted_count == 0:
        raise HTTPException(status_code=404, detail="Shitja është fshirë tashmë")
    if sale.get("cash_drawer_id") and (not sale.get("is_debt") or sale.get("request_id")):
        # New atomic sales include partial cash for debts; historical debts used the old balance rule.
        net_cash = sale.get("cash_amount", 0) - sale.get("change_amount", 0)
        await db.cash_drawers.update_one({"id": sale["cash_drawer_id"], **tenant_filter},
                                          {"$inc": {"expected_balance": -net_cash}})
    await log_audit(current_user["id"], "delete_sale", "sale", sale_id,
                    {"tenant_id": current_user["tenant_id"], "total": sale.get("grand_total", 0)})
    return {"success": True, "message": "Shitja u fshi nga raportet"}
