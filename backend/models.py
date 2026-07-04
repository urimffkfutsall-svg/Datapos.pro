"""Pydantic models for the POS system"""
from pydantic import BaseModel, Field, ConfigDict
from typing import List, Optional, Dict, Any
from datetime import datetime, timezone
from enum import Enum
import uuid

# ============ ENUMS ============
class UserRole(str, Enum):
    SUPER_ADMIN = "super_admin"
    ADMIN = "admin"
    MANAGER = "manager"
    CASHIER = "cashier"

class StockMovementType(str, Enum):
    IN = "in"
    OUT = "out"
    ADJUSTMENT = "adjustment"
    SALE = "sale"

class PaymentMethod(str, Enum):
    CASH = "cash"
    BANK = "bank"
    MIXED = "mixed"

class CashDrawerStatus(str, Enum):
    OPEN = "open"
    CLOSED = "closed"

class TenantStatus(str, Enum):
    ACTIVE = "active"
    SUSPENDED = "suspended"
    TRIAL = "trial"

# ============ TENANT MODELS ============
class TenantBranding(BaseModel):
    logo_url: Optional[str] = None
    primary_color: str = "#00a79d"
    secondary_color: str = "#f3f4f6"
    company_name: str = "POS System"

class TenantCreate(BaseModel):
    name: str
    company_name: str
    email: str
    phone: Optional[str] = None
    address: Optional[str] = None
    logo_url: Optional[str] = None
    primary_color: str = "#00a79d"
    secondary_color: str = "#f3f4f6"
    stripe_payment_link: Optional[str] = None
    admin_username: str
    admin_password: str
    admin_full_name: str

class TenantUpdate(BaseModel):
    company_name: Optional[str] = None
    email: Optional[str] = None
    phone: Optional[str] = None
    address: Optional[str] = None
    city: Optional[str] = None
    logo_url: Optional[str] = None
    stamp_url: Optional[str] = None  # Vula digjitale
    whatsapp_qr_url: Optional[str] = None  # QR code për WhatsApp
    primary_color: Optional[str] = None
    secondary_color: Optional[str] = None
    stripe_payment_link: Optional[str] = None
    status: Optional[TenantStatus] = None
    subscription_expires: Optional[str] = None
    nui: Optional[str] = None
    nf: Optional[str] = None

class TenantResponse(BaseModel):
    id: str
    name: str
    company_name: str
    email: str
    phone: Optional[str] = None
    address: Optional[str] = None
    city: Optional[str] = None
    logo_url: Optional[str] = None
    stamp_url: Optional[str] = None  # Vula digjitale
    whatsapp_qr_url: Optional[str] = None  # QR code për WhatsApp
    primary_color: str
    secondary_color: str
    stripe_payment_link: Optional[str] = None
    status: TenantStatus
    subscription_expires: Optional[str] = None
    created_at: str
    users_count: Optional[int] = 0
    sales_count: Optional[int] = 0
    nui: Optional[str] = None
    nf: Optional[str] = None

class TenantPublicInfo(BaseModel):
    id: str
    name: str
    company_name: str
    logo_url: Optional[str] = None
    stamp_url: Optional[str] = None  # Vula digjitale
    whatsapp_qr_url: Optional[str] = None  # QR code për WhatsApp
    primary_color: str
    secondary_color: str

# ============ USER MODELS ============
class UserBase(BaseModel):
    username: str
    full_name: str
    role: UserRole = UserRole.CASHIER
    branch_id: Optional[str] = None
    is_active: bool = True
    pin: Optional[str] = None
    tenant_id: Optional[str] = None

class UserCreate(UserBase):
    password: str

class UserUpdate(BaseModel):
    full_name: Optional[str] = None
    role: Optional[UserRole] = None
    branch_id: Optional[str] = None
    is_active: Optional[bool] = None
    password: Optional[str] = None
    pin: Optional[str] = None

class User(UserBase):
    model_config = ConfigDict(extra="ignore")
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

