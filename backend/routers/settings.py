"""Settings routes (Company, POS, Warehouses, VAT Rates, Comment Templates)"""
from fastapi import APIRouter, HTTPException, Depends
from typing import List
from datetime import datetime, timezone
import uuid
import qrcode
import io
import base64

from database import db
from models import (
    CompanySettings, CompanySettingsUpdate, POSSettings, POSSettingsUpdate,
    WarehouseCreate, WarehouseUpdate, WarehouseResponse, Warehouse,
    VATRateCreate, VATRateUpdate, VATRateResponse, VATRate,
    CommentTemplateCreate, CommentTemplateUpdate, CommentTemplateResponse,
    UserRole
)
from auth import (
    get_current_user, require_role,
    get_tenant_filter, add_tenant_id, log_audit
)

router = APIRouter(prefix="/settings", tags=["Settings"])
warehouses_router = APIRouter(prefix="/warehouses", tags=["Warehouses"])
vat_router = APIRouter(prefix="/vat-rates", tags=["VAT Rates"])
templates_router = APIRouter(prefix="/comment-templates", tags=["Comment Templates"])


def generate_whatsapp_qr(phone: str) -> str:
    """Generate QR code for WhatsApp link as base64 data URL"""
    if not phone:
        return None
    
    # Clean phone number - remove spaces and special chars except +
    clean_phone = ''.join(c for c in phone if c.isdigit() or c == '+')
    if clean_phone.startswith('+'):
        clean_phone = clean_phone[1:]  # Remove + for wa.me link
    
    if not clean_phone:
        return None
    
    # Create WhatsApp link
    whatsapp_url = f"https://wa.me/{clean_phone}"
    
    # Generate QR code
    qr = qrcode.QRCode(
        version=1,
        error_correction=qrcode.constants.ERROR_CORRECT_L,
        box_size=6,
        border=2,
    )
    qr.add_data(whatsapp_url)
    qr.make(fit=True)
    
    # Create image
    img = qr.make_image(fill_color="black", back_color="white")
    
    # Convert to base64
    buffer = io.BytesIO()
    img.save(buffer, format='PNG')
    buffer.seek(0)
    
    img_base64 = base64.b64encode(buffer.getvalue()).decode('utf-8')
    return f"data:image/png;base64,{img_base64}"


# ============ COMPANY SETTINGS ============
@router.get("/company")
async def get_company_settings(current_user: dict = Depends(get_current_user)):
    """Get company settings - pulls from tenant data for tenant users"""
    tenant_id = current_user.get("tenant_id")
    
    # For tenant users, get company info from the tenant record
    if tenant_id:
        tenant = await db.tenants.find_one({"id": tenant_id}, {"_id": 0})
        if tenant:
            return {
                "company_name": tenant.get("company_name") or tenant.get("name", ""),
                "address": tenant.get("address", ""),
                "city": tenant.get("city", ""),
                "postal_code": tenant.get("postal_code", ""),
                "phone": tenant.get("phone", ""),
                "email": tenant.get("email", ""),
                "website": tenant.get("website"),
                "nui": tenant.get("nui", ""),
                "nf": tenant.get("nf", ""),
                "vat_number": tenant.get("vat_number", ""),
                "bank_name": tenant.get("bank_name"),
                "bank_account": tenant.get("bank_account"),
                "logo_url": tenant.get("logo_url", ""),
                "stamp_url": tenant.get("stamp_url", ""),  # Vula digjitale
                "whatsapp_qr_url": tenant.get("whatsapp_qr_url", ""),  # QR code WhatsApp
                "show_warranty_in_pos": tenant.get("show_warranty_in_pos", True)  # Warranty toggle
            }
    
    # Fallback to settings collection for super_admin or legacy data
    tenant_filter = get_tenant_filter(current_user)
    settings_query = {"type": "company", **tenant_filter} if tenant_filter else {"type": "company"}
    settings = await db.settings.find_one(settings_query, {"_id": 0})
    if not settings:
        return CompanySettings().model_dump()
    return settings.get("data", CompanySettings().model_dump())


