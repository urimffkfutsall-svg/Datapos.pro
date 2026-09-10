from fastapi import FastAPI, APIRouter, HTTPException, Depends, status, Query, Response
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from dotenv import load_dotenv
from starlette.middleware.cors import CORSMiddleware
from motor.motor_asyncio import AsyncIOMotorClient
import os
import logging
from pathlib import Path
from pydantic import BaseModel, Field, ConfigDict
from typing import List, Optional, Dict, Any
import uuid
from datetime import datetime, timezone, timedelta
import jwt
from passlib.context import CryptContext
from enum import Enum
import io
from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
from reportlab.lib.styles import getSampleStyleSheet
import xlsxwriter

ROOT_DIR = Path(__file__).parent
load_dotenv(ROOT_DIR / '.env')

# MongoDB connection
mongo_url = os.environ['MONGO_URL']
client = AsyncIOMotorClient(mongo_url)
db = client[os.environ['DB_NAME']]

# JWT Config
JWT_SECRET = os.environ.get('JWT_SECRET', 't3next_pos_secret_key')
JWT_ALGORITHM = os.environ.get('JWT_ALGORITHM', 'HS256')
JWT_EXPIRATION_HOURS = int(os.environ.get('JWT_EXPIRATION_HOURS', 24))

# Password hashing
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
security = HTTPBearer()

# Create the main app
app = FastAPI(title="t3next POS API", version="1.0.0")
api_router = APIRouter(prefix="/api")

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# ============ ENUMS ============
class UserRole(str, Enum):
    SUPER_ADMIN = "super_admin"  # Can manage all tenants
    ADMIN = "admin"              # Tenant admin
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
    name: str  # Unique tenant identifier (used in subdomain)
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
    logo_url: Optional[str] = None
    primary_color: Optional[str] = None
    secondary_color: Optional[str] = None
    stripe_payment_link: Optional[str] = None
    status: Optional[TenantStatus] = None
    subscription_expires: Optional[str] = None

class TenantResponse(BaseModel):
    id: str
    name: str
    company_name: str
    email: str
    phone: Optional[str] = None
    address: Optional[str] = None
    logo_url: Optional[str] = None
    primary_color: str
    secondary_color: str
    stripe_payment_link: Optional[str] = None
    status: TenantStatus
    subscription_expires: Optional[str] = None
    created_at: str
    users_count: Optional[int] = 0
    sales_count: Optional[int] = 0

class TenantPublicInfo(BaseModel):
    """Public tenant info for branding (no sensitive data)"""
    id: str
    name: str
    company_name: str
    logo_url: Optional[str] = None
    primary_color: str
    secondary_color: str

# ============ MODELS ============
class UserBase(BaseModel):
    username: str
    full_name: str
    role: UserRole = UserRole.CASHIER
    branch_id: Optional[str] = None
    is_active: bool = True
    pin: Optional[str] = None
    tenant_id: Optional[str] = None  # None for super_admin

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

class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user: UserResponse

# Branch Models
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

# Product Models - ALL FIELDS OPTIONAL except id
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

# Stock Movement Models
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

# Cash Drawer Models
class CashDrawerOpen(BaseModel):
    opening_balance: float
    branch_id: Optional[str] = None

class CashDrawerTransaction(BaseModel):
    amount: float
    transaction_type: str  # "in" or "out"
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

# Sale Models
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

# Audit Log
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

# Company Settings Models
class CompanySettings(BaseModel):
    company_name: str = ""
    address: str = ""
    city: str = ""
    postal_code: str = ""
    phone: str = ""
    email: str = ""
    website: str = ""
    nui: str = ""  # Numri Unik Identifikues
    nf: str = ""   # Numri Fiskal
    vat_number: str = ""
    bank_name: str = ""
    bank_account: str = ""
    logo_url: str = ""

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

# POS Settings Models
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

# Warehouse (Depot) Models
class WarehouseCreate(BaseModel):
    name: str
    code: Optional[str] = None
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

# VAT Rate Models
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

# Reset Data Models
class ResetDataRequest(BaseModel):
    admin_password: str
    user_ids: Optional[List[str]] = None  # If None, reset all users
    reset_type: str = "all"  # "all", "daily", "user_specific"
    reset_options: Optional[Dict] = None  # Additional options like date range

# Comment Templates Models
class CommentTemplateCreate(BaseModel):
    title: str
    content: str
    is_default: bool = False
    is_active: bool = True

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

# ============ HELPER FUNCTIONS ============
def hash_password(password: str) -> str:
    return pwd_context.hash(password)

def verify_password(plain_password: str, hashed_password: str) -> bool:
    return pwd_context.verify(plain_password, hashed_password)

def create_token(user_id: str, username: str, role: str) -> str:
    payload = {
        "sub": user_id,
        "username": username,
        "role": role,
        "exp": datetime.now(timezone.utc) + timedelta(hours=JWT_EXPIRATION_HOURS)
    }
    return jwt.encode(payload, JWT_SECRET, algorithm=JWT_ALGORITHM)

async def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(security)) -> dict:
    token = credentials.credentials
    try:
        payload = jwt.decode(token, JWT_SECRET, algorithms=[JWT_ALGORITHM])
        user = await db.users.find_one({"id": payload["sub"]}, {"_id": 0, "password_hash": 0})
        if not user:
            raise HTTPException(status_code=401, detail="Përdoruesi nuk u gjet")
        return user
    except jwt.ExpiredSignatureError:
        raise HTTPException(status_code=401, detail="Token-i ka skaduar")
    except jwt.InvalidTokenError:
        raise HTTPException(status_code=401, detail="Token i pavlefshëm")

def require_role(allowed_roles: List[UserRole]):
    async def role_checker(current_user: dict = Depends(get_current_user)):
        if current_user["role"] not in [r.value for r in allowed_roles]:
            raise HTTPException(status_code=403, detail="Nuk keni leje për këtë veprim")
        return current_user
    return role_checker

def get_tenant_filter(current_user: dict) -> dict:
    """Get tenant filter for queries - returns empty dict for super_admin"""
    if current_user.get("role") == UserRole.SUPER_ADMIN or current_user.get("role") == "super_admin":
        return {}  # Super admin sees all
    tenant_id = current_user.get("tenant_id")
    if not tenant_id:
        return {}  # Legacy users without tenant_id
    return {"tenant_id": tenant_id}

def add_tenant_id(data: dict, current_user: dict) -> dict:
    """Add tenant_id to data for create operations"""
    tenant_id = current_user.get("tenant_id")
    if tenant_id:
        data["tenant_id"] = tenant_id
    return data

async def log_audit(user_id: str, action: str, entity_type: str, entity_id: str, details: dict = None):
    audit = AuditLog(user_id=user_id, action=action, entity_type=entity_type, entity_id=entity_id, details=details)
    doc = audit.model_dump()
    doc['created_at'] = doc['created_at'].isoformat()
    await db.audit_logs.insert_one(doc)

async def generate_receipt_number(branch_id: str = None, tenant_id: str = None) -> str:
    today = datetime.now(timezone.utc).strftime("%Y%m%d")
    prefix = f"RCP-{today}"
    query = {"receipt_number": {"$regex": f"^{prefix}"}}
    if tenant_id:
        query["tenant_id"] = tenant_id
    count = await db.sales.count_documents(query)
    return f"{prefix}-{str(count + 1).zfill(4)}"

# Helper to get tenant from request header or subdomain
async def get_tenant_from_request(tenant_id: Optional[str] = None):
    """Get tenant info - used for branding"""
    if not tenant_id:
        return None
    tenant = await db.tenants.find_one({"id": tenant_id}, {"_id": 0})
    return tenant

# ============ TENANT ROUTES (Super Admin Only) ============
@api_router.get("/tenants", response_model=List[TenantResponse])
async def get_all_tenants(
    current_user: dict = Depends(get_current_user)
):
    """Get all tenants - Super Admin only"""
    if current_user.get("role") != UserRole.SUPER_ADMIN:
        raise HTTPException(status_code=403, detail="Vetëm Super Admin mund të shohë të gjitha firmat")
    
    tenants = await db.tenants.find({}, {"_id": 0}).sort("created_at", -1).to_list(1000)
    
    # Enrich with counts
    for tenant in tenants:
        tenant["users_count"] = await db.users.count_documents({"tenant_id": tenant["id"]})
        tenant["sales_count"] = await db.sales.count_documents({"tenant_id": tenant["id"]})
    
    return tenants

@api_router.post("/tenants", response_model=TenantResponse)
async def create_tenant(
    tenant: TenantCreate,
    current_user: dict = Depends(get_current_user)
):
    """Create a new tenant - Super Admin only"""
    if current_user.get("role") != UserRole.SUPER_ADMIN:
        raise HTTPException(status_code=403, detail="Vetëm Super Admin mund të krijojë firma të reja")
    
    # Check if tenant name already exists
    existing = await db.tenants.find_one({"name": tenant.name.lower()})
    if existing:
        raise HTTPException(status_code=400, detail="Emri i firmës ekziston tashmë")
    
    # Check if email already exists
    existing_email = await db.tenants.find_one({"email": tenant.email.lower()})
    if existing_email:
        raise HTTPException(status_code=400, detail="Email-i ekziston tashmë")
    
    tenant_id = str(uuid.uuid4())
    tenant_data = {
        "id": tenant_id,
        "name": tenant.name.lower(),
        "company_name": tenant.company_name,
        "email": tenant.email.lower(),
        "phone": tenant.phone,
        "address": tenant.address,
        "logo_url": tenant.logo_url,
        "primary_color": tenant.primary_color,
        "secondary_color": tenant.secondary_color,
        "stripe_payment_link": tenant.stripe_payment_link,
        "status": TenantStatus.TRIAL,
        "subscription_expires": None,
        "created_at": datetime.now(timezone.utc).isoformat(),
        "created_by": current_user["id"]
    }
    
    await db.tenants.insert_one(tenant_data)
    
    # Create admin user for the tenant
    admin_user = {
        "id": str(uuid.uuid4()),
        "username": tenant.admin_username,
        "password_hash": hash_password(tenant.admin_password),
        "full_name": tenant.admin_full_name,
        "role": UserRole.ADMIN,
        "tenant_id": tenant_id,
        "is_active": True,
        "created_at": datetime.now(timezone.utc).isoformat()
    }
    await db.users.insert_one(admin_user)
    
    await log_audit(current_user["id"], "create", "tenant", tenant_id)
    
    return TenantResponse(**tenant_data, users_count=1, sales_count=0)

@api_router.get("/tenants/{tenant_id}", response_model=TenantResponse)
async def get_tenant(
    tenant_id: str,
    current_user: dict = Depends(get_current_user)
):
    """Get tenant details - Super Admin only"""
    if current_user.get("role") != UserRole.SUPER_ADMIN:
        raise HTTPException(status_code=403, detail="Vetëm Super Admin mund të shohë detajet e firmës")
    
    tenant = await db.tenants.find_one({"id": tenant_id}, {"_id": 0})
    if not tenant:
        raise HTTPException(status_code=404, detail="Firma nuk u gjet")
    
    tenant["users_count"] = await db.users.count_documents({"tenant_id": tenant_id})
    tenant["sales_count"] = await db.sales.count_documents({"tenant_id": tenant_id})
    
    return TenantResponse(**tenant)

