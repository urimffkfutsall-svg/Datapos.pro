"""
HealthPRO - Pydantic Models for Healthcare Institute Management
"""
from pydantic import BaseModel, ConfigDict
from typing import Optional, List
from datetime import datetime
from enum import Enum


# ============ ENUMS ============
class ResidentStatus(str, Enum):
    ACTIVE = "active"
    INACTIVE = "inactive"
    DECEASED = "deceased"
    TRANSFERRED = "transferred"

class Gender(str, Enum):
    MALE = "male"
    FEMALE = "female"
    OTHER = "other"

class CheckupType(str, Enum):
    GENERAL = "general"  # QKMF
    PULMONOLOGY = "pulmonology"
    CARDIOLOGY = "cardiology"
    GYNECOLOGY = "gynecology"
    PSYCHIATRY = "psychiatry"
    OTHER = "other"

class CheckupStatus(str, Enum):
    PLANNED = "planned"
    COMPLETED = "completed"
    CANCELLED = "cancelled"

class TherapyType(str, Enum):
    MEDICATION = "medication"
    PHYSICAL = "physical"
    SUPPORTIVE = "supportive"
    PSYCHOLOGICAL = "psychological"
    OTHER = "other"

class VisitType(str, Enum):
    HOME = "home"
    COMMUNITY = "community"

class EmployeeStatus(str, Enum):
    ACTIVE = "active"
    INACTIVE = "inactive"
    ON_LEAVE = "on_leave"

class EmployeeRole(str, Enum):
    ADMIN = "admin"
    DOCTOR = "doctor"
    NURSE = "nurse"
    CAREGIVER = "caregiver"
    THERAPIST = "therapist"
    SUPPORT = "support"
    VISITOR = "visitor"  # Read-only access


# ============ RESIDENT MODELS ============
class ResidentBase(BaseModel):
    first_name: str
    last_name: str
    date_of_birth: Optional[str] = None
    gender: Optional[Gender] = None
    personal_id: Optional[str] = None
    address: Optional[str] = None
    phone: Optional[str] = None
    guardian_name: Optional[str] = None
    guardian_phone: Optional[str] = None
    guardian_relation: Optional[str] = None
    health_status: Optional[str] = None
    diagnoses: Optional[List[str]] = []
    medical_history: Optional[str] = None
    allergies: Optional[str] = None
    blood_type: Optional[str] = None
    emergency_contact: Optional[str] = None
    admission_date: Optional[str] = None
    room_number: Optional[str] = None
    notes: Optional[str] = None

class ResidentCreate(ResidentBase):
    pass

class ResidentUpdate(BaseModel):
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    date_of_birth: Optional[str] = None
    gender: Optional[Gender] = None
    personal_id: Optional[str] = None
    address: Optional[str] = None
    phone: Optional[str] = None
    guardian_name: Optional[str] = None
    guardian_phone: Optional[str] = None
    guardian_relation: Optional[str] = None
    health_status: Optional[str] = None
    diagnoses: Optional[List[str]] = None
    medical_history: Optional[str] = None
    allergies: Optional[str] = None
    blood_type: Optional[str] = None
    emergency_contact: Optional[str] = None
    room_number: Optional[str] = None
    notes: Optional[str] = None
    status: Optional[ResidentStatus] = None

class ResidentResponse(ResidentBase):
    id: str
    status: ResidentStatus = ResidentStatus.ACTIVE
    created_at: str
    updated_at: Optional[str] = None
    tenant_id: str


# ============ MEDICAL CHECKUP MODELS ============
class CheckupBase(BaseModel):
    resident_id: str
    checkup_type: CheckupType
    scheduled_date: str
    scheduled_time: Optional[str] = None
    institution: Optional[str] = None
    doctor_name: Optional[str] = None
    notes: Optional[str] = None
    results: Optional[str] = None
    recommendations: Optional[str] = None
    is_systematic: bool = False  # Auto-generated every 6 months

class CheckupCreate(CheckupBase):
    pass

class CheckupUpdate(BaseModel):
    checkup_type: Optional[CheckupType] = None
    scheduled_date: Optional[str] = None
    scheduled_time: Optional[str] = None
    institution: Optional[str] = None
    doctor_name: Optional[str] = None
    notes: Optional[str] = None
    results: Optional[str] = None
    recommendations: Optional[str] = None
    status: Optional[CheckupStatus] = None

