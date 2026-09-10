"""
HealthPRO - Notifications Router
Real-time notifications for the dashboard
"""
from fastapi import APIRouter, HTTPException, Query, Header
from typing import List, Optional
from datetime import datetime, timezone, timedelta
import uuid
import jwt
import os

from database import db
from .tasks import run_daily_tasks, generate_systematic_checkups_for_tenant

router = APIRouter(prefix="/healthpro/notifications", tags=["HealthPRO Notifications"])

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


@router.get("")
async def get_notifications(
    unread_only: bool = Query(False),
    limit: int = Query(20, ge=1, le=100),
    authorization: str = Header(None)
):
    """Get all notifications for the current tenant"""
    user = await get_current_hp_user(authorization)
    tenant_id = user.get("tenant_id")
    
    query = {"tenant_id": tenant_id}
    if unread_only:
        query["is_read"] = False
    
    cursor = db.hp_notifications.find(query, {"_id": 0}).sort("created_at", -1).limit(limit)
    notifications = await cursor.to_list(length=limit)
    
    return notifications


@router.get("/dashboard")
async def get_dashboard_notifications(authorization: str = Header(None)):
    """Get notifications specifically for the dashboard view"""
    user = await get_current_hp_user(authorization)
    tenant_id = user.get("tenant_id")
    
    today = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    tomorrow = (datetime.now(timezone.utc) + timedelta(days=1)).strftime("%Y-%m-%d")
    next_week = (datetime.now(timezone.utc) + timedelta(days=7)).strftime("%Y-%m-%d")
    
    notifications = []
    
    # Today's checkups
    todays_checkups = await db.hp_checkups.find({
        "tenant_id": tenant_id,
        "status": "planned",
        "scheduled_date": today
    }, {"_id": 0}).to_list(length=10)
    
    for c in todays_checkups:
        resident = await db.hp_residents.find_one({"id": c["resident_id"]}, {"_id": 0, "first_name": 1, "last_name": 1})
        name = f"{resident.get('first_name', '')} {resident.get('last_name', '')}".strip() if resident else "?"
        notifications.append({
            "id": f"checkup-{c['id']}",
            "type": "checkup_today",
            "icon": "stethoscope",
            "title": "Kontroll sot",
            "message": f"{name} - {c.get('checkup_type', 'QKMF')} në {c.get('scheduled_time', '09:00')}",
            "priority": "high",
            "date": today,
            "link": "/healthpro/checkups"
        })
    
    # Today's visits
    todays_visits = await db.hp_visits.find({
        "tenant_id": tenant_id,
        "is_completed": False,
        "visit_date": today
    }, {"_id": 0}).to_list(length=10)
    
    for v in todays_visits:
        resident = await db.hp_residents.find_one({"id": v["resident_id"]}, {"_id": 0, "first_name": 1, "last_name": 1})
        name = f"{resident.get('first_name', '')} {resident.get('last_name', '')}".strip() if resident else "?"
        notifications.append({
            "id": f"visit-{v['id']}",
            "type": "visit_today",
            "icon": "map-pin",
            "title": "Vizitë sot",
            "message": f"{name} - {v.get('visit_type', 'home')} në {v.get('visit_time', '10:00')}",
            "priority": "high",
            "date": today,
            "link": "/healthpro/visits"
        })
    
    # Upcoming checkups this week
    upcoming_checkups = await db.hp_checkups.find({
        "tenant_id": tenant_id,
        "status": "planned",
        "scheduled_date": {"$gt": today, "$lte": next_week}
    }, {"_id": 0}).sort("scheduled_date", 1).to_list(length=5)
    
    for c in upcoming_checkups:
        resident = await db.hp_residents.find_one({"id": c["resident_id"]}, {"_id": 0, "first_name": 1, "last_name": 1})
        name = f"{resident.get('first_name', '')} {resident.get('last_name', '')}".strip() if resident else "?"
        notifications.append({
            "id": f"upcoming-{c['id']}",
            "type": "checkup_upcoming",
            "icon": "calendar",
            "title": "Kontroll e ardhshme",
            "message": f"{name} - {c.get('scheduled_date')}",
            "priority": "medium",
            "date": c.get("scheduled_date"),
            "link": "/healthpro/checkups"
        })
    
    # Overdue checkups
    overdue_checkups = await db.hp_checkups.find({
        "tenant_id": tenant_id,
        "status": "planned",
        "scheduled_date": {"$lt": today}
    }, {"_id": 0}).to_list(length=5)
    
    for c in overdue_checkups:
        resident = await db.hp_residents.find_one({"id": c["resident_id"]}, {"_id": 0, "first_name": 1, "last_name": 1})
        name = f"{resident.get('first_name', '')} {resident.get('last_name', '')}".strip() if resident else "?"
        notifications.append({
            "id": f"overdue-{c['id']}",
            "type": "checkup_overdue",
            "icon": "alert-circle",
            "title": "Kontroll e vonuar!",
            "message": f"{name} - ishte planifikuar për {c.get('scheduled_date')}",
            "priority": "urgent",
            "date": c.get("scheduled_date"),
            "link": "/healthpro/checkups"
        })
    
    # Therapies count for today
    active_therapies = await db.hp_therapies.count_documents({
        "tenant_id": tenant_id,
        "is_active": True
    })
    
    if active_therapies > 0:
        notifications.append({
            "id": "therapies-active",
            "type": "therapies_reminder",
            "icon": "pill",
            "title": "Terapi aktive",
            "message": f"{active_therapies} terapi aktive për t'u administruar sot",
            "priority": "normal",
            "date": today,
            "link": "/healthpro/therapies"
        })
    
    # Sort by priority
    priority_order = {"urgent": 0, "high": 1, "medium": 2, "normal": 3}
    notifications.sort(key=lambda x: (priority_order.get(x["priority"], 99), x.get("date", "")))
    
    return notifications[:15]


