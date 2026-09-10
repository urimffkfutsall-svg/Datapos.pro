"""Mobilshop Cash Drawer Router"""
from fastapi import APIRouter, HTTPException, Depends
from typing import List, Optional
from datetime import datetime, timezone
import uuid

from database import db
from auth import get_current_user
from mobilshop_models import (
    MobilshopCashDrawerOpen, MobilshopCashDrawerClose, MobilshopCashDrawerResponse
)

router = APIRouter(prefix="/mobilshop/cash-drawer", tags=["Mobilshop Cash Drawer"])


@router.get("/current", response_model=Optional[MobilshopCashDrawerResponse])
async def get_current_drawer(current_user: dict = Depends(get_current_user)):
    """Get current open cash drawer for the user"""
    tenant_id = current_user.get("tenant_id")
    user_id = current_user.get("id")
    
    drawer = await db.mobilshop_cash_drawers.find_one(
        {"user_id": user_id, "tenant_id": tenant_id, "status": "open"},
        {"_id": 0}
    )
    
    if drawer:
        # Get user name
        user = await db.users.find_one({"id": user_id}, {"_id": 0, "full_name": 1})
        drawer["user_name"] = user["full_name"] if user else "Unknown"
    
    return drawer


@router.post("/open", response_model=MobilshopCashDrawerResponse)
async def open_drawer(
    data: MobilshopCashDrawerOpen,
    current_user: dict = Depends(get_current_user)
):
    """Open a new cash drawer"""
    tenant_id = current_user.get("tenant_id")
    user_id = current_user.get("id")
    
    # Check if there's already an open drawer
    existing = await db.mobilshop_cash_drawers.find_one(
        {"user_id": user_id, "tenant_id": tenant_id, "status": "open"}
    )
    
    if existing:
        raise HTTPException(status_code=400, detail="Tashmë keni një arkë të hapur. Mbylleni atë para se të hapni një të re.")
    
    now = datetime.now(timezone.utc).isoformat()
    
    drawer = {
        "id": str(uuid.uuid4()),
        "tenant_id": tenant_id,
        "user_id": user_id,
        "opening_balance": data.opening_balance,
        "current_balance": data.opening_balance,
        "expected_balance": data.opening_balance,
        "cash_sales": 0,
        "card_sales": 0,
        "total_sales": 0,
        "status": "open",
        "transactions": [
            {
                "type": "open",
                "amount": data.opening_balance,
                "description": "Hapja e arkës",
                "timestamp": now
            }
        ],
        "opened_at": now,
        "closed_at": None,
        "closing_notes": None
    }
    
    await db.mobilshop_cash_drawers.insert_one(drawer)
    drawer.pop("_id", None)
    
    # Get user name
    user = await db.users.find_one({"id": user_id}, {"_id": 0, "full_name": 1})
    drawer["user_name"] = user["full_name"] if user else "Unknown"
    
    return drawer


@router.post("/close", response_model=MobilshopCashDrawerResponse)
async def close_drawer(
    data: MobilshopCashDrawerClose,
    current_user: dict = Depends(get_current_user)
):
    """Close the current cash drawer"""
    tenant_id = current_user.get("tenant_id")
    user_id = current_user.get("id")
    
    drawer = await db.mobilshop_cash_drawers.find_one(
        {"user_id": user_id, "tenant_id": tenant_id, "status": "open"}
    )
    
    if not drawer:
        raise HTTPException(status_code=400, detail="Nuk keni arkë të hapur")
    
    now = datetime.now(timezone.utc).isoformat()
    difference = data.actual_balance - drawer.get("expected_balance", 0)
    
    closing_transaction = {
        "type": "close",
        "amount": data.actual_balance,
        "expected": drawer.get("expected_balance", 0),
        "difference": difference,
        "description": data.notes or "Mbyllja e arkës",
        "timestamp": now
    }
    
    await db.mobilshop_cash_drawers.update_one(
        {"id": drawer["id"]},
        {
            "$set": {
                "status": "closed",
                "current_balance": data.actual_balance,
                "closed_at": now,
                "closing_notes": data.notes,
                "difference": difference
            },
            "$push": {"transactions": closing_transaction}
        }
    )
    
    updated_drawer = await db.mobilshop_cash_drawers.find_one(
        {"id": drawer["id"]},
        {"_id": 0}
    )
    
    # Get user name
    user = await db.users.find_one({"id": user_id}, {"_id": 0, "full_name": 1})
    updated_drawer["user_name"] = user["full_name"] if user else "Unknown"
    
    return updated_drawer


@router.post("/transaction")
async def add_transaction(
    amount: float,
    transaction_type: str,  # in, out, sale
    description: str = "",
    current_user: dict = Depends(get_current_user)
):
    """Add a manual transaction to the drawer"""
    tenant_id = current_user.get("tenant_id")
    user_id = current_user.get("id")
    
    drawer = await db.mobilshop_cash_drawers.find_one(
        {"user_id": user_id, "tenant_id": tenant_id, "status": "open"}
    )
    
    if not drawer:
        raise HTTPException(status_code=400, detail="Nuk keni arkë të hapur")
    
    now = datetime.now(timezone.utc).isoformat()
    
    transaction = {
        "type": transaction_type,
        "amount": amount,
        "description": description,
        "timestamp": now
    }
    
    # Update balance
    if transaction_type == "in":
        balance_change = amount
    elif transaction_type == "out":
        balance_change = -amount
    else:
        balance_change = amount
    
    await db.mobilshop_cash_drawers.update_one(
        {"id": drawer["id"]},
        {
            "$inc": {
                "current_balance": balance_change,
                "expected_balance": balance_change
            },
            "$push": {"transactions": transaction}
        }
    )
    
    return {"message": "Transaksioni u regjistrua", "amount": amount}


@router.get("/history")
async def get_drawer_history(
    date_from: Optional[str] = None,
    date_to: Optional[str] = None,
    current_user: dict = Depends(get_current_user)
):
    """Get cash drawer history"""
    tenant_id = current_user.get("tenant_id")
    
    query = {"tenant_id": tenant_id, "status": "closed"}
    
    if date_from:
        query["opened_at"] = {"$gte": date_from}
    if date_to:
        if "opened_at" in query:
            query["opened_at"]["$lte"] = date_to + "T23:59:59"
        else:
            query["opened_at"] = {"$lte": date_to + "T23:59:59"}
    
    drawers = await db.mobilshop_cash_drawers.find(
        query,
        {"_id": 0}
    ).sort("closed_at", -1).to_list(100)
    
    # Add user names
    for drawer in drawers:
        user = await db.users.find_one(
            {"id": drawer["user_id"]},
            {"_id": 0, "full_name": 1}
        )
        drawer["user_name"] = user["full_name"] if user else "Unknown"
    
    return drawers