@api_router.put("/tenants/{tenant_id}", response_model=TenantResponse)
async def update_tenant(
    tenant_id: str,
    tenant: TenantUpdate,
    current_user: dict = Depends(get_current_user)
):
    """Update tenant - Super Admin only"""
    if current_user.get("role") != UserRole.SUPER_ADMIN:
        raise HTTPException(status_code=403, detail="Vetëm Super Admin mund të përditësojë firmën")
    
    existing = await db.tenants.find_one({"id": tenant_id})
    if not existing:
        raise HTTPException(status_code=404, detail="Firma nuk u gjet")
    
    update_data = {k: v for k, v in tenant.model_dump().items() if v is not None}
    if update_data:
        await db.tenants.update_one({"id": tenant_id}, {"$set": update_data})
    
    updated = await db.tenants.find_one({"id": tenant_id}, {"_id": 0})
    updated["users_count"] = await db.users.count_documents({"tenant_id": tenant_id})
    updated["sales_count"] = await db.sales.count_documents({"tenant_id": tenant_id})
    
    await log_audit(current_user["id"], "update", "tenant", tenant_id)
    
    return TenantResponse(**updated)

@api_router.delete("/tenants/{tenant_id}")
async def delete_tenant(
    tenant_id: str,
    current_user: dict = Depends(get_current_user)
):
    """Delete tenant and all its data - Super Admin only"""
    if current_user.get("role") != UserRole.SUPER_ADMIN:
        raise HTTPException(status_code=403, detail="Vetëm Super Admin mund të fshijë firmën")
    
    existing = await db.tenants.find_one({"id": tenant_id})
    if not existing:
        raise HTTPException(status_code=404, detail="Firma nuk u gjet")
    
    # Delete all tenant data
    await db.users.delete_many({"tenant_id": tenant_id})
    await db.products.delete_many({"tenant_id": tenant_id})
    await db.sales.delete_many({"tenant_id": tenant_id})
    await db.branches.delete_many({"tenant_id": tenant_id})
    await db.cash_drawers.delete_many({"tenant_id": tenant_id})
    await db.stock_movements.delete_many({"tenant_id": tenant_id})
    await db.settings.delete_many({"tenant_id": tenant_id})
    await db.tenants.delete_one({"id": tenant_id})
    
    await log_audit(current_user["id"], "delete", "tenant", tenant_id)
    
    return {"message": "Firma dhe të gjitha të dhënat u fshinë me sukses"}

@api_router.get("/tenant/public/{tenant_name}", response_model=TenantPublicInfo)
async def get_tenant_public_info(tenant_name: str):
    """Get public tenant info for branding - No auth required"""
    tenant = await db.tenants.find_one({"name": tenant_name.lower()}, {"_id": 0})
    if not tenant:
        # Return default branding if tenant not found
        return TenantPublicInfo(
            id="default",
            name="default",
            company_name="MobilshopurimiPOS",
            logo_url="https://customer-assets.emergentagent.com/job_retailsys-1/artifacts/9i1h1bxb_logo%20icon.png",
            primary_color="#00a79d",
            secondary_color="#f3f4f6"
        )
    
    return TenantPublicInfo(
        id=tenant["id"],
        name=tenant["name"],
        company_name=tenant["company_name"],
        logo_url=tenant.get("logo_url"),
        primary_color=tenant.get("primary_color", "#00a79d"),
        secondary_color=tenant.get("secondary_color", "#f3f4f6")
    )

# ============ AUTH ROUTES ============
@api_router.post("/auth/login", response_model=TokenResponse)
async def login(request: LoginRequest):
    # First try to find by username
    user = await db.users.find_one({"username": request.username}, {"_id": 0})
    
    # If not found by username, try to find by PIN (for PIN login)
    if not user:
        user = await db.users.find_one({"pin": request.username}, {"_id": 0})
        if user and request.password == request.username:
            # PIN login successful (PIN used as both username and password)
            pass
        else:
            user = None
    else:
        # Regular username login - verify password
        if not verify_password(request.password, user.get("password_hash", "")):
            raise HTTPException(status_code=401, detail="Username ose fjalëkalim i gabuar")
    
    if not user:
        raise HTTPException(status_code=401, detail="Username ose fjalëkalim i gabuar")
    
    if not user.get("is_active", True):
        raise HTTPException(status_code=403, detail="Llogaria është e çaktivizuar")
    
    # Check tenant status (skip for super_admin)
    tenant_id = user.get("tenant_id")
    tenant_info = None
    if tenant_id and user.get("role") != UserRole.SUPER_ADMIN:
        tenant = await db.tenants.find_one({"id": tenant_id}, {"_id": 0})
        if not tenant:
            raise HTTPException(status_code=403, detail="Firma nuk ekziston")
        if tenant.get("status") == TenantStatus.SUSPENDED:
            raise HTTPException(status_code=403, detail="Firma është e pezulluar. Kontaktoni administratorin.")
        tenant_info = {
            "id": tenant["id"],
            "name": tenant["name"],
            "company_name": tenant["company_name"],
            "logo_url": tenant.get("logo_url"),
            "primary_color": tenant.get("primary_color", "#00a79d"),
            "secondary_color": tenant.get("secondary_color", "#f3f4f6")
        }
    
    token = create_token(user["id"], user["username"], user["role"])
    await log_audit(user["id"], "login", "user", user["id"])
    
    response_data = TokenResponse(
        access_token=token,
        user=UserResponse(
            id=user["id"],
            username=user["username"],
            full_name=user["full_name"],
            role=user["role"],
            branch_id=user.get("branch_id"),
            is_active=user["is_active"],
            created_at=user["created_at"],
            pin=user.get("pin"),
            tenant_id=tenant_id
        )
    )
    
    # Add tenant info to response
    return response_data

@api_router.get("/auth/me", response_model=UserResponse)
async def get_me(current_user: dict = Depends(get_current_user)):
    return UserResponse(
        id=current_user["id"],
        username=current_user["username"],
        full_name=current_user["full_name"],
        role=current_user["role"],
        branch_id=current_user.get("branch_id"),
        is_active=current_user["is_active"],
        created_at=current_user["created_at"],
        pin=current_user.get("pin"),
        tenant_id=current_user.get("tenant_id")
    )

# ============ USER ROUTES ============
@api_router.post("/users", response_model=UserResponse)
async def create_user(user_data: UserCreate, current_user: dict = Depends(require_role([UserRole.ADMIN]))):
    # Check username uniqueness within tenant
    tenant_filter = get_tenant_filter(current_user)
    existing = await db.users.find_one({"username": user_data.username, **tenant_filter})
    if existing:
        raise HTTPException(status_code=400, detail="Username ekziston tashmë")
    
    # Check if PIN is unique within tenant (if provided)
    if user_data.pin:
        existing_pin = await db.users.find_one({"pin": user_data.pin, **tenant_filter})
        if existing_pin:
            raise HTTPException(status_code=400, detail="Ky PIN përdoret nga një përdorues tjetër")
    
    user = User(**user_data.model_dump(exclude={"password"}))
    doc = user.model_dump()
    doc['password_hash'] = hash_password(user_data.password)
    doc['created_at'] = doc['created_at'].isoformat()
    doc = add_tenant_id(doc, current_user)  # Add tenant_id
    await db.users.insert_one(doc)
    await log_audit(current_user["id"], "create_user", "user", user.id)
    
    return UserResponse(**{**doc, "created_at": doc["created_at"]})

@api_router.get("/users", response_model=List[UserResponse])
async def get_users(
    branch_id: Optional[str] = None,
    role: Optional[UserRole] = None,
    current_user: dict = Depends(require_role([UserRole.ADMIN, UserRole.MANAGER]))
):
    query = get_tenant_filter(current_user)  # Filter by tenant
    if branch_id:
        query["branch_id"] = branch_id
    if role:
        query["role"] = role.value
    
    users = await db.users.find(query, {"_id": 0, "password_hash": 0}).to_list(1000)
    return [UserResponse(**u) for u in users]

@api_router.get("/users/{user_id}", response_model=UserResponse)
async def get_user(user_id: str, current_user: dict = Depends(require_role([UserRole.ADMIN, UserRole.MANAGER]))):
    query = {"id": user_id, **get_tenant_filter(current_user)}
    user = await db.users.find_one(query, {"_id": 0, "password_hash": 0})
    if not user:
        raise HTTPException(status_code=404, detail="Përdoruesi nuk u gjet")
    return UserResponse(**user)

@api_router.put("/users/{user_id}", response_model=UserResponse)
async def update_user(user_id: str, user_data: UserUpdate, current_user: dict = Depends(require_role([UserRole.ADMIN]))):
    tenant_filter = get_tenant_filter(current_user)
    update_dict = {k: v for k, v in user_data.model_dump().items() if v is not None}
    if "password" in update_dict:
        update_dict["password_hash"] = hash_password(update_dict.pop("password"))
    
    # Check if PIN is unique within tenant (if provided and changed)
    if "pin" in update_dict and update_dict["pin"]:
        existing_pin = await db.users.find_one({"pin": update_dict["pin"], "id": {"$ne": user_id}, **tenant_filter})
        if existing_pin:
            raise HTTPException(status_code=400, detail="Ky PIN përdoret nga një përdorues tjetër")
    
    if update_dict:
        await db.users.update_one({"id": user_id, **tenant_filter}, {"$set": update_dict})
    
    user = await db.users.find_one({"id": user_id, **tenant_filter}, {"_id": 0, "password_hash": 0})
    if not user:
        raise HTTPException(status_code=404, detail="Përdoruesi nuk u gjet")
    
    await log_audit(current_user["id"], "update_user", "user", user_id, update_dict)
    return UserResponse(**user)

@api_router.delete("/users/{user_id}")
async def delete_user(user_id: str, current_user: dict = Depends(require_role([UserRole.ADMIN]))):
    tenant_filter = get_tenant_filter(current_user)
    result = await db.users.delete_one({"id": user_id, **tenant_filter})
    if result.deleted_count == 0:
        raise HTTPException(status_code=404, detail="Përdoruesi nuk u gjet")
    await log_audit(current_user["id"], "delete_user", "user", user_id)
    return {"message": "Përdoruesi u fshi me sukses"}

# ============ BRANCH ROUTES ============
@api_router.post("/branches", response_model=BranchResponse)
async def create_branch(branch_data: BranchCreate, current_user: dict = Depends(require_role([UserRole.ADMIN]))):
    branch = Branch(**branch_data.model_dump())
    doc = branch.model_dump()
    doc['created_at'] = doc['created_at'].isoformat()
    doc = add_tenant_id(doc, current_user)  # Add tenant_id
    await db.branches.insert_one(doc)
    await log_audit(current_user["id"], "create_branch", "branch", branch.id)
    return BranchResponse(**doc)

@api_router.get("/branches", response_model=List[BranchResponse])
async def get_branches(current_user: dict = Depends(get_current_user)):
    tenant_filter = get_tenant_filter(current_user)
    branches = await db.branches.find(tenant_filter, {"_id": 0}).to_list(1000)
    return [BranchResponse(**b) for b in branches]

