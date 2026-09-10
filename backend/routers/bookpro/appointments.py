"""BookPRO Appointments/Booking Management Routes"""
from fastapi import APIRouter, HTTPException, Depends
from typing import List, Optional
from datetime import datetime, timezone, timedelta
import uuid

from .database import bp_appointments, bp_clients, bp_services, bp_users, bp_working_hours
from .models import (
    BPAppointmentCreate, BPAppointmentUpdate, BPAppointmentResponse,
    AppointmentStatus, AppointmentServiceItem, PaymentMethod
)
from .auth import verify_bp_token

router = APIRouter(prefix="/bookpro/appointments", tags=["BookPRO Appointments"])


def get_tenant_filter(user: dict) -> dict:
    """Get tenant filter for queries"""
    if user.get("role") == "super_admin":
        return {}
    return {"tenant_id": user.get("tenant_id")}


async def generate_appointment_number(tenant_id: str) -> str:
    """Generate unique appointment number"""
    today = datetime.now(timezone.utc).strftime("%Y%m%d")
    prefix = f"BP-{today}"
    count = await bp_appointments.count_documents({
        "tenant_id": tenant_id,
        "appointment_number": {"$regex": f"^{prefix}"}
    })
    return f"{prefix}-{str(count + 1).zfill(4)}"


def calculate_end_time(start_time: str, total_minutes: int) -> str:
    """Calculate end time from start time and duration"""
    hour, minute = map(int, start_time.split(":"))
    start_datetime = datetime.now().replace(hour=hour, minute=minute, second=0)
    end_datetime = start_datetime + timedelta(minutes=total_minutes)
    return end_datetime.strftime("%H:%M")


@router.post("", response_model=BPAppointmentResponse)
async def create_appointment(
    appointment_data: BPAppointmentCreate,
    current_user: dict = Depends(verify_bp_token)
):
    """Create a new appointment/booking"""
    tenant_id = current_user.get("tenant_id")
    if not tenant_id and current_user.get("role") != "super_admin":
        raise HTTPException(status_code=400, detail="Tenant ID mungon")
    
    # Validate stylist exists
    stylist = await bp_users.find_one({"id": appointment_data.stylist_id, "tenant_id": tenant_id}, {"_id": 0})
    if not stylist:
        raise HTTPException(status_code=404, detail="Stilisti nuk u gjet")
    
    # Get client info if client_id provided
    client_name = appointment_data.client_name
    client_phone = appointment_data.client_phone
    
    if appointment_data.client_id:
        client = await bp_clients.find_one({"id": appointment_data.client_id}, {"_id": 0})
        if client:
            client_name = client.get("full_name")
            client_phone = client.get("phone")
    
    # Calculate total duration and price
    total_duration = sum(s.duration_minutes for s in appointment_data.services)
    total_price = sum(s.price for s in appointment_data.services)
    
    # Enrich services with names
    services_with_names = []
    for service_item in appointment_data.services:
        service = await bp_services.find_one({"id": service_item.service_id}, {"_id": 0})
        services_with_names.append(AppointmentServiceItem(
            service_id=service_item.service_id,
            service_name=service.get("name") if service else service_item.service_name,
            price=service_item.price,
            duration_minutes=service_item.duration_minutes
        ).model_dump())
    
    end_time = calculate_end_time(appointment_data.start_time, total_duration)
    
    # Check for conflicts
    existing = await bp_appointments.find_one({
        "stylist_id": appointment_data.stylist_id,
        "appointment_date": appointment_data.appointment_date,
        "status": {"$nin": ["cancelled", "no_show"]},
        "$or": [
            {
                "start_time": {"$lt": end_time},
                "end_time": {"$gt": appointment_data.start_time}
            }
        ]
    }, {"_id": 0})
    
    if existing:
        raise HTTPException(
            status_code=400, 
            detail=f"Stilisti ka një rezervim tjetër në këtë orar ({existing.get('start_time')} - {existing.get('end_time')})"
        )
    
    now = datetime.now(timezone.utc)
    appointment_number = await generate_appointment_number(tenant_id)
    
    appointment = {
        "id": str(uuid.uuid4()),
        "appointment_number": appointment_number,
        "client_id": appointment_data.client_id,
        "client_name": client_name,
        "client_phone": client_phone,
        "stylist_id": appointment_data.stylist_id,
        "stylist_name": stylist.get("full_name"),
        "services": services_with_names,
        "appointment_date": appointment_data.appointment_date,
        "start_time": appointment_data.start_time,
        "end_time": end_time,
        "total_duration": total_duration,
        "total_price": total_price,
        "status": AppointmentStatus.CONFIRMED.value,
        "notes": appointment_data.notes,
        "source": appointment_data.source,
        "payment_method": None,
        "payment_amount": 0,
        "tip_amount": 0,
        "tenant_id": tenant_id,
        "created_by": current_user["id"],
        "created_at": now.isoformat(),
        "updated_at": now.isoformat(),
        "completed_at": None
    }
    
    await bp_appointments.insert_one(appointment)
    
    return BPAppointmentResponse(**appointment)


