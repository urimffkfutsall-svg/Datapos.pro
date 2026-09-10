"""
HealthPRO - Background Tasks (Cron Jobs)
Automatic scheduling of systematic checkups and notifications
"""
from datetime import datetime, timezone, timedelta
from database import db
import uuid
import asyncio


async def generate_systematic_checkups_for_tenant(tenant_id: str):
    """
    Generate systematic checkups for all residents who haven't had one in 6 months.
    This should be called periodically (e.g., daily) or manually by admin.
    """
    today = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    six_months_ago = (datetime.now(timezone.utc) - timedelta(days=180)).strftime("%Y-%m-%d")
    six_months_later = (datetime.now(timezone.utc) + timedelta(days=180)).strftime("%Y-%m-%d")
    
    # Get all active residents
    residents = await db.hp_residents.find(
        {"tenant_id": tenant_id, "status": "active"},
        {"_id": 0}
    ).to_list(length=1000)
    
    created_count = 0
    skipped_count = 0
    
    for resident in residents:
        resident_id = resident["id"]
        
        # Check if resident has a systematic checkup in the last 6 months or upcoming
        existing_checkup = await db.hp_checkups.find_one({
            "tenant_id": tenant_id,
            "resident_id": resident_id,
            "is_systematic": True,
            "$or": [
                {"scheduled_date": {"$gte": six_months_ago}},
                {"status": "planned"}
            ]
        })
        
        if existing_checkup:
            skipped_count += 1
            continue
        
        # Create new systematic checkup scheduled 1 month from now
        scheduled_date = (datetime.now(timezone.utc) + timedelta(days=30)).strftime("%Y-%m-%d")
        
        checkup_doc = {
            "id": str(uuid.uuid4()),
            "tenant_id": tenant_id,
            "resident_id": resident_id,
            "checkup_type": "general",
            "scheduled_date": scheduled_date,
            "scheduled_time": "09:00",
            "status": "planned",
            "is_systematic": True,
            "notes": "Kontroll sistematike e gjeneruar automatikisht",
            "created_at": datetime.now(timezone.utc).isoformat(),
            "auto_generated": True
        }
        
        await db.hp_checkups.insert_one(checkup_doc)
        created_count += 1
    
    return {
        "created": created_count,
        "skipped": skipped_count,
        "total_residents": len(residents)
    }


async def check_and_create_therapy_reminders(tenant_id: str):
    """
    Check for therapies ending soon and create notifications
    """
    today = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    week_later = (datetime.now(timezone.utc) + timedelta(days=7)).strftime("%Y-%m-%d")
    
    # Find therapies ending in next 7 days
    ending_therapies = await db.hp_therapies.find({
        "tenant_id": tenant_id,
        "is_active": True,
        "end_date": {"$gte": today, "$lte": week_later}
    }, {"_id": 0}).to_list(length=100)
    
    notifications = []
    for therapy in ending_therapies:
        # Check if notification already exists
        existing = await db.hp_notifications.find_one({
            "tenant_id": tenant_id,
            "reference_id": therapy["id"],
            "type": "therapy_ending"
        })
        
        if not existing:
            notification = {
                "id": str(uuid.uuid4()),
                "tenant_id": tenant_id,
                "type": "therapy_ending",
                "reference_id": therapy["id"],
                "title": "Terapi që mbaron së shpejti",
                "message": f"Terapia '{therapy['name']}' mbaron më {therapy['end_date']}",
                "priority": "medium",
                "is_read": False,
                "created_at": datetime.now(timezone.utc).isoformat()
            }
            await db.hp_notifications.insert_one(notification)
            notifications.append(notification)
    
    return notifications


async def check_overdue_checkups(tenant_id: str):
    """
    Find checkups that are overdue (past date but still planned)
    """
    today = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    
    overdue = await db.hp_checkups.find({
        "tenant_id": tenant_id,
        "status": "planned",
        "scheduled_date": {"$lt": today}
    }, {"_id": 0}).to_list(length=100)
    
    notifications = []
    for checkup in overdue:
        existing = await db.hp_notifications.find_one({
            "tenant_id": tenant_id,
            "reference_id": checkup["id"],
            "type": "checkup_overdue"
        })
        
        if not existing:
            resident = await db.hp_residents.find_one(
                {"id": checkup["resident_id"]},
                {"_id": 0, "first_name": 1, "last_name": 1}
            )
            resident_name = f"{resident.get('first_name', '')} {resident.get('last_name', '')}".strip() if resident else "Unknown"
            
            notification = {
                "id": str(uuid.uuid4()),
                "tenant_id": tenant_id,
                "type": "checkup_overdue",
                "reference_id": checkup["id"],
                "title": "Kontroll e vonuar",
                "message": f"Kontrolla e {resident_name} ishte planifikuar për {checkup['scheduled_date']}",
                "priority": "high",
                "is_read": False,
                "created_at": datetime.now(timezone.utc).isoformat()
            }
            await db.hp_notifications.insert_one(notification)
            notifications.append(notification)
    
    return notifications


async def run_daily_tasks(tenant_id: str):
    """
    Run all daily background tasks for a tenant
    """
    results = {
        "systematic_checkups": await generate_systematic_checkups_for_tenant(tenant_id),
        "therapy_reminders": len(await check_and_create_therapy_reminders(tenant_id)),
        "overdue_checkups": len(await check_overdue_checkups(tenant_id)),
        "run_at": datetime.now(timezone.utc).isoformat()
    }
    
    # Log the run
    await db.hp_task_logs.insert_one({
        "id": str(uuid.uuid4()),
        "tenant_id": tenant_id,
        "task_type": "daily_tasks",
        "results": results,
        "created_at": datetime.now(timezone.utc).isoformat()
    })
    
    return results