class CheckupResponse(CheckupBase):
    id: str
    status: CheckupStatus = CheckupStatus.PLANNED
    created_at: str
    completed_at: Optional[str] = None
    tenant_id: str
    resident_name: Optional[str] = None


# ============ THERAPY MODELS ============
class TherapyBase(BaseModel):
    resident_id: str
    therapy_type: TherapyType
    name: str  # Medication name or therapy name
    dosage: Optional[str] = None
    frequency: Optional[str] = None  # e.g., "3 herë në ditë"
    duration: Optional[str] = None  # e.g., "2 javë"
    start_date: str
    end_date: Optional[str] = None
    administration_time: Optional[List[str]] = []  # e.g., ["08:00", "14:00", "20:00"]
    prescribed_by: Optional[str] = None
    notes: Optional[str] = None

class TherapyCreate(TherapyBase):
    pass

class TherapyUpdate(BaseModel):
    therapy_type: Optional[TherapyType] = None
    name: Optional[str] = None
    dosage: Optional[str] = None
    frequency: Optional[str] = None
    duration: Optional[str] = None
    start_date: Optional[str] = None
    end_date: Optional[str] = None
    administration_time: Optional[List[str]] = None
    prescribed_by: Optional[str] = None
    notes: Optional[str] = None
    is_active: Optional[bool] = None

class TherapyResponse(TherapyBase):
    id: str
    is_active: bool = True
    created_at: str
    tenant_id: str
    resident_name: Optional[str] = None


# ============ VISIT MODELS ============
class VisitBase(BaseModel):
    resident_id: str
    visit_type: VisitType
    visit_date: str
    visit_time: Optional[str] = None
    reason: str
    staff_ids: Optional[List[str]] = []
    result: Optional[str] = None
    notes: Optional[str] = None
    address: Optional[str] = None  # For home visits

class VisitCreate(VisitBase):
    pass

class VisitUpdate(BaseModel):
    visit_type: Optional[VisitType] = None
    visit_date: Optional[str] = None
    visit_time: Optional[str] = None
    reason: Optional[str] = None
    staff_ids: Optional[List[str]] = None
    result: Optional[str] = None
    notes: Optional[str] = None
    address: Optional[str] = None
    is_completed: Optional[bool] = None

class VisitResponse(VisitBase):
    id: str
    is_completed: bool = False
    created_at: str
    completed_at: Optional[str] = None
    tenant_id: str
    resident_name: Optional[str] = None
    staff_names: Optional[List[str]] = []


# ============ EMPLOYEE MODELS ============
class EmployeeBase(BaseModel):
    first_name: str
    last_name: str
    email: Optional[str] = None
    phone: Optional[str] = None
    role: EmployeeRole
    department: Optional[str] = None
    position: Optional[str] = None
    hire_date: Optional[str] = None
    contract_type: Optional[str] = None  # Full-time, Part-time, Contract
    work_schedule: Optional[str] = None
    salary: Optional[float] = None
    bank_account: Optional[str] = None
    personal_id: Optional[str] = None
    address: Optional[str] = None
    emergency_contact: Optional[str] = None
    notes: Optional[str] = None

class EmployeeCreate(EmployeeBase):
    username: str
    password: str

class EmployeeUpdate(BaseModel):
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    email: Optional[str] = None
    phone: Optional[str] = None
    role: Optional[EmployeeRole] = None
    department: Optional[str] = None
    position: Optional[str] = None
    contract_type: Optional[str] = None
    work_schedule: Optional[str] = None
    salary: Optional[float] = None
    bank_account: Optional[str] = None
    address: Optional[str] = None
    emergency_contact: Optional[str] = None
    notes: Optional[str] = None
    status: Optional[EmployeeStatus] = None

class EmployeeResponse(EmployeeBase):
    id: str
    username: str
    status: EmployeeStatus = EmployeeStatus.ACTIVE
    created_at: str
    tenant_id: str


# ============ ATTENDANCE/TIME TRACKING ============
class AttendanceRecord(BaseModel):
    employee_id: str
    date: str
    check_in: Optional[str] = None
    check_out: Optional[str] = None
    hours_worked: Optional[float] = None
    overtime: Optional[float] = None
    leave_type: Optional[str] = None  # sick, vacation, personal
    notes: Optional[str] = None

class AttendanceCreate(AttendanceRecord):
    pass

class AttendanceResponse(AttendanceRecord):
    id: str
    tenant_id: str
    employee_name: Optional[str] = None


