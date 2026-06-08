"""BookPRO Dashboard and Statistics Routes"""
from fastapi import APIRouter, HTTPException, Depends
from datetime import datetime, timezone, timedelta

from .database import bp_appointments, bp_clients, bp_services, bp_users
from .models import BPDashboardStats, AppointmentStatus
from .auth import verify_bp_token

router = APIRouter(prefix="/bookpro/dashboard", tags=["BookPRO Dashboard"])


def get_tenant_filter(user: dict) -> dict:
    """Get tenant filter for queries"""
    if user.get("role") == "super_admin":
        return {}
    return {"tenant_id": user.get("tenant_id")}


@router.get("/stats", response_model=BPDashboardStats)
async def get_dashboard_stats(current_user: dict = Depends(verify_bp_token)):
    """Get dashboard statistics"""
    tenant_filter = get_tenant_filter(current_user)
    now = datetime.now(timezone.utc)
    today = now.strftime("%Y-%m-%d")
    
    # Get week start (Monday)
    week_start = now - timedelta(days=now.weekday())
    week_start_str = week_start.strftime("%Y-%m-%d")
    
    # Get month start
    month_start_str = now.strftime("%Y-%m-01")
    
    # Today's stats
    today_appointments = await bp_appointments.count_documents({
        "appointment_date": today,
        "status": {"$nin": ["cancelled", "no_show"]},
        **tenant_filter
    })
    
    today_completed = await bp_appointments.find({
        "appointment_date": today,
        "status": AppointmentStatus.COMPLETED.value,
        **tenant_filter
    }, {"_id": 0, "payment_amount": 1, "tip_amount": 1}).to_list(100)
    
    today_revenue = sum(a.get("payment_amount", 0) + a.get("tip_amount", 0) for a in today_completed)
    
    # Week stats
    week_appointments = await bp_appointments.count_documents({
        "appointment_date": {"$gte": week_start_str, "$lte": today},
        "status": {"$nin": ["cancelled", "no_show"]},
        **tenant_filter
    })
    
    week_completed = await bp_appointments.find({
        "appointment_date": {"$gte": week_start_str, "$lte": today},
        "status": AppointmentStatus.COMPLETED.value,
        **tenant_filter
    }, {"_id": 0, "payment_amount": 1, "tip_amount": 1}).to_list(500)
    
    week_revenue = sum(a.get("payment_amount", 0) + a.get("tip_amount", 0) for a in week_completed)
    
    # Month stats
    month_appointments = await bp_appointments.count_documents({
        "appointment_date": {"$gte": month_start_str, "$lte": today},
        "status": {"$nin": ["cancelled", "no_show"]},
        **tenant_filter
    })
    
    month_completed = await bp_appointments.find({
        "appointment_date": {"$gte": month_start_str, "$lte": today},
        "status": AppointmentStatus.COMPLETED.value,
        **tenant_filter
    }, {"_id": 0, "payment_amount": 1, "tip_amount": 1}).to_list(1000)
    
    month_revenue = sum(a.get("payment_amount", 0) + a.get("tip_amount", 0) for a in month_completed)
    
    # Client stats
    total_clients = await bp_clients.count_documents(tenant_filter)
    new_clients = await bp_clients.count_documents({
        "created_at": {"$gte": month_start_str},
        **tenant_filter
    })
    
    # Pending appointments
    pending = await bp_appointments.count_documents({
        "appointment_date": {"$gte": today},
        "status": {"$in": [AppointmentStatus.PENDING.value, AppointmentStatus.CONFIRMED.value]},
        **tenant_filter
    })
    
    completed_today = len(today_completed)
    
    return BPDashboardStats(
        today_appointments=today_appointments,
        today_revenue=round(today_revenue, 2),
        week_appointments=week_appointments,
        week_revenue=round(week_revenue, 2),
        month_appointments=month_appointments,
        month_revenue=round(month_revenue, 2),
        total_clients=total_clients,
        new_clients_this_month=new_clients,
        pending_appointments=pending,
        completed_today=completed_today
    )


@router.get("/revenue-chart")
async def get_revenue_chart(
    period: str = "week",  # week, month, year
    current_user: dict = Depends(verify_bp_token)
):
    """Get revenue data for charts"""
    tenant_filter = get_tenant_filter(current_user)
    now = datetime.now(timezone.utc)
    
    if period == "week":
        days = 7
    elif period == "month":
        days = 30
    else:
        days = 365
    
    start_date = (now - timedelta(days=days)).strftime("%Y-%m-%d")
    
    appointments = await bp_appointments.find({
        "appointment_date": {"$gte": start_date},
        "status": AppointmentStatus.COMPLETED.value,
        **tenant_filter
    }, {"_id": 0, "appointment_date": 1, "payment_amount": 1, "tip_amount": 1}).to_list(1000)
    
    # Group by date
    revenue_by_date = {}
    for apt in appointments:
        date = apt["appointment_date"]
        if date not in revenue_by_date:
            revenue_by_date[date] = 0
        revenue_by_date[date] += apt.get("payment_amount", 0) + apt.get("tip_amount", 0)
    
    # Fill in missing dates with 0
    chart_data = []
    for i in range(days):
        date = (now - timedelta(days=days - i - 1)).strftime("%Y-%m-%d")
        chart_data.append({
            "date": date,
            "revenue": round(revenue_by_date.get(date, 0), 2)
        })
    
    return chart_data


@router.get("/top-services")
async def get_top_services(current_user: dict = Depends(verify_bp_token)):
    """Get top services by bookings"""
    tenant_filter = get_tenant_filter(current_user)
    
    # Get all completed appointments
    appointments = await bp_appointments.find({
        "status": AppointmentStatus.COMPLETED.value,
        **tenant_filter
    }, {"_id": 0, "services": 1}).to_list(1000)
    
    # Count services
    service_counts = {}
    for apt in appointments:
        for service in apt.get("services", []):
            service_id = service.get("service_id")
            if service_id:
                if service_id not in service_counts:
                    service_counts[service_id] = {
                        "service_id": service_id,
                        "service_name": service.get("service_name", "Unknown"),
                        "count": 0,
                        "revenue": 0
                    }
                service_counts[service_id]["count"] += 1
                service_counts[service_id]["revenue"] += service.get("price", 0)
    
    # Sort by count
    sorted_services = sorted(service_counts.values(), key=lambda x: x["count"], reverse=True)
    
    return sorted_services[:10]


@router.get("/top-stylists")
async def get_top_stylists(current_user: dict = Depends(verify_bp_token)):
    """Get top performing stylists"""
    tenant_filter = get_tenant_filter(current_user)
    
    # Get all staff
    stylists = await bp_users.find({
        "role": {"$in": ["stylist", "admin"]},
        "is_active": True,
        **tenant_filter
    }, {"_id": 0, "id": 1, "full_name": 1}).to_list(50)
    
    result = []
    for stylist in stylists:
        completed = await bp_appointments.find({
            "stylist_id": stylist["id"],
            "status": AppointmentStatus.COMPLETED.value,
            **tenant_filter
        }, {"_id": 0, "payment_amount": 1, "tip_amount": 1}).to_list(1000)
        
        total_appointments = len(completed)
        total_revenue = sum(a.get("payment_amount", 0) + a.get("tip_amount", 0) for a in completed)
        
        result.append({
            "stylist_id": stylist["id"],
            "stylist_name": stylist["full_name"],
            "appointments": total_appointments,
            "revenue": round(total_revenue, 2)
        })
    
    # Sort by revenue
    result.sort(key=lambda x: x["revenue"], reverse=True)
    
    return result
