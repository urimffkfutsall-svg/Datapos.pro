"""File upload routes for logos and stamps"""
from fastapi import APIRouter, HTTPException, Depends, UploadFile, File
from fastapi.responses import JSONResponse
from typing import Optional
from datetime import datetime, timezone
import uuid
import os
import base64
from pathlib import Path

from database import db
from models import UserRole
from auth import get_current_user, get_tenant_filter

router = APIRouter(prefix="/upload", tags=["Upload"])

# Directory for storing uploaded files
UPLOAD_DIR = Path("/app/uploads")
UPLOAD_DIR.mkdir(parents=True, exist_ok=True)

ALLOWED_EXTENSIONS = {'.png', '.jpg', '.jpeg', '.gif', '.webp'}
MAX_FILE_SIZE = 5 * 1024 * 1024  # 5MB


def get_file_extension(filename: str) -> str:
    """Get file extension from filename"""
    return Path(filename).suffix.lower()


def is_valid_image(filename: str) -> bool:
    """Check if file has valid image extension"""
    return get_file_extension(filename) in ALLOWED_EXTENSIONS


@router.post("/logo")
async def upload_logo(
    file: UploadFile = File(...),
    current_user: dict = Depends(get_current_user)
):
    """Upload company logo - returns base64 data URL"""
    if not is_valid_image(file.filename):
        raise HTTPException(status_code=400, detail="Formati i file-it nuk lejohet. Përdorni: PNG, JPG, GIF, WEBP")
    
    contents = await file.read()
    if len(contents) > MAX_FILE_SIZE:
        raise HTTPException(status_code=400, detail="File-i është shumë i madh. Maksimumi: 5MB")
    
    # Convert to base64 data URL
    ext = get_file_extension(file.filename).replace('.', '')
    if ext == 'jpg':
        ext = 'jpeg'
    base64_data = base64.b64encode(contents).decode('utf-8')
    data_url = f"data:image/{ext};base64,{base64_data}"
    
    # Update tenant's logo_url if user is tenant admin
    tenant_id = current_user.get("tenant_id")
    if tenant_id:
        await db.tenants.update_one(
            {"id": tenant_id},
            {"$set": {"logo_url": data_url, "updated_at": datetime.now(timezone.utc).isoformat()}}
        )
    
    return {"url": data_url, "message": "Logo u ngarkua me sukses"}


@router.post("/stamp")
async def upload_stamp(
    file: UploadFile = File(...),
    current_user: dict = Depends(get_current_user)
):
    """Upload company digital stamp (vula digjitale) - returns base64 data URL"""
    if not is_valid_image(file.filename):
        raise HTTPException(status_code=400, detail="Formati i file-it nuk lejohet. Përdorni: PNG, JPG, GIF, WEBP")
    
    contents = await file.read()
    if len(contents) > MAX_FILE_SIZE:
        raise HTTPException(status_code=400, detail="File-i është shumë i madh. Maksimumi: 5MB")
    
    # Convert to base64 data URL
    ext = get_file_extension(file.filename).replace('.', '')
    if ext == 'jpg':
        ext = 'jpeg'
    base64_data = base64.b64encode(contents).decode('utf-8')
    data_url = f"data:image/{ext};base64,{base64_data}"
    
    # Update tenant's stamp_url if user is tenant admin
    tenant_id = current_user.get("tenant_id")
    if tenant_id:
        await db.tenants.update_one(
            {"id": tenant_id},
            {"$set": {"stamp_url": data_url, "updated_at": datetime.now(timezone.utc).isoformat()}}
        )
    
    return {"url": data_url, "message": "Vula digjitale u ngarkua me sukses"}


