"""
HealthPRO - Overtime Management Router
Menaxhimi i orëve shtesë për punonjësit
"""
from fastapi import APIRouter, HTTPException, Query, Header
from typing import List, Optional
from datetime import datetime, timezone
from calendar import monthrange
import uuid
import jwt
import os

from database import db
from .models import (
    OvertimeEntryCreate, OvertimeEntryUpdate, OvertimeEntryResponse,
    OvertimeType, MonthlyOvertimeSummary, OvertimeCoefficients
)

router = APIRouter(prefix="/healthpro/overtime", tags=["HealthPRO Overtime"])

SECRET_KEY = os.environ.get("JWT_SECRET", "healthpro-secret-key-2026")
ALGORITHM = "HS256"

# Default coefficients
DEFAULT_COEFFICIENTS = {
    "normal": 1.25,
    "night": 1.5,
    "weekend": 1.5,
    "holiday": 2.0
}


async def get_current_hp_user(authorization: str = Header(None)):
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Jo i autorizuar")
    token = authorization.replace("Bearer ", "")
    try:
        return jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
    except:
        raise HTTPException(status_code=401, detail="Token i pavlefshëm")


def calculate_overtime_pay(hours: float, overtime_type: str, hourly_rate: float, coefficients: dict) -> float:
    """Llogarit pagën e orëve shtesë bazuar në koeficient"""
    coef = coefficients.get(overtime_type, 1.25)
    return round(hours * hourly_rate * coef, 2)


async def get_tenant_coefficients(tenant_id: str) -> dict:
    """Merr koeficientët e tenant-it ose default"""
    tenant = await db.hp_tenants.find_one({"id": tenant_id}, {"_id": 0})
    if tenant and tenant.get("settings", {}).get("overtime_coefficients"):
        return tenant["settings"]["overtime_coefficients"]
    return DEFAULT_COEFFICIENTS


# ============ COEFFICIENTS ROUTES (MUST BE BEFORE /{entry_id}) ============

@router.get("/coefficients")
async def get_overtime_coefficients(authorization: str = Header(None)):
    """Merr koeficientët e orëve shtesë"""
    user = await get_current_hp_user(authorization)
    tenant_id = user.get("tenant_id")
    
    coefficients = await get_tenant_coefficients(tenant_id)
    return OvertimeCoefficients(**coefficients)


@router.put("/coefficients")
async def update_overtime_coefficients(
    coefficients: OvertimeCoefficients,
    authorization: str = Header(None)
):
    """Përditëso koeficientët e orëve shtesë"""
    user = await get_current_hp_user(authorization)
    tenant_id = user.get("tenant_id")
    
    if user.get("role") not in ["admin", "super_admin"]:
        raise HTTPException(status_code=403, detail="Vetëm administratori mund të ndryshojë cilësimet")
    
    result = await db.hp_tenants.update_one(
        {"id": tenant_id},
        {"$set": {"settings.overtime_coefficients": coefficients.model_dump()}}
    )
    
    return {"message": "Koeficientët u përditësuan me sukses", "coefficients": coefficients}


# ============ MAIN ROUTES ============