class UserResponse(BaseModel):
    id: str
    username: str
    full_name: str
    role: UserRole
    branch_id: Optional[str] = None
    is_active: bool
    created_at: str
    pin: Optional[str] = None
    tenant_id: Optional[str] = None

class LoginRequest(BaseModel):
    username: str
    password: str
    tenant_id: Optional[str] = None

class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user: UserResponse

# ============ BRANCH MODELS ============
class BranchBase(BaseModel):
    name: str
    address: Optional[str] = None
    phone: Optional[str] = None
    is_active: bool = True

class BranchCreate(BranchBase):
    pass

class Branch(BranchBase):
    model_config = ConfigDict(extra="ignore")
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

class BranchResponse(BaseModel):
    id: str
    name: str
    address: Optional[str] = None
    phone: Optional[str] = None
    is_active: bool
    created_at: str

# ============ PRODUCT MODELS ============
class ProductCreate(BaseModel):
    name: Optional[str] = None
    barcode: Optional[str] = None
    purchase_price: Optional[float] = None
    sale_price: Optional[float] = None
    category: Optional[str] = None
    subcategory: Optional[str] = None
    vat_rate: Optional[float] = None
    expiry_date: Optional[str] = None
    supplier: Optional[str] = None
    unit: Optional[str] = None
    initial_stock: Optional[float] = 0
    metadata: Optional[Dict[str, Any]] = None
    branch_id: Optional[str] = None

class ProductUpdate(ProductCreate):
    pass

class Product(BaseModel):
    model_config = ConfigDict(extra="ignore")
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    name: Optional[str] = None
    barcode: Optional[str] = None
    purchase_price: Optional[float] = None
    sale_price: Optional[float] = None
    category: Optional[str] = None
    subcategory: Optional[str] = None
    vat_rate: Optional[float] = None
    expiry_date: Optional[str] = None
    supplier: Optional[str] = None
    unit: Optional[str] = None
    current_stock: float = 0
    metadata: Optional[Dict[str, Any]] = None
    branch_id: Optional[str] = None
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

class ProductResponse(BaseModel):
    id: str
    name: Optional[str] = None
    barcode: Optional[str] = None
    purchase_price: Optional[float] = None
    sale_price: Optional[float] = None
    category: Optional[str] = None
    subcategory: Optional[str] = None
    vat_rate: Optional[float] = None
    expiry_date: Optional[str] = None
    supplier: Optional[str] = None
    unit: Optional[str] = None
    current_stock: float = 0
    metadata: Optional[Dict[str, Any]] = None
    branch_id: Optional[str] = None
    created_at: str
    updated_at: str

# ============ STOCK MOVEMENT MODELS ============
class StockMovementCreate(BaseModel):
    product_id: str
    quantity: float
    movement_type: StockMovementType
    reason: Optional[str] = None
    reference: Optional[str] = None
    branch_id: Optional[str] = None

class StockMovement(BaseModel):
    model_config = ConfigDict(extra="ignore")
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    product_id: str
    quantity: float
    movement_type: StockMovementType
    reason: Optional[str] = None
    reference: Optional[str] = None
    branch_id: Optional[str] = None
    user_id: str
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

class StockMovementResponse(BaseModel):
    id: str
    product_id: str
    quantity: float
    movement_type: StockMovementType
    reason: Optional[str] = None
    reference: Optional[str] = None
    branch_id: Optional[str] = None
    user_id: str
    created_at: str

# ============ CASH DRAWER MODELS ============
class CashDrawerOpen(BaseModel):
    opening_balance: float
    branch_id: Optional[str] = None

class CashDrawerTransaction(BaseModel):
    amount: float
    transaction_type: str
    description: Optional[str] = None

class CashDrawer(BaseModel):
    model_config = ConfigDict(extra="ignore")
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    user_id: str
    branch_id: Optional[str] = None
    opening_balance: float
    current_balance: float
    expected_balance: float = 0
    status: CashDrawerStatus = CashDrawerStatus.OPEN
    transactions: List[Dict] = []
    opened_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    closed_at: Optional[datetime] = None