@api_router.get("/branches/{branch_id}", response_model=BranchResponse)
async def get_branch(branch_id: str, current_user: dict = Depends(get_current_user)):
    tenant_filter = get_tenant_filter(current_user)
    branch = await db.branches.find_one({"id": branch_id, **tenant_filter}, {"_id": 0})
    if not branch:
        raise HTTPException(status_code=404, detail="Dega nuk u gjet")
    return BranchResponse(**branch)

@api_router.put("/branches/{branch_id}", response_model=BranchResponse)
async def update_branch(branch_id: str, branch_data: BranchCreate, current_user: dict = Depends(require_role([UserRole.ADMIN]))):
    tenant_filter = get_tenant_filter(current_user)
    update_dict = branch_data.model_dump()
    await db.branches.update_one({"id": branch_id, **tenant_filter}, {"$set": update_dict})
    branch = await db.branches.find_one({"id": branch_id, **tenant_filter}, {"_id": 0})
    if not branch:
        raise HTTPException(status_code=404, detail="Dega nuk u gjet")
    await log_audit(current_user["id"], "update_branch", "branch", branch_id)
    return BranchResponse(**branch)

@api_router.delete("/branches/{branch_id}")
async def delete_branch(branch_id: str, current_user: dict = Depends(require_role([UserRole.ADMIN]))):
    tenant_filter = get_tenant_filter(current_user)
    result = await db.branches.delete_one({"id": branch_id, **tenant_filter})
    if result.deleted_count == 0:
        raise HTTPException(status_code=404, detail="Dega nuk u gjet")
    await log_audit(current_user["id"], "delete_branch", "branch", branch_id)
    return {"message": "Dega u fshi me sukses"}

# ============ PRODUCT ROUTES ============
@api_router.post("/products", response_model=ProductResponse)
async def create_product(product_data: ProductCreate, current_user: dict = Depends(require_role([UserRole.ADMIN, UserRole.MANAGER]))):
    product = Product(**product_data.model_dump())
    product.current_stock = product_data.initial_stock or 0
    doc = product.model_dump()
    doc['created_at'] = doc['created_at'].isoformat()
    doc['updated_at'] = doc['updated_at'].isoformat()
    doc = add_tenant_id(doc, current_user)  # Add tenant_id
    await db.products.insert_one(doc)
    
    # Create initial stock movement if initial_stock > 0
    if product_data.initial_stock and product_data.initial_stock > 0:
        movement = StockMovement(
            product_id=product.id,
            quantity=product_data.initial_stock,
            movement_type=StockMovementType.IN,
            reason="Stok fillestar",
            user_id=current_user["id"],
            branch_id=product_data.branch_id
        )
        mov_doc = movement.model_dump()
        mov_doc['created_at'] = mov_doc['created_at'].isoformat()
        mov_doc = add_tenant_id(mov_doc, current_user)  # Add tenant_id
        await db.stock_movements.insert_one(mov_doc)
    
    await log_audit(current_user["id"], "create_product", "product", product.id)
    return ProductResponse(**doc)

@api_router.get("/products", response_model=List[ProductResponse])
async def get_products(
    branch_id: Optional[str] = None,
    category: Optional[str] = None,
    search: Optional[str] = None,
    low_stock: Optional[bool] = None,
    current_user: dict = Depends(get_current_user)
):
    query = get_tenant_filter(current_user)  # Filter by tenant
    if branch_id:
        query["branch_id"] = branch_id
    if category:
        query["category"] = category
    if search:
        query["$or"] = [
            {"name": {"$regex": search, "$options": "i"}},
            {"barcode": {"$regex": search, "$options": "i"}}
        ]
    if low_stock:
        query["current_stock"] = {"$lt": 10}
    
    products = await db.products.find(query, {"_id": 0}).to_list(10000)
    return [ProductResponse(**p) for p in products]

@api_router.get("/products/{product_id}", response_model=ProductResponse)
async def get_product(product_id: str, current_user: dict = Depends(get_current_user)):
    query = {"id": product_id, **get_tenant_filter(current_user)}
    product = await db.products.find_one(query, {"_id": 0})
    if not product:
        raise HTTPException(status_code=404, detail="Produkti nuk u gjet")
    return ProductResponse(**product)

@api_router.get("/products/barcode/{barcode}", response_model=ProductResponse)
async def get_product_by_barcode(barcode: str, current_user: dict = Depends(get_current_user)):
    query = {"barcode": barcode, **get_tenant_filter(current_user)}
    product = await db.products.find_one(query, {"_id": 0})
    if not product:
        raise HTTPException(status_code=404, detail="Produkti nuk u gjet")
    return ProductResponse(**product)

@api_router.put("/products/{product_id}", response_model=ProductResponse)
async def update_product(product_id: str, product_data: ProductUpdate, current_user: dict = Depends(require_role([UserRole.ADMIN, UserRole.MANAGER]))):
    tenant_filter = get_tenant_filter(current_user)
    update_dict = {k: v for k, v in product_data.model_dump().items() if v is not None}
    update_dict["updated_at"] = datetime.now(timezone.utc).isoformat()
    
    await db.products.update_one({"id": product_id, **tenant_filter}, {"$set": update_dict})
    product = await db.products.find_one({"id": product_id, **tenant_filter}, {"_id": 0})
    if not product:
        raise HTTPException(status_code=404, detail="Produkti nuk u gjet")
    
    await log_audit(current_user["id"], "update_product", "product", product_id)
    return ProductResponse(**product)

@api_router.delete("/products/{product_id}")
async def delete_product(product_id: str, current_user: dict = Depends(require_role([UserRole.ADMIN]))):
    tenant_filter = get_tenant_filter(current_user)
    result = await db.products.delete_one({"id": product_id, **tenant_filter})
    if result.deleted_count == 0:
        raise HTTPException(status_code=404, detail="Produkti nuk u gjet")
    await log_audit(current_user["id"], "delete_product", "product", product_id)
    return {"message": "Produkti u fshi me sukses"}

# ============ STOCK ROUTES ============
@api_router.post("/stock/movements", response_model=StockMovementResponse)
async def create_stock_movement(movement_data: StockMovementCreate, current_user: dict = Depends(require_role([UserRole.ADMIN, UserRole.MANAGER]))):
    tenant_filter = get_tenant_filter(current_user)
    product = await db.products.find_one({"id": movement_data.product_id, **tenant_filter}, {"_id": 0})
    if not product:
        raise HTTPException(status_code=404, detail="Produkti nuk u gjet")
    
    # Calculate new stock
    current_stock = product.get("current_stock", 0)
    if movement_data.movement_type in [StockMovementType.IN]:
        new_stock = current_stock + movement_data.quantity
    else:
        new_stock = current_stock - movement_data.quantity
        if new_stock < 0:
            raise HTTPException(status_code=400, detail="Stoku nuk mund të jetë negativ")
    
    # Create movement
    movement = StockMovement(**movement_data.model_dump(), user_id=current_user["id"])
    mov_doc = movement.model_dump()
    mov_doc['created_at'] = mov_doc['created_at'].isoformat()
    mov_doc = add_tenant_id(mov_doc, current_user)  # Add tenant_id
    await db.stock_movements.insert_one(mov_doc)
    
    # Update product stock
    await db.products.update_one(
        {"id": movement_data.product_id, **tenant_filter},
        {"$set": {"current_stock": new_stock, "updated_at": datetime.now(timezone.utc).isoformat()}}
    )
    
    await log_audit(current_user["id"], "stock_movement", "stock", movement.id, {"type": movement_data.movement_type, "qty": movement_data.quantity})
    return StockMovementResponse(**mov_doc)

@api_router.get("/stock/movements", response_model=List[StockMovementResponse])
async def get_stock_movements(
    product_id: Optional[str] = None,
    branch_id: Optional[str] = None,
    movement_type: Optional[StockMovementType] = None,
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
    current_user: dict = Depends(get_current_user)
):
    query = get_tenant_filter(current_user)  # Filter by tenant
    if product_id:
        query["product_id"] = product_id
    if branch_id:
        query["branch_id"] = branch_id
    if movement_type:
        query["movement_type"] = movement_type.value
    if start_date:
        query["created_at"] = {"$gte": start_date}
    if end_date:
        query.setdefault("created_at", {})["$lte"] = end_date
    
    movements = await db.stock_movements.find(query, {"_id": 0}).sort("created_at", -1).to_list(10000)
    return [StockMovementResponse(**m) for m in movements]

# ============ CASH DRAWER ROUTES ============
@api_router.post("/cashier/open", response_model=CashDrawerResponse)
async def open_cash_drawer(drawer_data: CashDrawerOpen, current_user: dict = Depends(get_current_user)):
    tenant_filter = get_tenant_filter(current_user)
    # Check if user already has an open drawer
    existing = await db.cash_drawers.find_one({
        "user_id": current_user["id"],
        "status": CashDrawerStatus.OPEN.value,
        **tenant_filter
    })
    if existing:
        raise HTTPException(status_code=400, detail="Arka është tashmë e hapur")
    
    drawer = CashDrawer(
        user_id=current_user["id"],
        branch_id=drawer_data.branch_id or current_user.get("branch_id"),
        opening_balance=drawer_data.opening_balance,
        current_balance=drawer_data.opening_balance,
        expected_balance=drawer_data.opening_balance
    )
    doc = drawer.model_dump()
    doc['opened_at'] = doc['opened_at'].isoformat()
    doc = add_tenant_id(doc, current_user)  # Add tenant_id
    await db.cash_drawers.insert_one(doc)
    await log_audit(current_user["id"], "open_drawer", "cash_drawer", drawer.id)
    
    return CashDrawerResponse(**{**doc, "closed_at": None})

@api_router.get("/cashier/current", response_model=CashDrawerResponse)
async def get_current_drawer(current_user: dict = Depends(get_current_user)):
    tenant_filter = get_tenant_filter(current_user)
    drawer = await db.cash_drawers.find_one({
        "user_id": current_user["id"],
        "status": CashDrawerStatus.OPEN.value,
        **tenant_filter
    }, {"_id": 0})
    if not drawer:
        raise HTTPException(status_code=404, detail="Nuk keni arkë të hapur")
    return CashDrawerResponse(**drawer)

@api_router.post("/cashier/transaction")
async def add_drawer_transaction(transaction: CashDrawerTransaction, current_user: dict = Depends(get_current_user)):
    tenant_filter = get_tenant_filter(current_user)
    drawer = await db.cash_drawers.find_one({
        "user_id": current_user["id"],
        "status": CashDrawerStatus.OPEN.value,
        **tenant_filter
    }, {"_id": 0})
    if not drawer:
        raise HTTPException(status_code=404, detail="Nuk keni arkë të hapur")
    
    new_balance = drawer["current_balance"]
    if transaction.transaction_type == "in":
        new_balance += transaction.amount
    else:
        new_balance -= transaction.amount
    
    trans_record = {
        "amount": transaction.amount,
        "type": transaction.transaction_type,
        "description": transaction.description,
        "timestamp": datetime.now(timezone.utc).isoformat()
    }
    
    await db.cash_drawers.update_one(
        {"id": drawer["id"], **tenant_filter},
        {
            "$set": {"current_balance": new_balance},
            "$push": {"transactions": trans_record}
        }
    )
    
    return {"message": "Transaksioni u regjistrua", "new_balance": new_balance}