@router.put("/company")
async def update_company_settings(
    settings: CompanySettingsUpdate,
    current_user: dict = Depends(require_role([UserRole.ADMIN]))
):
    """Update company settings - saves to tenant for tenant users"""
    tenant_id = current_user.get("tenant_id")
    update_data = {k: v for k, v in settings.model_dump().items() if v is not None}
    
    # For tenant users, update the tenant record
    if tenant_id:
        tenant_update = {}
        if "company_name" in update_data:
            tenant_update["company_name"] = update_data["company_name"]
        if "address" in update_data:
            tenant_update["address"] = update_data["address"]
        if "city" in update_data:
            tenant_update["city"] = update_data["city"]
        if "phone" in update_data:
            tenant_update["phone"] = update_data["phone"]
        if "email" in update_data:
            tenant_update["email"] = update_data["email"]
        if "nui" in update_data:
            tenant_update["nui"] = update_data["nui"]
        if "nf" in update_data:
            tenant_update["nf"] = update_data["nf"]
        if "logo_url" in update_data:
            tenant_update["logo_url"] = update_data["logo_url"]
        if "vat_number" in update_data:
            tenant_update["vat_number"] = update_data["vat_number"]
        if "show_warranty_in_pos" in update_data:
            tenant_update["show_warranty_in_pos"] = update_data["show_warranty_in_pos"]
        
        if tenant_update:
            await db.tenants.update_one({"id": tenant_id}, {"$set": tenant_update})
        
        await log_audit(current_user["id"], "update_settings", "company", "company")
        
        # Return updated tenant data
        tenant = await db.tenants.find_one({"id": tenant_id}, {"_id": 0})
        if tenant:
            return {
                "company_name": tenant.get("company_name") or tenant.get("name", ""),
                "address": tenant.get("address", ""),
                "city": tenant.get("city", ""),
                "postal_code": tenant.get("postal_code", ""),
                "phone": tenant.get("phone", ""),
                "email": tenant.get("email", ""),
                "website": tenant.get("website"),
                "nui": tenant.get("nui", ""),
                "nf": tenant.get("nf", ""),
                "vat_number": tenant.get("vat_number", ""),
                "bank_name": tenant.get("bank_name"),
                "bank_account": tenant.get("bank_account"),
                "logo_url": tenant.get("logo_url", ""),
                "stamp_url": tenant.get("stamp_url", ""),  # Vula digjitale
                "whatsapp_qr_url": tenant.get("whatsapp_qr_url", ""),  # QR code WhatsApp
                "show_warranty_in_pos": tenant.get("show_warranty_in_pos", True)  # Warranty toggle
            }
    
    # Fallback to settings collection for super_admin or legacy
    tenant_filter = get_tenant_filter(current_user)
    settings_query = {"type": "company", **tenant_filter} if tenant_filter else {"type": "company"}
    
    existing = await db.settings.find_one(settings_query)
    
    if existing:
        current_data = existing.get("data", {})
        current_data.update(update_data)
        
        await db.settings.update_one(
            settings_query,
            {"$set": {"data": current_data, "updated_at": datetime.now(timezone.utc).isoformat()}}
        )
    else:
        new_settings = {
            "type": "company",
            "data": settings.model_dump(),
            "created_at": datetime.now(timezone.utc).isoformat(),
            "updated_at": datetime.now(timezone.utc).isoformat()
        }
        new_settings = add_tenant_id(new_settings, current_user)
        await db.settings.insert_one(new_settings)
    
    await log_audit(current_user["id"], "update_settings", "company", "company")
    
    updated = await db.settings.find_one(settings_query, {"_id": 0})
    return updated.get("data", {})


# ============ POS SETTINGS ============
@router.get("/pos")
async def get_pos_settings(current_user: dict = Depends(get_current_user)):
    """Get POS settings"""
    tenant_filter = get_tenant_filter(current_user)
    settings_query = {"type": "pos", **tenant_filter} if tenant_filter else {"type": "pos"}
    settings = await db.settings.find_one(settings_query, {"_id": 0})
    if not settings:
        return POSSettings().model_dump()
    return settings.get("data", POSSettings().model_dump())


@router.put("/pos")
async def update_pos_settings(
    settings: POSSettingsUpdate,
    current_user: dict = Depends(require_role([UserRole.ADMIN]))
):
    """Update POS settings"""
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
        new_settings = add_tenant_id(new_settings, current_user)
        await db.settings.insert_one(new_settings)
    
    await log_audit(current_user["id"], "update_settings", "pos", "pos")
    updated = await db.settings.find_one(settings_query, {"_id": 0})
    return updated.get("data", {})


@router.post("/regenerate-whatsapp-qr")
async def regenerate_whatsapp_qr_for_tenant(
    current_user: dict = Depends(require_role([UserRole.ADMIN]))
):
    """Regenerate WhatsApp QR code for current tenant"""
    tenant_id = current_user.get("tenant_id")
    if not tenant_id:
        raise HTTPException(status_code=400, detail="Tenant ID nuk u gjet")
    
    tenant = await db.tenants.find_one({"id": tenant_id})
    if not tenant:
        raise HTTPException(status_code=404, detail="Firma nuk u gjet")
    
    phone = tenant.get("phone")
    if not phone:
        raise HTTPException(status_code=400, detail="Numri i telefonit nuk është konfiguruar. Vendosni numrin e telefonit në cilësimet e kompanisë.")
    
    qr_url = generate_whatsapp_qr(phone)
    await db.tenants.update_one({"id": tenant_id}, {"$set": {"whatsapp_qr_url": qr_url}})
    
    await log_audit(current_user["id"], "regenerate_qr", "tenant", tenant_id)
    
    return {"message": "QR code u ri-gjenerua me sukses", "whatsapp_qr_url": qr_url}


