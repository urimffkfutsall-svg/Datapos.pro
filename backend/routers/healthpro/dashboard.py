"""
HealthPRO - Dashboard & Reports Router
"""
from fastapi import APIRouter, HTTPException, Query, Header
from typing import Optional
from datetime import datetime, timezone, timedelta
import jwt
import os

from database import db

router = APIRouter(prefix="/healthpro/dashboard", tags=["HealthPRO Dashboard"])

SECRET_KEY = os.environ.get("JWT_SECRET", "healthpro-secret-key-2026")
ALGORITHM = "HS256"


async def get_current_hp_user(authorization: str = Header(None)):
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Jo i autorizuar")
    token = authorization.replace("Bearer ", "")
    try:
        return jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
    except:
        raise HTTPException(status_code=401, detail="Token i pavlefshëm")


@router.get("/stats")
async def get_dashboard_stats(authorization: str = Header(None)):
    """Get main dashboard statistics"""
    user = await get_current_hp_user(authorization)
    tenant_id = user.get("tenant_id")
    
    today = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    week_ago = (datetime.now(timezone.utc) - timedelta(days=7)).strftime("%Y-%m-%d")
    month_ago = (datetime.now(timezone.utc) - timedelta(days=30)).strftime("%Y-%m-%d")
    
    # Residents
    total_residents = await db.hp_residents.count_documents({"tenant_id": tenant_id})
    active_residents = await db.hp_residents.count_documents({"tenant_id": tenant_id, "status": "active"})
    
    # Employees
    total_employees = await db.hp_users.count_documents({"tenant_id": tenant_id})
    active_employees = await db.hp_users.count_documents({"tenant_id": tenant_id, "status": "active"})
    
    # Checkups
    total_checkups = await db.hp_checkups.count_documents({"tenant_id": tenant_id})
    upcoming_checkups = await db.hp_checkups.count_documents({
        "tenant_id": tenant_id,
        "status": "planned",
        "scheduled_date": {"$gte": today}
    })
    checkups_this_month = await db.hp_checkups.count_documents({
        "tenant_id": tenant_id,
        "scheduled_date": {"$gte": month_ago}
    })
    
    # Therapies
    total_therapies = await db.hp_therapies.count_documents({"tenant_id": tenant_id})
    active_therapies = await db.hp_therapies.count_documents({
        "tenant_id": tenant_id,
        "is_active": True
    })
    
    # Visits
    total_visits = await db.hp_visits.count_documents({"tenant_id": tenant_id})
    visits_this_week = await db.hp_visits.count_documents({
        "tenant_id": tenant_id,
        "visit_date": {"$gte": week_ago}
    })
    visits_this_month = await db.hp_visits.count_documents({
        "tenant_id": tenant_id,
        "visit_date": {"$gte": month_ago}
    })
    pending_visits = await db.hp_visits.count_documents({
        "tenant_id": tenant_id,
        "is_completed": False,
        "visit_date": {"$gte": today}
    })
    
    return {
        # Simple counts for reports page
        "residents": total_residents,
        "employees": total_employees,
        "checkups": total_checkups,
        "therapies": total_therapies,
        "visits": total_visits,
        # Detailed stats
        "residents_detail": {
            "total": total_residents,
            "active": active_residents,
            "inactive": total_residents - active_residents
        },
        "employees_detail": {
            "total": total_employees,
            "active": active_employees
        },
        "checkups_detail": {
            "total": total_checkups,
            "upcoming": upcoming_checkups,
            "this_month": checkups_this_month
        },
        "therapies_detail": {
            "total": total_therapies,
            "active": active_therapies
        },
        "visits_detail": {
            "total": total_visits,
            "this_week": visits_this_week,
            "this_month": visits_this_month,
            "pending": pending_visits
        }
    }


