"""
MobilshopurimiPOS - Multi-Tenant SaaS POS System
Main FastAPI Application Entry Point
"""
from fastapi import FastAPI
from starlette.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
import logging

# Import routers
from routers import auth, tenants, users, branches, products, stock, cashier, sales, reports, upload, registration, coupons
from routers import ai_assistant
from routers.settings import router as settings_router, warehouses_router, vat_router, templates_router
from routers.admin import router as admin_router, audit_router, categories_router, init_router
from routers.warranties import router as warranties_router

# Import Mobilshop routers
from routers.mobilshop import products as mobilshop_products
from routers.mobilshop import customers as mobilshop_customers
from routers.mobilshop import repairs as mobilshop_repairs
from routers.mobilshop import sales as mobilshop_sales
from routers.mobilshop import reports as mobilshop_reports
from routers.mobilshop import cash_drawer as mobilshop_cash_drawer

# Import PhoneSoftware routers
from routers.phonesoftware import phonesoftware_router

# Import BookPRO routers
from routers.bookpro import bookpro_router

# Import HealthPRO routers
from routers.healthpro.auth import router as hp_auth_router
from routers.healthpro.residents import router as hp_residents_router
from routers.healthpro.checkups import router as hp_checkups_router
from routers.healthpro.therapies import router as hp_therapies_router
from routers.healthpro.visits import router as hp_visits_router
from routers.healthpro.employees import router as hp_employees_router
from routers.healthpro.dashboard import router as hp_dashboard_router
from routers.healthpro.overtime import router as hp_overtime_router
from routers.healthpro.visitors import router as hp_visitors_router
from routers.healthpro.notifications import router as hp_notifications_router

from database import db
from auth import hash_password

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


async def init_super_admin():
    """Initialize or update super admin on startup"""
    try:
        new_username = "urimi1806"
        new_password = "1806"
        password_hash = hash_password(new_password)
        
        existing = await db.users.find_one({"role": "super_admin"})
        
        if existing:
            # Update existing super admin
            await db.users.update_one(
                {"role": "super_admin"},
                {"$set": {
                    "username": new_username,
                    "password_hash": password_hash,
                    "is_active": True
                }}
            )
            logger.info(f"Super Admin updated: {new_username}")
        else:
            # Create new super admin
            import uuid
            from datetime import datetime, timezone
            super_admin = {
                "id": str(uuid.uuid4()),
                "username": new_username,
                "password_hash": password_hash,
                "full_name": "Super Administrator",
                "role": "super_admin",
                "is_active": True,
                "tenant_id": None,
                "created_at": datetime.now(timezone.utc).isoformat()
            }
            await db.users.insert_one(super_admin)
            logger.info(f"Super Admin created: {new_username}")
    except Exception as e:
        logger.error(f"Error initializing super admin: {e}")


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Lifespan context manager for startup/shutdown events"""
    # Startup
    logger.info("Starting MobilshopurimiPOS API...")
    await init_super_admin()
    yield
    # Shutdown
    logger.info("Shutting down MobilshopurimiPOS API...")


# Create the main app
app = FastAPI(
    title="MobilshopurimiPOS API",
    description="Multi-Tenant SaaS Point of Sale System",
    version="2.0.0",
    lifespan=lifespan
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Register routers with /api prefix
app.include_router(auth.router, prefix="/api")
app.include_router(tenants.router, prefix="/api")
app.include_router(users.router, prefix="/api")
app.include_router(branches.router, prefix="/api")
app.include_router(products.router, prefix="/api")
app.include_router(stock.router, prefix="/api")
app.include_router(cashier.router, prefix="/api")
app.include_router(sales.router, prefix="/api")
app.include_router(reports.router, prefix="/api")
app.include_router(settings_router, prefix="/api")
app.include_router(warehouses_router, prefix="/api")
app.include_router(vat_router, prefix="/api")
app.include_router(templates_router, prefix="/api")
app.include_router(admin_router, prefix="/api")
app.include_router(audit_router, prefix="/api")
app.include_router(categories_router, prefix="/api")
app.include_router(init_router, prefix="/api")
app.include_router(upload.router, prefix="/api")
app.include_router(registration.router, prefix="/api")
app.include_router(coupons.router, prefix="/api")
app.include_router(ai_assistant.router, prefix="/api")
app.include_router(warranties_router, prefix="/api")

# Mobilshop routers
app.include_router(mobilshop_products.router, prefix="/api")
app.include_router(mobilshop_customers.router, prefix="/api")
app.include_router(mobilshop_repairs.router, prefix="/api")
app.include_router(mobilshop_sales.router, prefix="/api")
app.include_router(mobilshop_reports.router, prefix="/api")
app.include_router(mobilshop_cash_drawer.router, prefix="/api")

# PhoneSoftware routers
app.include_router(phonesoftware_router, prefix="/api")

# BookPRO routers (Salon Management)
app.include_router(bookpro_router, prefix="/api")

# HealthPRO routers (Healthcare Institute Management)
# HealthPRO routers (Healthcare Institute Management)
app.include_router(hp_auth_router, prefix="/api")
app.include_router(hp_residents_router, prefix="/api")
app.include_router(hp_checkups_router, prefix="/api")
app.include_router(hp_therapies_router, prefix="/api")
app.include_router(hp_visits_router, prefix="/api")
app.include_router(hp_employees_router, prefix="/api")
app.include_router(hp_dashboard_router, prefix="/api")
app.include_router(hp_overtime_router, prefix="/api")
app.include_router(hp_visitors_router, prefix="/api")
app.include_router(hp_notifications_router, prefix="/api")


@app.get("/")
async def root():
    """Root endpoint"""
    return {
        "name": "MobilshopurimiPOS API",
        "version": "2.0.0",
        "status": "running",
        "docs": "/docs"
    }


@app.get("/health")
async def health():
    """Health check endpoint for Kubernetes"""
    return {"status": "healthy"}


@app.get("/api/health")
async def health_check():
    """Health check endpoint"""
    return {"status": "healthy"}
