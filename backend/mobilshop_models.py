"""Pydantic models for the Mobilshop Management System"""
from pydantic import BaseModel, Field, ConfigDict
from typing import List, Optional, Dict, Any
from datetime import datetime, timezone
from enum import Enum
import uuid


# ============ ENUMS ============
class MobilshopUserRole(str, Enum):
    ADMIN = "admin"
    MANAGER = "manager"
    SALESPERSON = "salesperson"
    TECHNICIAN = "technician"


class ProductType(str, Enum):
    PHONE = "phone"
    ACCESSORY = "accessory"
    PART = "part"


class RepairStatus(str, Enum):
    RECEIVED = "received"
    DIAGNOSING = "diagnosing"
    WAITING_PARTS = "waiting_parts"
    REPAIRING = "repairing"
    COMPLETED = "completed"
    DELIVERED = "delivered"
    CANCELLED = "cancelled"


class PaymentMethod(str, Enum):
    CASH = "cash"
    CARD = "card"
    SPLIT = "split"
    CREDIT = "credit"


class PaymentStatus(str, Enum):
    PENDING = "pending"
    PARTIAL = "partial"
    PAID = "paid"
    REFUNDED = "refunded"


# ============ SUPPLIER MODELS ============
class SupplierCreate(BaseModel):
    name: str
    contact_person: Optional[str] = None
    phone: Optional[str] = None
    email: Optional[str] = None
    address: Optional[str] = None
    notes: Optional[str] = None


class SupplierUpdate(BaseModel):
    name: Optional[str] = None
    contact_person: Optional[str] = None
    phone: Optional[str] = None
    email: Optional[str] = None
    address: Optional[str] = None
    notes: Optional[str] = None
    is_active: Optional[bool] = None


class SupplierResponse(BaseModel):
    id: str
    name: str
    contact_person: Optional[str] = None
    phone: Optional[str] = None
    email: Optional[str] = None
    address: Optional[str] = None
    notes: Optional[str] = None
    is_active: bool
    created_at: str


# ============ PRODUCT MODELS (Phones & Accessories) ============
class MobilshopProductCreate(BaseModel):
    name: str
    product_type: ProductType
    brand: Optional[str] = None
    model: Optional[str] = None
    sku: Optional[str] = None
    barcode: Optional[str] = None
    imei: Optional[str] = None  # For phones
    serial_number: Optional[str] = None
    purchase_price: float = 0
    sale_price: float = 0
    category: Optional[str] = None
    color: Optional[str] = None
    storage: Optional[str] = None  # For phones (64GB, 128GB, etc.)
    condition: Optional[str] = "new"  # new, used, refurbished
    warranty_months: Optional[int] = 0
    supplier_id: Optional[str] = None
    location: Optional[str] = None  # Store location
    quantity: int = 1  # For accessories
    min_stock: int = 1
    description: Optional[str] = None
    specifications: Optional[Dict[str, Any]] = None


class MobilshopProductUpdate(BaseModel):
    name: Optional[str] = None
    product_type: Optional[ProductType] = None
    brand: Optional[str] = None
    model: Optional[str] = None
    sku: Optional[str] = None
    barcode: Optional[str] = None
    imei: Optional[str] = None
    serial_number: Optional[str] = None
    purchase_price: Optional[float] = None
    sale_price: Optional[float] = None
    category: Optional[str] = None
    color: Optional[str] = None
    storage: Optional[str] = None
    condition: Optional[str] = None
    warranty_months: Optional[int] = None
    supplier_id: Optional[str] = None
    location: Optional[str] = None
    quantity: Optional[int] = None
    min_stock: Optional[int] = None
    description: Optional[str] = None
    specifications: Optional[Dict[str, Any]] = None
    is_active: Optional[bool] = None
    is_sold: Optional[bool] = None


class MobilshopProductResponse(BaseModel):
    id: str
    name: str
    product_type: ProductType
    brand: Optional[str] = None
    model: Optional[str] = None
    sku: Optional[str] = None
    barcode: Optional[str] = None
    imei: Optional[str] = None
    serial_number: Optional[str] = None
    purchase_price: float
    sale_price: float
    category: Optional[str] = None
    color: Optional[str] = None
    storage: Optional[str] = None
    condition: Optional[str] = None
    warranty_months: Optional[int] = None
    supplier_id: Optional[str] = None
    supplier_name: Optional[str] = None
    location: Optional[str] = None
    quantity: int
    min_stock: int
    description: Optional[str] = None
    specifications: Optional[Dict[str, Any]] = None
    is_active: bool
    is_sold: bool
    created_at: str
    updated_at: str