class CloseDrawerRequest(BaseModel):
    actual_balance: float

@api_router.post("/cashier/close")
async def close_cash_drawer(request: CloseDrawerRequest, current_user: dict = Depends(get_current_user)):
    tenant_filter = get_tenant_filter(current_user)
    drawer = await db.cash_drawers.find_one({
        "user_id": current_user["id"],
        "status": CashDrawerStatus.OPEN.value,
        **tenant_filter
    }, {"_id": 0})
    if not drawer:
        raise HTTPException(status_code=404, detail="Nuk keni arkë të hapur")
    
    actual_balance = request.actual_balance
    discrepancy = actual_balance - drawer["expected_balance"]
    
    await db.cash_drawers.update_one(
        {"id": drawer["id"], **tenant_filter},
        {"$set": {
            "status": CashDrawerStatus.CLOSED.value,
            "current_balance": actual_balance,
            "closed_at": datetime.now(timezone.utc).isoformat()
        }}
    )
    
    await log_audit(current_user["id"], "close_drawer", "cash_drawer", drawer["id"], {"discrepancy": discrepancy})
    
    return {
        "message": "Arka u mbyll me sukses",
        "expected_balance": drawer["expected_balance"],
        "actual_balance": actual_balance,
        "discrepancy": discrepancy
    }

# ============ SALES ROUTES ============
@api_router.post("/sales", response_model=SaleResponse)
async def create_sale(sale_data: SaleCreate, current_user: dict = Depends(get_current_user)):
    tenant_filter = get_tenant_filter(current_user)
    
    # Get current cash drawer
    drawer = await db.cash_drawers.find_one({
        "user_id": current_user["id"],
        "status": CashDrawerStatus.OPEN.value,
        **tenant_filter
    }, {"_id": 0})
    
    items = []
    subtotal = 0
    total_discount = 0
    total_vat = 0
    
    for item_data in sale_data.items:
        product = await db.products.find_one({"id": item_data.product_id, **tenant_filter}, {"_id": 0})
        if not product:
            raise HTTPException(status_code=404, detail=f"Produkti {item_data.product_id} nuk u gjet")
        
        # Allow selling without stock - no stock check (negative stock allowed)
        
        item_subtotal = item_data.quantity * item_data.unit_price
        item_discount = item_subtotal * (item_data.discount_percent / 100)
        item_after_discount = item_subtotal - item_discount
        item_vat = item_after_discount * (item_data.vat_percent / 100)
        item_total = item_after_discount + item_vat
        
        items.append(SaleItem(
            product_id=item_data.product_id,
            product_name=product.get("name"),
            quantity=item_data.quantity,
            unit_price=item_data.unit_price,
            discount_percent=item_data.discount_percent,
            vat_percent=item_data.vat_percent,
            subtotal=item_subtotal,
            vat_amount=item_vat,
            total=item_total
        ))
        
        subtotal += item_subtotal
        total_discount += item_discount
        total_vat += item_vat
        
        # Update stock (can go negative)
        new_stock = product.get("current_stock", 0) - item_data.quantity
        await db.products.update_one(
            {"id": item_data.product_id, **tenant_filter},
            {"$set": {"current_stock": new_stock, "updated_at": datetime.now(timezone.utc).isoformat()}}
        )
        
        # Create stock movement
        movement = StockMovement(
            product_id=item_data.product_id,
            quantity=item_data.quantity,
            movement_type=StockMovementType.SALE,
            reason="Shitje",
            user_id=current_user["id"],
            branch_id=current_user.get("branch_id")
        )
        mov_doc = movement.model_dump()
        mov_doc['created_at'] = mov_doc['created_at'].isoformat()
        mov_doc = add_tenant_id(mov_doc, current_user)  # Add tenant_id
        await db.stock_movements.insert_one(mov_doc)
    
    grand_total = subtotal - total_discount + total_vat
    change_amount = (sale_data.cash_amount or 0) - grand_total if sale_data.payment_method == PaymentMethod.CASH else 0
    
    receipt_number = await generate_receipt_number(current_user.get("branch_id"), current_user.get("tenant_id"))
    
    sale = Sale(
        receipt_number=receipt_number,
        items=[item.model_dump() for item in items],
        subtotal=round(subtotal, 2),
        total_discount=round(total_discount, 2),
        total_vat=round(total_vat, 2),
        grand_total=round(grand_total, 2),
        payment_method=sale_data.payment_method,
        cash_amount=sale_data.cash_amount or 0,
        bank_amount=sale_data.bank_amount or 0,
        change_amount=round(max(0, change_amount), 2),
        customer_name=sale_data.customer_name,
        notes=sale_data.notes,
        user_id=current_user["id"],
        branch_id=current_user.get("branch_id"),
        cash_drawer_id=drawer["id"] if drawer else None
    )
    
    doc = sale.model_dump()
    doc['created_at'] = doc['created_at'].isoformat()
    doc = add_tenant_id(doc, current_user)  # Add tenant_id
    await db.sales.insert_one(doc)
    
    # Update cash drawer expected balance
    if drawer and sale_data.cash_amount:
        new_expected = drawer["expected_balance"] + sale_data.cash_amount - change_amount
        await db.cash_drawers.update_one(
            {"id": drawer["id"], **tenant_filter},
            {"$set": {"expected_balance": new_expected}}
        )
    
    await log_audit(current_user["id"], "create_sale", "sale", sale.id, {"total": grand_total})
    return SaleResponse(**doc)

@api_router.get("/sales", response_model=List[SaleResponse])
async def get_sales(
    branch_id: Optional[str] = None,
    user_id: Optional[str] = None,
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
    limit: int = 100,
    current_user: dict = Depends(get_current_user)
):
    query = get_tenant_filter(current_user)  # Filter by tenant
    if branch_id:
        query["branch_id"] = branch_id
    if user_id:
        query["user_id"] = user_id
    if start_date:
        query["created_at"] = {"$gte": start_date}
    if end_date:
        query.setdefault("created_at", {})["$lte"] = end_date
    
    sales = await db.sales.find(query, {"_id": 0}).sort("created_at", -1).to_list(limit)
    return [SaleResponse(**s) for s in sales]

@api_router.get("/sales/{sale_id}", response_model=SaleResponse)
async def get_sale(sale_id: str, current_user: dict = Depends(get_current_user)):
    query = {"id": sale_id, **get_tenant_filter(current_user)}
    sale = await db.sales.find_one(query, {"_id": 0})
    if not sale:
        raise HTTPException(status_code=404, detail="Shitja nuk u gjet")
    return SaleResponse(**sale)

# ============ REPORTS ROUTES ============
@api_router.get("/reports/dashboard")
async def get_dashboard_stats(
    branch_id: Optional[str] = None,
    current_user: dict = Depends(get_current_user)
):
    today = datetime.now(timezone.utc).replace(hour=0, minute=0, second=0, microsecond=0).isoformat()
    
    tenant_filter = get_tenant_filter(current_user)
    query = {"created_at": {"$gte": today}, **tenant_filter}
    if branch_id:
        query["branch_id"] = branch_id
    
    # Today's sales
    sales_today = await db.sales.find(query, {"_id": 0}).to_list(10000)
    total_sales = sum(s.get("grand_total", 0) for s in sales_today)
    total_transactions = len(sales_today)
    
    # Low stock products
    low_stock_query = {"current_stock": {"$lt": 10}, **tenant_filter}
    if branch_id:
        low_stock_query["branch_id"] = branch_id
    low_stock_count = await db.products.count_documents(low_stock_query)
    
    # Total products
    product_query = {**tenant_filter}
    if branch_id:
        product_query["branch_id"] = branch_id
    total_products = await db.products.count_documents(product_query)
    
    # Recent sales
    recent_sales = await db.sales.find({**query}, {"_id": 0}).sort("created_at", -1).to_list(10)
    
    return {
        "total_sales_today": round(total_sales, 2),
        "total_transactions_today": total_transactions,
        "low_stock_products": low_stock_count,
        "total_products": total_products,
        "recent_sales": recent_sales
    }

@api_router.get("/reports/sales")
async def get_sales_report(
    start_date: str = Query(...),
    end_date: str = Query(...),
    branch_id: Optional[str] = None,
    user_id: Optional[str] = None,
    current_user: dict = Depends(require_role([UserRole.ADMIN, UserRole.MANAGER]))
):
    tenant_filter = get_tenant_filter(current_user)
    query = {"created_at": {"$gte": start_date, "$lte": end_date}, **tenant_filter}
    if branch_id:
        query["branch_id"] = branch_id
    if user_id:
        query["user_id"] = user_id
    
    sales = await db.sales.find(query, {"_id": 0}).to_list(100000)
    
    total_revenue = sum(s.get("grand_total", 0) for s in sales)
    total_vat = sum(s.get("total_vat", 0) for s in sales)
    total_discount = sum(s.get("total_discount", 0) for s in sales)
    
    # Daily breakdown
    daily_sales = {}
    for sale in sales:
        date = sale["created_at"][:10]
        if date not in daily_sales:
            daily_sales[date] = {"total": 0, "count": 0}
        daily_sales[date]["total"] += sale.get("grand_total", 0)
        daily_sales[date]["count"] += 1
    
    return {
        "period": {"start": start_date, "end": end_date},
        "summary": {
            "total_revenue": round(total_revenue, 2),
            "total_vat": round(total_vat, 2),
            "total_discount": round(total_discount, 2),
            "total_transactions": len(sales)
        },
        "daily_breakdown": [{"date": k, **v} for k, v in sorted(daily_sales.items())]
    }

@api_router.get("/reports/profit-loss")
async def get_profit_loss_report(
    start_date: str = Query(...),
    end_date: str = Query(...),
    branch_id: Optional[str] = None,
    current_user: dict = Depends(require_role([UserRole.ADMIN, UserRole.MANAGER]))
):
    """Calculate profit/loss report based on sales and purchase prices"""
    query = {"created_at": {"$gte": start_date, "$lte": end_date}}
    if branch_id:
        query["branch_id"] = branch_id
    
    sales = await db.sales.find(query, {"_id": 0}).to_list(100000)
    
    total_revenue = 0
    total_cost = 0
    total_vat = 0
    total_discount = 0
    
    # Get product purchase prices
    product_ids = set()
    for sale in sales:
        for item in sale.get("items", []):
            product_ids.add(item.get("product_id"))
    
    products = await db.products.find({"product_id": {"$in": list(product_ids)}}, {"_id": 0}).to_list(100000)
    product_prices = {p["product_id"]: p.get("purchase_price", 0) or 0 for p in products}
    
    # Calculate totals
    for sale in sales:
        total_revenue += sale.get("grand_total", 0)
        total_vat += sale.get("total_vat", 0)
        total_discount += sale.get("total_discount", 0)
        
        for item in sale.get("items", []):
            purchase_price = product_prices.get(item.get("product_id"), 0)
            quantity = item.get("quantity", 0)
            total_cost += purchase_price * quantity
    
    gross_profit = total_revenue - total_cost
    net_profit = gross_profit - total_vat
    profit_margin = (gross_profit / total_revenue * 100) if total_revenue > 0 else 0
    
    # Daily profit breakdown
    daily_profit = {}
    for sale in sales:
        date = sale["created_at"][:10]
        if date not in daily_profit:
            daily_profit[date] = {"revenue": 0, "cost": 0, "profit": 0}
        
        sale_revenue = sale.get("grand_total", 0)
        sale_cost = 0
        for item in sale.get("items", []):
            purchase_price = product_prices.get(item.get("product_id"), 0)
            sale_cost += purchase_price * item.get("quantity", 0)
        
        daily_profit[date]["revenue"] += sale_revenue
        daily_profit[date]["cost"] += sale_cost
        daily_profit[date]["profit"] += sale_revenue - sale_cost
    
    return {
        "period": {"start": start_date, "end": end_date},
        "summary": {
            "total_revenue": round(total_revenue, 2),
            "total_cost": round(total_cost, 2),
            "gross_profit": round(gross_profit, 2),
            "total_vat": round(total_vat, 2),
            "net_profit": round(net_profit, 2),
            "profit_margin": round(profit_margin, 2),
            "total_transactions": len(sales)
        },
        "daily_breakdown": [{"date": k, **v} for k, v in sorted(daily_profit.items())]
    }

