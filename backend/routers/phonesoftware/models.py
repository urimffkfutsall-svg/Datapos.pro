"""Pydantic models for PhoneSoftware - Mobile Repair & Shop Management System"""
from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any
from datetime import datetime, timezone
from enum import Enum
import uuid


# ============ ENUMS ============
class PSUserRole(str, Enum):
    SUPER_ADMIN = "super_admin"
    ADMIN = "admin"
    MANAGER = "manager"
    TECHNICIAN = "technician"
    STAFF = "staff"
    WORKER = "worker"  # Limited access - only repairs


class PSTenantStatus(str, Enum):
    ACTIVE = "active"
    SUSPENDED = "suspended"
    TRIAL = "trial"


class RepairStatus(str, Enum):
    RECEIVED = "received"              # Pranuar në servis
    IN_PROGRESS = "in_progress"        # Në proces
    COMPLETED = "completed"            # I rregulluar
    CANNOT_REPAIR = "cannot_repair"    # Nuk rregullohet
    DELIVERED = "delivered"            # Dorëzuar


class DeviceType(str, Enum):
    PHONE = "phone"
    TABLET = "tablet"
    LAPTOP = "laptop"
    SMARTWATCH = "smartwatch"
    OTHER = "other"


class PhoneCondition(str, Enum):
    NEW = "new"
    LIKE_NEW = "like_new"
    GOOD = "good"
    FAIR = "fair"
    POOR = "poor"


class InventoryCategory(str, Enum):
    PHONE_NEW = "phone_new"
    PHONE_USED = "phone_used"
    ACCESSORY = "accessory"
    SPARE_PART = "spare_part"


# ============ TENANT MODELS ============
class PSTenantCreate(BaseModel):
    name: str
    company_name: str
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


class PSTenantUpdate(BaseModel):
    company_name: Optional[str] = None
    email: Optional[str] = None
    phone: Optional[str] = None
    address: Optional[str] = None
    city: Optional[str] = None
    logo_url: Optional[str] = None
    primary_color: Optional[str] = None
    secondary_color: Optional[str] = None
    status: Optional[PSTenantStatus] = None
    subscription_expires: Optional[str] = None
    nui: Optional[str] = None
    nf: Optional[str] = None


class PSTenantResponse(BaseModel):
    id: str
    name: str
    company_name: str
    email: str
    phone: Optional[str] = None
    address: Optional[str] = None
    city: Optional[str] = None
    logo_url: Optional[str] = None
    primary_color: str
    secondary_color: str
    status: PSTenantStatus
    subscription_expires: Optional[str] = None
    created_at: str
    users_count: Optional[int] = 0
    repairs_count: Optional[int] = 0
    nui: Optional[str] = None
    nf: Optional[str] = None


# ============ USER MODELS ============
class PSUserCreate(BaseModel):
    username: str
    password: str
    full_name: str
    role: PSUserRole = PSUserRole.STAFF
    phone: Optional[str] = None
    email: Optional[str] = None
    specialization: Optional[str] = None  # For technicians


class PSUserUpdate(BaseModel):
    full_name: Optional[str] = None
    role: Optional[PSUserRole] = None
    phone: Optional[str] = None
    email: Optional[str] = None
    specialization: Optional[str] = None
    is_active: Optional[bool] = None
    password: Optional[str] = None


class PSUserResponse(BaseModel):
    id: str
    username: str
    full_name: str
    role: PSUserRole
    phone: Optional[str] = None
    email: Optional[str] = None
    specialization: Optional[str] = None
    is_active: bool
    tenant_id: Optional[str] = None
    created_at: str
    repairs_completed: Optional[int] = 0


# ============ CUSTOMER MODELS ============
class CustomerCreate(BaseModel):
    full_name: str
    phone: str
    email: Optional[str] = None
    address: Optional[str] = None
    notes: Optional[str] = None


class CustomerUpdate(BaseModel):
    full_name: Optional[str] = None
    phone: Optional[str] = None
    email: Optional[str] = None
    address: Optional[str] = None
    notes: Optional[str] = None


class CustomerResponse(BaseModel):
    id: str
    full_name: str
    phone: str
    email: Optional[str] = None
    address: Optional[str] = None
    notes: Optional[str] = None
    tenant_id: str
    created_at: str
    total_repairs: Optional[int] = 0
    total_purchases: Optional[int] = 0


# ============ REPAIR MODELS ============
class RepairPartUsed(BaseModel):
    part_id: str
    part_name: str
    quantity: int = 1
    unit_cost: float
    total_cost: float


class RepairCreate(BaseModel):
    # Customer - optional, can use customer_id OR manual customer_name
    customer_id: Optional[str] = None
    customer_name: Optional[str] = None  # Manual entry if no customer_id
    customer_phone: Optional[str] = None  # Manual entry
    
    # Device info - all optional except basic description
    device_type: Optional[str] = "phone"
    brand: Optional[str] = None
    model: Optional[str] = None
    imei: Optional[str] = None
    serial_number: Optional[str] = None
    color: Optional[str] = None
    
    # Problem - required
    problem_description: str
    
    # Optional fields
    customer_notes: Optional[str] = None
    estimated_cost: Optional[float] = None
    estimated_completion: Optional[str] = None
    warranty_months: int = 1
    accessories_received: Optional[List[str]] = []


class RepairUpdate(BaseModel):
    status: Optional[RepairStatus] = None
    technician_id: Optional[str] = None
    diagnosis: Optional[str] = None
    repair_notes: Optional[str] = None
    parts_used: Optional[List[RepairPartUsed]] = None
    labor_cost: Optional[float] = None
    total_cost: Optional[float] = None
    completed_at: Optional[str] = None
    delivered_at: Optional[str] = None
    warranty_months: Optional[int] = None


