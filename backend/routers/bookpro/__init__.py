"""BookPRO Router Initialization"""
from fastapi import APIRouter
from .auth import router as auth_router
from .tenants import router as tenants_router
from .services import router as services_router
from .clients import router as clients_router
from .staff import router as staff_router
from .appointments import router as appointments_router
from .dashboard import router as dashboard_router
from .public import router as public_router

# Main BookPRO router
bookpro_router = APIRouter()

# Include all sub-routers
bookpro_router.include_router(auth_router)
bookpro_router.include_router(tenants_router)
bookpro_router.include_router(services_router)
bookpro_router.include_router(clients_router)
bookpro_router.include_router(staff_router)
bookpro_router.include_router(appointments_router)
bookpro_router.include_router(dashboard_router)
bookpro_router.include_router(public_router)
