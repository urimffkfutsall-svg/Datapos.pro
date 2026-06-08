"""PhoneSoftware Module - Mobile Repair & Shop Management System"""
from fastapi import APIRouter

from .auth import router as auth_router
from .tenants import router as tenants_router
from .repairs import router as repairs_router
from .customers import router as customers_router
from .inventory import router as inventory_router
from .staff import router as staff_router
from .reports import router as reports_router
from .public import router as public_router

# Main PhoneSoftware router
phonesoftware_router = APIRouter()

# Include all sub-routers
phonesoftware_router.include_router(auth_router)
phonesoftware_router.include_router(tenants_router)
phonesoftware_router.include_router(repairs_router)
phonesoftware_router.include_router(customers_router)
phonesoftware_router.include_router(inventory_router)
phonesoftware_router.include_router(staff_router)
phonesoftware_router.include_router(reports_router)
phonesoftware_router.include_router(public_router)