class RepairResponse(BaseModel):
    id: str
    ticket_number: str
    customer_id: Optional[str] = None
    customer_name: Optional[str] = None
    customer_phone: Optional[str] = None
    device_type: Optional[str] = "phone"
    brand: Optional[str] = None
    model: Optional[str] = None
    imei: Optional[str] = None
    serial_number: Optional[str] = None
    color: Optional[str] = None
    problem_description: str
    customer_notes: Optional[str] = None
    status: RepairStatus
    technician_id: Optional[str] = None
    technician_name: Optional[str] = None
    diagnosis: Optional[str] = None
    repair_notes: Optional[str] = None
    parts_used: List[RepairPartUsed] = []
    labor_cost: float = 0
    parts_cost: float = 0
    total_cost: float = 0
    estimated_cost: Optional[float] = None
    estimated_completion: Optional[str] = None
    warranty_months: int = 1
    warranty_expires: Optional[str] = None
    accessories_received: List[str] = []
    tenant_id: str
    created_by: str
    created_at: str
    updated_at: str
    completed_at: Optional[str] = None
    delivered_at: Optional[str] = None


# ============ INVENTORY MODELS ============
class InventoryItemCreate(BaseModel):
    name: str
    category: InventoryCategory
    brand: Optional[str] = None
    model: Optional[str] = None
    sku: Optional[str] = None
    barcode: Optional[str] = None
    imei: Optional[str] = None  # For phones
    serial_number: Optional[str] = None
    condition: Optional[PhoneCondition] = None  # For used phones
    purchase_price: float
    sale_price: float
    quantity: int = 1
    min_stock: int = 5
    location: Optional[str] = None
    supplier: Optional[str] = None
    warranty_months: Optional[int] = None
    specifications: Optional[Dict[str, Any]] = None
    notes: Optional[str] = None


class InventoryItemUpdate(BaseModel):
    name: Optional[str] = None
    category: Optional[InventoryCategory] = None
    brand: Optional[str] = None
    model: Optional[str] = None
    sku: Optional[str] = None
    barcode: Optional[str] = None
    condition: Optional[PhoneCondition] = None
    purchase_price: Optional[float] = None
    sale_price: Optional[float] = None
    quantity: Optional[int] = None
    min_stock: Optional[int] = None
    location: Optional[str] = None
    supplier: Optional[str] = None
    warranty_months: Optional[int] = None
    specifications: Optional[Dict[str, Any]] = None
    notes: Optional[str] = None
    is_active: Optional[bool] = None


class InventoryItemResponse(BaseModel):
    id: str
    name: str
    category: InventoryCategory
    brand: Optional[str] = None
    model: Optional[str] = None
    sku: Optional[str] = None
    barcode: Optional[str] = None
    imei: Optional[str] = None
    serial_number: Optional[str] = None
    condition: Optional[PhoneCondition] = None
    purchase_price: float
    sale_price: float
    quantity: int
    min_stock: int
    is_low_stock: bool = False
    location: Optional[str] = None
    supplier: Optional[str] = None
    warranty_months: Optional[int] = None
    specifications: Optional[Dict[str, Any]] = None
    notes: Optional[str] = None
    is_active: bool = True
    tenant_id: str
    created_at: str
    updated_at: str


# ============ STOCK MOVEMENT ============
class StockMovementType(str, Enum):
    IN = "in"
    OUT = "out"
    ADJUSTMENT = "adjustment"
    REPAIR_USE = "repair_use"
    SALE = "sale"
    RETURN = "return"


class StockMovementCreate(BaseModel):
    item_id: str
    quantity: int
    movement_type: StockMovementType
    reference_id: Optional[str] = None  # Repair ticket or sale ID
    reason: Optional[str] = None
    unit_cost: Optional[float] = None


class StockMovementResponse(BaseModel):
    id: str
    item_id: str
    item_name: str
    quantity: int
    movement_type: StockMovementType
    reference_id: Optional[str] = None
    reason: Optional[str] = None
    unit_cost: Optional[float] = None
    user_id: str
    user_name: str
    tenant_id: str
    created_at: str


# ============ SALE MODELS (Simple - No POS) ============
class SaleItemCreate(BaseModel):
    item_id: str
    quantity: int = 1
    unit_price: float
    discount: float = 0


class SaleCreate(BaseModel):
    customer_id: Optional[str] = None
    items: List[SaleItemCreate]
    payment_method: str = "cash"  # cash, card, transfer
    payment_reference: Optional[str] = None
    notes: Optional[str] = None


class SaleItemResponse(BaseModel):
    item_id: str
    item_name: str
    category: str
    quantity: int
    unit_price: float
    discount: float
    subtotal: float


class SaleResponse(BaseModel):
    id: str
    sale_number: str
    customer_id: Optional[str] = None
    customer_name: Optional[str] = None
    items: List[SaleItemResponse]
    subtotal: float
    total_discount: float
    grand_total: float
    payment_method: str
    payment_reference: Optional[str] = None
    notes: Optional[str] = None
    tenant_id: str
    created_by: str
    created_by_name: str
    created_at: str


# ============ NOTIFICATION MODELS ============
class NotificationType(str, Enum):
    REPAIR_RECEIVED = "repair_received"
    REPAIR_IN_PROGRESS = "repair_in_progress"
    REPAIR_COMPLETED = "repair_completed"
    REPAIR_READY = "repair_ready"


class NotificationCreate(BaseModel):
    customer_id: str
    repair_id: str
    notification_type: NotificationType
    channel: str = "email"  # email, sms


# ============ AUTH MODELS ============
class PSLoginRequest(BaseModel):
    username: str
    password: str


class PSTokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user: PSUserResponse
