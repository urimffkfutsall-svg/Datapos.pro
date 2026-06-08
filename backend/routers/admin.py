"""Admin routes (Reset Data, Backups, Audit Logs, Categories, Super Admin Init)"""
from fastapi import APIRouter, HTTPException, Depends, Query
from typing import List, Optional
from datetime import datetime, timezone
import uuid

from database import db
from models import UserRole, ResetDataRequest
from auth import (
    hash_password, verify_password, get_current_user, require_role,
    get_tenant_filter, add_tenant_id, log_audit
)

router = APIRouter(prefix="/admin", tags=["Admin"])
audit_router = APIRouter(prefix="/audit-logs", tags=["Audit"])
categories_router = APIRouter(prefix="/categories", tags=["Categories"])
init_router = APIRouter(prefix="/init", tags=["Init"])


# ============ DATA RESET ============
@router.post("/verify-password")
async def verify_admin_password(
    request: dict,
    current_user: dict = Depends(require_role([UserRole.ADMIN]))
):
    """Verify admin password before reset operations"""
    tenant_filter = get_tenant_filter(current_user)
    password = request.get("password", "")
    
    admin = await db.users.find_one({"id": current_user["id"], **tenant_filter})
    if not admin:
        raise HTTPException(status_code=404, detail="Përdoruesi nuk u gjet")
    
    if not verify_password(password, admin.get("password_hash", "")):
        raise HTTPException(status_code=401, detail="Fjalëkalimi i gabuar")
    
    return {"verified": True, "message": "Fjalëkalimi u verifikua"}


@router.get("/users-for-reset")
async def get_users_for_reset(current_user: dict = Depends(require_role([UserRole.ADMIN]))):
    """Get list of users with sales statistics for reset selection"""
    tenant_filter = get_tenant_filter(current_user)
    users = await db.users.find(tenant_filter, {"_id": 0, "password_hash": 0, "pin": 0}).to_list(1000)
    
    user_stats = []
    for user in users:
        sales_count = await db.sales.count_documents({"user_id": user["id"], **tenant_filter})
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


@router.post("/reset-data")
async def reset_data(request: ResetDataRequest, current_user: dict = Depends(require_role([UserRole.ADMIN]))):
    """Reset sales data based on request parameters"""
    tenant_filter = get_tenant_filter(current_user)
    
    admin = await db.users.find_one({"id": current_user["id"], **tenant_filter})
    if not admin or not verify_password(request.admin_password, admin.get("password_hash", "")):
        raise HTTPException(status_code=401, detail="Fjalëkalimi i gabuar")
    
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
    backup_data = add_tenant_id(backup_data, current_user)
    
    deleted_sales = 0
    deleted_drawers = 0
    deleted_movements = 0
    
    if request.reset_type == "daily":
        today = datetime.now(timezone.utc).replace(hour=0, minute=0, second=0, microsecond=0).isoformat()
        
        sales_to_backup = await db.sales.find({"created_at": {"$gte": today}, **tenant_filter}, {"_id": 0}).to_list(10000)
        backup_data["sales"] = sales_to_backup
        
        drawers_to_backup = await db.cash_drawers.find({"opened_at": {"$gte": today}, **tenant_filter}, {"_id": 0}).to_list(1000)
        backup_data["cash_drawers"] = drawers_to_backup
        
        result = await db.sales.delete_many({"created_at": {"$gte": today}, **tenant_filter})
        deleted_sales = result.deleted_count
        
        result = await db.cash_drawers.delete_many({"opened_at": {"$gte": today}, **tenant_filter})
        deleted_drawers = result.deleted_count
        
    elif request.reset_type == "user_specific" and request.user_ids:
        for user_id in request.user_ids:
            user_sales = await db.sales.find({"user_id": user_id, **tenant_filter}, {"_id": 0}).to_list(10000)
            backup_data["sales"].extend(user_sales)
            
            user_drawers = await db.cash_drawers.find({"user_id": user_id, **tenant_filter}, {"_id": 0}).to_list(1000)
            backup_data["cash_drawers"].extend(user_drawers)
            
            result = await db.sales.delete_many({"user_id": user_id, **tenant_filter})
            deleted_sales += result.deleted_count
            
            result = await db.cash_drawers.delete_many({"user_id": user_id, **tenant_filter})
            deleted_drawers += result.deleted_count
            
    elif request.reset_type == "all":
        all_sales = await db.sales.find(tenant_filter, {"_id": 0}).to_list(100000)
        backup_data["sales"] = all_sales
        
        all_drawers = await db.cash_drawers.find(tenant_filter, {"_id": 0}).to_list(10000)
        backup_data["cash_drawers"] = all_drawers
        
        all_movements = await db.stock_movements.find(tenant_filter, {"_id": 0}).to_list(100000)
        backup_data["stock_movements"] = all_movements
        
        result = await db.sales.delete_many(tenant_filter)
        deleted_sales = result.deleted_count
        
        result = await db.cash_drawers.delete_many(tenant_filter)
        deleted_drawers = result.deleted_count
        
        result = await db.stock_movements.delete_many(tenant_filter)
        deleted_movements = result.deleted_count
    
    backup_data["deleted_counts"] = {
        "sales": deleted_sales,
        "cash_drawers": deleted_drawers,
        "stock_movements": deleted_movements
    }
    await db.reset_backups.insert_one(backup_data)
    
    await log_audit(current_user["id"], "reset_data", "system", request.reset_type, {
        "backup_id": backup_id,
        "deleted_sales": deleted_sales,
        "deleted_drawers": deleted_drawers,
        "deleted_movements": deleted_movements
    })
    
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