@router.post("", response_model=OvertimeEntryResponse)
async def create_overtime_entry(entry: OvertimeEntryCreate, authorization: str = Header(None)):
    """Shto orë shtesë për një punëtor"""
    user = await get_current_hp_user(authorization)
    tenant_id = user.get("tenant_id")
    
    # Vetëm admin mund të shtojë orë shtesë
    if user.get("role") not in ["admin", "super_admin"]:
        raise HTTPException(status_code=403, detail="Vetëm administratori mund të regjistrojë orë shtesë")
    
    # Verifiko që punëtori ekziston
    employee = await db.hp_users.find_one(
        {"id": entry.employee_id, "tenant_id": tenant_id},
        {"_id": 0}
    )
    if not employee:
        raise HTTPException(status_code=404, detail="Punëtori nuk u gjet")
    
    # Merr koeficientët dhe llogarit pagën
    coefficients = await get_tenant_coefficients(tenant_id)
    hourly_rate = (employee.get("salary", 0) / 176) if employee.get("salary") else 0  # 22 ditë * 8 orë
    
    # Përdor koeficientin manual nëse është dhënë, përndryshe koeficientin standard
    if entry.custom_coefficient and entry.custom_coefficient > 0:
        used_coefficient = entry.custom_coefficient
        calculated_pay = round(entry.hours * hourly_rate * used_coefficient, 2)
    else:
        used_coefficient = coefficients.get(entry.overtime_type.value, 1.25)
        calculated_pay = calculate_overtime_pay(entry.hours, entry.overtime_type.value, hourly_rate, coefficients)
    
    entry_id = str(uuid.uuid4())
    now = datetime.now(timezone.utc).isoformat()
    
    entry_doc = {
        "id": entry_id,
        "tenant_id": tenant_id,
        "employee_id": entry.employee_id,
        "date": entry.date,
        "overtime_type": entry.overtime_type.value,
        "hours": entry.hours,
        "calculated_pay": calculated_pay,
        "used_coefficient": used_coefficient,
        "custom_coefficient": entry.custom_coefficient,
        "notes": entry.notes,
        "created_at": now,
        "created_by": user.get("sub")
    }
    
    await db.hp_overtime.insert_one(entry_doc)
    
    employee_name = f"{employee.get('first_name', '')} {employee.get('last_name', '')}".strip()
    
    return OvertimeEntryResponse(
        id=entry_id,
        tenant_id=tenant_id,
        employee_id=entry.employee_id,
        employee_name=employee_name,
        date=entry.date,
        overtime_type=entry.overtime_type,
        hours=entry.hours,
        calculated_pay=calculated_pay,
        used_coefficient=used_coefficient,
        custom_coefficient=entry.custom_coefficient,
        notes=entry.notes,
        created_at=now,
        created_by=user.get("sub")
    )


@router.get("", response_model=List[OvertimeEntryResponse])
async def list_overtime_entries(
    employee_id: Optional[str] = Query(None),
    overtime_type: Optional[OvertimeType] = Query(None),
    month: Optional[int] = Query(None, ge=1, le=12),
    year: Optional[int] = Query(None),
    limit: int = Query(100, ge=1, le=500),
    authorization: str = Header(None)
):
    """Lista e orëve shtesë"""
    user = await get_current_hp_user(authorization)
    tenant_id = user.get("tenant_id")
    
    query = {"tenant_id": tenant_id}
    
    if employee_id:
        query["employee_id"] = employee_id
    if overtime_type:
        query["overtime_type"] = overtime_type.value
    
    # Filter by month/year if provided
    if month and year:
        start_date = f"{year}-{month:02d}-01"
        last_day = monthrange(year, month)[1]
        end_date = f"{year}-{month:02d}-{last_day}"
        query["date"] = {"$gte": start_date, "$lte": end_date}
    elif year:
        query["date"] = {"$regex": f"^{year}"}
    
    cursor = db.hp_overtime.find(query, {"_id": 0}).sort("date", -1).limit(limit)
    entries = await cursor.to_list(length=limit)
    
    # Merr emrat e punonjësve
    employee_ids = list(set(e["employee_id"] for e in entries))
    employees = {}
    if employee_ids:
        emp_cursor = db.hp_users.find({"id": {"$in": employee_ids}}, {"_id": 0})
        async for emp in emp_cursor:
            employees[emp["id"]] = f"{emp.get('first_name', '')} {emp.get('last_name', '')}".strip()
    
    return [
        OvertimeEntryResponse(
            id=e["id"],
            tenant_id=e["tenant_id"],
            employee_id=e["employee_id"],
            employee_name=employees.get(e["employee_id"], ""),
            date=e["date"],
            overtime_type=e["overtime_type"],
            hours=e["hours"],
            calculated_pay=e.get("calculated_pay"),
            used_coefficient=e.get("used_coefficient"),
            custom_coefficient=e.get("custom_coefficient"),
            notes=e.get("notes"),
            created_at=e["created_at"],
            created_by=e.get("created_by")
        )
        for e in entries
    ]