@router.get("/notifications")
async def get_notifications(authorization: str = Header(None)):
    """Get dashboard notifications/alerts"""
    user = await get_current_hp_user(authorization)
    tenant_id = user.get("tenant_id")
    
    today = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    next_week = (datetime.now(timezone.utc) + timedelta(days=7)).strftime("%Y-%m-%d")
    
    notifications = []
    
    # Upcoming checkups in next 7 days
    upcoming_checkups = await db.hp_checkups.find({
        "tenant_id": tenant_id,
        "status": "planned",
        "scheduled_date": {"$gte": today, "$lte": next_week}
    }, {"_id": 0}).to_list(length=10)
    
    for c in upcoming_checkups:
        resident = await db.hp_residents.find_one(
            {"id": c.get("resident_id")},
            {"_id": 0, "first_name": 1, "last_name": 1}
        )
        notifications.append({
            "type": "checkup_reminder",
            "title": "Kontrollë e planifikuar",
            "message": f"{resident.get('first_name', '')} {resident.get('last_name', '')} - {c.get('checkup_type')} më {c.get('scheduled_date')}",
            "date": c.get("scheduled_date"),
            "priority": "high" if c.get("is_systematic") else "normal"
        })
    
    # Pending visits for today
    today_visits = await db.hp_visits.find({
        "tenant_id": tenant_id,
        "is_completed": False,
        "visit_date": today
    }, {"_id": 0}).to_list(length=10)
    
    for v in today_visits:
        resident = await db.hp_residents.find_one(
            {"id": v.get("resident_id")},
            {"_id": 0, "first_name": 1, "last_name": 1}
        )
        notifications.append({
            "type": "visit_today",
            "title": "Vizitë sot",
            "message": f"{resident.get('first_name', '')} {resident.get('last_name', '')} - {v.get('visit_type')} vizitë në {v.get('visit_time', 'pa kohë')}",
            "date": today,
            "priority": "high"
        })
    
    # Sort by priority and date
    notifications.sort(key=lambda x: (0 if x["priority"] == "high" else 1, x["date"]))
    
    return notifications


@router.get("/reports/visits")
async def get_visits_report(
    period: str = Query("month", regex="^(week|month|year)$"),
    authorization: str = Header(None)
):
    """Get visits report"""
    user = await get_current_hp_user(authorization)
    tenant_id = user.get("tenant_id")
    
    now = datetime.now(timezone.utc)
    if period == "week":
        start_date = (now - timedelta(days=7)).strftime("%Y-%m-%d")
    elif period == "month":
        start_date = (now - timedelta(days=30)).strftime("%Y-%m-%d")
    else:
        start_date = (now - timedelta(days=365)).strftime("%Y-%m-%d")
    
    # Get visits in period
    visits = await db.hp_visits.find({
        "tenant_id": tenant_id,
        "visit_date": {"$gte": start_date}
    }, {"_id": 0}).to_list(length=1000)
    
    # Aggregate by type
    home_visits = len([v for v in visits if v.get("visit_type") == "home"])
    community_visits = len([v for v in visits if v.get("visit_type") == "community"])
    completed = len([v for v in visits if v.get("is_completed")])
    
    # Aggregate by resident
    by_resident = {}
    for v in visits:
        rid = v.get("resident_id")
        if rid not in by_resident:
            by_resident[rid] = 0
        by_resident[rid] += 1
    
    # Get top residents
    top_residents = sorted(by_resident.items(), key=lambda x: x[1], reverse=True)[:10]
    
    # Get resident names
    resident_names = {}
    if top_residents:
        rids = [r[0] for r in top_residents]
        async for r in db.hp_residents.find({"id": {"$in": rids}}, {"_id": 0, "id": 1, "first_name": 1, "last_name": 1}):
            resident_names[r["id"]] = f"{r.get('first_name', '')} {r.get('last_name', '')}".strip()
    
    return {
        "period": period,
        "total": len(visits),
        "by_type": {
            "home": home_visits,
            "community": community_visits
        },
        "completed": completed,
        "pending": len(visits) - completed,
        "top_residents": [
            {"resident_id": rid, "name": resident_names.get(rid, ""), "count": count}
            for rid, count in top_residents
        ]
    }


@router.get("/reports/checkups")
async def get_checkups_report(
    period: str = Query("month", regex="^(week|month|year)$"),
    authorization: str = Header(None)
):
    """Get checkups report"""
    user = await get_current_hp_user(authorization)
    tenant_id = user.get("tenant_id")
    
    now = datetime.now(timezone.utc)
    if period == "week":
        start_date = (now - timedelta(days=7)).strftime("%Y-%m-%d")
    elif period == "month":
        start_date = (now - timedelta(days=30)).strftime("%Y-%m-%d")
    else:
        start_date = (now - timedelta(days=365)).strftime("%Y-%m-%d")
    
    checkups = await db.hp_checkups.find({
        "tenant_id": tenant_id,
        "scheduled_date": {"$gte": start_date}
    }, {"_id": 0}).to_list(length=1000)
    
    # By type
    by_type = {}
    for c in checkups:
        ctype = c.get("checkup_type", "other")
        if ctype not in by_type:
            by_type[ctype] = 0
        by_type[ctype] += 1
    
    # By status
    planned = len([c for c in checkups if c.get("status") == "planned"])
    completed = len([c for c in checkups if c.get("status") == "completed"])
    cancelled = len([c for c in checkups if c.get("status") == "cancelled"])
    
    return {
        "period": period,
        "total": len(checkups),
        "by_type": by_type,
        "by_status": {
            "planned": planned,
            "completed": completed,
            "cancelled": cancelled
        }
    }