@api_router.get("/reports/stock")
async def get_stock_report(
    branch_id: Optional[str] = None,
    category: Optional[str] = None,
    current_user: dict = Depends(require_role([UserRole.ADMIN, UserRole.MANAGER]))
):
    tenant_filter = get_tenant_filter(current_user)
    query = {**tenant_filter}
    if branch_id:
        query["branch_id"] = branch_id
    if category:
        query["category"] = category
    
    products = await db.products.find(query, {"_id": 0}).to_list(100000)
    
    total_value = sum((p.get("current_stock", 0) * (p.get("purchase_price", 0) or 0)) for p in products)
    total_items = sum(p.get("current_stock", 0) for p in products)
    low_stock = [p for p in products if p.get("current_stock", 0) < 10]
    out_of_stock = [p for p in products if p.get("current_stock", 0) <= 0]
    
    return {
        "summary": {
            "total_products": len(products),
            "total_items": total_items,
            "total_value": round(total_value, 2),
            "low_stock_count": len(low_stock),
            "out_of_stock_count": len(out_of_stock)
        },
        "low_stock_products": low_stock[:20],
        "out_of_stock_products": out_of_stock[:20]
    }

@api_router.get("/reports/cashier-performance")
async def get_cashier_performance(
    start_date: str = Query(...),
    end_date: str = Query(...),
    branch_id: Optional[str] = None,
    current_user: dict = Depends(require_role([UserRole.ADMIN, UserRole.MANAGER]))
):
    tenant_filter = get_tenant_filter(current_user)
    query = {"created_at": {"$gte": start_date, "$lte": end_date}, **tenant_filter}
    if branch_id:
        query["branch_id"] = branch_id
    
    sales = await db.sales.find(query, {"_id": 0}).to_list(100000)
    
    # Group by user
    user_stats = {}
    for sale in sales:
        user_id = sale["user_id"]
        if user_id not in user_stats:
            user_stats[user_id] = {"total_sales": 0, "total_transactions": 0, "total_items": 0}
        user_stats[user_id]["total_sales"] += sale.get("grand_total", 0)
        user_stats[user_id]["total_transactions"] += 1
        user_stats[user_id]["total_items"] += sum(item.get("quantity", 0) for item in sale.get("items", []))
    
    # Get user names
    result = []
    for user_id, stats in user_stats.items():
        user = await db.users.find_one({"id": user_id, **tenant_filter}, {"_id": 0, "full_name": 1})
        result.append({
            "user_id": user_id,
            "user_name": user.get("full_name", "Unknown") if user else "Unknown",
            **stats
        })
    
    return sorted(result, key=lambda x: x["total_sales"], reverse=True)

@api_router.get("/reports/export/pdf")
async def export_pdf_report(
    report_type: str = Query(..., description="sales, stock, cashier"),
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
    branch_id: Optional[str] = None,
    current_user: dict = Depends(require_role([UserRole.ADMIN, UserRole.MANAGER]))
):
    buffer = io.BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=A4, topMargin=30, bottomMargin=30)
    elements = []
    styles = getSampleStyleSheet()
    
    # Get company info
    company = await db.settings.find_one({"type": "company"}, {"_id": 0})
    company_name = company.get("company_name", "iPOS") if company else "iPOS"
    
    # Header with company name
    elements.append(Paragraph(f"<b>{company_name}</b>", styles['Heading1']))
    elements.append(Spacer(1, 6))
    
    # Report title and date range
    report_titles = {
        "sales": "Raport Shitjesh",
        "stock": "Raport Stoku",
        "cashier": "Raport Arkëtarësh",
        "profit": "Raport Fitimi/Humbje"
    }
    title = report_titles.get(report_type, f"Raport {report_type.capitalize()}")
    elements.append(Paragraph(f"<b>{title}</b>", styles['Heading2']))
    
    if start_date and end_date:
        elements.append(Paragraph(f"Periudha: {start_date} - {end_date}", styles['Normal']))
    elements.append(Paragraph(f"Gjeneruar: {datetime.now().strftime('%d/%m/%Y %H:%M')}", styles['Normal']))
    elements.append(Spacer(1, 20))
    
    if report_type == "sales" and start_date and end_date:
        tenant_filter = get_tenant_filter(current_user)
        query = {"created_at": {"$gte": start_date, "$lte": end_date + "T23:59:59"}, **tenant_filter}
        if branch_id:
            query["branch_id"] = branch_id
        sales = await db.sales.find(query, {"_id": 0}).sort("created_at", -1).to_list(10000)
        
        # Summary section
        total_sales = sum(s.get("grand_total", 0) for s in sales)
        total_vat = sum(s.get("vat_total", 0) for s in sales)
        cash_sales = sum(s.get("grand_total", 0) for s in sales if s.get("payment_method") == "cash")
        card_sales = sum(s.get("grand_total", 0) for s in sales if s.get("payment_method") in ["card", "bank"])
        
        summary_data = [
            ["PËRMBLEDHJE", ""],
            ["Numri i Transaksioneve", str(len(sales))],
            ["Të Ardhura Totale", f"€{total_sales:.2f}"],
            ["TVSH Total", f"€{total_vat:.2f}"],
            ["Pagesa Cash", f"€{cash_sales:.2f}"],
            ["Pagesa Kartë/Bank", f"€{card_sales:.2f}"],
        ]
        
        summary_table = Table(summary_data, colWidths=[200, 150])
        summary_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#00a79d')),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
            ('ALIGN', (1, 0), (1, -1), 'RIGHT'),
            ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
            ('FONTSIZE', (0, 0), (-1, -1), 10),
        ]))
        elements.append(summary_table)
        elements.append(Spacer(1, 20))
        
        # Sales detail table
        elements.append(Paragraph("<b>Detajet e Shitjeve</b>", styles['Heading3']))
        elements.append(Spacer(1, 10))
        
        data = [["#", "Data", "Nr. Faturës", "Totali", "TVSH", "Metoda"]]
        for i, sale in enumerate(sales, 1):
            data.append([
                str(i),
                sale["created_at"][:10],
                sale.get("receipt_number", "-"),
                f"€{sale.get('grand_total', 0):.2f}",
                f"€{sale.get('vat_total', 0):.2f}",
                sale.get("payment_method", "-")
            ])
        
        if len(data) > 1:
            table = Table(data, colWidths=[30, 80, 100, 80, 60, 80])
            table.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#00a79d')),
                ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
                ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
                ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                ('FONTSIZE', (0, 0), (-1, 0), 10),
                ('FONTSIZE', (0, 1), (-1, -1), 9),
                ('BOTTOMPADDING', (0, 0), (-1, 0), 10),
                ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
                ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.HexColor('#f5f5f5')]),
            ]))
            elements.append(table)
        else:
            elements.append(Paragraph("Nuk ka shitje në këtë periudhë.", styles['Normal']))
    
    elif report_type == "stock":
        tenant_filter = get_tenant_filter(current_user)
        products = await db.products.find(tenant_filter, {"_id": 0}).sort("name", 1).to_list(10000)
        
        # Summary
        total_products = len(products)
        low_stock = len([p for p in products if (p.get("current_stock", 0) or 0) < 10])
        total_value = sum((p.get("current_stock", 0) or 0) * (p.get("purchase_price", 0) or 0) for p in products)
        
        summary_data = [
            ["PËRMBLEDHJE STOKU", ""],
            ["Numri i Produkteve", str(total_products)],
            ["Produkte me Stok të Ulët (<10)", str(low_stock)],
            ["Vlera Totale e Stokut", f"€{total_value:.2f}"],
        ]
        
        summary_table = Table(summary_data, colWidths=[200, 150])
        summary_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#00a79d')),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
        ]))
        elements.append(summary_table)
        elements.append(Spacer(1, 20))
        
        # Stock detail table
        data = [["Emri", "Barkodi", "Stoku", "Ç. Blerjes", "Ç. Shitjes"]]
        for p in products:
            data.append([
                (p.get("name", "-"))[:30],
                p.get("barcode", "-"),
                str(p.get("current_stock", 0) or 0),
                f"€{p.get('purchase_price', 0) or 0:.2f}",
                f"€{p.get('sale_price', 0) or 0:.2f}",
            ])
        
        if len(data) > 1:
            table = Table(data, colWidths=[150, 100, 60, 70, 70])
            table.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#00a79d')),
                ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
                ('ALIGN', (2, 0), (-1, -1), 'RIGHT'),
                ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                ('FONTSIZE', (0, 0), (-1, -1), 9),
                ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
                ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.HexColor('#f5f5f5')]),
            ]))
            elements.append(table)
    
    doc.build(elements)
    buffer.seek(0)
    
    return Response(
        content=buffer.read(),
        media_type="application/pdf",
        headers={"Content-Disposition": f"attachment; filename=raport_{report_type}_{datetime.now().strftime('%Y%m%d')}.pdf"}
    )

