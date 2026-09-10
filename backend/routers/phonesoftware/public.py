"""PhoneSoftware Public Routes - Status checking for customers"""
from fastapi import APIRouter, HTTPException, Request
from fastapi.responses import Response
from datetime import datetime, timezone
import qrcode
import io
import base64
import os

from .database import ps_repairs, ps_tenants

router = APIRouter(prefix="/phonesoftware/public", tags=["PhoneSoftware Public"])


def get_status_label_albanian(status: str) -> str:
    """Get Albanian status label"""
    labels = {
        'received': 'Pranuar në servis',
        'in_progress': 'Në proces',
        'completed': 'I rregulluar',
        'cannot_repair': 'Nuk rregullohet',
        'delivered': 'Dorëzuar'
    }
    return labels.get(status, status)


def get_base_url(request: Request = None) -> str:
    """Get the base URL for QR codes - works with any deployment"""
    # First try environment variable (set during deployment)
    env_url = os.environ.get('FRONTEND_URL') or os.environ.get('REACT_APP_BACKEND_URL')
    if env_url:
        # Remove /api suffix if present
        base = env_url.replace('/api', '').rstrip('/')
        return base
    
    # Fallback: construct from request
    if request:
        # Get the origin from headers or construct from request
        origin = request.headers.get('origin')
        if origin:
            return origin
        
        # Construct from request URL
        scheme = request.headers.get('x-forwarded-proto', 'https')
        host = request.headers.get('x-forwarded-host') or request.headers.get('host', '')
        if host:
            return f"{scheme}://{host}"
    
    # Last resort fallback
    return "https://localhost:3000"


@router.get("/repair-status/{ticket_number}")
async def get_public_repair_status(ticket_number: str):
    """Get repair status by ticket number - PUBLIC endpoint for customers"""
    repair = await ps_repairs.find_one(
        {"ticket_number": ticket_number}, 
        {"_id": 0, "customer_id": 0, "technician_id": 0, "created_by": 0, 
         "diagnosis": 0, "repair_notes": 0, "parts_used": 0, "labor_cost": 0, 
         "parts_cost": 0}
    )
    
    if not repair:
        raise HTTPException(status_code=404, detail="Riparimi nuk u gjet")
    
    # Get tenant info for branding
    tenant = await ps_tenants.find_one(
        {"id": repair.get("tenant_id")}, 
        {"_id": 0, "company_name": 1, "phone": 1, "address": 1, "city": 1, 
         "logo_url": 1, "primary_color": 1}
    )
    
    # Build device name
    brand = repair.get("brand", "") or ""
    model = repair.get("model", "") or ""
    device_name = f"{brand} {model}".strip() or "Pajisje"
    
    return {
        "ticket_number": repair.get("ticket_number"),
        "status": repair.get("status"),
        "status_label": get_status_label_albanian(repair.get("status", "")),
        "device": device_name,
        "brand": brand,
        "model": model,
        "device_type": repair.get("device_type", "phone"),
        "color": repair.get("color"),
        "imei": repair.get("imei"),
        "problem": repair.get("problem_description"),
        "customer_name": repair.get("customer_name"),
        "accessories_received": repair.get("accessories_received", []),
        "created_at": repair.get("created_at"),
        "estimated_cost": repair.get("estimated_cost"),
        "total_cost": repair.get("total_cost") if repair.get("status") in ["completed", "delivered"] else None,
        "warranty_months": repair.get("warranty_months"),
        "warranty_expires": repair.get("warranty_expires") if repair.get("status") == "delivered" else None,
        "completed_at": repair.get("completed_at"),
        "delivered_at": repair.get("delivered_at"),
        "shop": {
            "name": tenant.get("company_name") if tenant else "PhoneSoftware",
            "phone": tenant.get("phone"),
            "address": f"{tenant.get('address', '')} {tenant.get('city', '')}".strip() if tenant else None,
            "logo": tenant.get("logo_url"),
            "color": tenant.get("primary_color", "#00a79d")
        }
    }


@router.get("/qr/{ticket_number}")
async def generate_qr_code(ticket_number: str, request: Request, size: int = 200):
    """Generate QR code image for a repair ticket"""
    # Verify repair exists
    repair = await ps_repairs.find_one({"ticket_number": ticket_number})
    if not repair:
        raise HTTPException(status_code=404, detail="Riparimi nuk u gjet")
    
    # Generate QR code URL - dynamic based on deployment
    base_url = get_base_url(request)
    status_url = f"{base_url}/#/repair-status/{ticket_number}"
    
    # Create QR code
    qr = qrcode.QRCode(
        version=1,
        error_correction=qrcode.constants.ERROR_CORRECT_M,
        box_size=10,
        border=2,
    )
    qr.add_data(status_url)
    qr.make(fit=True)
    
    # Create image
    img = qr.make_image(fill_color="black", back_color="white")
    
    # Resize to requested size
    img = img.resize((size, size))
    
    # Convert to bytes
    img_byte_arr = io.BytesIO()
    img.save(img_byte_arr, format='PNG')
    img_byte_arr.seek(0)
    
    return Response(content=img_byte_arr.getvalue(), media_type="image/png")


