"""
HealthPRO - Employees (HR) Management Router
"""
from fastapi import APIRouter, HTTPException, Query, Header
from typing import List, Optional
from datetime import datetime, timezone
import uuid
import hashlib
import jwt
import os

from database import db
from .models import EmployeeCreate, EmployeeUpdate, EmployeeResponse, EmployeeStatus, EmployeeRole

router = APIRouter(prefix="/healthpro/employees", tags=["HealthPRO Employees"])

SECRET_KEY = os.environ.get("JWT_SECRET", "healthpro-secret-key-2026")
ALGORITHM = "HS256"


def hash_password(password: str) -> str:
    return hashlib.sha256(password.encode()).hexdigest()


async def get_current_hp_user(authorization: str = Header(None)):
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Jo i autorizuar")
    token = authorization.replace("Bearer ", "")
    try:
        return jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
    except:
        raise HTTPException(status_code=401, detail="Token i pavlefshëm")


@router.post("", response_model=EmployeeResponse)
async def create_employee(employee: EmployeeCreate, authorization: str = Header(None)):
    """Create a new employee"""
    user = await get_current_hp_user(authorization)
    tenant_id = user.get("tenant_id")
    
    if user.get("role") not in ["admin", "super_admin"]:
        raise HTTPException(status_code=403, detail="Vetëm administratori mund të shtojë punëtor")
    
    # Check if username exists
    existing = await db.hp_users.find_one({"username": employee.username})
    if existing:
        raise HTTPException(status_code=400, detail="Username tashmë ekziston")
    
    employee_id = str(uuid.uuid4())
    now = datetime.now(timezone.utc).isoformat()
    
    employee_doc = {
        "id": employee_id,
        "tenant_id": tenant_id,
        "username": employee.username,
        "password": hash_password(employee.password),
        "first_name": employee.first_name,
        "last_name": employee.last_name,
        "email": employee.email,
        "phone": employee.phone,
        "role": employee.role,
        "department": employee.department,
        "position": employee.position,
        "hire_date": employee.hire_date,
        "contract_type": employee.contract_type,
        "work_schedule": employee.work_schedule,
        "salary": employee.salary,
        "bank_account": employee.bank_account,
        "personal_id": employee.personal_id,
        "address": employee.address,
        "emergency_contact": employee.emergency_contact,
        "notes": employee.notes,
        "status": EmployeeStatus.ACTIVE,
        "is_active": True,
        "created_at": now
    }
    
    await db.hp_users.insert_one(employee_doc)
    
    return EmployeeResponse(
        id=employee_id,
        tenant_id=tenant_id,
        username=employee.username,
        first_name=employee.first_name,
        last_name=employee.last_name,
        email=employee.email,
        phone=employee.phone,
        role=employee.role,
        department=employee.department,
        position=employee.position,
        hire_date=employee.hire_date,
        contract_type=employee.contract_type,
        work_schedule=employee.work_schedule,
        salary=employee.salary,
        bank_account=employee.bank_account,
        personal_id=employee.personal_id,
        address=employee.address,
        emergency_contact=employee.emergency_contact,
        notes=employee.notes,
        status=EmployeeStatus.ACTIVE,
        created_at=now
    )


@router.get("", response_model=List[EmployeeResponse])
async def list_employees(
    role: Optional[EmployeeRole] = Query(None),
    department: Optional[str] = Query(None),
    status: Optional[EmployeeStatus] = Query(None),
    search: Optional[str] = Query(None),
    limit: int = Query(100, ge=1, le=500),
    authorization: str = Header(None)
):
    """List all employees"""
    user = await get_current_hp_user(authorization)
    tenant_id = user.get("tenant_id")
    
    query = {"tenant_id": tenant_id}
    if role:
        query["role"] = role
    if department:
        query["department"] = department
    if status:
        query["status"] = status
    if search:
        search_regex = {"$regex": search, "$options": "i"}
        query["$or"] = [
            {"first_name": search_regex},
            {"last_name": search_regex},
            {"username": search_regex},
            {"email": search_regex}
        ]
    
    cursor = db.hp_users.find(query, {"_id": 0, "password": 0}).sort("created_at", -1).limit(limit)
    employees = await cursor.to_list(length=limit)
    
    return [
        EmployeeResponse(
            id=e["id"],
            tenant_id=e["tenant_id"],
            username=e.get("username", ""),
            first_name=e.get("first_name", ""),
            last_name=e.get("last_name", ""),
            email=e.get("email"),
            phone=e.get("phone"),
            role=e.get("role", EmployeeRole.SUPPORT),
            department=e.get("department"),
            position=e.get("position"),
            hire_date=e.get("hire_date"),
            contract_type=e.get("contract_type"),
            work_schedule=e.get("work_schedule"),
            salary=e.get("salary"),
            bank_account=e.get("bank_account"),
            personal_id=e.get("personal_id"),
            address=e.get("address"),
            emergency_contact=e.get("emergency_contact"),
            notes=e.get("notes"),
            status=e.get("status", EmployeeStatus.ACTIVE),
            created_at=e.get("created_at", "")
        )
        for e in employees
    ]