@api_router.get("/reports/export/excel")
async def export_excel_report(
    report_type: str = Query(..., description="sales, stock, cashier"),
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
    branch_id: Optional[str] = None,
    current_user: dict = Depends(require_role([UserRole.ADMIN, UserRole.MANAGER]))
):
    buffer = io.BytesIO()
    workbook = xlsxwriter.Workbook(buffer)
    
    # Formats
    title_format = workbook.add_format({'bold': True, 'font_size': 16, 'font_color': '#00a79d'})
    header_format = workbook.add_format({'bold': True, 'bg_color': '#00a79d', 'font_color': 'white', 'border': 1})
    summary_header = workbook.add_format({'bold': True, 'bg_color': '#f0f0f0', 'border': 1})
    summary_value = workbook.add_format({'num_format': '€#,##0.00', 'border': 1})
    money_format = workbook.add_format({'num_format': '€#,##0.00'})
    date_format = workbook.add_format({'num_format': 'dd/mm/yyyy'})
    
    # Get company info
    company = await db.settings.find_one({"type": "company"}, {"_id": 0})
    company_name = company.get("company_name", "iPOS") if company else "iPOS"
    
    if report_type == "sales" and start_date and end_date:
        worksheet = workbook.add_worksheet("Shitjet")
        
        # Title
        worksheet.write(0, 0, company_name, title_format)
        worksheet.write(1, 0, f"Raport Shitjesh: {start_date} - {end_date}")
        worksheet.write(2, 0, f"Gjeneruar: {datetime.now().strftime('%d/%m/%Y %H:%M')}")
        
        # Get data
        tenant_filter = get_tenant_filter(current_user)
        query = {"created_at": {"$gte": start_date, "$lte": end_date + "T23:59:59"}, **tenant_filter}
        if branch_id:
            query["branch_id"] = branch_id
        sales = await db.sales.find(query, {"_id": 0}).sort("created_at", -1).to_list(10000)
        
        # Summary section
        total_sales = sum(s.get("grand_total", 0) for s in sales)
        total_vat = sum(s.get("vat_total", 0) for s in sales)
        cash_sales = sum(s.get("grand_total", 0) for s in sales if s.get("payment_method") == "cash")
        card_sales = sum(s.get("grand_total", 0) for s in sales if s.get("payment_method") in ["card", "bank"])
        
        worksheet.write(4, 0, "PËRMBLEDHJE", summary_header)
        worksheet.write(4, 1, "", summary_header)
        worksheet.write(5, 0, "Numri i Transaksioneve", summary_header)
        worksheet.write(5, 1, len(sales))
        worksheet.write(6, 0, "Të Ardhura Totale", summary_header)
        worksheet.write(6, 1, total_sales, summary_value)
        worksheet.write(7, 0, "TVSH Total", summary_header)
        worksheet.write(7, 1, total_vat, summary_value)
        worksheet.write(8, 0, "Pagesa Cash", summary_header)
        worksheet.write(8, 1, cash_sales, summary_value)
        worksheet.write(9, 0, "Pagesa Kartë/Bank", summary_header)
        worksheet.write(9, 1, card_sales, summary_value)
        
        # Detail headers
        headers = ["#", "Data", "Nr. Faturës", "Nëntotali", "TVSH", "Totali", "Metoda"]
        for col, header in enumerate(headers):
            worksheet.write(11, col, header, header_format)
        
        # Detail data
        for row, sale in enumerate(sales, start=12):
            worksheet.write(row, 0, row - 11)
            worksheet.write(row, 1, sale["created_at"][:10])
            worksheet.write(row, 2, sale.get("receipt_number", "-"))
            worksheet.write(row, 3, sale.get("subtotal", 0), money_format)
            worksheet.write(row, 4, sale.get("vat_total", 0), money_format)
            worksheet.write(row, 5, sale.get("grand_total", 0), money_format)
            worksheet.write(row, 6, sale.get("payment_method", "-"))
        
        # Auto-fit columns
        worksheet.set_column(0, 0, 5)
        worksheet.set_column(1, 1, 12)
        worksheet.set_column(2, 2, 15)
        worksheet.set_column(3, 5, 12)
        worksheet.set_column(6, 6, 10)
    
    elif report_type == "stock":
        worksheet = workbook.add_worksheet("Stoku")
        
        # Title
        worksheet.write(0, 0, company_name, title_format)
        worksheet.write(1, 0, "Raport Stoku")
        worksheet.write(2, 0, f"Gjeneruar: {datetime.now().strftime('%d/%m/%Y %H:%M')}")
        
        # Get data
        tenant_filter = get_tenant_filter(current_user)
        products = await db.products.find(tenant_filter, {"_id": 0}).sort("name", 1).to_list(10000)
        
        # Summary
        total_products = len(products)
        low_stock = len([p for p in products if (p.get("current_stock", 0) or 0) < 10])
        total_value = sum((p.get("current_stock", 0) or 0) * (p.get("purchase_price", 0) or 0) for p in products)
        
        worksheet.write(4, 0, "PËRMBLEDHJE STOKU", summary_header)
        worksheet.write(4, 1, "", summary_header)
        worksheet.write(5, 0, "Numri i Produkteve", summary_header)
        worksheet.write(5, 1, total_products)
        worksheet.write(6, 0, "Stok i Ulët (<10)", summary_header)
        worksheet.write(6, 1, low_stock)
        worksheet.write(7, 0, "Vlera Totale", summary_header)
        worksheet.write(7, 1, total_value, summary_value)
        
        # Headers
        headers = ["Emri", "Barkodi", "Stoku", "Ç. Blerjes", "Ç. Shitjes", "Kategoria", "Vlera Stokut"]
        for col, header in enumerate(headers):
            worksheet.write(9, col, header, header_format)
        
        # Data
        for row, product in enumerate(products, start=10):
            stock = product.get("current_stock", 0) or 0
            purchase = product.get("purchase_price", 0) or 0
            worksheet.write(row, 0, product.get("name", ""))
            worksheet.write(row, 1, product.get("barcode", ""))
            worksheet.write(row, 2, stock)
            worksheet.write(row, 3, purchase, money_format)
            worksheet.write(row, 4, product.get("sale_price", 0) or 0, money_format)
            worksheet.write(row, 5, product.get("category", ""))
            worksheet.write(row, 6, stock * purchase, money_format)
        
        # Auto-fit
        worksheet.set_column(0, 0, 30)
        worksheet.set_column(1, 1, 15)
        worksheet.set_column(2, 6, 12)
    
    workbook.close()
    buffer.seek(0)
    
    return Response(
        content=buffer.read(),
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        headers={"Content-Disposition": f"attachment; filename=raport_{report_type}_{datetime.now().strftime('%Y%m%d')}.xlsx"}
    )

# ============ AUDIT ROUTES ============
@api_router.get("/audit-logs")
async def get_audit_logs(
    user_id: Optional[str] = None,
    action: Optional[str] = None,
    entity_type: Optional[str] = None,
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
    limit: int = 100,
    current_user: dict = Depends(require_role([UserRole.ADMIN]))
):
    query = {}
    if user_id:
        query["user_id"] = user_id
    if action:
        query["action"] = action
    if entity_type:
        query["entity_type"] = entity_type
    if start_date:
        query["created_at"] = {"$gte": start_date}
    if end_date:
        query.setdefault("created_at", {})["$lte"] = end_date
    
    logs = await db.audit_logs.find(query, {"_id": 0}).sort("created_at", -1).to_list(limit)
    return logs

# ============ CATEGORIES ROUTES ============
@api_router.get("/categories")
async def get_categories(current_user: dict = Depends(get_current_user)):
    tenant_filter = get_tenant_filter(current_user)
    products = await db.products.find(tenant_filter, {"_id": 0, "category": 1}).to_list(100000)
    categories = list(set(p.get("category") for p in products if p.get("category")))
    return sorted(categories)

# ============ COMPANY SETTINGS ROUTES ============
@api_router.get("/settings/company")
async def get_company_settings(current_user: dict = Depends(get_current_user)):
    tenant_filter = get_tenant_filter(current_user)
    settings_query = {"type": "company", **tenant_filter} if tenant_filter else {"type": "company"}
    settings = await db.settings.find_one(settings_query, {"_id": 0})
    if not settings:
        # Return default settings
        return CompanySettings().model_dump()
    return settings.get("data", CompanySettings().model_dump())

@api_router.put("/settings/company")
async def update_company_settings(
    settings: CompanySettingsUpdate,
    current_user: dict = Depends(require_role([UserRole.ADMIN]))
):
    tenant_filter = get_tenant_filter(current_user)
    settings_query = {"type": "company", **tenant_filter} if tenant_filter else {"type": "company"}
    
    # Get existing settings or create new
    existing = await db.settings.find_one(settings_query)
    
    if existing:
        current_data = existing.get("data", {})
        # Update only provided fields
        update_data = {k: v for k, v in settings.model_dump().items() if v is not None}
        current_data.update(update_data)
        
        await db.settings.update_one(
            settings_query,
            {"$set": {"data": current_data, "updated_at": datetime.now(timezone.utc).isoformat()}}
        )
    else:
        # Create new settings document
        new_settings = {
            "type": "company",
            "data": settings.model_dump(),
            "created_at": datetime.now(timezone.utc).isoformat(),
            "updated_at": datetime.now(timezone.utc).isoformat()
        }
        new_settings = add_tenant_id(new_settings, current_user)  # Add tenant_id
        await db.settings.insert_one(new_settings)
    
    await log_audit(current_user["id"], "update_settings", "company", "company")
    
    # Return updated settings
    updated = await db.settings.find_one(settings_query, {"_id": 0})
    return updated.get("data", {})

# ============ POS SETTINGS ROUTES ============
@api_router.get("/settings/pos")
async def get_pos_settings(current_user: dict = Depends(get_current_user)):
    tenant_filter = get_tenant_filter(current_user)
    settings_query = {"type": "pos", **tenant_filter} if tenant_filter else {"type": "pos"}
    settings = await db.settings.find_one(settings_query, {"_id": 0})
    if not settings:
        return POSSettings().model_dump()
    return settings.get("data", POSSettings().model_dump())

@api_router.put("/settings/pos")
async def update_pos_settings(
    settings: POSSettingsUpdate,
    current_user: dict = Depends(require_role([UserRole.ADMIN]))
):
    tenant_filter = get_tenant_filter(current_user)
    settings_query = {"type": "pos", **tenant_filter} if tenant_filter else {"type": "pos"}
    existing = await db.settings.find_one(settings_query)
    
    if existing:
        current_data = existing.get("data", {})
        update_data = {k: v for k, v in settings.model_dump().items() if v is not None}
        current_data.update(update_data)
        
        await db.settings.update_one(
            settings_query,
            {"$set": {"data": current_data, "updated_at": datetime.now(timezone.utc).isoformat()}}
        )
    else:
        new_settings = {
            "type": "pos",
            "data": settings.model_dump(),
            "created_at": datetime.now(timezone.utc).isoformat(),
            "updated_at": datetime.now(timezone.utc).isoformat()
        }
        new_settings = add_tenant_id(new_settings, current_user)  # Add tenant_id
        await db.settings.insert_one(new_settings)
    
    await log_audit(current_user["id"], "update_settings", "pos", "pos")
    updated = await db.settings.find_one({"type": "pos"}, {"_id": 0})
    return updated.get("data", {})

# ============ WAREHOUSE (DEPOT) ROUTES ============
@api_router.post("/warehouses", response_model=WarehouseResponse)
async def create_warehouse(
    warehouse: WarehouseCreate,
    current_user: dict = Depends(require_role([UserRole.ADMIN]))
):
    tenant_filter = get_tenant_filter(current_user)
    # If this is set as default, unset other defaults for this tenant
    if warehouse.is_default:
        await db.warehouses.update_many(tenant_filter, {"$set": {"is_default": False}})
    
    new_warehouse = Warehouse(**warehouse.model_dump())
    doc = new_warehouse.model_dump()
    doc['created_at'] = doc['created_at'].isoformat()
    doc = add_tenant_id(doc, current_user)  # Add tenant_id
    await db.warehouses.insert_one(doc)
    
    await log_audit(current_user["id"], "create", "warehouse", new_warehouse.id)
    doc.pop('_id', None)
    return WarehouseResponse(**doc)

@api_router.get("/warehouses", response_model=List[WarehouseResponse])
async def get_warehouses(current_user: dict = Depends(get_current_user)):
    tenant_filter = get_tenant_filter(current_user)
    warehouses = await db.warehouses.find(tenant_filter, {"_id": 0}).to_list(1000)
    return [WarehouseResponse(**w) for w in warehouses]

