"""Pydantic models for BookPRO - Hair Salon Management System"""
from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any
from datetime import datetime, timezone, time
from enum import Enum
import uuid


# ============ ENUMS ============
class BPUserRole(str, Enum):
    SUPER_ADMIN = "super_admin"
    ADMIN = "admin"  # Salon owner - full access
    STYLIST = "stylist"  # Hair stylist - limited access
    RECEPTIONIST = "receptionist"  # Same access as stylist


class BPTenantStatus(str, Enum):
    ACTIVE = "active"
    SUSPENDED = "suspended"
    TRIAL = "trial"


class AppointmentStatus(str, Enum):
    PENDING = "pending"           # Në pritje
    CONFIRMED = "confirmed"       # Konfirmuar
    IN_PROGRESS = "in_progress"   # Në proces
    COMPLETED = "completed"       # Përfunduar
    CANCELLED = "cancelled"       # Anuluar
    NO_SHOW = "no_show"          # Nuk u paraqit


class ServiceCategory(str, Enum):
    HAIRCUT = "haircut"           # Prerje flokësh
    COLORING = "coloring"         # Ngjyrosje
    STYLING = "styling"           # Stilim
    TREATMENT = "treatment"       # Trajtim
    EXTENSIONS = "extensions"     # Zgjatim flokësh
    BRIDAL = "bridal"            # Nuse
    MAKEUP = "makeup"            # Grim
    NAILS = "nails"              # Thonj
    OTHER = "other"


class PaymentMethod(str, Enum):
    CASH = "cash"
    CARD = "card"
    TRANSFER = "transfer"
    PENDING = "pending"  # Not paid yet


class DayOfWeek(str, Enum):
    MONDAY = "monday"
    TUESDAY = "tuesday"
    WEDNESDAY = "wednesday"
    THURSDAY = "thursday"
    FRIDAY = "friday"
    SATURDAY = "saturday"
    SUNDAY = "sunday"


# ============ TENANT MODELS ============
class BPTenantCreate(BaseModel):
    name: str  # Slug/identifier
    salon_name: str
    email: str
    phone: Optional[str] = None
    address: Optional[str] = None
    city: Optional[str] = None
    logo_url: Optional[str] = None
    primary_color: str = "#00a79d"
    secondary_color: str = "#f3f4f6"
    admin_username: str
    admin_password: str
    admin_full_name: str
    subscription_months: int = 1


class BPTenantUpdate(BaseModel):
    salon_name: Optional[str] = None
    email: Optional[str] = None
    phone: Optional[str] = None
    address: Optional[str] = None
    city: Optional[str] = None
    logo_url: Optional[str] = None
    primary_color: Optional[str] = None
    secondary_color: Optional[str] = None
    status: Optional[BPTenantStatus] = None
    subscription_expires: Optional[str] = None
    nui: Optional[str] = None
    nf: Optional[str] = None
    # Business hours
    opening_time: Optional[str] = None  # "09:00"
    closing_time: Optional[str] = None  # "19:00"
    working_days: Optional[List[DayOfWeek]] = None


class BPTenantResponse(BaseModel):
    id: str
    name: str
    salon_name: str
    email: str
    phone: Optional[str] = None
    address: Optional[str] = None
    city: Optional[str] = None
    logo_url: Optional[str] = None
    primary_color: str
    secondary_color: str
    status: BPTenantStatus
    subscription_expires: Optional[str] = None
    created_at: str
    users_count: Optional[int] = 0
    appointments_count: Optional[int] = 0
    clients_count: Optional[int] = 0
    nui: Optional[str] = None
    nf: Optional[str] = None
    opening_time: str = "09:00"
    closing_time: str = "19:00"
    working_days: List[str] = ["monday", "tuesday", "wednesday", "thursday", "friday", "saturday"]