@router.get("/summary/{employee_id}")
async def get_employee_overtime_summary(
    employee_id: str,
    month: int = Query(..., ge=1, le=12),
    year: int = Query(...),
    authorization: str = Header(None)
):
    """Përmbledhje e orëve shtesë për një punëtor për një muaj"""
    user = await get_current_hp_user(authorization)
    tenant_id = user.get("tenant_id")
    
    # Verifiko punëtorin
    employee = await db.hp_users.find_one(
        {"id": employee_id, "tenant_id": tenant_id},
        {"_id": 0}
    )
    if not employee:
        raise HTTPException(status_code=404, detail="Punëtori nuk u gjet")
    
    # Merr të gjitha orët shtesë për këtë muaj
    start_date = f"{year}-{month:02d}-01"
    last_day = monthrange(year, month)[1]
    end_date = f"{year}-{month:02d}-{last_day}"
    
    cursor = db.hp_overtime.find({
        "tenant_id": tenant_id,
        "employee_id": employee_id,
        "date": {"$gte": start_date, "$lte": end_date}
    }, {"_id": 0})
    
    entries = await cursor.to_list(length=1000)
    
    # Llogarit totalet
    summary = {
        "normal": 0,
        "night": 0,
        "weekend": 0,
        "holiday": 0
    }
    total_pay = 0
    
    for entry in entries:
        otype = entry.get("overtime_type", "normal")
        summary[otype] = summary.get(otype, 0) + entry.get("hours", 0)
        total_pay += entry.get("calculated_pay", 0)
    
    employee_name = f"{employee.get('first_name', '')} {employee.get('last_name', '')}".strip()
    base_salary = employee.get("salary", 0)
    
    return MonthlyOvertimeSummary(
        employee_id=employee_id,
        employee_name=employee_name,
        month=month,
        year=year,
        base_salary=base_salary,
        normal_hours=summary["normal"],
        night_hours=summary["night"],
        weekend_hours=summary["weekend"],
        holiday_hours=summary["holiday"],
        total_overtime_hours=sum(summary.values()),
        total_overtime_pay=round(total_pay, 2)
    )


@router.get("/monthly-report")
async def get_monthly_overtime_report(
    month: int = Query(..., ge=1, le=12),
    year: int = Query(...),
    authorization: str = Header(None)
):
    """Raporti mujor i orëve shtesë për të gjithë punëtorët"""
    user = await get_current_hp_user(authorization)
    tenant_id = user.get("tenant_id")
    
    # Merr të gjithë punëtorët aktivë
    emp_cursor = db.hp_users.find(
        {"tenant_id": tenant_id, "status": "active"},
        {"_id": 0}
    )
    employees = await emp_cursor.to_list(length=500)
    
    # Merr të gjitha orët shtesë për këtë muaj
    start_date = f"{year}-{month:02d}-01"
    last_day = monthrange(year, month)[1]
    end_date = f"{year}-{month:02d}-{last_day}"
    
    ot_cursor = db.hp_overtime.find({
        "tenant_id": tenant_id,
        "date": {"$gte": start_date, "$lte": end_date}
    }, {"_id": 0})
    
    overtime_entries = await ot_cursor.to_list(length=5000)
    
    # Grupo sipas punëtorit
    by_employee = {}
    for entry in overtime_entries:
        emp_id = entry["employee_id"]
        if emp_id not in by_employee:
            by_employee[emp_id] = {"normal": 0, "night": 0, "weekend": 0, "holiday": 0, "total_pay": 0}
        otype = entry.get("overtime_type", "normal")
        by_employee[emp_id][otype] += entry.get("hours", 0)
        by_employee[emp_id]["total_pay"] += entry.get("calculated_pay", 0)
    
    # Ndërto raportin
    report = []
    for emp in employees:
        emp_id = emp["id"]
        emp_name = f"{emp.get('first_name', '')} {emp.get('last_name', '')}".strip()
        emp_data = by_employee.get(emp_id, {"normal": 0, "night": 0, "weekend": 0, "holiday": 0, "total_pay": 0})
        
        total_hours = emp_data["normal"] + emp_data["night"] + emp_data["weekend"] + emp_data["holiday"]
        
        report.append({
            "employee_id": emp_id,
            "employee_name": emp_name,
            "role": emp.get("role", ""),
            "base_salary": emp.get("salary", 0),
            "normal_hours": emp_data["normal"],
            "night_hours": emp_data["night"],
            "weekend_hours": emp_data["weekend"],
            "holiday_hours": emp_data["holiday"],
            "total_overtime_hours": total_hours,
            "total_overtime_pay": round(emp_data["total_pay"], 2)
        })
    
    # Sorto sipas pagës së orëve shtesë (descending)
    report.sort(key=lambda x: x["total_overtime_pay"], reverse=True)
    
    return {
        "month": month,
        "year": year,
        "employees": report,
        "totals": {
            "total_employees": len(report),
            "total_overtime_hours": sum(r["total_overtime_hours"] for r in report),
            "total_overtime_pay": round(sum(r["total_overtime_pay"] for r in report), 2)
        }
    }