# ============ CUSTOMER MODELS ============
class CustomerCreate(BaseModel):
    full_name: str
    phone: str
    email: Optional[str] = None
    address: Optional[str] = None
    city: Optional[str] = None
    id_number: Optional[str] = None  # Personal ID
    notes: Optional[str] = None
    loyalty_points: int = 0


class CustomerUpdate(BaseModel):
    full_name: Optional[str] = None
    phone: Optional[str] = None
    email: Optional[str] = None
    address: Optional[str] = None
    city: Optional[str] = None
    id_number: Optional[str] = None
    notes: Optional[str] = None
    loyalty_points: Optional[int] = None
    is_active: Optional[bool] = None


class CustomerResponse(BaseModel):
    id: str
    full_name: str
    phone: str
    email: Optional[str] = None
    address: Optional[str] = None
    city: Optional[str] = None
    id_number: Optional[str] = None
    notes: Optional[str] = None
    loyalty_points: int
    total_purchases: float
    total_repairs: int
    is_active: bool
    created_at: str


# ============ REPAIR TICKET MODELS ============
class RepairTicketCreate(BaseModel):
    customer_id: str
    device_brand: str
    device_model: str
    device_imei: Optional[str] = None
    device_color: Optional[str] = None
    device_password: Optional[str] = None  # Device unlock code
    issue_description: str
    accessories_received: Optional[str] = None  # Charger, case, etc.
    estimated_cost: float = 0
    estimated_completion: Optional[str] = None
    technician_id: Optional[str] = None
    priority: str = "normal"  # low, normal, high, urgent
    notes: Optional[str] = None


class RepairTicketUpdate(BaseModel):
    status: Optional[RepairStatus] = None
    technician_id: Optional[str] = None
    diagnosis: Optional[str] = None
    parts_used: Optional[List[Dict[str, Any]]] = None
    labor_cost: Optional[float] = None
    parts_cost: Optional[float] = None
    total_cost: Optional[float] = None
    estimated_completion: Optional[str] = None
    actual_completion: Optional[str] = None
    priority: Optional[str] = None
    notes: Optional[str] = None
    payment_status: Optional[PaymentStatus] = None
    payment_method: Optional[PaymentMethod] = None
    amount_paid: Optional[float] = None


class RepairStatusUpdate(BaseModel):
    status: RepairStatus
    notes: Optional[str] = None


class RepairTicketResponse(BaseModel):
    id: str
    ticket_number: str
    customer_id: str
    customer_name: str
    customer_phone: str
    device_brand: str
    device_model: str
    device_imei: Optional[str] = None
    device_color: Optional[str] = None
    device_password: Optional[str] = None
    issue_description: str
    accessories_received: Optional[str] = None
    status: RepairStatus
    diagnosis: Optional[str] = None
    parts_used: Optional[List[Dict[str, Any]]] = None
    labor_cost: float
    parts_cost: float
    total_cost: float
    estimated_cost: float
    estimated_completion: Optional[str] = None
    actual_completion: Optional[str] = None
    technician_id: Optional[str] = None
    technician_name: Optional[str] = None
    priority: str
    notes: Optional[str] = None
    payment_status: PaymentStatus
    payment_method: Optional[PaymentMethod] = None
    amount_paid: float
    status_history: List[Dict[str, Any]]
    created_at: str
    updated_at: str


# ============ SALE MODELS ============
class SaleItemCreate(BaseModel):
    product_id: str
    quantity: int = 1
    unit_price: float
    discount_percent: float = 0
    discount_amount: float = 0


class MobilshopSaleCreate(BaseModel):
    customer_id: Optional[str] = None
    items: List[SaleItemCreate]
    payment_method: PaymentMethod
    cash_amount: float = 0
    card_amount: float = 0
    discount_percent: float = 0
    discount_amount: float = 0
    notes: Optional[str] = None
    warranty_terms: Optional[str] = None


