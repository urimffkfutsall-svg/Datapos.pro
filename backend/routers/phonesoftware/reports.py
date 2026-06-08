"""PhoneSoftware Reports & Analytics Routes"""
from fastapi import APIRouter, HTTPException, Depends, Query
from typing import Optional
from datetime import datetime, timezone, timedelta
from io import BytesIO
import json

from .database import ps_repairs, ps_inventory, ps_customers, ps_sales, ps_users, ps_stock_movements
from .models import RepairStatus, InventoryCategory
from .database import get_ps_current_user

router = APIRouter(prefix="/phonesoftware/reports", tags=["PhoneSoftware Reports"])


@router.get("/dashboard")
async def get_dashboard_stats(current_user: dict = Depends(get_ps_current_user)):
    """Get main dashboard statistics"""
    tenant_id = current_user.get("tenant_id")
    if not tenant_id and current_user.get("role") != "super_admin":
        raise HTTPException(status_code=403, detail="Nuk keni akses")
    
    query = {"tenant_id": tenant_id} if tenant_id else {}
    
    today = datetime.now(timezone.utc).replace(hour=0, minute=0, second=0, microsecond=0)
    week_ago = today - timedelta(days=7)
    month_ago = today - timedelta(days=30)
    
    # Repairs stats
    total_repairs = await ps_repairs.count_documents(query)
    pending_repairs = await ps_repairs.count_documents({
        **query,
        "status": {"$nin": [RepairStatus.COMPLETED.value, RepairStatus.DELIVERED.value, RepairStatus.CANNOT_REPAIR.value]}
    })
    today_repairs = await ps_repairs.count_documents({
        **query,
        "created_at": {"$gte": today.isoformat()}
    })
    
    # Revenue
    completed_repairs = await ps_repairs.find({
        **query,
        "status": {"$in": [RepairStatus.COMPLETED.value, RepairStatus.DELIVERED.value]}
    }, {"_id": 0, "total_cost": 1, "completed_at": 1}).to_list(10000)
    
    total_revenue = sum(r.get("total_cost", 0) for r in completed_repairs)
    
    # This month's revenue
    month_repairs = [r for r in completed_repairs if r.get("completed_at") and r["completed_at"] >= month_ago.isoformat()]
    month_revenue = sum(r.get("total_cost", 0) for r in month_repairs)
    
    # Inventory stats
    inventory_query = {**query, "is_active": True}
    total_inventory = await ps_inventory.count_documents(inventory_query)
    low_stock = await ps_inventory.count_documents({
        **inventory_query,
        "$expr": {"$lte": ["$quantity", "$min_stock"]}
    })
    
    # Customer stats
    total_customers = await ps_customers.count_documents(query)
    
    # Staff stats
    total_staff = await ps_users.count_documents(query)
    
    # Recent repairs
    recent_repairs = await ps_repairs.find(query, {"_id": 0}).sort("created_at", -1).limit(5).to_list(5)
    
    # Enrich recent repairs
    for repair in recent_repairs:
        if repair.get("customer_id"):
            customer = await ps_customers.find_one({"id": repair["customer_id"]}, {"_id": 0})
            if customer:
                repair["customer_name"] = customer.get("full_name")
    
    return {
        "repairs": {
            "total": total_repairs,
            "pending": pending_repairs,
            "today": today_repairs
        },
        "revenue": {
            "total": total_revenue,
            "this_month": month_revenue
        },
        "inventory": {
            "total": total_inventory,
            "low_stock": low_stock
        },
        "customers": {
            "total": total_customers
        },
        "staff": {
            "total": total_staff
        },
        "recent_repairs": recent_repairs
    }