@router.get("/qr-base64/{ticket_number}")
async def generate_qr_code_base64(ticket_number: str, request: Request, size: int = 150):
    """Generate QR code as base64 string for embedding in receipts"""
    # Verify repair exists
    repair = await ps_repairs.find_one({"ticket_number": ticket_number})
    if not repair:
        raise HTTPException(status_code=404, detail="Riparimi nuk u gjet")
    
    # Generate QR code URL - dynamic based on deployment
    base_url = get_base_url(request)
    status_url = f"{base_url}/#/repair-status/{ticket_number}"
    
    # Create QR code
    qr = qrcode.QRCode(
        version=1,
        error_correction=qrcode.constants.ERROR_CORRECT_M,
        box_size=8,
        border=2,
    )
    qr.add_data(status_url)
    qr.make(fit=True)
    
    img = qr.make_image(fill_color="black", back_color="white")
    img = img.resize((size, size))
    
    # Convert to base64
    img_byte_arr = io.BytesIO()
    img.save(img_byte_arr, format='PNG')
    img_byte_arr.seek(0)
    base64_str = base64.b64encode(img_byte_arr.getvalue()).decode('utf-8')
    
    return {
        "qr_code": f"data:image/png;base64,{base64_str}",
        "status_url": status_url,
        "ticket_number": ticket_number
    }


@router.get("/receipt-data/{ticket_number}")
async def get_receipt_data(ticket_number: str, request: Request):
    """Get all data needed to print a repair receipt/coupon"""
    repair = await ps_repairs.find_one(
        {"ticket_number": ticket_number}, 
        {"_id": 0}
    )
    
    if not repair:
        raise HTTPException(status_code=404, detail="Riparimi nuk u gjet")
    
    # Get tenant info
    tenant = await ps_tenants.find_one(
        {"id": repair.get("tenant_id")}, 
        {"_id": 0}
    )
    
    # Generate QR code - dynamic URL
    base_url = get_base_url(request)
    status_url = f"{base_url}/#/repair-status/{ticket_number}"
    
    qr = qrcode.QRCode(version=1, error_correction=qrcode.constants.ERROR_CORRECT_M, box_size=8, border=2)
    qr.add_data(status_url)
    qr.make(fit=True)
    img = qr.make_image(fill_color="black", back_color="white")
    img = img.resize((150, 150))
    
    img_byte_arr = io.BytesIO()
    img.save(img_byte_arr, format='PNG')
    img_byte_arr.seek(0)
    qr_base64 = base64.b64encode(img_byte_arr.getvalue()).decode('utf-8')
    
    return {
        "ticket_number": repair.get("ticket_number"),
        "status": repair.get("status"),
        "status_label": get_status_label_albanian(repair.get("status", "")),
        "customer_name": repair.get("customer_name"),
        "customer_phone": repair.get("customer_phone"),
        "device_type": repair.get("device_type"),
        "brand": repair.get("brand"),
        "model": repair.get("model"),
        "color": repair.get("color"),
        "imei": repair.get("imei"),
        "problem_description": repair.get("problem_description"),
        "customer_notes": repair.get("customer_notes"),
        "accessories_received": repair.get("accessories_received", []),
        "estimated_cost": repair.get("estimated_cost"),
        "warranty_months": repair.get("warranty_months"),
        "created_at": repair.get("created_at"),
        "qr_code": f"data:image/png;base64,{qr_base64}",
        "status_url": status_url,
        "shop": {
            "name": tenant.get("company_name") if tenant else "PhoneSoftware",
            "phone": tenant.get("phone") if tenant else None,
            "email": tenant.get("email") if tenant else None,
            "address": tenant.get("address") if tenant else None,
            "city": tenant.get("city") if tenant else None,
            "logo_url": tenant.get("logo_url") if tenant else None,
            "primary_color": tenant.get("primary_color", "#00a79d") if tenant else "#00a79d",
            "nui": tenant.get("nui") if tenant else None,
            "nf": tenant.get("nf") if tenant else None
        }
    }
