"""Shared business-calendar boundaries; Mongo timestamps are stored in UTC."""
import os
from datetime import datetime, timezone, timedelta
from zoneinfo import ZoneInfo
from fastapi import HTTPException

BUSINESS_TZ = ZoneInfo(os.getenv("BUSINESS_TIMEZONE", "Europe/Tirane"))

def period_bounds(period, now=None):
    local = (now or datetime.now(timezone.utc)).astimezone(BUSINESS_TZ)
    start = local.replace(hour=0, minute=0, second=0, microsecond=0)
    if period == "daily":
        end = start + timedelta(days=1)
    elif period == "monthly":
        start = start.replace(day=1)
        end = (start.replace(year=start.year + 1, month=1) if start.month == 12
               else start.replace(month=start.month + 1))
    else:
        raise ValueError("Unknown period")
    return {"$gte": start.astimezone(timezone.utc).isoformat(),
            "$lt": end.astimezone(timezone.utc).isoformat()}

def date_filter(start_date=None, end_date=None):
    bounds = {}
    try:
        for value, lower in ((start_date, True), (end_date, False)):
            if not value:
                continue
            dt = datetime.fromisoformat(value.replace("Z", "+00:00"))
            if dt.tzinfo is None:
                dt = dt.replace(tzinfo=BUSINESS_TZ)
            if not lower and len(value) == 10:
                dt += timedelta(days=1)
            key = "$gte" if lower else ("$lt" if len(value) == 10 else "$lte")
            bounds[key] = dt.astimezone(timezone.utc).isoformat()
        if start_date and end_date and bounds["$gte"] > bounds.get("$lt", bounds.get("$lte")):
            raise ValueError("Invalid range")
    except (ValueError, TypeError):
        raise HTTPException(status_code=422, detail="Data ose periudha është e pavlefshme")
    return bounds