@api_router.get("/warehouses/{warehouse_id}", response_model=WarehouseResponse)
async def get_warehouse(warehouse_id: str, current_user: dict = Depends(get_current_user)):
    tenant_filter = get_tenant_filter(current_user)
    warehouse = await db.warehouses.find_one({"id": warehouse_id, **tenant_filter}, {"_id": 0})
    if not warehouse:
        raise HTTPException(status_code=404, detail="Depoja nuk u gjet")
    return WarehouseResponse(**warehouse)

@api_router.put("/warehouses/{warehouse_id}", response_model=WarehouseResponse)
async def update_warehouse(
    warehouse_id: str,
    update: WarehouseUpdate,
    current_user: dict = Depends(require_role([UserRole.ADMIN]))
):
    tenant_filter = get_tenant_filter(current_user)
    # If setting as default, unset other defaults for this tenant
    if update.is_default:
        await db.warehouses.update_many({"id": {"$ne": warehouse_id}, **tenant_filter}, {"$set": {"is_default": False}})
    
    update_dict = {k: v for k, v in update.model_dump().items() if v is not None}
    await db.warehouses.update_one({"id": warehouse_id, **tenant_filter}, {"$set": update_dict})
    
    warehouse = await db.warehouses.find_one({"id": warehouse_id, **tenant_filter}, {"_id": 0})
    if not warehouse:
        raise HTTPException(status_code=404, detail="Depoja nuk u gjet")
    
    await log_audit(current_user["id"], "update", "warehouse", warehouse_id)
    return WarehouseResponse(**warehouse)

@api_router.delete("/warehouses/{warehouse_id}")
async def delete_warehouse(
    warehouse_id: str,
    current_user: dict = Depends(require_role([UserRole.ADMIN]))
):
    tenant_filter = get_tenant_filter(current_user)
    result = await db.warehouses.delete_one({"id": warehouse_id, **tenant_filter})
    if result.deleted_count == 0:
        raise HTTPException(status_code=404, detail="Depoja nuk u gjet")
    
    await log_audit(current_user["id"], "delete", "warehouse", warehouse_id)
    return {"message": "Depoja u fshi me sukses"}

# ============ VAT RATES ROUTES ============
@api_router.post("/vat-rates", response_model=VATRateResponse)
async def create_vat_rate(
    vat_rate: VATRateCreate,
    current_user: dict = Depends(require_role([UserRole.ADMIN]))
):
    tenant_filter = get_tenant_filter(current_user)
    # If this is set as default, unset other defaults for this tenant
    if vat_rate.is_default:
        await db.vat_rates.update_many(tenant_filter, {"$set": {"is_default": False}})
    
    new_vat = VATRate(**vat_rate.model_dump())
    doc = new_vat.model_dump()
    doc['created_at'] = doc['created_at'].isoformat()
    doc = add_tenant_id(doc, current_user)  # Add tenant_id
    await db.vat_rates.insert_one(doc)
    
    await log_audit(current_user["id"], "create", "vat_rate", new_vat.id)
    doc.pop('_id', None)
    return VATRateResponse(**doc)

@api_router.get("/vat-rates", response_model=List[VATRateResponse])
async def get_vat_rates(current_user: dict = Depends(get_current_user)):
    tenant_filter = get_tenant_filter(current_user)
    vat_rates = await db.vat_rates.find(tenant_filter, {"_id": 0}).to_list(1000)
    # If no VAT rates exist for this tenant, return default ones
    if not vat_rates:
        tenant_id = current_user.get("tenant_id")
        defaults = [
            {"id": str(uuid.uuid4()), "name": "TVSH Standard", "rate": 18.0, "code": "18", "is_default": True, "is_active": True, "created_at": datetime.now(timezone.utc).isoformat(), "tenant_id": tenant_id},
            {"id": str(uuid.uuid4()), "name": "TVSH Reduktuar", "rate": 8.0, "code": "8", "is_default": False, "is_active": True, "created_at": datetime.now(timezone.utc).isoformat(), "tenant_id": tenant_id},
            {"id": str(uuid.uuid4()), "name": "Pa TVSH", "rate": 0.0, "code": "0", "is_default": False, "is_active": True, "created_at": datetime.now(timezone.utc).isoformat(), "tenant_id": tenant_id},
        ]
        await db.vat_rates.insert_many(defaults)
        return [VATRateResponse(**v) for v in defaults]
    return [VATRateResponse(**v) for v in vat_rates]

@api_router.get("/vat-rates/{vat_id}", response_model=VATRateResponse)
async def get_vat_rate(vat_id: str, current_user: dict = Depends(get_current_user)):
    vat_rate = await db.vat_rates.find_one({"id": vat_id}, {"_id": 0})
    if not vat_rate:
        raise HTTPException(status_code=404, detail="Norma e TVSH nuk u gjet")
    return VATRateResponse(**vat_rate)

@api_router.put("/vat-rates/{vat_id}", response_model=VATRateResponse)
async def update_vat_rate(
    vat_id: str,
    update: VATRateUpdate,
    current_user: dict = Depends(require_role([UserRole.ADMIN]))
):
    tenant_filter = get_tenant_filter(current_user)
    # If setting as default, unset other defaults for this tenant
    if update.is_default:
        await db.vat_rates.update_many({"id": {"$ne": vat_id}, **tenant_filter}, {"$set": {"is_default": False}})
    
    update_dict = {k: v for k, v in update.model_dump().items() if v is not None}
    await db.vat_rates.update_one({"id": vat_id, **tenant_filter}, {"$set": update_dict})
    
    vat_rate = await db.vat_rates.find_one({"id": vat_id, **tenant_filter}, {"_id": 0})
    if not vat_rate:
        raise HTTPException(status_code=404, detail="Norma e TVSH nuk u gjet")
    
    await log_audit(current_user["id"], "update", "vat_rate", vat_id)
    return VATRateResponse(**vat_rate)

@api_router.delete("/vat-rates/{vat_id}")
async def delete_vat_rate(
    vat_id: str,
    current_user: dict = Depends(require_role([UserRole.ADMIN]))
):
    tenant_filter = get_tenant_filter(current_user)
    result = await db.vat_rates.delete_one({"id": vat_id, **tenant_filter})
    if result.deleted_count == 0:
        raise HTTPException(status_code=404, detail="Norma e TVSH nuk u gjet")
    
    await log_audit(current_user["id"], "delete", "vat_rate", vat_id)
    return {"message": "Norma e TVSH u fshi me sukses"}

# ============ COMMENT TEMPLATES ROUTES ============
@api_router.get("/comment-templates", response_model=List[CommentTemplateResponse])
async def get_comment_templates(
    current_user: dict = Depends(get_current_user)
):
    """Get all comment templates for this tenant"""
    tenant_filter = get_tenant_filter(current_user)
    templates = await db.comment_templates.find(tenant_filter, {"_id": 0}).sort("created_at", -1).to_list(100)
    return templates

@api_router.post("/comment-templates", response_model=CommentTemplateResponse)
async def create_comment_template(
    template: CommentTemplateCreate,
    current_user: dict = Depends(require_role([UserRole.ADMIN, UserRole.MANAGER]))
):
    """Create a new comment template"""
    tenant_filter = get_tenant_filter(current_user)
    template_data = template.model_dump()
    template_data["id"] = str(uuid.uuid4())
    template_data["created_at"] = datetime.now(timezone.utc).isoformat()
    template_data["created_by"] = current_user["id"]
    template_data = add_tenant_id(template_data, current_user)  # Add tenant_id
    
    # If this is default, unset other defaults for this tenant
    if template_data.get("is_default"):
        await db.comment_templates.update_many(tenant_filter, {"$set": {"is_default": False}})
    
    await db.comment_templates.insert_one(template_data)
    await log_audit(current_user["id"], "create", "comment_template", template_data["id"])
    
    return CommentTemplateResponse(**template_data)

@api_router.put("/comment-templates/{template_id}", response_model=CommentTemplateResponse)
async def update_comment_template(
    template_id: str,
    template: CommentTemplateUpdate,
    current_user: dict = Depends(require_role([UserRole.ADMIN, UserRole.MANAGER]))
):
    """Update a comment template"""
    tenant_filter = get_tenant_filter(current_user)
    existing = await db.comment_templates.find_one({"id": template_id, **tenant_filter})
    if not existing:
        raise HTTPException(status_code=404, detail="Template nuk u gjet")
    
    update_data = {k: v for k, v in template.model_dump().items() if v is not None}
    
    # If setting as default, unset other defaults for this tenant
    if update_data.get("is_default"):
        await db.comment_templates.update_many({"id": {"$ne": template_id}, **tenant_filter}, {"$set": {"is_default": False}})
    
    await db.comment_templates.update_one({"id": template_id, **tenant_filter}, {"$set": update_data})
    
    updated = await db.comment_templates.find_one({"id": template_id, **tenant_filter}, {"_id": 0})
    await log_audit(current_user["id"], "update", "comment_template", template_id)
    
    return CommentTemplateResponse(**updated)

@api_router.delete("/comment-templates/{template_id}")
async def delete_comment_template(
    template_id: str,
    current_user: dict = Depends(require_role([UserRole.ADMIN, UserRole.MANAGER]))
):
    """Delete a comment template"""
    tenant_filter = get_tenant_filter(current_user)
    result = await db.comment_templates.delete_one({"id": template_id, **tenant_filter})
    if result.deleted_count == 0:
        raise HTTPException(status_code=404, detail="Template nuk u gjet")
    
    await log_audit(current_user["id"], "delete", "comment_template", template_id)
    return {"message": "Template u fshi me sukses"}

# ============ DATA RESET ROUTES ============
@api_router.post("/admin/verify-password")
async def verify_admin_password(
    request: dict,
    current_user: dict = Depends(require_role([UserRole.ADMIN]))
):
    """Verify admin password before allowing reset operations"""
    tenant_filter = get_tenant_filter(current_user)
    password = request.get("password", "")
    
    # Get the admin user with password hash
    admin = await db.users.find_one({"id": current_user["id"], **tenant_filter})
    if not admin:
        raise HTTPException(status_code=404, detail="Përdoruesi nuk u gjet")
    
    if not verify_password(password, admin.get("password_hash", "")):
        raise HTTPException(status_code=401, detail="Fjalëkalimi i gabuar")
    
    return {"verified": True, "message": "Fjalëkalimi u verifikua"}

@api_router.get("/admin/users-for-reset")
async def get_users_for_reset(
    current_user: dict = Depends(require_role([UserRole.ADMIN]))
):
    """Get list of users with their sales statistics for reset selection"""
    tenant_filter = get_tenant_filter(current_user)
    users = await db.users.find(tenant_filter, {"_id": 0, "password_hash": 0, "pin": 0}).to_list(1000)
    
    # Get sales count per user
    user_stats = []
    for user in users:
        # Query by user_id (the field used in sales collection)
        sales_count = await db.sales.count_documents({"user_id": user["id"], **tenant_filter})
        total_sales = 0
        sales = await db.sales.find({"user_id": user["id"], **tenant_filter}, {"grand_total": 1, "_id": 0}).to_list(10000)
        total_sales = sum(s.get("grand_total", 0) for s in sales)
        
        user_stats.append({
            "id": user["id"],
            "username": user["username"],
            "full_name": user.get("full_name", ""),
            "role": user["role"],
            "sales_count": sales_count,
            "total_sales": round(total_sales, 2)
        })
    
    return user_stats