@router.get("", response_model=List[BPAppointmentResponse])
async def get_appointments(
    date: Optional[str] = None,
    stylist_id: Optional[str] = None,
    status: Optional[AppointmentStatus] = None,
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
    limit: int = 100,
    current_user: dict = Depends(verify_bp_token)
):
    """Get appointments with filters"""
    query = get_tenant_filter(current_user)
    
    if date:
        query["appointment_date"] = date
    if stylist_id:
        query["stylist_id"] = stylist_id
    if status:
        query["status"] = status.value
    if start_date and end_date:
        query["appointment_date"] = {"$gte": start_date, "$lte": end_date}
    elif start_date:
        query["appointment_date"] = {"$gte": start_date}
    elif end_date:
        query["appointment_date"] = {"$lte": end_date}
    
    appointments = await bp_appointments.find(query, {"_id": 0}).sort([
        ("appointment_date", 1),
        ("start_time", 1)
    ]).to_list(limit)
    
    return [BPAppointmentResponse(**a) for a in appointments]


@router.get("/today", response_model=List[BPAppointmentResponse])
async def get_today_appointments(current_user: dict = Depends(verify_bp_token)):
    """Get today's appointments"""
    today = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    query = {
        "appointment_date": today,
        **get_tenant_filter(current_user)
    }
    
    appointments = await bp_appointments.find(query, {"_id": 0}).sort("start_time", 1).to_list(100)
    
    return [BPAppointmentResponse(**a) for a in appointments]


@router.get("/calendar")
async def get_calendar_view(
    start_date: str,
    end_date: str,
    stylist_id: Optional[str] = None,
    current_user: dict = Depends(verify_bp_token)
):
    """Get appointments for calendar view"""
    query = {
        "appointment_date": {"$gte": start_date, "$lte": end_date},
        **get_tenant_filter(current_user)
    }
    
    if stylist_id:
        query["stylist_id"] = stylist_id
    
    appointments = await bp_appointments.find(query, {"_id": 0}).to_list(500)
    
    # Group by date
    calendar = {}
    for apt in appointments:
        date = apt["appointment_date"]
        if date not in calendar:
            calendar[date] = []
        calendar[date].append(apt)
    
    return calendar


@router.get("/{appointment_id}", response_model=BPAppointmentResponse)
async def get_appointment(appointment_id: str, current_user: dict = Depends(verify_bp_token)):
    """Get a specific appointment"""
    query = {"id": appointment_id, **get_tenant_filter(current_user)}
    appointment = await bp_appointments.find_one(query, {"_id": 0})
    
    if not appointment:
        raise HTTPException(status_code=404, detail="Rezervimi nuk u gjet")
    
    return BPAppointmentResponse(**appointment)


@router.put("/{appointment_id}", response_model=BPAppointmentResponse)
async def update_appointment(
    appointment_id: str,
    update_data: BPAppointmentUpdate,
    current_user: dict = Depends(verify_bp_token)
):
    """Update an appointment"""
    query = {"id": appointment_id, **get_tenant_filter(current_user)}
    appointment = await bp_appointments.find_one(query, {"_id": 0})
    
    if not appointment:
        raise HTTPException(status_code=404, detail="Rezervimi nuk u gjet")
    
    now = datetime.now(timezone.utc)
    update_dict = {"updated_at": now.isoformat()}
    
    for k, v in update_data.model_dump().items():
        if v is not None:
            if k == "status":
                update_dict[k] = v.value
                if v == AppointmentStatus.COMPLETED:
                    update_dict["completed_at"] = now.isoformat()
                    # Update client stats
                    if appointment.get("client_id"):
                        await bp_clients.update_one(
                            {"id": appointment["client_id"]},
                            {
                                "$inc": {
                                    "total_visits": 1,
                                    "total_spent": appointment.get("total_price", 0)
                                },
                                "$set": {"last_visit": now.isoformat()}
                            }
                        )
            elif k == "payment_method":
                update_dict[k] = v.value
            elif k == "services":
                # Recalculate totals
                total_duration = sum(s.duration_minutes for s in v)
                total_price = sum(s.price for s in v)
                update_dict["services"] = [s.model_dump() for s in v]
                update_dict["total_duration"] = total_duration
                update_dict["total_price"] = total_price
                update_dict["end_time"] = calculate_end_time(
                    update_data.start_time or appointment["start_time"],
                    total_duration
                )
            else:
                update_dict[k] = v
    
    # Recalculate end time if start_time changed
    if update_data.start_time and "end_time" not in update_dict:
        update_dict["end_time"] = calculate_end_time(
            update_data.start_time,
            appointment.get("total_duration", 30)
        )
    
    await bp_appointments.update_one({"id": appointment_id}, {"$set": update_dict})
    
    updated = await bp_appointments.find_one({"id": appointment_id}, {"_id": 0})
    return BPAppointmentResponse(**updated)


