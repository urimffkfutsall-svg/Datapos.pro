"""Shared business-calendar boundaries; Mongo timestamps are stored in UTC."""
import os
from datetime import datetime, timezone, timedelta
from zoneinfo import ZoneInfo
from fastapi import HTTPException

REPORTING_REVISION = "sales-panel-v2"

BUSINESS_TZ = ZoneInfo(os.getenv("BUSINESS_TIMEZONE", "Europe/Tirane"))

def period_bounds(period, now=None, anchor=None):
    if anchor:
        try:
            local = datetime.strptime(anchor, "%Y-%m-%d").replace(tzinfo=BUSINESS_TZ)
        except (ValueError, TypeError):
            raise HTTPException(status_code=422, detail="Data është e pavlefshme")
    else:
        local = (now or datetime.now(timezone.utc)).astimezone(BUSINESS_TZ)
    start = local.replace(hour=0, minute=0, second=0, microsecond=0)
    if period == "daily":
        end = start + timedelta(days=1)
    elif period == "weekly":
        start -= timedelta(days=start.weekday())
        end = start + timedelta(days=7)
    elif period == "yearly":
        start = start.replace(month=1, day=1)
        end = start.replace(year=start.year + 1)
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


def period_query(tenant_filter, bounds):
    """Compare parsed BSON dates, not strings (supports legacy Z/offset/BSON dates).
    Invalid dates are excluded instead of crashing a report. Tenant scope is mandatory
    for tenant endpoints and is checked by their role dependencies.
    """
    converted = {"$convert": {"input": "$created_at", "to": "date", "onError": None, "onNull": None}}
    conditions = [{"$ne": [converted, None]}]
    for op, value in bounds.items():
        conditions.append({op: [converted, datetime.fromisoformat(value.replace("Z", "+00:00"))]})
    return {**tenant_filter, "$expr": {"$and": conditions}}


def business_date(value):
    if not isinstance(value, datetime):
        value = datetime.fromisoformat(value.replace("Z", "+00:00"))
    if value.tzinfo is None:
        value = value.replace(tzinfo=timezone.utc)
    return value.astimezone(BUSINESS_TZ).date().isoformat()