@router.get("/{employee_id}", response_model=EmployeeResponse)
async def get_employee(employee_id: str, authorization: str = Header(None)):
    """Get a specific employee"""
    user = await get_current_hp_user(authorization)
    tenant_id = user.get("tenant_id")
    
    employee = await db.hp_users.find_one(
        {"id": employee_id, "tenant_id": tenant_id},
        {"_id": 0, "password": 0}
    )
    
    if not employee:
        raise HTTPException(status_code=404, detail="Punëtori nuk u gjet")
    
    return EmployeeResponse(
        id=employee["id"],
        tenant_id=employee["tenant_id"],
        username=employee.get("username", ""),
        first_name=employee.get("first_name", ""),
        last_name=employee.get("last_name", ""),
        email=employee.get("email"),
        phone=employee.get("phone"),
        role=employee.get("role", EmployeeRole.SUPPORT),
        department=employee.get("department"),
        position=employee.get("position"),
        hire_date=employee.get("hire_date"),
        contract_type=employee.get("contract_type"),
        work_schedule=employee.get("work_schedule"),
        salary=employee.get("salary"),
        bank_account=employee.get("bank_account"),
        personal_id=employee.get("personal_id"),
        address=employee.get("address"),
        emergency_contact=employee.get("emergency_contact"),
        notes=employee.get("notes"),
        status=employee.get("status", EmployeeStatus.ACTIVE),
        created_at=employee.get("created_at", "")
    )


@router.put("/{employee_id}", response_model=EmployeeResponse)
async def update_employee(employee_id: str, update: EmployeeUpdate, authorization: str = Header(None)):
    """Update an employee"""
    user = await get_current_hp_user(authorization)
    tenant_id = user.get("tenant_id")
    
    if user.get("role") not in ["admin", "super_admin"]:
        raise HTTPException(status_code=403, detail="Vetëm administratori mund të modifikojë")
    
    existing = await db.hp_users.find_one({"id": employee_id, "tenant_id": tenant_id})
    if not existing:
        raise HTTPException(status_code=404, detail="Punëtori nuk u gjet")
    
    update_data = {k: v for k, v in update.model_dump().items() if v is not None}
    
    await db.hp_users.update_one(
        {"id": employee_id, "tenant_id": tenant_id},
        {"$set": update_data}
    )
    
    updated = await db.hp_users.find_one({"id": employee_id}, {"_id": 0, "password": 0})
    
    return EmployeeResponse(
        id=updated["id"],
        tenant_id=updated["tenant_id"],
        username=updated.get("username", ""),
        first_name=updated.get("first_name", ""),
        last_name=updated.get("last_name", ""),
        email=updated.get("email"),
        phone=updated.get("phone"),
        role=updated.get("role", EmployeeRole.SUPPORT),
        department=updated.get("department"),
        position=updated.get("position"),
        hire_date=updated.get("hire_date"),
        contract_type=updated.get("contract_type"),
        work_schedule=updated.get("work_schedule"),
        salary=updated.get("salary"),
        bank_account=updated.get("bank_account"),
        personal_id=updated.get("personal_id"),
        address=updated.get("address"),
        emergency_contact=updated.get("emergency_contact"),
        notes=updated.get("notes"),
        status=updated.get("status", EmployeeStatus.ACTIVE),
        created_at=updated.get("created_at", "")
    )


@router.delete("/{employee_id}")
async def delete_employee(employee_id: str, authorization: str = Header(None)):
    """Deactivate an employee"""
    user = await get_current_hp_user(authorization)
    tenant_id = user.get("tenant_id")
    
    if user.get("role") not in ["admin", "super_admin"]:
        raise HTTPException(status_code=403, detail="Vetëm administratori mund të fshijë")
    
    # Don't allow deleting yourself
    if user.get("sub") == employee_id:
        raise HTTPException(status_code=400, detail="Nuk mund të fshini veten")
    
    result = await db.hp_users.update_one(
        {"id": employee_id, "tenant_id": tenant_id},
        {"$set": {"status": EmployeeStatus.INACTIVE, "is_active": False}}
    )
    
    if result.modified_count == 0:
        raise HTTPException(status_code=404, detail="Punëtori nuk u gjet")
    
    return {"message": "Punëtori u çaktivizua me sukses"}


@router.get("/stats/summary")
async def get_employee_stats(authorization: str = Header(None)):
    """Get employee statistics"""
    user = await get_current_hp_user(authorization)
    tenant_id = user.get("tenant_id")
    
    total = await db.hp_users.count_documents({"tenant_id": tenant_id})
    active = await db.hp_users.count_documents({"tenant_id": tenant_id, "status": "active"})
    
    # By role
    doctors = await db.hp_users.count_documents({"tenant_id": tenant_id, "role": "doctor", "status": "active"})
    nurses = await db.hp_users.count_documents({"tenant_id": tenant_id, "role": "nurse", "status": "active"})
    caregivers = await db.hp_users.count_documents({"tenant_id": tenant_id, "role": "caregiver", "status": "active"})
    
    return {
        "total": total,
        "active": active,
        "inactive": total - active,
        "by_role": {
            "doctors": doctors,
            "nurses": nurses,
            "caregivers": caregivers,
            "other": active - doctors - nurses - caregivers
        }
    }