class CashDrawerResponse(BaseModel):
    id: str
    user_id: str
    branch_id: Optional[str] = None
    opening_balance: float
    current_balance: float
    expected_balance: float
    status: CashDrawerStatus
    transactions: List[Dict]
    opened_at: str
    closed_at: Optional[str] = None

class CloseDrawerRequest(BaseModel):
    actual_balance: float

# ============ SALE MODELS ============
class SaleItemCreate(BaseModel):
    product_id: str
    quantity: float
    unit_price: float
    discount_percent: Optional[float] = 0
    vat_percent: Optional[float] = 0

class SaleCreate(BaseModel):
    items: List[SaleItemCreate]
    payment_method: PaymentMethod
    cash_amount: Optional[float] = 0
    bank_amount: Optional[float] = 0
    customer_name: Optional[str] = None
    notes: Optional[str] = None
    # Debt fields
    is_debt: bool = False
    debtor_name: Optional[str] = None
    remaining_debt: Optional[float] = None
    # Coupon fields
    coupon_code: Optional[str] = None

class SaleItem(BaseModel):
    product_id: str
    product_name: Optional[str] = None
    quantity: float
    unit_price: float
    discount_percent: float = 0
    vat_percent: float = 0
    subtotal: float
    vat_amount: float
    total: float

class Sale(BaseModel):
    model_config = ConfigDict(extra="ignore")
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    receipt_number: str
    items: List[SaleItem]
    subtotal: float
    total_discount: float
    total_vat: float
    grand_total: float
    payment_method: PaymentMethod
    cash_amount: float = 0
    bank_amount: float = 0
    change_amount: float = 0
    customer_name: Optional[str] = None
    notes: Optional[str] = None
    user_id: str
    branch_id: Optional[str] = None
    cash_drawer_id: Optional[str] = None
    # Debt fields
    is_debt: bool = False
    debtor_name: Optional[str] = None
    remaining_debt: float = 0
    # Coupon fields
    coupon_code: Optional[str] = None
    coupon_discount: float = 0
    debt_paid_at: Optional[datetime] = None
    debt_paid_by: Optional[str] = None
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

class SaleResponse(BaseModel):
    id: str
    receipt_number: str
    items: List[SaleItem]
    subtotal: float
    total_discount: float
    total_vat: float
    grand_total: float
    payment_method: PaymentMethod
    cash_amount: float
    bank_amount: float
    change_amount: float
    customer_name: Optional[str] = None
    notes: Optional[str] = None
    user_id: str
    branch_id: Optional[str] = None
    created_at: str
    # Debt fields
    is_debt: bool = False
    debtor_name: Optional[str] = None
    remaining_debt: float = 0
    # Coupon fields
    coupon_code: Optional[str] = None
    coupon_discount: float = 0
    debt_paid_at: Optional[str] = None
    debt_paid_by: Optional[str] = None

# ============ AUDIT LOG ============
class AuditLog(BaseModel):
    model_config = ConfigDict(extra="ignore")
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    user_id: str
    action: str
    entity_type: str
    entity_id: str
    details: Optional[Dict] = None
    ip_address: Optional[str] = None
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

# ============ SETTINGS MODELS ============
class CompanySettings(BaseModel):
    company_name: str = ""
    address: str = ""
    city: str = ""
    postal_code: str = ""
    phone: str = ""
    email: str = ""
    website: str = ""
    nui: str = ""
    nf: str = ""
    vat_number: str = ""
    bank_name: str = ""
    bank_account: str = ""
    logo_url: str = ""
    show_warranty_in_pos: bool = True  # Show warranty buttons in POS