@router.post("/tenant/{tenant_id}/logo")
async def upload_tenant_logo(
    tenant_id: str,
    file: UploadFile = File(...),
    current_user: dict = Depends(get_current_user)
):
    """Upload logo for a specific tenant - Super Admin only"""
    if current_user.get("role") != UserRole.SUPER_ADMIN and current_user.get("role") != "super_admin":
        raise HTTPException(status_code=403, detail="Vetëm Super Admin mund të ngarkojë logo për firma të tjera")
    
    if not is_valid_image(file.filename):
        raise HTTPException(status_code=400, detail="Formati i file-it nuk lejohet. Përdorni: PNG, JPG, GIF, WEBP")
    
    contents = await file.read()
    if len(contents) > MAX_FILE_SIZE:
        raise HTTPException(status_code=400, detail="File-i është shumë i madh. Maksimumi: 5MB")
    
    # Verify tenant exists
    tenant = await db.tenants.find_one({"id": tenant_id})
    if not tenant:
        raise HTTPException(status_code=404, detail="Firma nuk u gjet")
    
    # Convert to base64 data URL
    ext = get_file_extension(file.filename).replace('.', '')
    if ext == 'jpg':
        ext = 'jpeg'
    base64_data = base64.b64encode(contents).decode('utf-8')
    data_url = f"data:image/{ext};base64,{base64_data}"
    
    await db.tenants.update_one(
        {"id": tenant_id},
        {"$set": {"logo_url": data_url, "updated_at": datetime.now(timezone.utc).isoformat()}}
    )
    
    return {"url": data_url, "message": "Logo u ngarkua me sukses"}


@router.post("/tenant/{tenant_id}/stamp")
async def upload_tenant_stamp(
    tenant_id: str,
    file: UploadFile = File(...),
    current_user: dict = Depends(get_current_user)
):
    """Upload digital stamp for a specific tenant - Super Admin only"""
    if current_user.get("role") != UserRole.SUPER_ADMIN and current_user.get("role") != "super_admin":
        raise HTTPException(status_code=403, detail="Vetëm Super Admin mund të ngarkojë vulën për firma të tjera")
    
    if not is_valid_image(file.filename):
        raise HTTPException(status_code=400, detail="Formati i file-it nuk lejohet. Përdorni: PNG, JPG, GIF, WEBP")
    
    contents = await file.read()
    if len(contents) > MAX_FILE_SIZE:
        raise HTTPException(status_code=400, detail="File-i është shumë i madh. Maksimumi: 5MB")
    
    # Verify tenant exists
    tenant = await db.tenants.find_one({"id": tenant_id})
    if not tenant:
        raise HTTPException(status_code=404, detail="Firma nuk u gjet")
    
    # Convert to base64 data URL
    ext = get_file_extension(file.filename).replace('.', '')
    if ext == 'jpg':
        ext = 'jpeg'
    base64_data = base64.b64encode(contents).decode('utf-8')
    data_url = f"data:image/{ext};base64,{base64_data}"
    
    await db.tenants.update_one(
        {"id": tenant_id},
        {"$set": {"stamp_url": data_url, "updated_at": datetime.now(timezone.utc).isoformat()}}
    )
    
    return {"url": data_url, "message": "Vula digjitale u ngarkua me sukses"}


@router.delete("/tenant/{tenant_id}/stamp")
async def delete_tenant_stamp(
    tenant_id: str,
    current_user: dict = Depends(get_current_user)
):
    """Delete digital stamp for a tenant"""
    # Check if user is super admin or owns this tenant
    if current_user.get("role") != UserRole.SUPER_ADMIN and current_user.get("role") != "super_admin":
        if current_user.get("tenant_id") != tenant_id:
            raise HTTPException(status_code=403, detail="Nuk keni leje për këtë veprim")
    
    tenant = await db.tenants.find_one({"id": tenant_id})
    if not tenant:
        raise HTTPException(status_code=404, detail="Firma nuk u gjet")
    
    await db.tenants.update_one(
        {"id": tenant_id},
        {"$set": {"stamp_url": None, "updated_at": datetime.now(timezone.utc).isoformat()}}
    )
    
    return {"message": "Vula digjitale u fshi me sukses"}