@router.put("/{entry_id}", response_model=OvertimeEntryResponse)
async def update_overtime_entry(
    entry_id: str,
    update: OvertimeEntryUpdate,
    authorization: str = Header(None)
):
    """Përditëso një regjistrim orësh shtesë"""
    user = await get_current_hp_user(authorization)
    tenant_id = user.get("tenant_id")
    
    if user.get("role") not in ["admin", "super_admin"]:
        raise HTTPException(status_code=403, detail="Vetëm administratori mund të modifikojë")
    
    existing = await db.hp_overtime.find_one({"id": entry_id, "tenant_id": tenant_id}, {"_id": 0})
    if not existing:
        raise HTTPException(status_code=404, detail="Regjistrimi nuk u gjet")
    
    update_data = {k: v for k, v in update.model_dump().items() if v is not None}
    
    # Ri-llogarit pagën nëse ndryshojnë orët ose tipi
    if update_data:
        employee = await db.hp_users.find_one({"id": existing["employee_id"]}, {"_id": 0})
        coefficients = await get_tenant_coefficients(tenant_id)
        hourly_rate = (employee.get("salary", 0) / 176) if employee and employee.get("salary") else 0
        
        new_hours = update_data.get("hours", existing.get("hours", 0))
        new_type = update_data.get("overtime_type", existing.get("overtime_type", "normal"))
        if isinstance(new_type, OvertimeType):
            new_type = new_type.value
        
        update_data["calculated_pay"] = calculate_overtime_pay(new_hours, new_type, hourly_rate, coefficients)
        if "overtime_type" in update_data and isinstance(update_data["overtime_type"], OvertimeType):
            update_data["overtime_type"] = update_data["overtime_type"].value
    
    await db.hp_overtime.update_one(
        {"id": entry_id, "tenant_id": tenant_id},
        {"$set": update_data}
    )
    
    updated = await db.hp_overtime.find_one({"id": entry_id}, {"_id": 0})
    employee = await db.hp_users.find_one({"id": updated["employee_id"]}, {"_id": 0})
    employee_name = f"{employee.get('first_name', '')} {employee.get('last_name', '')}".strip() if employee else ""
    
    return OvertimeEntryResponse(
        id=updated["id"],
        tenant_id=updated["tenant_id"],
        employee_id=updated["employee_id"],
        employee_name=employee_name,
        date=updated["date"],
        overtime_type=updated["overtime_type"],
        hours=updated["hours"],
        calculated_pay=updated.get("calculated_pay"),
        notes=updated.get("notes"),
        created_at=updated["created_at"],
        created_by=updated.get("created_by")
    )


@router.delete("/{entry_id}")
async def delete_overtime_entry(entry_id: str, authorization: str = Header(None)):
    """Fshi një regjistrim orësh shtesë"""
    user = await get_current_hp_user(authorization)
    tenant_id = user.get("tenant_id")
    
    if user.get("role") not in ["admin", "super_admin"]:
        raise HTTPException(status_code=403, detail="Vetëm administratori mund të fshijë")
    
    result = await db.hp_overtime.delete_one({"id": entry_id, "tenant_id": tenant_id})
    
    if result.deleted_count == 0:
        raise HTTPException(status_code=404, detail="Regjistrimi nuk u gjet")
    
    return {"message": "Regjistrimi u fshi me sukses"}