class CompanySettingsUpdate(BaseModel):
    company_name: Optional[str] = None
    address: Optional[str] = None
    city: Optional[str] = None
    postal_code: Optional[str] = None
    phone: Optional[str] = None
    email: Optional[str] = None
    website: Optional[str] = None
    nui: Optional[str] = None
    nf: Optional[str] = None
    vat_number: Optional[str] = None
    bank_name: Optional[str] = None
    bank_account: Optional[str] = None
    logo_url: Optional[str] = None
    show_warranty_in_pos: Optional[bool] = None  # Show warranty buttons in POS

class POSSettings(BaseModel):
    model_config = ConfigDict(extra="ignore")
    eshte_me_tvsh: bool = True
    norma_tvsh_default: float = 18.0
    shfaq_artikuj_me_minus: bool = True
    lejo_shitjen_me_minus: bool = True
    gjenero_automatik_numrin: bool = True
    lejo_shume_zbritje: bool = False
    valuta: str = "EUR"
    simboli_valutes: str = "€"
    metoda_gjenerimit: str = "auto"
    orientimi_fatures: str = "vertikal"
    shteku_printer: str = ""
    printo_automatikisht: bool = False
    hap_sirtar_automatikisht: bool = False

class POSSettingsUpdate(BaseModel):
    eshte_me_tvsh: Optional[bool] = None
    norma_tvsh_default: Optional[float] = None
    shfaq_artikuj_me_minus: Optional[bool] = None
    lejo_shitjen_me_minus: Optional[bool] = None
    gjenero_automatik_numrin: Optional[bool] = None
    lejo_shume_zbritje: Optional[bool] = None
    valuta: Optional[str] = None
    simboli_valutes: Optional[str] = None
    metoda_gjenerimit: Optional[str] = None
    orientimi_fatures: Optional[str] = None
    shteku_printer: Optional[str] = None
    printo_automatikisht: Optional[bool] = None
    hap_sirtar_automatikisht: Optional[bool] = None

# ============ WAREHOUSE MODELS ============
class WarehouseCreate(BaseModel):
    name: str
    code: Optional[str] = None


# ============ WARRANTY MODELS ============
class WarrantyCreate(BaseModel):
    """Create a new warranty document"""
    customer_name: Optional[str] = None
    customer_phone: Optional[str] = None
    customer_address: Optional[str] = None
    product_name: Optional[str] = None
    product_brand: Optional[str] = None
    product_model: Optional[str] = None
    serial_number: Optional[str] = None
    imei: Optional[str] = None
    purchase_date: Optional[str] = None
    warranty_period: int = 12  # months
    product_condition: str = "I ri"
    accessories: Optional[str] = None
    notes: Optional[str] = None

class WarrantyUpdate(BaseModel):
    """Update warranty document"""
    customer_name: Optional[str] = None
    customer_phone: Optional[str] = None
    customer_address: Optional[str] = None
    product_name: Optional[str] = None
    product_brand: Optional[str] = None
    product_model: Optional[str] = None
    serial_number: Optional[str] = None
    imei: Optional[str] = None
    purchase_date: Optional[str] = None
    warranty_period: Optional[int] = None
    product_condition: Optional[str] = None
    accessories: Optional[str] = None
    notes: Optional[str] = None

class WarrantyResponse(BaseModel):
    """Warranty document response"""
    id: str
    warranty_number: str
    customer_name: Optional[str] = None
    customer_phone: Optional[str] = None
    customer_address: Optional[str] = None
    product_name: Optional[str] = None
    product_brand: Optional[str] = None
    product_model: Optional[str] = None
    serial_number: Optional[str] = None
    imei: Optional[str] = None
    purchase_date: Optional[str] = None
    warranty_period: int = 12
    expiry_date: Optional[str] = None
    product_condition: str = "I ri"
    accessories: Optional[str] = None
    notes: Optional[str] = None
    created_by: str
    created_at: str
    tenant_id: str

    address: Optional[str] = None
    phone: Optional[str] = None
    is_active: bool = True
    is_default: bool = False

class Warehouse(BaseModel):
    model_config = ConfigDict(extra="ignore")
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    name: str
    code: Optional[str] = None
    address: Optional[str] = None
    phone: Optional[str] = None
    is_active: bool = True
    is_default: bool = False
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

