"""BookPRO Public Booking API - No Authentication Required"""
from fastapi import APIRouter, HTTPException
from typing import List, Optional
from datetime import datetime, timezone, timedelta
import uuid

from .database import bp_tenants, bp_services, bp_users, bp_appointments, bp_clients
from .models import AppointmentStatus

router = APIRouter(prefix="/bookpro/public", tags=["BookPRO Public"])


@router.get("/{salon_slug}")
async def get_public_salon(salon_slug: str):
    """Get public salon info for booking page"""
    # Find tenant by slug (name field)
    tenant = await bp_tenants.find_one(
        {"name": salon_slug, "status": "active"},
        {"_id": 0, "password_hash": 0}
    )
    
    if not tenant:
        raise HTTPException(status_code=404, detail="Salloni nuk u gjet")
    
    tenant_id = tenant["id"]
    
    # Get active services
    services = await bp_services.find(
        {"tenant_id": tenant_id, "is_active": True},
        {"_id": 0}
    ).to_list(100)
    
    # Get active stylists
    staff = await bp_users.find(
        {"tenant_id": tenant_id, "is_active": True, "role": {"$in": ["admin", "stylist"]}},
        {"_id": 0, "password_hash": 0, "username": 0}
    ).to_list(50)
    
    return {
        "salon": {
            "id": tenant["id"],
            "salon_name": tenant.get("salon_name"),
            "email": tenant.get("email"),
            "phone": tenant.get("phone"),
            "address": tenant.get("address"),
            "city": tenant.get("city"),
            "opening_time": tenant.get("opening_time", "09:00"),
            "closing_time": tenant.get("closing_time", "19:00"),
            "working_days": tenant.get("working_days", ["monday", "tuesday", "wednesday", "thursday", "friday", "saturday"]),
            "instagram": tenant.get("instagram"),
            "facebook": tenant.get("facebook"),
            "primary_color": tenant.get("primary_color", "#e11d48")
        },
        "services": services,
        "staff": staff
    }


@router.get("/{salon_slug}/availability")
async def get_availability(
    salon_slug: str,
    stylist_id: str,
    date: str,
    duration: int = 60
):
    """Get available time slots for a stylist on a specific date"""
    tenant = await bp_tenants.find_one({"name": salon_slug, "status": "active"})
    if not tenant:
        raise HTTPException(status_code=404, detail="Salloni nuk u gjet")
    
    tenant_id = tenant["id"]
    
    # Validate stylist belongs to this tenant
    stylist = await bp_users.find_one({
        "id": stylist_id,
        "tenant_id": tenant_id,
        "is_active": True
    })
    if not stylist:
        raise HTTPException(status_code=404, detail="Stilisti nuk u gjet")
    
    # Get salon working hours
    opening = tenant.get("opening_time", "09:00")
    closing = tenant.get("closing_time", "19:00")
    
    # Check if selected date is a working day
    try:
        selected_date = datetime.strptime(date, "%Y-%m-%d")
        day_name = selected_date.strftime("%A").lower()
        working_days = tenant.get("working_days", ["monday", "tuesday", "wednesday", "thursday", "friday", "saturday"])
        
        if day_name not in working_days:
            return {"slots": [], "message": "Salloni është i mbyllur në këtë ditë"}
    except ValueError:
        raise HTTPException(status_code=400, detail="Format i gabuar i datës")
    
    # Generate all possible time slots (30 min intervals)
    slots = []
    opening_hour, opening_min = map(int, opening.split(":"))
    closing_hour, closing_min = map(int, closing.split(":"))
    
    current_time = datetime(2000, 1, 1, opening_hour, opening_min)
    end_time = datetime(2000, 1, 1, closing_hour, closing_min)
    
    while current_time.hour * 60 + current_time.minute + duration <= closing_hour * 60 + closing_min:
        slots.append(current_time.strftime("%H:%M"))
        current_time += timedelta(minutes=30)
    
    # Get existing appointments for the stylist on this date
    existing = await bp_appointments.find({
        "tenant_id": tenant_id,
        "stylist_id": stylist_id,
        "appointment_date": date,
        "status": {"$nin": ["cancelled", "no_show"]}
    }).to_list(100)
    
    # Remove occupied slots
    available = []
    for slot in slots:
        slot_start = int(slot.split(":")[0]) * 60 + int(slot.split(":")[1])
        slot_end = slot_start + duration
        
        is_available = True
        for apt in existing:
            apt_start = int(apt["start_time"].split(":")[0]) * 60 + int(apt["start_time"].split(":")[1])
            apt_end = int(apt["end_time"].split(":")[0]) * 60 + int(apt["end_time"].split(":")[1])
            
            # Check for overlap
            if not (slot_end <= apt_start or slot_start >= apt_end):
                is_available = False
                break
        
        if is_available:
            available.append(slot)
    
    # If date is today, remove past times
    today = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    if date == today:
        now_minutes = datetime.now(timezone.utc).hour * 60 + datetime.now(timezone.utc).minute
        available = [s for s in available if int(s.split(":")[0]) * 60 + int(s.split(":")[1]) > now_minutes]
    
    return {"slots": available}