# ============ USER/STAFF MODELS ============
class BPUserCreate(BaseModel):
    username: str
    password: str
    full_name: str
    role: BPUserRole = BPUserRole.STYLIST
    phone: Optional[str] = None
    email: Optional[str] = None
    specializations: Optional[List[str]] = []  # ["coloring", "bridal", "extensions"]
    bio: Optional[str] = None
    photo_url: Optional[str] = None
    commission_percent: float = 0  # Commission on services


class BPUserUpdate(BaseModel):
    full_name: Optional[str] = None
    role: Optional[BPUserRole] = None
    phone: Optional[str] = None
    email: Optional[str] = None
    specializations: Optional[List[str]] = None
    bio: Optional[str] = None
    photo_url: Optional[str] = None
    commission_percent: Optional[float] = None
    is_active: Optional[bool] = None
    password: Optional[str] = None


class BPUserResponse(BaseModel):
    id: str
    username: str
    full_name: str
    role: BPUserRole
    phone: Optional[str] = None
    email: Optional[str] = None
    specializations: List[str] = []
    bio: Optional[str] = None
    photo_url: Optional[str] = None
    commission_percent: float = 0
    is_active: bool = True
    tenant_id: Optional[str] = None
    created_at: str
    appointments_count: Optional[int] = 0
    total_revenue: Optional[float] = 0


# ============ WORKING HOURS MODELS ============
class WorkingHoursCreate(BaseModel):
    user_id: str
    day_of_week: DayOfWeek
    start_time: str  # "09:00"
    end_time: str    # "18:00"
    is_working: bool = True


class WorkingHoursResponse(BaseModel):
    id: str
    user_id: str
    day_of_week: DayOfWeek
    start_time: str
    end_time: str
    is_working: bool
    tenant_id: str


# ============ CLIENT MODELS ============
class BPClientCreate(BaseModel):
    full_name: str
    phone: str
    email: Optional[str] = None
    gender: str = "female"  # female, male, other
    birthdate: Optional[str] = None
    address: Optional[str] = None
    notes: Optional[str] = None
    preferences: Optional[str] = None  # Hair type, preferred products, allergies
    referral_source: Optional[str] = None  # How they found the salon


class BPClientUpdate(BaseModel):
    full_name: Optional[str] = None
    phone: Optional[str] = None
    email: Optional[str] = None
    gender: Optional[str] = None
    birthdate: Optional[str] = None
    address: Optional[str] = None
    notes: Optional[str] = None
    preferences: Optional[str] = None
    referral_source: Optional[str] = None


class BPClientResponse(BaseModel):
    id: str
    full_name: str
    phone: str
    email: Optional[str] = None
    gender: str = "female"
    birthdate: Optional[str] = None
    address: Optional[str] = None
    notes: Optional[str] = None
    preferences: Optional[str] = None
    referral_source: Optional[str] = None
    tenant_id: str
    created_at: str
    last_visit: Optional[str] = None
    total_visits: int = 0
    total_spent: float = 0
    loyalty_points: int = 0


# ============ SERVICE MODELS ============
class BPServiceCreate(BaseModel):
    name: str
    category: ServiceCategory
    description: Optional[str] = None
    duration_minutes: int = 30  # Default 30 minutes
    price: float
    deposit_required: float = 0  # Deposit for booking
    assigned_staff: Optional[List[str]] = []  # List of user IDs who can perform this service
    is_popular: bool = False


class BPServiceUpdate(BaseModel):
    name: Optional[str] = None
    category: Optional[ServiceCategory] = None
    description: Optional[str] = None
    duration_minutes: Optional[int] = None
    price: Optional[float] = None
    deposit_required: Optional[float] = None
    assigned_staff: Optional[List[str]] = None
    is_popular: Optional[bool] = None
    is_active: Optional[bool] = None


class BPServiceResponse(BaseModel):
    id: str
    name: str
    category: ServiceCategory
    description: Optional[str] = None
    duration_minutes: int
    price: float
    deposit_required: float = 0
    assigned_staff: List[str] = []
    is_popular: bool = False
    is_active: bool = True
    tenant_id: str
    created_at: str
    bookings_count: Optional[int] = 0