class WarehouseResponse(BaseModel):
    id: str
    name: str
    code: Optional[str] = None
    address: Optional[str] = None
    phone: Optional[str] = None
    is_active: bool
    is_default: bool
    created_at: str

class WarehouseUpdate(BaseModel):
    name: Optional[str] = None
    code: Optional[str] = None
    address: Optional[str] = None
    phone: Optional[str] = None
    is_active: Optional[bool] = None
    is_default: Optional[bool] = None

# ============ VAT RATE MODELS ============
class VATRateCreate(BaseModel):
    name: str
    rate: float
    code: Optional[str] = None
    is_default: bool = False
    is_active: bool = True

class VATRate(BaseModel):
    model_config = ConfigDict(extra="ignore")
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    name: str
    rate: float
    code: Optional[str] = None
    is_default: bool = False
    is_active: bool = True
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

class VATRateResponse(BaseModel):
    id: str
    name: str
    rate: float
    code: Optional[str] = None
    is_default: bool
    is_active: bool
    created_at: str

class VATRateUpdate(BaseModel):
    name: Optional[str] = None
    rate: Optional[float] = None
    code: Optional[str] = None
    is_default: Optional[bool] = None
    is_active: Optional[bool] = None

# ============ RESET DATA MODELS ============
class ResetDataRequest(BaseModel):
    admin_password: str
    user_ids: Optional[List[str]] = None
    reset_type: str = "all"
    reset_options: Optional[Dict] = None

# ============ COMMENT TEMPLATES MODELS ============
class CommentTemplateCreate(BaseModel):
    title: str
    content: str
    is_default: bool = False
    is_active: bool = True


# ============ DEBT MODELS ============
class PayDebtRequest(BaseModel):
    """Request to pay/close a debt"""
    amount: float
    notes: Optional[str] = None

class DebtSummary(BaseModel):
    """Summary of debt for reporting"""
    total_debt: float
    total_paid: float
    outstanding: float
    debt_count: int

class CommentTemplateUpdate(BaseModel):
    title: Optional[str] = None
    content: Optional[str] = None
    is_default: Optional[bool] = None
    is_active: Optional[bool] = None

class CommentTemplateResponse(BaseModel):
    id: str
    title: str
    content: str
    is_default: bool
    is_active: bool
    created_at: str

# ============================
# Coupon / Discount Codes
# ============================
class CouponBase(BaseModel):
    code: str = Field(..., min_length=2, max_length=50)
    name: str = Field(..., min_length=1, max_length=200)
    discount_type: str = "percent"  # "percent" ose "fixed"
    discount_value: float = Field(..., ge=0)
    active: bool = True
    valid_from: Optional[datetime] = None
    valid_until: Optional[datetime] = None
    max_uses: Optional[int] = Field(None, ge=1)
    min_purchase_amount: Optional[float] = Field(None, ge=0)


class CouponCreate(CouponBase):
    pass


class CouponUpdate(BaseModel):
    code: Optional[str] = Field(None, min_length=2, max_length=50)
    name: Optional[str] = Field(None, min_length=1, max_length=200)
    discount_type: Optional[str] = None
    discount_value: Optional[float] = Field(None, ge=0)
    active: Optional[bool] = None
    valid_from: Optional[datetime] = None
    valid_until: Optional[datetime] = None
    max_uses: Optional[int] = Field(None, ge=1)
    min_purchase_amount: Optional[float] = Field(None, ge=0)


class Coupon(CouponBase):
    id: str
    tenant_id: str
    used_count: int = 0
    created_at: datetime
    updated_at: datetime


class CouponValidateRequest(BaseModel):
    code: str
    subtotal: Optional[float] = None


class CouponValidateResponse(BaseModel):
    valid: bool
    code: Optional[str] = None
    name: Optional[str] = None
    discount_type: Optional[str] = None
    discount_value: Optional[float] = None
    discount_amount: Optional[float] = None
    error: Optional[str] = None