@router.post("/{salon_slug}/book")
async def create_public_booking(salon_slug: str, booking_data: dict):
    """Create a new booking from public page"""
    tenant = await bp_tenants.find_one({"name": salon_slug, "status": "active"})
    if not tenant:
        raise HTTPException(status_code=404, detail="Salloni nuk u gjet")
    
    tenant_id = tenant["id"]
    
    # Validate required fields
    required = ["services", "stylist_id", "appointment_date", "start_time", "client_name", "client_phone"]
    for field in required:
        if not booking_data.get(field):
            raise HTTPException(status_code=400, detail=f"Fusha '{field}' është e detyrueshme")
    
    # Validate stylist
    stylist = await bp_users.find_one({
        "id": booking_data["stylist_id"],
        "tenant_id": tenant_id,
        "is_active": True
    })
    if not stylist:
        raise HTTPException(status_code=404, detail="Stilisti nuk u gjet")
    
    # Calculate end time
    total_duration = sum(s.get("duration_minutes", 30) for s in booking_data["services"])
    start_parts = booking_data["start_time"].split(":")
    start_minutes = int(start_parts[0]) * 60 + int(start_parts[1])
    end_minutes = start_minutes + total_duration
    end_time = f"{end_minutes // 60:02d}:{end_minutes % 60:02d}"
    
    # Check for conflicts
    existing = await bp_appointments.find_one({
        "tenant_id": tenant_id,
        "stylist_id": booking_data["stylist_id"],
        "appointment_date": booking_data["appointment_date"],
        "status": {"$nin": ["cancelled", "no_show"]},
        "$or": [
            {"start_time": {"$lt": end_time}, "end_time": {"$gt": booking_data["start_time"]}}
        ]
    })
    if existing:
        raise HTTPException(status_code=409, detail="Kjo kohë nuk është e disponueshme")
    
    # Create or find client
    client = await bp_clients.find_one({
        "tenant_id": tenant_id,
        "phone": booking_data["client_phone"]
    })
    
    client_id = None
    if client:
        client_id = client["id"]
    else:
        # Create new client
        client_id = str(uuid.uuid4())
        new_client = {
            "id": client_id,
            "tenant_id": tenant_id,
            "full_name": booking_data["client_name"],
            "phone": booking_data["client_phone"],
            "email": booking_data.get("client_email"),
            "created_at": datetime.now(timezone.utc).isoformat(),
            "total_visits": 0,
            "total_spent": 0,
            "loyalty_points": 0
        }
        await bp_clients.insert_one(new_client)
    
    # Generate appointment number
    today = datetime.now(timezone.utc).strftime("%Y%m%d")
    prefix = f"BP-{today}"
    count = await bp_appointments.count_documents({
        "tenant_id": tenant_id,
        "appointment_number": {"$regex": f"^{prefix}"}
    })
    appointment_number = f"{prefix}-{count + 1:04d}"
    
    # Calculate total price
    total_price = sum(s.get("price", 0) for s in booking_data["services"])
    
    now = datetime.now(timezone.utc)
    
    appointment = {
        "id": str(uuid.uuid4()),
        "appointment_number": appointment_number,
        "tenant_id": tenant_id,
        "client_id": client_id,
        "client_name": booking_data["client_name"],
        "client_phone": booking_data["client_phone"],
        "client_email": booking_data.get("client_email"),
        "stylist_id": booking_data["stylist_id"],
        "stylist_name": stylist.get("full_name"),
        "services": booking_data["services"],
        "appointment_date": booking_data["appointment_date"],
        "start_time": booking_data["start_time"],
        "end_time": end_time,
        "total_duration": total_duration,
        "total_price": total_price,
        "status": AppointmentStatus.CONFIRMED.value,
        "notes": booking_data.get("notes"),
        "booked_online": True,
        "created_at": now.isoformat(),
        "updated_at": now.isoformat()
    }
    
    await bp_appointments.insert_one(appointment)
    
    # Return without _id
    appointment.pop("_id", None)
    
    return appointment