@router.post("/{appointment_id}/complete")
async def complete_appointment(
    appointment_id: str,
    payment_method: PaymentMethod = PaymentMethod.CASH,
    payment_amount: Optional[float] = None,
    tip_amount: float = 0,
    current_user: dict = Depends(verify_bp_token)
):
    """Complete an appointment with payment"""
    query = {"id": appointment_id, **get_tenant_filter(current_user)}
    appointment = await bp_appointments.find_one(query, {"_id": 0})
    
    if not appointment:
        raise HTTPException(status_code=404, detail="Rezervimi nuk u gjet")
    
    if appointment.get("status") == "completed":
        raise HTTPException(status_code=400, detail="Rezervimi është përfunduar tashmë")
    
    now = datetime.now(timezone.utc)
    final_payment = payment_amount if payment_amount is not None else appointment.get("total_price", 0)
    
    update_dict = {
        "status": AppointmentStatus.COMPLETED.value,
        "payment_method": payment_method.value,
        "payment_amount": final_payment,
        "tip_amount": tip_amount,
        "completed_at": now.isoformat(),
        "updated_at": now.isoformat()
    }
    
    await bp_appointments.update_one({"id": appointment_id}, {"$set": update_dict})
    
    # Update client stats
    if appointment.get("client_id"):
        await bp_clients.update_one(
            {"id": appointment["client_id"]},
            {
                "$inc": {
                    "total_visits": 1,
                    "total_spent": final_payment + tip_amount,
                    "loyalty_points": int(final_payment / 10)  # 1 point per 10 EUR
                },
                "$set": {"last_visit": now.isoformat()}
            }
        )
    
    return {"message": "Rezervimi u përfundua me sukses", "payment": final_payment, "tip": tip_amount}


@router.post("/{appointment_id}/cancel")
async def cancel_appointment(
    appointment_id: str,
    reason: Optional[str] = None,
    current_user: dict = Depends(verify_bp_token)
):
    """Cancel an appointment"""
    query = {"id": appointment_id, **get_tenant_filter(current_user)}
    appointment = await bp_appointments.find_one(query, {"_id": 0})
    
    if not appointment:
        raise HTTPException(status_code=404, detail="Rezervimi nuk u gjet")
    
    if appointment.get("status") in ["completed", "cancelled"]:
        raise HTTPException(status_code=400, detail="Rezervimi nuk mund të anulohet")
    
    now = datetime.now(timezone.utc)
    notes = appointment.get("notes") or ""
    if reason:
        notes += f"\n[Anuluar: {reason}]"
    
    await bp_appointments.update_one(
        {"id": appointment_id},
        {"$set": {
            "status": AppointmentStatus.CANCELLED.value,
            "notes": notes,
            "updated_at": now.isoformat()
        }}
    )
    
    return {"message": "Rezervimi u anulua"}


@router.get("/available-slots/{stylist_id}/{date}")
async def get_available_slots(
    stylist_id: str,
    date: str,
    duration: int = 30,
    current_user: dict = Depends(verify_bp_token)
):
    """Get available time slots for a stylist on a specific date"""
    # Get stylist's working hours for this day
    from datetime import datetime as dt
    date_obj = dt.strptime(date, "%Y-%m-%d")
    day_name = date_obj.strftime("%A").lower()
    
    working_hour = await bp_working_hours.find_one({
        "user_id": stylist_id,
        "day_of_week": day_name,
        "is_working": True,
        **get_tenant_filter(current_user)
    }, {"_id": 0})
    
    if not working_hour:
        return {"available_slots": [], "message": "Stilisti nuk punon në këtë ditë"}
    
    start_hour, start_min = map(int, working_hour["start_time"].split(":"))
    end_hour, end_min = map(int, working_hour["end_time"].split(":"))
    
    # Get existing appointments for this day
    existing = await bp_appointments.find({
        "stylist_id": stylist_id,
        "appointment_date": date,
        "status": {"$nin": ["cancelled", "no_show"]}
    }, {"_id": 0, "start_time": 1, "end_time": 1}).to_list(100)
    
    # Generate all possible slots
    slots = []
    current_time = start_hour * 60 + start_min
    end_time = end_hour * 60 + end_min
    
    while current_time + duration <= end_time:
        slot_start = f"{current_time // 60:02d}:{current_time % 60:02d}"
        slot_end = f"{(current_time + duration) // 60:02d}:{(current_time + duration) % 60:02d}"
        
        # Check if slot conflicts with existing appointments
        is_available = True
        for apt in existing:
            apt_start = apt["start_time"]
            apt_end = apt["end_time"]
            if not (slot_end <= apt_start or slot_start >= apt_end):
                is_available = False
                break
        
        if is_available:
            slots.append({
                "start_time": slot_start,
                "end_time": slot_end
            })
        
        current_time += 30  # 30 minute intervals
    
    return {"available_slots": slots}
