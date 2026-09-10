"""Cash drawer management routes"""
from fastapi import APIRouter, HTTPException, Depends
from datetime import datetime, timezone

from database import db
from models import (
    CashDrawerOpen, CashDrawerTransaction, CashDrawerResponse, CashDrawer,
    CashDrawerStatus, CloseDrawerRequest
)
from auth import get_current_user, get_tenant_filter, add_tenant_id, log_audit

router = APIRouter(prefix="/cashier", tags=["Cashier"])


@router.post("/open", response_model=CashDrawerResponse)
async def open_cash_drawer(drawer_data: CashDrawerOpen, current_user: dict = Depends(get_current_user)):
    """Open a new cash drawer"""
    tenant_filter = get_tenant_filter(current_user)
    existing = await db.cash_drawers.find_one({
        "user_id": current_user["id"],
        "status": CashDrawerStatus.OPEN.value,
        **tenant_filter
    })
    if existing:
        raise HTTPException(status_code=400, detail="Arka është tashmë e hapur")
    
    drawer = CashDrawer(
        user_id=current_user["id"],
        branch_id=drawer_data.branch_id or current_user.get("branch_id"),
        opening_balance=drawer_data.opening_balance,
        current_balance=drawer_data.opening_balance,
        expected_balance=drawer_data.opening_balance
    )
    doc = drawer.model_dump()
    doc['opened_at'] = doc['opened_at'].isoformat()
    doc = add_tenant_id(doc, current_user)
    await db.cash_drawers.insert_one(doc)
    await log_audit(current_user["id"], "open_drawer", "cash_drawer", drawer.id)
    
    return CashDrawerResponse(**{**doc, "closed_at": None})


@router.get("/current", response_model=CashDrawerResponse)
async def get_current_drawer(current_user: dict = Depends(get_current_user)):
    """Get current open cash drawer"""
    tenant_filter = get_tenant_filter(current_user)
    drawer = await db.cash_drawers.find_one({
        "user_id": current_user["id"],
        "status": CashDrawerStatus.OPEN.value,
        **tenant_filter
    }, {"_id": 0})
    if not drawer:
        raise HTTPException(status_code=404, detail="Nuk keni arkë të hapur")
    return CashDrawerResponse(**drawer)


@router.post("/transaction")
async def add_drawer_transaction(transaction: CashDrawerTransaction, current_user: dict = Depends(get_current_user)):
    """Add a transaction to the current drawer"""
    tenant_filter = get_tenant_filter(current_user)
    drawer = await db.cash_drawers.find_one({
        "user_id": current_user["id"],
        "status": CashDrawerStatus.OPEN.value,
        **tenant_filter
    }, {"_id": 0})
    if not drawer:
        raise HTTPException(status_code=404, detail="Nuk keni arkë të hapur")
    
    new_balance = drawer["current_balance"]
    if transaction.transaction_type == "in":
        new_balance += transaction.amount
    else:
        new_balance -= transaction.amount
    
    trans_record = {
        "amount": transaction.amount,
        "type": transaction.transaction_type,
        "description": transaction.description,
        "timestamp": datetime.now(timezone.utc).isoformat()
    }
    
    await db.cash_drawers.update_one(
        {"id": drawer["id"], **tenant_filter},
        {
            "$set": {"current_balance": new_balance},
            "$push": {"transactions": trans_record}
        }
    )
    
    return {"message": "Transaksioni u regjistrua", "new_balance": new_balance}


@router.post("/close")
async def close_cash_drawer(request: CloseDrawerRequest, current_user: dict = Depends(get_current_user)):
    """Close the current cash drawer"""
    tenant_filter = get_tenant_filter(current_user)
    drawer = await db.cash_drawers.find_one({
        "user_id": current_user["id"],
        "status": CashDrawerStatus.OPEN.value,
        **tenant_filter
    }, {"_id": 0})
    if not drawer:
        raise HTTPException(status_code=404, detail="Nuk keni arkë të hapur")
    
    actual_balance = request.actual_balance
    discrepancy = actual_balance - drawer["expected_balance"]
    
    # Get sales during this shift
    sales = await db.sales.find({
        "cash_drawer_id": drawer["id"],
        **tenant_filter
    }, {"_id": 0}).to_list(1000)
    
    # Calculate debt totals for this shift
    debt_sales = [s for s in sales if s.get("is_debt")]
    total_debt_amount = sum(s.get("remaining_debt", 0) for s in debt_sales)
    debt_count = len(debt_sales)
    
    await db.cash_drawers.update_one(
        {"id": drawer["id"], **tenant_filter},
        {"$set": {
            "status": CashDrawerStatus.CLOSED.value,
            "current_balance": actual_balance,
            "closed_at": datetime.now(timezone.utc).isoformat(),
            "total_debt_amount": total_debt_amount,
            "debt_count": debt_count
        }}
    )
    
    await log_audit(current_user["id"], "close_drawer", "cash_drawer", drawer["id"], {
        "discrepancy": discrepancy,
        "total_debt": total_debt_amount,
        "debt_count": debt_count
    })
    
    return {
        "message": "Arka u mbyll me sukses",
        "expected_balance": drawer["expected_balance"],
        "actual_balance": actual_balance,
        "discrepancy": discrepancy,
        "total_debt_amount": total_debt_amount,
        "debt_count": debt_count
    }


@router.get("/report/{drawer_id}")
async def get_drawer_report(drawer_id: str, current_user: dict = Depends(get_current_user)):
    """Get detailed report for a specific drawer session"""
    tenant_filter = get_tenant_filter(current_user)
    drawer = await db.cash_drawers.find_one({
        "id": drawer_id,
        **tenant_filter
    }, {"_id": 0})
    
    if not drawer:
        raise HTTPException(status_code=404, detail="Arka nuk u gjet")
    
    # Get all sales for this drawer
    sales = await db.sales.find({
        "cash_drawer_id": drawer_id,
        **tenant_filter
    }, {"_id": 0}).to_list(1000)
    
    # Calculate statistics
    total_sales = len(sales)
    total_revenue = sum(s.get("grand_total", 0) for s in sales if not s.get("is_debt"))
    total_cash = sum(s.get("cash_amount", 0) for s in sales if not s.get("is_debt"))
    total_bank = sum(s.get("bank_amount", 0) for s in sales if not s.get("is_debt"))
    
    # Debt statistics
    debt_sales = [s for s in sales if s.get("is_debt")]
    total_debt_amount = sum(s.get("remaining_debt", 0) for s in debt_sales)
    debt_count = len(debt_sales)
    
    # Get user info
    user = await db.users.find_one({"id": drawer.get("user_id")}, {"_id": 0, "full_name": 1})
    
    return {
        "drawer": drawer,
        "user_name": user.get("full_name") if user else "N/A",
        "statistics": {
            "total_sales": total_sales,
            "total_revenue": round(total_revenue, 2),
            "total_cash": round(total_cash, 2),
            "total_bank": round(total_bank, 2),
            "debt_count": debt_count,
            "total_debt_amount": round(total_debt_amount, 2)
        },
        "sales": sales,
        "debt_sales": debt_sales
    }
