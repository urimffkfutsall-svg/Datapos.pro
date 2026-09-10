"""Mobilshop Reports Router - Analytics & Reporting"""
from fastapi import APIRouter, HTTPException, Depends
from typing import List, Optional
from datetime import datetime, timezone, timedelta
from collections import defaultdict

from database import db
from auth import get_current_user
from mobilshop_models import (
    SalesReportResponse, InventoryReportResponse, TechnicianPerformanceResponse,
    ProductType, RepairStatus
)

router = APIRouter(prefix="/mobilshop/reports", tags=["Mobilshop Reports"])


@router.get("/dashboard")
async def get_dashboard_stats(current_user: dict = Depends(get_current_user)):
    """Get dashboard overview statistics"""
    tenant_id = current_user.get("tenant_id")
    today = datetime.now(timezone.utc)
    today_str = today.strftime("%Y-%m-%d")
    month_start = today.replace(day=1).strftime("%Y-%m-%d")
    
    # Today's sales
    today_sales = await db.mobilshop_sales.find(
        {"tenant_id": tenant_id, "created_at": {"$regex": f"^{today_str}"}, "voided": {"$ne": True}},
        {"_id": 0}
    ).to_list(1000)
    
    today_revenue = sum(s.get("grand_total", 0) for s in today_sales)
    
    # Month's sales
    month_sales = await db.mobilshop_sales.find(
        {"tenant_id": tenant_id, "created_at": {"$gte": month_start}, "voided": {"$ne": True}},
        {"_id": 0}
    ).to_list(10000)
    
    month_revenue = sum(s.get("grand_total", 0) for s in month_sales)
    
    # Pending repairs
    pending_repairs = await db.mobilshop_repairs.count_documents({
        "tenant_id": tenant_id,
        "status": {"$nin": [RepairStatus.DELIVERED, RepairStatus.CANCELLED]}
    })
    
    # Low stock items
    products = await db.mobilshop_products.find(
        {"tenant_id": tenant_id, "is_active": True, "is_sold": False},
        {"_id": 0}
    ).to_list(5000)
    
    low_stock = len([p for p in products if p.get("quantity", 0) <= p.get("min_stock", 1)])
    
    # Total customers
    total_customers = await db.mobilshop_customers.count_documents({
        "tenant_id": tenant_id, "is_active": True
    })
    
    # Total inventory value
    inventory_value = sum(
        p.get("purchase_price", 0) * p.get("quantity", 1) 
        for p in products 
        if p.get("product_type") == ProductType.ACCESSORY
    )
    inventory_value += sum(
        p.get("purchase_price", 0) 
        for p in products 
        if p.get("product_type") == ProductType.PHONE and not p.get("is_sold")
    )
    
    # Repairs completed this month
    completed_repairs = await db.mobilshop_repairs.count_documents({
        "tenant_id": tenant_id,
        "status": RepairStatus.COMPLETED,
        "actual_completion": {"$gte": month_start}
    })
    
    # Repair revenue this month
    repairs = await db.mobilshop_repairs.find(
        {
            "tenant_id": tenant_id,
            "payment_status": "paid",
            "updated_at": {"$gte": month_start}
        },
        {"_id": 0, "total_cost": 1}
    ).to_list(1000)
    repair_revenue = sum(r.get("total_cost", 0) for r in repairs)
    
    return {
        "today": {
            "sales_count": len(today_sales),
            "revenue": today_revenue
        },
        "month": {
            "sales_count": len(month_sales),
            "revenue": month_revenue,
            "repair_revenue": repair_revenue,
            "completed_repairs": completed_repairs
        },
        "pending_repairs": pending_repairs,
        "low_stock_items": low_stock,
        "total_customers": total_customers,
        "inventory_value": inventory_value,
        "total_products": len(products)
    }