# ============ BACKUPS ============
@router.get("/backups")
async def get_backups(current_user: dict = Depends(require_role([UserRole.ADMIN]))):
    """Get list of all reset backups"""
    tenant_filter = get_tenant_filter(current_user)
    backups = await db.reset_backups.find(tenant_filter, {"_id": 0, "sales": 0, "cash_drawers": 0, "stock_movements": 0}).sort("created_at", -1).to_list(100)
    
    for backup in backups:
        user = await db.users.find_one({"id": backup.get("created_by"), **tenant_filter}, {"_id": 0, "username": 1, "full_name": 1})
        backup["created_by_name"] = user.get("full_name") or user.get("username") if user else "Unknown"
    
    return backups


@router.get("/backups/{backup_id}")
async def get_backup_detail(backup_id: str, current_user: dict = Depends(require_role([UserRole.ADMIN]))):
    """Get detailed backup info"""
    tenant_filter = get_tenant_filter(current_user)
    backup = await db.reset_backups.find_one({"id": backup_id, **tenant_filter}, {"_id": 0})
    if not backup:
        raise HTTPException(status_code=404, detail="Backup nuk u gjet")
    return backup


@router.post("/backups/{backup_id}/restore")
async def restore_backup(backup_id: str, request: dict, current_user: dict = Depends(require_role([UserRole.ADMIN]))):
    """Restore data from a backup"""
    tenant_filter = get_tenant_filter(current_user)
    
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
    
    if backup.get("sales"):
        for sale in backup["sales"]:
            existing = await db.sales.find_one({"id": sale.get("id"), **tenant_filter})
            if not existing:
                await db.sales.insert_one(sale)
                restored_sales += 1
    
    if backup.get("cash_drawers"):
        for drawer in backup["cash_drawers"]:
            existing = await db.cash_drawers.find_one({"id": drawer.get("id"), **tenant_filter})
            if not existing:
                await db.cash_drawers.insert_one(drawer)
                restored_drawers += 1
    
    if backup.get("stock_movements"):
        for movement in backup["stock_movements"]:
            existing = await db.stock_movements.find_one({"id": movement.get("id"), **tenant_filter})
            if not existing:
                await db.stock_movements.insert_one(movement)
                restored_movements += 1
    
    await db.reset_backups.update_one(
        {"id": backup_id, **tenant_filter},
        {"$set": {"restored_at": datetime.now(timezone.utc).isoformat(), "restored_by": current_user["id"]}}
    )
    
    await log_audit(current_user["id"], "restore_backup", "system", backup_id, {
        "restored_sales": restored_sales,
        "restored_drawers": restored_drawers,
        "restored_movements": restored_movements
    })
    
    return {
        "success": True,
        "message": "Të dhënat u rikthyen me sukses",
        "restored": {
            "sales": restored_sales,
            "cash_drawers": restored_drawers,
            "stock_movements": restored_movements
        }
    }


