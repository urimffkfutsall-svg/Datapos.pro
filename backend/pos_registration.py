"""One-operation administrator PIN approval. Never issues an admin session."""
import hmac
import math
import time
import uuid
from datetime import datetime, timezone
from fastapi import HTTPException
from pydantic import BaseModel, Field, ConfigDict
from database import db
from models import ProductCreate, Product, ProductResponse
from auth import log_audit

class ApprovedProductRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")
    product: ProductCreate
    admin_pin: str = Field(min_length=4, max_length=12, pattern=r"^[0-9]+$")

async def register_approved_product(request: ApprovedProductRequest, current_user: dict):
    tenant = current_user.get("tenant_id")
    if not tenant or current_user.get("role") not in ("cashier", "manager", "admin"):
        raise HTTPException(403, "Regjistrimi kërkon llogari të kësaj firme")
    p = request.product
    if not p.name or not p.name.strip() or len(p.name.strip()) > 200:
        raise HTTPException(422, "Emri i produktit është i detyrueshëm (maksimum 200 shkronja)")
    if not p.barcode or not p.barcode.strip() or len(p.barcode.strip()) > 128:
        raise HTTPException(422, "Barkodi është i detyrueshëm (maksimum 128 shenja)")
    for key in ("sale_price", "purchase_price", "vat_rate"):
        value = getattr(p, key)
        if value is None or not math.isfinite(value) or value < 0 or value > (100 if key == "vat_rate" else 999999999):
            raise HTTPException(422, "Çmimet dhe TVSH-ja duhet të jenë numra të vlefshëm, jo negativë")
    if p.initial_stock not in (0, None):
        raise HTTPException(422, "Stokun fillestar vendoseni nga faqja e produkteve")
    branch = current_user.get("branch_id")
    if p.branch_id and p.branch_id != branch:
        raise HTTPException(403, "Nuk mund të regjistroni për një degë tjetër")
    # Atomic, shared-database attempt counters survive workers/restarts. No PIN stored.
    now = int(time.time()); bucket = now // 300
    await db.pos_pin_attempts.delete_many({"expires_at": {"$lt": now}})
    counters = [f"pos-pin:{tenant}:{current_user['id']}:{bucket}", f"pos-pin:{tenant}:all:{bucket}"]
    for key, limit in zip(counters, (5, 60)):
        await db.pos_pin_attempts.update_one({"_id": key}, {"$inc": {"attempts": 1}, "$setOnInsert": {"expires_at": (bucket + 2) * 300}}, upsert=True)
        row = await db.pos_pin_attempts.find_one({"_id": key})
        if row.get("attempts", 0) > limit:
            raise HTTPException(429, "Shumë tentativa. Provoni përsëri pas 5 minutash.")
    admins = await db.users.find({"tenant_id": tenant, "role": "admin", "is_active": {"$ne": False}}, {"_id": 0}).to_list(1000)
    approvers = [a for a in admins if isinstance(a.get("pin"), str) and hmac.compare_digest(a["pin"], request.admin_pin)]
    if len(approvers) != 1:
        # Ambiguous PINs fail closed too; assign distinct PINs to administrators.
        raise HTTPException(422, "PIN-i nuk i përket një administratori aktiv të kësaj firme, ose është i dyfishuar")
    for key in counters:
        await db.pos_pin_attempts.update_one({"_id": key}, {"$inc": {"attempts": -1}})
    barcode = p.barcode.strip()
    if await db.products.find_one({"tenant_id": tenant, "barcode": barcode}):
        raise HTTPException(409, "Ky barkod është regjistruar tashmë. Skanoni përsëri.")
    product = Product(**{**p.model_dump(), "name": p.name.strip(), "barcode": barcode, "branch_id": branch})
    doc = product.model_dump();doc.update(tenant_id=tenant, current_stock=0)
    for key in ("created_at", "updated_at"):doc[key] = doc[key].isoformat()
    # Mongo _id uniqueness protects concurrent registrations through this endpoint.
    doc["_id"] = "pos-product:" + str(uuid.uuid5(uuid.NAMESPACE_URL, tenant + ":" + barcode))
    result = await db.products.update_one({"_id": doc["_id"]}, {"$setOnInsert": doc}, upsert=True)
    if not result.upserted_id:
        raise HTTPException(409, "Ky barkod është regjistruar tashmë. Skanoni përsëri.")
    await log_audit(current_user["id"], "pos_register_product_admin_approved", "product", product.id,
                    {"tenant_id": tenant, "approved_by": approvers[0]["id"]})
    return ProductResponse(**doc)