class SaleItemResponse(BaseModel):
    product_id: str
    product_name: str
    product_type: ProductType
    imei: Optional[str] = None
    quantity: int
    unit_price: float
    discount_percent: float
    discount_amount: float
    subtotal: float
    total: float


class MobilshopSaleResponse(BaseModel):
    id: str
    invoice_number: str
    customer_id: Optional[str] = None
    customer_name: Optional[str] = None
    customer_phone: Optional[str] = None
    items: List[SaleItemResponse]
    subtotal: float
    discount_percent: float
    discount_amount: float
    total_discount: float
    grand_total: float
    payment_method: PaymentMethod
    cash_amount: float
    card_amount: float
    change_amount: float
    notes: Optional[str] = None
    warranty_terms: Optional[str] = None
    user_id: str
    user_name: str
    created_at: str


# ============ PURCHASE ORDER MODELS ============
class PurchaseItemCreate(BaseModel):
    product_id: Optional[str] = None
    name: str
    product_type: ProductType
    brand: Optional[str] = None
    model: Optional[str] = None
    imei: Optional[str] = None
    quantity: int = 1
    unit_cost: float
    sale_price: float = 0


class PurchaseOrderCreate(BaseModel):
    supplier_id: str
    items: List[PurchaseItemCreate]
    notes: Optional[str] = None
    payment_status: PaymentStatus = PaymentStatus.PENDING
    amount_paid: float = 0


class PurchaseOrderResponse(BaseModel):
    id: str
    order_number: str
    supplier_id: str
    supplier_name: str
    items: List[Dict[str, Any]]
    total_items: int
    total_cost: float
    payment_status: PaymentStatus
    amount_paid: float
    notes: Optional[str] = None
    user_id: str
    user_name: str
    created_at: str


# ============ CASH DRAWER MODELS ============
class MobilshopCashDrawerOpen(BaseModel):
    opening_balance: float


class MobilshopCashDrawerClose(BaseModel):
    actual_balance: float
    notes: Optional[str] = None


class MobilshopCashDrawerResponse(BaseModel):
    id: str
    user_id: str
    user_name: str
    opening_balance: float
    current_balance: float
    expected_balance: float
    cash_sales: float
    card_sales: float
    total_sales: float
    status: str
    transactions: List[Dict[str, Any]]
    opened_at: str
    closed_at: Optional[str] = None
    closing_notes: Optional[str] = None


# ============ NOTIFICATION MODELS ============
class NotificationCreate(BaseModel):
    type: str  # repair_status, low_stock, payment_due, etc.
    title: str
    message: str
    recipient_id: Optional[str] = None  # User ID
    customer_id: Optional[str] = None
    reference_id: Optional[str] = None  # Repair ID, Product ID, etc.
    reference_type: Optional[str] = None
    send_sms: bool = False
    send_email: bool = False


class NotificationResponse(BaseModel):
    id: str
    type: str
    title: str
    message: str
    recipient_id: Optional[str] = None
    customer_id: Optional[str] = None
    reference_id: Optional[str] = None
    reference_type: Optional[str] = None
    is_read: bool
    sms_sent: bool
    email_sent: bool
    created_at: str


# ============ REPORT MODELS ============
class SalesReportResponse(BaseModel):
    period: str
    total_sales: float
    total_transactions: int
    cash_sales: float
    card_sales: float
    phone_sales: int
    phone_revenue: float
    accessory_sales: int
    accessory_revenue: float
    repair_revenue: float
    repair_count: int
    average_sale: float
    top_products: List[Dict[str, Any]]
    sales_by_day: List[Dict[str, Any]]


class InventoryReportResponse(BaseModel):
    total_products: int
    total_phones: int
    total_accessories: int
    total_value: float
    low_stock_items: List[Dict[str, Any]]
    stock_by_category: List[Dict[str, Any]]
    stock_by_brand: List[Dict[str, Any]]


class TechnicianPerformanceResponse(BaseModel):
    technician_id: str
    technician_name: str
    total_repairs: int
    completed_repairs: int
    average_completion_time: float
    total_revenue: float
    repairs_by_status: Dict[str, int]