@router.get("/repairs")
async def get_repairs_report(
    date_from: Optional[str] = None,
    date_to: Optional[str] = None,
    status: Optional[RepairStatus] = None,
    current_user: dict = Depends(get_ps_current_user)
):
    """Get detailed repairs report"""
    tenant_id = current_user.get("tenant_id")
    if not tenant_id and current_user.get("role") != "super_admin":
        raise HTTPException(status_code=403, detail="Nuk keni akses")
    
    # Default to last 30 days
    if not date_from:
        date_from = (datetime.now(timezone.utc) - timedelta(days=30)).isoformat()
    if not date_to:
        date_to = datetime.now(timezone.utc).isoformat()
    
    query = {"created_at": {"$gte": date_from, "$lte": date_to}}
    if tenant_id:
        query["tenant_id"] = tenant_id
    if status:
        query["status"] = status.value
    
    repairs = await ps_repairs.find(query, {"_id": 0}).sort("created_at", -1).to_list(10000)
    
    # Calculate summary
    total_count = len(repairs)
    completed_count = len([r for r in repairs if r.get("status") in [RepairStatus.COMPLETED.value, RepairStatus.DELIVERED.value]])
    total_revenue = sum(r.get("total_cost", 0) for r in repairs if r.get("status") in [RepairStatus.COMPLETED.value, RepairStatus.DELIVERED.value])
    total_parts_cost = sum(r.get("parts_cost", 0) for r in repairs)
    total_labor = sum(r.get("labor_cost", 0) for r in repairs)
    
    # Status breakdown
    status_breakdown = {}
    for s in RepairStatus:
        status_breakdown[s.value] = len([r for r in repairs if r.get("status") == s.value])
    
    # Device type breakdown
    device_breakdown = {}
    for r in repairs:
        dt = r.get("device_type", "other")
        device_breakdown[dt] = device_breakdown.get(dt, 0) + 1
    
    return {
        "period": {"from": date_from, "to": date_to},
        "summary": {
            "total_repairs": total_count,
            "completed": completed_count,
            "completion_rate": round(completed_count / total_count * 100, 1) if total_count > 0 else 0,
            "total_revenue": total_revenue,
            "total_parts_cost": total_parts_cost,
            "total_labor": total_labor,
            "profit": total_revenue - total_parts_cost
        },
        "status_breakdown": status_breakdown,
        "device_breakdown": device_breakdown,
        "repairs": repairs[:100]  # Limit to 100 for response
    }


@router.get("/inventory")
async def get_inventory_report(
    category: Optional[InventoryCategory] = None,
    current_user: dict = Depends(get_ps_current_user)
):
    """Get inventory report"""
    tenant_id = current_user.get("tenant_id")
    if not tenant_id and current_user.get("role") != "super_admin":
        raise HTTPException(status_code=403, detail="Nuk keni akses")
    
    query = {"is_active": True}
    if tenant_id:
        query["tenant_id"] = tenant_id
    if category:
        query["category"] = category.value
    
    items = await ps_inventory.find(query, {"_id": 0}).to_list(10000)
    
    # Calculate totals
    total_items = len(items)
    total_quantity = sum(i.get("quantity", 0) for i in items)
    total_value = sum(i.get("quantity", 0) * i.get("purchase_price", 0) for i in items)
    potential_revenue = sum(i.get("quantity", 0) * i.get("sale_price", 0) for i in items)
    
    # Category breakdown
    category_breakdown = {}
    for cat in InventoryCategory:
        cat_items = [i for i in items if i.get("category") == cat.value]
        category_breakdown[cat.value] = {
            "count": len(cat_items),
            "quantity": sum(i.get("quantity", 0) for i in cat_items),
            "value": sum(i.get("quantity", 0) * i.get("purchase_price", 0) for i in cat_items)
        }
    
    # Low stock items
    low_stock_items = [i for i in items if i.get("quantity", 0) <= i.get("min_stock", 5)]
    
    return {
        "summary": {
            "total_items": total_items,
            "total_quantity": total_quantity,
            "total_value": total_value,
            "potential_revenue": potential_revenue,
            "potential_profit": potential_revenue - total_value,
            "low_stock_count": len(low_stock_items)
        },
        "category_breakdown": category_breakdown,
        "low_stock_items": low_stock_items[:20]
    }


@router.get("/parts-usage")
async def get_parts_usage_report(
    date_from: Optional[str] = None,
    date_to: Optional[str] = None,
    current_user: dict = Depends(get_ps_current_user)
):
    """Get spare parts usage report"""
    tenant_id = current_user.get("tenant_id")
    if not tenant_id and current_user.get("role") != "super_admin":
        raise HTTPException(status_code=403, detail="Nuk keni akses")
    
    # Default to last 30 days
    if not date_from:
        date_from = (datetime.now(timezone.utc) - timedelta(days=30)).isoformat()
    if not date_to:
        date_to = datetime.now(timezone.utc).isoformat()
    
    query = {
        "created_at": {"$gte": date_from, "$lte": date_to},
        "movement_type": "repair_use"
    }
    if tenant_id:
        query["tenant_id"] = tenant_id
    
    movements = await ps_stock_movements.find(query, {"_id": 0}).to_list(10000)
    
    # Aggregate by part
    parts_usage = {}
    for m in movements:
        part_name = m.get("item_name", "Unknown")
        if part_name not in parts_usage:
            parts_usage[part_name] = {
                "item_id": m.get("item_id"),
                "item_name": part_name,
                "total_quantity": 0,
                "total_cost": 0,
                "usage_count": 0
            }
        parts_usage[part_name]["total_quantity"] += abs(m.get("quantity", 0))
        parts_usage[part_name]["total_cost"] += abs(m.get("quantity", 0)) * (m.get("unit_cost", 0) or 0)
        parts_usage[part_name]["usage_count"] += 1
    
    # Sort by quantity used
    sorted_parts = sorted(parts_usage.values(), key=lambda x: x["total_quantity"], reverse=True)
    
    return {
        "period": {"from": date_from, "to": date_to},
        "total_parts_used": sum(p["total_quantity"] for p in sorted_parts),
        "total_parts_cost": sum(p["total_cost"] for p in sorted_parts),
        "parts_breakdown": sorted_parts[:50]
    }