# ============ WAREHOUSES ============
@warehouses_router.post("", response_model=WarehouseResponse)
async def create_warehouse(
    warehouse: WarehouseCreate,
    current_user: dict = Depends(require_role([UserRole.ADMIN]))
):
    """Create a warehouse"""
    tenant_filter = get_tenant_filter(current_user)
    if warehouse.is_default:
        await db.warehouses.update_many(tenant_filter, {"$set": {"is_default": False}})
    
    new_warehouse = Warehouse(**warehouse.model_dump())
    doc = new_warehouse.model_dump()
    doc['created_at'] = doc['created_at'].isoformat()
    doc = add_tenant_id(doc, current_user)
    await db.warehouses.insert_one(doc)
    
    await log_audit(current_user["id"], "create", "warehouse", new_warehouse.id)
    doc.pop('_id', None)
    return WarehouseResponse(**doc)


@warehouses_router.get("", response_model=List[WarehouseResponse])
async def get_warehouses(current_user: dict = Depends(get_current_user)):
    """Get all warehouses"""
    tenant_filter = get_tenant_filter(current_user)
    warehouses = await db.warehouses.find(tenant_filter, {"_id": 0}).to_list(1000)
    return [WarehouseResponse(**w) for w in warehouses]


@warehouses_router.get("/{warehouse_id}", response_model=WarehouseResponse)
async def get_warehouse(warehouse_id: str, current_user: dict = Depends(get_current_user)):
    """Get a warehouse by ID"""
    tenant_filter = get_tenant_filter(current_user)
    warehouse = await db.warehouses.find_one({"id": warehouse_id, **tenant_filter}, {"_id": 0})
    if not warehouse:
        raise HTTPException(status_code=404, detail="Depoja nuk u gjet")
    return WarehouseResponse(**warehouse)


@warehouses_router.put("/{warehouse_id}", response_model=WarehouseResponse)
async def update_warehouse(
    warehouse_id: str,
    update: WarehouseUpdate,
    current_user: dict = Depends(require_role([UserRole.ADMIN]))
):
    """Update a warehouse"""
    tenant_filter = get_tenant_filter(current_user)
    if update.is_default:
        await db.warehouses.update_many({"id": {"$ne": warehouse_id}, **tenant_filter}, {"$set": {"is_default": False}})
    
    update_dict = {k: v for k, v in update.model_dump().items() if v is not None}
    await db.warehouses.update_one({"id": warehouse_id, **tenant_filter}, {"$set": update_dict})
    
    warehouse = await db.warehouses.find_one({"id": warehouse_id, **tenant_filter}, {"_id": 0})
    if not warehouse:
        raise HTTPException(status_code=404, detail="Depoja nuk u gjet")
    
    await log_audit(current_user["id"], "update", "warehouse", warehouse_id)
    return WarehouseResponse(**warehouse)


@warehouses_router.delete("/{warehouse_id}")
async def delete_warehouse(
    warehouse_id: str,
    current_user: dict = Depends(require_role([UserRole.ADMIN]))
):
    """Delete a warehouse"""
    tenant_filter = get_tenant_filter(current_user)
    result = await db.warehouses.delete_one({"id": warehouse_id, **tenant_filter})
    if result.deleted_count == 0:
        raise HTTPException(status_code=404, detail="Depoja nuk u gjet")
    
    await log_audit(current_user["id"], "delete", "warehouse", warehouse_id)
    return {"message": "Depoja u fshi me sukses"}


# ============ VAT RATES ============
@vat_router.post("", response_model=VATRateResponse)
async def create_vat_rate(
    vat_rate: VATRateCreate,
    current_user: dict = Depends(require_role([UserRole.ADMIN]))
):
    """Create a VAT rate"""
    tenant_filter = get_tenant_filter(current_user)
    if vat_rate.is_default:
        await db.vat_rates.update_many(tenant_filter, {"$set": {"is_default": False}})
    
    new_vat = VATRate(**vat_rate.model_dump())
    doc = new_vat.model_dump()
    doc['created_at'] = doc['created_at'].isoformat()
    doc = add_tenant_id(doc, current_user)
    await db.vat_rates.insert_one(doc)
    
    await log_audit(current_user["id"], "create", "vat_rate", new_vat.id)
    doc.pop('_id', None)
    return VATRateResponse(**doc)