@router.put("/{notification_id}/read")
async def mark_notification_read(notification_id: str, authorization: str = Header(None)):
    """Mark a notification as read"""
    user = await get_current_hp_user(authorization)
    tenant_id = user.get("tenant_id")
    
    result = await db.hp_notifications.update_one(
        {"id": notification_id, "tenant_id": tenant_id},
        {"$set": {"is_read": True, "read_at": datetime.now(timezone.utc).isoformat()}}
    )
    
    return {"success": result.modified_count > 0}


@router.put("/read-all")
async def mark_all_read(authorization: str = Header(None)):
    """Mark all notifications as read"""
    user = await get_current_hp_user(authorization)
    tenant_id = user.get("tenant_id")
    
    result = await db.hp_notifications.update_many(
        {"tenant_id": tenant_id, "is_read": False},
        {"$set": {"is_read": True, "read_at": datetime.now(timezone.utc).isoformat()}}
    )
    
    return {"marked_read": result.modified_count}


@router.post("/run-tasks")
async def run_background_tasks(authorization: str = Header(None)):
    """Manually run background tasks (admin only)"""
    user = await get_current_hp_user(authorization)
    tenant_id = user.get("tenant_id")
    
    if user.get("role") not in ["admin", "super_admin"]:
        raise HTTPException(status_code=403, detail="Vetëm administratori mund të ekzekutojë task-et")
    
    results = await run_daily_tasks(tenant_id)
    
    return {
        "message": "Task-et u ekzekutuan me sukses",
        "results": results
    }


@router.get("/unread-count")
async def get_unread_count(authorization: str = Header(None)):
    """Get count of unread notifications"""
    user = await get_current_hp_user(authorization)
    tenant_id = user.get("tenant_id")
    
    count = await db.hp_notifications.count_documents({
        "tenant_id": tenant_id,
        "is_read": False
    })
    
    return {"count": count}