@router.get("/revenue")
async def get_revenue_report(
    period: str = "month",  # day, week, month, year
    current_user: dict = Depends(get_ps_current_user)
):
    """Get revenue report by period"""
    tenant_id = current_user.get("tenant_id")
    if not tenant_id and current_user.get("role") != "super_admin":
        raise HTTPException(status_code=403, detail="Nuk keni akses")
    
    now = datetime.now(timezone.utc)
    
    if period == "day":
        start_date = now.replace(hour=0, minute=0, second=0, microsecond=0)
        group_format = "%H:00"
    elif period == "week":
        start_date = now - timedelta(days=7)
        group_format = "%Y-%m-%d"
    elif period == "month":
        start_date = now - timedelta(days=30)
        group_format = "%Y-%m-%d"
    else:  # year
        start_date = now - timedelta(days=365)
        group_format = "%Y-%m"
    
    query = {
        "status": {"$in": [RepairStatus.COMPLETED.value, RepairStatus.DELIVERED.value]},
        "completed_at": {"$gte": start_date.isoformat()}
    }
    if tenant_id:
        query["tenant_id"] = tenant_id
    
    repairs = await ps_repairs.find(query, {"_id": 0, "completed_at": 1, "total_cost": 1, "parts_cost": 1, "labor_cost": 1}).to_list(10000)
    
    # Group by date
    grouped = {}
    for r in repairs:
        try:
            date_str = r.get("completed_at", "")[:10]
            if date_str not in grouped:
                grouped[date_str] = {
                    "date": date_str,
                    "revenue": 0,
                    "parts_cost": 0,
                    "labor": 0,
                    "count": 0
                }
            grouped[date_str]["revenue"] += r.get("total_cost", 0)
            grouped[date_str]["parts_cost"] += r.get("parts_cost", 0)
            grouped[date_str]["labor"] += r.get("labor_cost", 0)
            grouped[date_str]["count"] += 1
        except:
            pass
    
    # Sort by date
    timeline = sorted(grouped.values(), key=lambda x: x["date"])
    
    # Calculate totals
    total_revenue = sum(r.get("total_cost", 0) for r in repairs)
    total_parts = sum(r.get("parts_cost", 0) for r in repairs)
    total_labor = sum(r.get("labor_cost", 0) for r in repairs)
    
    return {
        "period": period,
        "start_date": start_date.isoformat(),
        "totals": {
            "revenue": total_revenue,
            "parts_cost": total_parts,
            "labor": total_labor,
            "profit": total_revenue - total_parts,
            "repairs_count": len(repairs)
        },
        "timeline": timeline
    }


@router.get("/customers")
async def get_customers_report(current_user: dict = Depends(get_ps_current_user)):
    """Get customers report"""
    tenant_id = current_user.get("tenant_id")
    if not tenant_id and current_user.get("role") != "super_admin":
        raise HTTPException(status_code=403, detail="Nuk keni akses")
    
    query = {"tenant_id": tenant_id} if tenant_id else {}
    
    customers = await ps_customers.find(query, {"_id": 0}).to_list(10000)
    
    # Enrich with repair counts
    top_customers = []
    for c in customers:
        repairs_count = await ps_repairs.count_documents({"customer_id": c["id"]})
        repairs = await ps_repairs.find(
            {"customer_id": c["id"], "status": {"$in": [RepairStatus.COMPLETED.value, RepairStatus.DELIVERED.value]}},
            {"_id": 0, "total_cost": 1}
        ).to_list(1000)
        total_spent = sum(r.get("total_cost", 0) for r in repairs)
        
        top_customers.append({
            "id": c["id"],
            "full_name": c.get("full_name"),
            "phone": c.get("phone"),
            "repairs_count": repairs_count,
            "total_spent": total_spent
        })
    
    # Sort by total spent
    top_customers.sort(key=lambda x: x["total_spent"], reverse=True)
    
    return {
        "total_customers": len(customers),
        "top_customers": top_customers[:20]
    }