@router.delete("/backups/{backup_id}")
async def delete_backup(backup_id: str, current_user: dict = Depends(require_role([UserRole.ADMIN]))):
    """Delete a backup"""
    tenant_filter = get_tenant_filter(current_user)
    result = await db.reset_backups.delete_one({"id": backup_id, **tenant_filter})
    if result.deleted_count == 0:
        raise HTTPException(status_code=404, detail="Backup nuk u gjet")
    
    await log_audit(current_user["id"], "delete_backup", "system", backup_id)
    return {"message": "Backup u fshi me sukses"}


# ============ AUDIT LOGS ============
@audit_router.get("")
async def get_audit_logs(
    entity_type: Optional[str] = None,
    action: Optional[str] = None,
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
    limit: int = 100,
    current_user: dict = Depends(require_role([UserRole.ADMIN]))
):
    """Get audit logs"""
    query = {}
    if entity_type:
        query["entity_type"] = entity_type
    if action:
        query["action"] = action
    if start_date:
        query["created_at"] = {"$gte": start_date}
    if end_date:
        query.setdefault("created_at", {})["$lte"] = end_date
    
    logs = await db.audit_logs.find(query, {"_id": 0}).sort("created_at", -1).to_list(limit)
    return logs


# ============ CATEGORIES ============
@categories_router.get("")
async def get_categories(current_user: dict = Depends(get_current_user)):
    """Get product categories"""
    tenant_filter = get_tenant_filter(current_user)
    products = await db.products.find(tenant_filter, {"_id": 0, "category": 1}).to_list(100000)
    categories = list(set(p.get("category") for p in products if p.get("category")))
    return sorted(categories)


# ============ SUPER ADMIN INIT ============
@init_router.post("/super-admin")
async def init_super_admin():
    """Initialize or reset super admin user - can be called anytime"""
    existing = await db.users.find_one({"role": "super_admin"})
    
    new_username = "urimi1806"
    new_password = "1806"
    password_hash = hash_password(new_password)
    
    if existing:
        # Update existing super admin with new credentials
        await db.users.update_one(
            {"role": "super_admin"},
            {"$set": {
                "username": new_username,
                "password_hash": password_hash,
                "is_active": True
            }}
        )
        return {"message": "Super Admin u përditësua me sukses", "username": new_username, "password": new_password}
    
    # Create new super admin
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
    
    return {"message": "Super Admin u krijua me sukses", "username": new_username, "password": new_password}


@init_router.get("/super-admin")
async def init_super_admin_get():
    """Initialize super admin via GET request (easier to call from browser)"""
    existing = await db.users.find_one({"role": "super_admin"})
    
    new_username = "urimi1806"
    new_password = "1806"
    password_hash = hash_password(new_password)
    
    if existing:
        await db.users.update_one(
            {"role": "super_admin"},
            {"$set": {
                "username": new_username,
                "password_hash": password_hash,
                "is_active": True
            }}
        )
        return {"message": "Super Admin u përditësua me sukses", "username": new_username, "password": new_password}
    
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
    
    return {"message": "Super Admin u krijua me sukses", "username": new_username, "password": new_password}