@router.get("/sales")
async def get_sales_report(
    period: str = "month",  # day, week, month, year, custom
    date_from: Optional[str] = None,
    date_to: Optional[str] = None,
    current_user: dict = Depends(get_current_user)
):
    """Get detailed sales report"""
    tenant_id = current_user.get("tenant_id")
    today = datetime.now(timezone.utc)
    
    # Determine date range
    if period == "day":
        start_date = today.strftime("%Y-%m-%d")
        end_date = start_date
    elif period == "week":
        start_date = (today - timedelta(days=today.weekday())).strftime("%Y-%m-%d")
        end_date = today.strftime("%Y-%m-%d")
    elif period == "month":
        start_date = today.replace(day=1).strftime("%Y-%m-%d")
        end_date = today.strftime("%Y-%m-%d")
    elif period == "year":
        start_date = today.replace(month=1, day=1).strftime("%Y-%m-%d")
        end_date = today.strftime("%Y-%m-%d")
    else:
        start_date = date_from or today.strftime("%Y-%m-%d")
        end_date = date_to or today.strftime("%Y-%m-%d")
    
    # Get sales in range
    sales = await db.mobilshop_sales.find(
        {
            "tenant_id": tenant_id,
            "created_at": {"$gte": start_date, "$lte": end_date + "T23:59:59"},
            "voided": {"$ne": True}
        },
        {"_id": 0}
    ).to_list(10000)
    
    # Calculate metrics
    total_sales = sum(s.get("grand_total", 0) for s in sales)
    cash_sales = sum(s.get("cash_amount", 0) for s in sales)
    card_sales = sum(s.get("card_amount", 0) for s in sales)
    
    # Phone vs accessory breakdown
    phone_count = 0
    phone_revenue = 0
    accessory_count = 0
    accessory_revenue = 0
    
    product_sales = defaultdict(lambda: {"count": 0, "revenue": 0, "name": ""})
    
    for sale in sales:
        for item in sale.get("items", []):
            if item.get("product_type") == ProductType.PHONE:
                phone_count += item.get("quantity", 1)
                phone_revenue += item.get("total", 0)
            else:
                accessory_count += item.get("quantity", 1)
                accessory_revenue += item.get("total", 0)
            
            pid = item.get("product_id")
            product_sales[pid]["count"] += item.get("quantity", 1)
            product_sales[pid]["revenue"] += item.get("total", 0)
            product_sales[pid]["name"] = item.get("product_name", "")
    
    # Top products
    top_products = sorted(
        [{"id": k, **v} for k, v in product_sales.items()],
        key=lambda x: x["revenue"],
        reverse=True
    )[:10]
    
    # Sales by day
    sales_by_day = defaultdict(lambda: {"count": 0, "revenue": 0})
    for sale in sales:
        day = sale.get("created_at", "")[:10]
        sales_by_day[day]["count"] += 1
        sales_by_day[day]["revenue"] += sale.get("grand_total", 0)
    
    # Get repairs in range
    repairs = await db.mobilshop_repairs.find(
        {
            "tenant_id": tenant_id,
            "payment_status": "paid",
            "updated_at": {"$gte": start_date, "$lte": end_date + "T23:59:59"}
        },
        {"_id": 0}
    ).to_list(1000)
    
    repair_revenue = sum(r.get("total_cost", 0) for r in repairs)
    
    return {
        "period": period,
        "date_from": start_date,
        "date_to": end_date,
        "total_sales": total_sales,
        "total_transactions": len(sales),
        "cash_sales": cash_sales,
        "card_sales": card_sales,
        "phone_sales": phone_count,
        "phone_revenue": phone_revenue,
        "accessory_sales": accessory_count,
        "accessory_revenue": accessory_revenue,
        "repair_revenue": repair_revenue,
        "repair_count": len(repairs),
        "average_sale": total_sales / len(sales) if sales else 0,
        "top_products": top_products,
        "sales_by_day": [{"date": k, **v} for k, v in sorted(sales_by_day.items())]
    }


@router.get("/inventory")
async def get_inventory_report(current_user: dict = Depends(get_current_user)):
    """Get inventory valuation report"""
    tenant_id = current_user.get("tenant_id")
    
    products = await db.mobilshop_products.find(
        {"tenant_id": tenant_id, "is_active": True},
        {"_id": 0}
    ).to_list(10000)
    
    # Separate by type
    phones = [p for p in products if p.get("product_type") == ProductType.PHONE and not p.get("is_sold")]
    accessories = [p for p in products if p.get("product_type") == ProductType.ACCESSORY]
    
    # Calculate values
    phone_value = sum(p.get("purchase_price", 0) for p in phones)
    accessory_value = sum(p.get("purchase_price", 0) * p.get("quantity", 1) for p in accessories)
    
    # Low stock
    low_stock = [
        {
            "id": p["id"],
            "name": p["name"],
            "quantity": p.get("quantity", 0),
            "min_stock": p.get("min_stock", 1),
            "product_type": p.get("product_type")
        }
        for p in accessories
        if p.get("quantity", 0) <= p.get("min_stock", 1)
    ]
    
    # By category
    by_category = defaultdict(lambda: {"count": 0, "value": 0})
    for p in products:
        cat = p.get("category") or "Pa Kategori"
        if p.get("product_type") == ProductType.PHONE and not p.get("is_sold"):
            by_category[cat]["count"] += 1
            by_category[cat]["value"] += p.get("purchase_price", 0)
        elif p.get("product_type") == ProductType.ACCESSORY:
            by_category[cat]["count"] += p.get("quantity", 0)
            by_category[cat]["value"] += p.get("purchase_price", 0) * p.get("quantity", 1)
    
    # By brand
    by_brand = defaultdict(lambda: {"count": 0, "value": 0})
    for p in phones:
        brand = p.get("brand") or "Pa Markë"
        by_brand[brand]["count"] += 1
        by_brand[brand]["value"] += p.get("purchase_price", 0)
    
    return {
        "total_products": len(phones) + sum(p.get("quantity", 0) for p in accessories),
        "total_phones": len(phones),
        "total_accessories": sum(p.get("quantity", 0) for p in accessories),
        "total_value": phone_value + accessory_value,
        "phone_value": phone_value,
        "accessory_value": accessory_value,
        "low_stock_items": low_stock,
        "stock_by_category": [{"category": k, **v} for k, v in by_category.items()],
        "stock_by_brand": [{"brand": k, **v} for k, v in by_brand.items()]
    }