@api_router.post("/admin/reset-data")
async def reset_data(
    request: ResetDataRequest,
    current_user: dict = Depends(require_role([UserRole.ADMIN]))
):
    """Reset sales data based on request parameters"""
    tenant_filter = get_tenant_filter(current_user)
    # Verify admin password first
    admin = await db.users.find_one({"id": current_user["id"], **tenant_filter})
    if not admin or not verify_password(request.admin_password, admin.get("password_hash", "")):
        raise HTTPException(status_code=401, detail="Fjalëkalimi i gabuar")
    
    # Create backup before reset
    backup_id = str(uuid.uuid4())
    backup_data = {
        "id": backup_id,
        "reset_type": request.reset_type,
        "user_ids": request.user_ids,
        "created_by": current_user["id"],
        "created_at": datetime.now(timezone.utc).isoformat(),
        "sales": [],
        "cash_drawers": [],
        "stock_movements": []
    }
    backup_data = add_tenant_id(backup_data, current_user)  # Add tenant_id
    
    deleted_sales = 0
    deleted_movements = 0
    deleted_drawers = 0
    
    if request.reset_type == "daily":
        # Reset only today's data
        today = datetime.now(timezone.utc).replace(hour=0, minute=0, second=0, microsecond=0).isoformat()
        
        # Backup today's sales before deleting
        sales_to_backup = await db.sales.find({"created_at": {"$gte": today}, **tenant_filter}, {"_id": 0}).to_list(10000)
        backup_data["sales"] = sales_to_backup
        
        # Backup today's cash drawers
        drawers_to_backup = await db.cash_drawers.find({"opened_at": {"$gte": today}, **tenant_filter}, {"_id": 0}).to_list(1000)
        backup_data["cash_drawers"] = drawers_to_backup
        
        # Delete today's sales
        result = await db.sales.delete_many({"created_at": {"$gte": today}, **tenant_filter})
        deleted_sales = result.deleted_count
        
        # Close and delete today's cash drawers
        result = await db.cash_drawers.delete_many({"opened_at": {"$gte": today}, **tenant_filter})
        deleted_drawers = result.deleted_count
        
    elif request.reset_type == "user_specific" and request.user_ids:
        # Reset specific users' data
        for user_id in request.user_ids:
            # Backup user's sales
            user_sales = await db.sales.find({"user_id": user_id, **tenant_filter}, {"_id": 0}).to_list(10000)
            backup_data["sales"].extend(user_sales)
            
            # Backup user's cash drawers
            user_drawers = await db.cash_drawers.find({"user_id": user_id, **tenant_filter}, {"_id": 0}).to_list(1000)
            backup_data["cash_drawers"].extend(user_drawers)
            
            # Query by user_id (the field used in sales and cash_drawers collections)
            result = await db.sales.delete_many({"user_id": user_id, **tenant_filter})
            deleted_sales += result.deleted_count
            
            result = await db.cash_drawers.delete_many({"user_id": user_id, **tenant_filter})
            deleted_drawers += result.deleted_count
            
    elif request.reset_type == "all":
        # Backup all data before deleting
        all_sales = await db.sales.find(tenant_filter, {"_id": 0}).to_list(100000)
        backup_data["sales"] = all_sales
        
        all_drawers = await db.cash_drawers.find(tenant_filter, {"_id": 0}).to_list(10000)
        backup_data["cash_drawers"] = all_drawers
        
        all_movements = await db.stock_movements.find(tenant_filter, {"_id": 0}).to_list(100000)
        backup_data["stock_movements"] = all_movements
        
        # Reset all sales data for this tenant
        result = await db.sales.delete_many(tenant_filter)
        deleted_sales = result.deleted_count
        
        result = await db.cash_drawers.delete_many(tenant_filter)
        deleted_drawers = result.deleted_count
        
        # Reset stock movements (optional - keep products but clear movement history)
        result = await db.stock_movements.delete_many(tenant_filter)
        deleted_movements = result.deleted_count
    
    # Save backup to database
    backup_data["deleted_counts"] = {
        "sales": deleted_sales,
        "cash_drawers": deleted_drawers,
        "stock_movements": deleted_movements
    }
    await db.reset_backups.insert_one(backup_data)
    
    # Log the reset action
    await log_audit(
        current_user["id"], 
        "reset_data", 
        "system", 
        request.reset_type,
        {
            "backup_id": backup_id,
            "deleted_sales": deleted_sales,
            "deleted_drawers": deleted_drawers,
            "deleted_movements": deleted_movements,
            "user_ids": request.user_ids,
            "reset_type": request.reset_type
        }
    )
    
    return {
        "success": True,
        "message": "Të dhënat u resetuan me sukses",
        "backup_id": backup_id,
        "deleted": {
            "sales": deleted_sales,
            "cash_drawers": deleted_drawers,
            "stock_movements": deleted_movements
        }
    }

@api_router.get("/admin/backups")
async def get_backups(
    current_user: dict = Depends(require_role([UserRole.ADMIN]))
):
    """Get list of all reset backups for this tenant"""
    tenant_filter = get_tenant_filter(current_user)
    backups = await db.reset_backups.find(tenant_filter, {"_id": 0, "sales": 0, "cash_drawers": 0, "stock_movements": 0}).sort("created_at", -1).to_list(100)
    
    # Enrich with user info
    for backup in backups:
        user = await db.users.find_one({"id": backup.get("created_by"), **tenant_filter}, {"_id": 0, "username": 1, "full_name": 1})
        backup["created_by_name"] = user.get("full_name") or user.get("username") if user else "Unknown"
    
    return backups

@api_router.get("/admin/backups/{backup_id}")
async def get_backup_detail(
    backup_id: str,
    current_user: dict = Depends(require_role([UserRole.ADMIN]))
):
    """Get detailed backup info"""
    tenant_filter = get_tenant_filter(current_user)
    backup = await db.reset_backups.find_one({"id": backup_id, **tenant_filter}, {"_id": 0})
    if not backup:
        raise HTTPException(status_code=404, detail="Backup nuk u gjet")
    return backup

@api_router.post("/admin/backups/{backup_id}/restore")
async def restore_backup(
    backup_id: str,
    request: dict,
    current_user: dict = Depends(require_role([UserRole.ADMIN]))
):
    """Restore data from a backup"""
    tenant_filter = get_tenant_filter(current_user)
    # Verify admin password
    password = request.get("admin_password", "")
    admin = await db.users.find_one({"id": current_user["id"], **tenant_filter})
    if not admin or not verify_password(password, admin.get("password_hash", "")):
        raise HTTPException(status_code=401, detail="Fjalëkalimi i gabuar")
    
    backup = await db.reset_backups.find_one({"id": backup_id, **tenant_filter}, {"_id": 0})
    if not backup:
        raise HTTPException(status_code=404, detail="Backup nuk u gjet")
    
    restored_sales = 0
    restored_drawers = 0
    restored_movements = 0
    
    # Restore sales
    if backup.get("sales"):
        for sale in backup["sales"]:
            # Check if sale already exists
            existing = await db.sales.find_one({"id": sale.get("id"), **tenant_filter})
            if not existing:
                await db.sales.insert_one(sale)
                restored_sales += 1
    
    # Restore cash drawers
    if backup.get("cash_drawers"):
        for drawer in backup["cash_drawers"]:
            existing = await db.cash_drawers.find_one({"id": drawer.get("id"), **tenant_filter})
            if not existing:
                await db.cash_drawers.insert_one(drawer)
                restored_drawers += 1
    
    # Restore stock movements
    if backup.get("stock_movements"):
        for movement in backup["stock_movements"]:
            existing = await db.stock_movements.find_one({"id": movement.get("id"), **tenant_filter})
            if not existing:
                await db.stock_movements.insert_one(movement)
                restored_movements += 1
    
    # Mark backup as restored
    await db.reset_backups.update_one(
        {"id": backup_id, **tenant_filter},
        {"$set": {"restored_at": datetime.now(timezone.utc).isoformat(), "restored_by": current_user["id"]}}
    )
    
    # Log the restore action
    await log_audit(
        current_user["id"],
        "restore_backup",
        "system",
        backup_id,
        {
            "restored_sales": restored_sales,
            "restored_drawers": restored_drawers,
            "restored_movements": restored_movements
        }
    )
    
    return {
        "success": True,
        "message": "Të dhënat u rikthyen me sukses",
        "restored": {
            "sales": restored_sales,
            "cash_drawers": restored_drawers,
            "stock_movements": restored_movements
        }
    }

@api_router.delete("/admin/backups/{backup_id}")
async def delete_backup(
    backup_id: str,
    current_user: dict = Depends(require_role([UserRole.ADMIN]))
):
    """Delete a backup permanently"""
    result = await db.reset_backups.delete_one({"id": backup_id})
    if result.deleted_count == 0:
        raise HTTPException(status_code=404, detail="Backup nuk u gjet")
    
    await log_audit(current_user["id"], "delete_backup", "system", backup_id)
    return {"message": "Backup u fshi me sukses"}

# ============ INIT ROUTES ============
@api_router.post("/init/super-admin")
async def create_super_admin():
    """Create initial Super Admin - can only be done once"""
    existing = await db.users.find_one({"role": UserRole.SUPER_ADMIN})
    if existing:
        return {"message": "Super Admin ekziston tashmë"}
    
    super_admin = {
        "id": str(uuid.uuid4()),
        "username": "superadmin",
        "password_hash": hash_password("super@admin123"),
        "full_name": "Super Administrator",
        "role": UserRole.SUPER_ADMIN,
        "tenant_id": None,  # Super admin has no tenant
        "is_active": True,
        "created_at": datetime.now(timezone.utc).isoformat()
    }
    await db.users.insert_one(super_admin)
    
    return {
        "message": "Super Admin u krijua me sukses",
        "username": "superadmin",
        "password": "super@admin123",
        "note": "Ndryshoni fjalëkalimin menjëherë pas hyrjes!"
    }

@api_router.post("/init/admin")
async def create_initial_admin():
    existing = await db.users.find_one({"role": "admin"})
    if existing:
        return {"message": "Admin ekziston tashmë"}
    
    admin = User(
        username="admin",
        full_name="Administrator",
        role=UserRole.ADMIN,
        is_active=True
    )
    doc = admin.model_dump()
    doc['password_hash'] = hash_password("admin123")
    doc['created_at'] = doc['created_at'].isoformat()
    await db.users.insert_one(doc)
    
    return {"message": "Admin u krijua me sukses", "username": "admin", "password": "admin123"}

@api_router.get("/")
async def root():
    return {"message": "t3next POS API", "version": "1.0.0"}

# Include router
app.include_router(api_router)

app.add_middleware(
    CORSMiddleware,
    allow_credentials=True,
    allow_origins=os.environ.get('CORS_ORIGINS', '*').split(','),
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.on_event("shutdown")
async def shutdown_db_client():
    client.close()