# ============ OVERTIME TRACKING MODELS ============
class OvertimeType(str, Enum):
    NORMAL = "normal"          # Orë shtesë normale (koeficient 1.25)
    NIGHT = "night"            # Orë nate (koeficient 1.5)
    WEEKEND = "weekend"        # Fundjavë (koeficient 1.5)
    HOLIDAY = "holiday"        # Festë zyrtare (koeficient 2.0)

class OvertimeEntryBase(BaseModel):
    employee_id: str
    date: str
    overtime_type: OvertimeType
    hours: float
    notes: Optional[str] = None
    custom_coefficient: Optional[float] = None  # Admin mund të vendosë koeficient manual
    
class OvertimeEntryCreate(OvertimeEntryBase):
    pass

class OvertimeEntryUpdate(BaseModel):
    overtime_type: Optional[OvertimeType] = None
    hours: Optional[float] = None
    notes: Optional[str] = None
    custom_coefficient: Optional[float] = None

class OvertimeEntryResponse(OvertimeEntryBase):
    id: str
    tenant_id: str
    employee_name: Optional[str] = None
    calculated_pay: Optional[float] = None  # Automatikisht llogaritur
    used_coefficient: Optional[float] = None  # Koeficienti i përdorur
    created_at: str
    created_by: Optional[str] = None


# ============ MONTHLY OVERTIME SUMMARY ============
class MonthlyOvertimeSummary(BaseModel):
    employee_id: str
    employee_name: str
    month: int
    year: int
    base_salary: float
    normal_hours: float = 0
    night_hours: float = 0
    weekend_hours: float = 0
    holiday_hours: float = 0
    total_overtime_hours: float = 0
    total_overtime_pay: float = 0
    
    
# ============ OVERTIME COEFFICIENTS (Settings) ============
class OvertimeCoefficients(BaseModel):
    normal: float = 1.25      # Orë shtesë normale
    night: float = 1.5        # Orë nate (22:00 - 06:00)
    weekend: float = 1.5      # Fundjavë (Shtunë/Diel)
    holiday: float = 2.0      # Festat zyrtare


# ============ PAYROLL MODELS ============
class PayrollRecord(BaseModel):
    employee_id: str
    month: int
    year: int
    base_salary: float
    overtime_pay: Optional[float] = 0
    bonuses: Optional[float] = 0
    deductions: Optional[float] = 0
    net_salary: Optional[float] = None
    payment_date: Optional[str] = None
    payment_status: str = "pending"  # pending, paid
    notes: Optional[str] = None

class PayrollCreate(PayrollRecord):
    pass

class PayrollResponse(PayrollRecord):
    id: str
    tenant_id: str
    employee_name: Optional[str] = None


# ============ SCHEDULE/DAILY ROUTINE ============
class DailyScheduleItem(BaseModel):
    resident_id: str
    time: str
    activity: str
    notes: Optional[str] = None
    assigned_staff: Optional[List[str]] = []

class DailyScheduleCreate(DailyScheduleItem):
    pass


# ============ NOTIFICATIONS/ALERTS ============
class NotificationBase(BaseModel):
    title: str
    message: str
    type: str  # checkup_reminder, therapy_due, visit_scheduled
    related_id: Optional[str] = None  # ID of related entity
    is_read: bool = False

class NotificationResponse(NotificationBase):
    id: str
    created_at: str
    tenant_id: str


# ============ INSTITUTE/TENANT SETTINGS ============
class HealthProTenantCreate(BaseModel):
    name: str
    institute_type: str  # nursing_home, community_center, rehabilitation
    address: Optional[str] = None
    phone: Optional[str] = None
    email: Optional[str] = None
    admin_name: str
    admin_username: str
    admin_password: str

class HealthProTenantResponse(BaseModel):
    id: str
    name: str
    slug: str
    institute_type: str
    address: Optional[str] = None
    phone: Optional[str] = None
    email: Optional[str] = None
    is_active: bool
    created_at: str


# ============ VISITOR USER MODEL ============
class VisitorUserCreate(BaseModel):
    username: str
    password: str
    full_name: str
    email: Optional[str] = None
    notes: Optional[str] = None  # Përshkrim i rolit të vizitorit
    
class VisitorUserResponse(BaseModel):
    id: str
    tenant_id: str
    username: str
    full_name: str
    email: Optional[str] = None
    notes: Optional[str] = None
    role: str = "visitor"
    is_active: bool
    created_at: str