@router.get("/technicians")
async def get_technician_performance(
    date_from: Optional[str] = None,
    date_to: Optional[str] = None,
    current_user: dict = Depends(get_current_user)
):
    """Get technician performance report"""
    tenant_id = current_user.get("tenant_id")
    today = datetime.now(timezone.utc)
    
    start_date = date_from or today.replace(day=1).strftime("%Y-%m-%d")
    end_date = date_to or today.strftime("%Y-%m-%d")
    
    # Get all technicians
    technicians = await db.users.find(
        {"tenant_id": tenant_id, "role": "technician", "is_active": True},
        {"_id": 0, "id": 1, "full_name": 1}
    ).to_list(100)
    
    results = []
    
    for tech in technicians:
        repairs = await db.mobilshop_repairs.find(
            {
                "tenant_id": tenant_id,
                "technician_id": tech["id"],
                "created_at": {"$gte": start_date, "$lte": end_date + "T23:59:59"}
            },
            {"_id": 0}
        ).to_list(1000)
        
        completed = [r for r in repairs if r.get("status") == RepairStatus.COMPLETED or r.get("status") == RepairStatus.DELIVERED]
        
        # Calculate average completion time
        completion_times = []
        for r in completed:
            if r.get("actual_completion") and r.get("created_at"):
                try:
                    start = datetime.fromisoformat(r["created_at"].replace("Z", "+00:00"))
                    end = datetime.fromisoformat(r["actual_completion"].replace("Z", "+00:00"))
                    hours = (end - start).total_seconds() / 3600
                    completion_times.append(hours)
                except:
                    pass
        
        avg_time = sum(completion_times) / len(completion_times) if completion_times else 0
        
        # Status breakdown
        status_counts = defaultdict(int)
        for r in repairs:
            status_counts[r.get("status", "unknown")] += 1
        
        results.append({
            "technician_id": tech["id"],
            "technician_name": tech["full_name"],
            "total_repairs": len(repairs),
            "completed_repairs": len(completed),
            "average_completion_time": round(avg_time, 1),
            "total_revenue": sum(r.get("total_cost", 0) for r in completed if r.get("payment_status") == "paid"),
            "repairs_by_status": dict(status_counts)
        })
    
    return results


@router.get("/profit")
async def get_profit_report(
    period: str = "month",
    current_user: dict = Depends(get_current_user)
):
    """Get profit and revenue overview"""
    tenant_id = current_user.get("tenant_id")
    today = datetime.now(timezone.utc)
    
    if period == "month":
        start_date = today.replace(day=1).strftime("%Y-%m-%d")
    elif period == "year":
        start_date = today.replace(month=1, day=1).strftime("%Y-%m-%d")
    else:
        start_date = (today - timedelta(days=7)).strftime("%Y-%m-%d")
    
    end_date = today.strftime("%Y-%m-%d")
    
    # Get sales
    sales = await db.mobilshop_sales.find(
        {
            "tenant_id": tenant_id,
            "created_at": {"$gte": start_date},
            "voided": {"$ne": True}
        },
        {"_id": 0}
    ).to_list(10000)
    
    # Calculate revenue and cost
    total_revenue = 0
    total_cost = 0
    
    for sale in sales:
        for item in sale.get("items", []):
            total_revenue += item.get("total", 0)
            
            # Get product cost
            product = await db.mobilshop_products.find_one(
                {"id": item["product_id"]},
                {"_id": 0, "purchase_price": 1}
            )
            if product:
                total_cost += product.get("purchase_price", 0) * item.get("quantity", 1)
    
    # Get repair revenue
    repairs = await db.mobilshop_repairs.find(
        {
            "tenant_id": tenant_id,
            "payment_status": "paid",
            "updated_at": {"$gte": start_date}
        },
        {"_id": 0}
    ).to_list(1000)
    
    repair_revenue = sum(r.get("total_cost", 0) for r in repairs)
    repair_cost = sum(r.get("parts_cost", 0) for r in repairs)
    
    gross_profit = (total_revenue - total_cost) + (repair_revenue - repair_cost)
    
    return {
        "period": period,
        "date_from": start_date,
        "date_to": end_date,
        "sales_revenue": total_revenue,
        "sales_cost": total_cost,
        "sales_profit": total_revenue - total_cost,
        "repair_revenue": repair_revenue,
        "repair_cost": repair_cost,
        "repair_profit": repair_revenue - repair_cost,
        "total_revenue": total_revenue + repair_revenue,
        "total_cost": total_cost + repair_cost,
        "gross_profit": gross_profit,
        "profit_margin": (gross_profit / (total_revenue + repair_revenue) * 100) if (total_revenue + repair_revenue) > 0 else 0
    }