# ============ APPOINTMENT MODELS ============
class AppointmentServiceItem(BaseModel):
    service_id: str
    service_name: Optional[str] = None
    price: float
    duration_minutes: int


class BPAppointmentCreate(BaseModel):
    client_id: Optional[str] = None
    # For walk-ins without client record
    client_name: Optional[str] = None
    client_phone: Optional[str] = None
    
    stylist_id: str
    services: List[AppointmentServiceItem]
    appointment_date: str  # "2024-01-15"
    start_time: str        # "10:00"
    notes: Optional[str] = None
    source: str = "in_salon"  # in_salon, online, phone


class BPAppointmentUpdate(BaseModel):
    status: Optional[AppointmentStatus] = None
    stylist_id: Optional[str] = None
    services: Optional[List[AppointmentServiceItem]] = None
    appointment_date: Optional[str] = None
    start_time: Optional[str] = None
    notes: Optional[str] = None
    payment_method: Optional[PaymentMethod] = None
    payment_amount: Optional[float] = None
    tip_amount: Optional[float] = None


class BPAppointmentResponse(BaseModel):
    id: str
    appointment_number: str
    client_id: Optional[str] = None
    client_name: Optional[str] = None
    client_phone: Optional[str] = None
    stylist_id: str
    stylist_name: Optional[str] = None
    services: List[AppointmentServiceItem]
    appointment_date: str
    start_time: str
    end_time: str  # Calculated
    total_duration: int  # Total minutes
    total_price: float
    status: AppointmentStatus
    notes: Optional[str] = None
    source: str
    payment_method: Optional[PaymentMethod] = None
    payment_amount: float = 0
    tip_amount: float = 0
    tenant_id: str
    created_by: str
    created_at: str
    updated_at: str
    completed_at: Optional[str] = None


# ============ PRODUCT/INVENTORY MODELS ============
class BPProductCategory(str, Enum):
    SHAMPOO = "shampoo"
    CONDITIONER = "conditioner"
    HAIR_COLOR = "hair_color"
    STYLING = "styling"
    TREATMENT = "treatment"
    TOOLS = "tools"
    OTHER = "other"


class BPProductCreate(BaseModel):
    name: str
    category: BPProductCategory
    brand: Optional[str] = None
    sku: Optional[str] = None
    barcode: Optional[str] = None
    purchase_price: float
    sale_price: float
    quantity: int = 0
    min_stock: int = 5
    description: Optional[str] = None


class BPProductUpdate(BaseModel):
    name: Optional[str] = None
    category: Optional[BPProductCategory] = None
    brand: Optional[str] = None
    sku: Optional[str] = None
    purchase_price: Optional[float] = None
    sale_price: Optional[float] = None
    quantity: Optional[int] = None
    min_stock: Optional[int] = None
    description: Optional[str] = None
    is_active: Optional[bool] = None


class BPProductResponse(BaseModel):
    id: str
    name: str
    category: BPProductCategory
    brand: Optional[str] = None
    sku: Optional[str] = None
    barcode: Optional[str] = None
    purchase_price: float
    sale_price: float
    quantity: int
    min_stock: int
    is_low_stock: bool = False
    description: Optional[str] = None
    is_active: bool = True
    tenant_id: str
    created_at: str


# ============ AUTH MODELS ============
class BPLoginRequest(BaseModel):
    username: str
    password: str


class BPTokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user: BPUserResponse


# ============ DASHBOARD/STATS MODELS ============
class BPDashboardStats(BaseModel):
    today_appointments: int = 0
    today_revenue: float = 0
    week_appointments: int = 0
    week_revenue: float = 0
    month_appointments: int = 0
    month_revenue: float = 0
    total_clients: int = 0
    new_clients_this_month: int = 0
    pending_appointments: int = 0
    completed_today: int = 0