@vat_router.get("", response_model=List[VATRateResponse])
async def get_vat_rates(current_user: dict = Depends(get_current_user)):
    """Get all VAT rates"""
    tenant_filter = get_tenant_filter(current_user)
    vat_rates = await db.vat_rates.find(tenant_filter, {"_id": 0}).to_list(1000)
    
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


@vat_router.get("/{vat_id}", response_model=VATRateResponse)
async def get_vat_rate(vat_id: str, current_user: dict = Depends(get_current_user)):
    """Get a VAT rate by ID"""
    tenant_filter = get_tenant_filter(current_user)
    vat_rate = await db.vat_rates.find_one({"id": vat_id, **tenant_filter}, {"_id": 0})
    if not vat_rate:
        raise HTTPException(status_code=404, detail="Norma e TVSH nuk u gjet")
    return VATRateResponse(**vat_rate)


@vat_router.put("/{vat_id}", response_model=VATRateResponse)
async def update_vat_rate(
    vat_id: str,
    update: VATRateUpdate,
    current_user: dict = Depends(require_role([UserRole.ADMIN]))
):
    """Update a VAT rate"""
    tenant_filter = get_tenant_filter(current_user)
    if update.is_default:
        await db.vat_rates.update_many({"id": {"$ne": vat_id}, **tenant_filter}, {"$set": {"is_default": False}})
    
    update_dict = {k: v for k, v in update.model_dump().items() if v is not None}
    await db.vat_rates.update_one({"id": vat_id, **tenant_filter}, {"$set": update_dict})
    
    vat_rate = await db.vat_rates.find_one({"id": vat_id, **tenant_filter}, {"_id": 0})
    if not vat_rate:
        raise HTTPException(status_code=404, detail="Norma e TVSH nuk u gjet")
    
    await log_audit(current_user["id"], "update", "vat_rate", vat_id)
    return VATRateResponse(**vat_rate)


@vat_router.delete("/{vat_id}")
async def delete_vat_rate(
    vat_id: str,
    current_user: dict = Depends(require_role([UserRole.ADMIN]))
):
    """Delete a VAT rate"""
    tenant_filter = get_tenant_filter(current_user)
    result = await db.vat_rates.delete_one({"id": vat_id, **tenant_filter})
    if result.deleted_count == 0:
        raise HTTPException(status_code=404, detail="Norma e TVSH nuk u gjet")
    
    await log_audit(current_user["id"], "delete", "vat_rate", vat_id)
    return {"message": "Norma e TVSH u fshi me sukses"}


# ============ COMMENT TEMPLATES ============
@templates_router.get("", response_model=List[CommentTemplateResponse])
async def get_comment_templates(current_user: dict = Depends(get_current_user)):
    """Get all comment templates"""
    tenant_filter = get_tenant_filter(current_user)
    templates = await db.comment_templates.find(tenant_filter, {"_id": 0}).sort("created_at", -1).to_list(100)
    return templates


@templates_router.post("", response_model=CommentTemplateResponse)
async def create_comment_template(
    template: CommentTemplateCreate,
    current_user: dict = Depends(require_role([UserRole.ADMIN, UserRole.MANAGER]))
):
    """Create a comment template"""
    tenant_filter = get_tenant_filter(current_user)
    template_data = template.model_dump()
    template_data["id"] = str(uuid.uuid4())
    template_data["created_at"] = datetime.now(timezone.utc).isoformat()
    template_data["created_by"] = current_user["id"]
    template_data = add_tenant_id(template_data, current_user)
    
    if template_data.get("is_default"):
        await db.comment_templates.update_many(tenant_filter, {"$set": {"is_default": False}})
    
    await db.comment_templates.insert_one(template_data)
    await log_audit(current_user["id"], "create", "comment_template", template_data["id"])
    
    return CommentTemplateResponse(**template_data)


@templates_router.put("/{template_id}", response_model=CommentTemplateResponse)
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
    
    if update_data.get("is_default"):
        await db.comment_templates.update_many({"id": {"$ne": template_id}, **tenant_filter}, {"$set": {"is_default": False}})
    
    await db.comment_templates.update_one({"id": template_id, **tenant_filter}, {"$set": update_data})
    
    updated = await db.comment_templates.find_one({"id": template_id, **tenant_filter}, {"_id": 0})
    await log_audit(current_user["id"], "update", "comment_template", template_id)
    
    return CommentTemplateResponse(**updated)


@templates_router.delete("/{template_id}")
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
