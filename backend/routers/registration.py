"""Public registration endpoint - No auth required"""
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, EmailStr
from typing import Optional
from datetime import datetime, timezone, timedelta
import uuid
import re

from database import db
from auth import hash_password

router = APIRouter(tags=["Registration"])


class PublicRegistration(BaseModel):
    company_name: str
    full_name: str
    username: str
    email: str
    phone: str
    password: str


class RegistrationResponse(BaseModel):
    success: bool
    message: str
    tenant_id: str
    trial_days: int
    trial_expires: str
    username: str


def generate_subdomain(company_name: str) -> str:
    """Generate URL-friendly subdomain from company name"""
    # Remove special characters, convert to lowercase, replace spaces with empty
    subdomain = re.sub(r'[^a-zA-Z0-9]', '', company_name.lower())
    # Limit length
    subdomain = subdomain[:30] if len(subdomain) > 30 else subdomain
    return subdomain


@router.post("/register", response_model=RegistrationResponse)
async def public_register(data: PublicRegistration):
    """
    Public registration endpoint - creates a new tenant with 30-day trial
    No authentication required
    """
    # Validate username
    if len(data.username) < 3:
        raise HTTPException(status_code=400, detail="Username duhet të ketë të paktën 3 karaktere")
    
    if not re.match(r'^[a-zA-Z0-9_]+$', data.username):
        raise HTTPException(status_code=400, detail="Username mund të përmbajë vetëm shkronja, numra dhe _")
    
    # Check if username already exists
    existing_username = await db.users.find_one({"username": data.username.lower()})
    if existing_username:
        raise HTTPException(status_code=400, detail="Ky username është përdorur tashmë. Ju lutem zgjidhni një tjetër.")
    
    # Validate email format
    if not re.match(r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$', data.email):
        raise HTTPException(status_code=400, detail="Email-i nuk është i vlefshëm")
    
    # Check if email already exists
    existing_email = await db.tenants.find_one({"email": data.email.lower()})
    if existing_email:
        raise HTTPException(status_code=400, detail="Ky email është regjistruar tashmë. Ju lutem kyçuni ose përdorni email tjetër.")
    
    # Generate unique subdomain
    base_subdomain = generate_subdomain(data.company_name)
    subdomain = base_subdomain
    counter = 1
    
    while await db.tenants.find_one({"name": subdomain}):
        subdomain = f"{base_subdomain}{counter}"
        counter += 1
    
    # Calculate trial expiration (30 days from now)
    trial_days = 30
    trial_expires = datetime.now(timezone.utc) + timedelta(days=trial_days)
    
    # Create tenant
    tenant_id = str(uuid.uuid4())
    tenant_data = {
        "id": tenant_id,
        "name": subdomain,  # This is used as subdomain
        "company_name": data.company_name,
        "email": data.email.lower(),
        "phone": data.phone,
        "address": None,
        "city": None,
        "logo_url": None,
        "stamp_url": None,
        "whatsapp_qr_url": None,
        "primary_color": "#00a79d",
        "secondary_color": "#f3f4f6",
        "stripe_payment_link": None,
        "status": "trial",
        "trial_started": datetime.now(timezone.utc).isoformat(),
        "trial_expires": trial_expires.isoformat(),
        "subscription_plan": None,
        "subscription_expires": None,
        "created_at": datetime.now(timezone.utc).isoformat(),
        "created_by": "self_registration"
    }
    
    await db.tenants.insert_one(tenant_data)
    
    # Create admin user for the tenant with provided username
    admin_user = {
        "id": str(uuid.uuid4()),
        "username": data.username.lower(),  # Use provided username
        "password_hash": hash_password(data.password),
        "full_name": data.full_name,
        "role": "admin",
        "tenant_id": tenant_id,
        "is_active": True,
        "created_at": datetime.now(timezone.utc).isoformat()
    }
    await db.users.insert_one(admin_user)
    
    return RegistrationResponse(
        success=True,
        message="Regjistrimi u krye me sukses! Keni 30 ditë provë falas.",
        tenant_id=tenant_id,
        trial_days=trial_days,
        trial_expires=trial_expires.isoformat(),
        username=data.username.lower()
    )


@router.get("/trial-status/{tenant_id}")
async def get_trial_status(tenant_id: str):
    """Get trial status for a tenant"""
    tenant = await db.tenants.find_one({"id": tenant_id}, {"_id": 0})
    
    if not tenant:
        raise HTTPException(status_code=404, detail="Firma nuk u gjet")
    
    trial_expires = tenant.get("trial_expires")
    subscription_expires = tenant.get("subscription_expires")
    status = tenant.get("status", "trial")
    
    # Calculate remaining days
    remaining_days = 0
    is_expired = False
    
    if status == "trial" and trial_expires:
        try:
            expires_dt = datetime.fromisoformat(trial_expires.replace('Z', '+00:00'))
            now = datetime.now(timezone.utc)
            delta = expires_dt - now
            remaining_days = max(0, delta.days)
            is_expired = remaining_days <= 0
        except:
            pass
    elif status == "active" and subscription_expires:
        try:
            expires_dt = datetime.fromisoformat(subscription_expires.replace('Z', '+00:00'))
            now = datetime.now(timezone.utc)
            delta = expires_dt - now
            remaining_days = max(0, delta.days)
            is_expired = remaining_days <= 0
        except:
            pass
    
    return {
        "status": status,
        "trial_expires": trial_expires,
        "subscription_expires": subscription_expires,
        "remaining_days": remaining_days,
        "is_expired": is_expired,
        "subscription_plan": tenant.get("subscription_plan")
    }
