from fastapi import APIRouter, HTTPException, Depends
from typing import List, Optional
from datetime import datetime, timezone
import uuid

from database import db
from models import (
    Coupon, CouponCreate, CouponUpdate,
    CouponValidateRequest, CouponValidateResponse,
)
from auth import get_current_user, get_tenant_filter, add_tenant_id, log_audit

router = APIRouter(prefix="/coupons", tags=["coupons"])


def _normalize_code(code: str) -> str:
    return code.strip().upper()


def _strip_doc(doc):
    if not doc:
        return doc
    doc.pop("_id", None)
    return doc


@router.post("", response_model=Coupon)
async def create_coupon(data: CouponCreate, user=Depends(get_current_user)):
    if data.discount_type not in ("percent", "fixed"):
        raise HTTPException(status_code=400, detail="discount_type duhet 'percent' ose 'fixed'")
    if data.discount_type == "percent" and data.discount_value > 100:
        raise HTTPException(status_code=400, detail="Perqindja s'mund te kaloje 100")

    code = _normalize_code(data.code)
    tenant_filter = get_tenant_filter(user)
    existing = await db.coupons.find_one({**tenant_filter, "code": code})
    if existing:
        raise HTTPException(status_code=400, detail=f"Kodi '{code}' ekziston tashme")

    now = datetime.now(timezone.utc)
    coupon_doc = {
        "id": str(uuid.uuid4()),
        "code": code,
        "name": data.name,
        "discount_type": data.discount_type,
        "discount_value": data.discount_value,
        "active": data.active,
        "valid_from": data.valid_from,
        "valid_until": data.valid_until,
        "max_uses": data.max_uses,
        "min_purchase_amount": data.min_purchase_amount,
        "used_count": 0,
        "created_at": now,
        "updated_at": now,
    }
    coupon_doc = add_tenant_id(coupon_doc, user)
    await db.coupons.insert_one(coupon_doc)
    try:
        await log_audit(user, "create", "coupon", coupon_doc["id"], {"code": code})
    except Exception:
        pass
    return Coupon(**_strip_doc(coupon_doc))


@router.get("", response_model=List[Coupon])
async def list_coupons(active_only: bool = False, user=Depends(get_current_user)):
    tenant_filter = get_tenant_filter(user)
    q = dict(tenant_filter)
    if active_only:
        q["active"] = True
    cursor = db.coupons.find(q).sort("created_at", -1)
    items = []
    async for doc in cursor:
        items.append(Coupon(**_strip_doc(doc)))
    return items


@router.get("/{coupon_id}", response_model=Coupon)
async def get_coupon(coupon_id: str, user=Depends(get_current_user)):
    tenant_filter = get_tenant_filter(user)
    doc = await db.coupons.find_one({**tenant_filter, "id": coupon_id})
    if not doc:
        raise HTTPException(status_code=404, detail="Kuponi s'u gjet")
    return Coupon(**_strip_doc(doc))


@router.put("/{coupon_id}", response_model=Coupon)
async def update_coupon(coupon_id: str, data: CouponUpdate, user=Depends(get_current_user)):
    tenant_filter = get_tenant_filter(user)
    existing = await db.coupons.find_one({**tenant_filter, "id": coupon_id})
    if not existing:
        raise HTTPException(status_code=404, detail="Kuponi s'u gjet")

    update_doc = {}
    for field in ["name", "discount_type", "discount_value", "active",
                  "valid_from", "valid_until", "max_uses", "min_purchase_amount"]:
        val = getattr(data, field, None)
        if val is not None:
            update_doc[field] = val

    if data.code is not None:
        new_code = _normalize_code(data.code)
        if new_code != existing.get("code"):
            conflict = await db.coupons.find_one({**tenant_filter, "code": new_code})
            if conflict:
                raise HTTPException(status_code=400, detail=f"Kodi '{new_code}' eshte i zene")
            update_doc["code"] = new_code

    if "discount_type" in update_doc and update_doc["discount_type"] not in ("percent", "fixed"):
        raise HTTPException(status_code=400, detail="discount_type duhet 'percent' ose 'fixed'")
    if update_doc.get("discount_type") == "percent" and update_doc.get("discount_value", 0) > 100:
        raise HTTPException(status_code=400, detail="Perqindja s'mund te kaloje 100")

    update_doc["updated_at"] = datetime.now(timezone.utc)
    await db.coupons.update_one({**tenant_filter, "id": coupon_id}, {"$set": update_doc})
    try:
        await log_audit(user, "update", "coupon", coupon_id, update_doc)
    except Exception:
        pass

    doc = await db.coupons.find_one({**tenant_filter, "id": coupon_id})
    return Coupon(**_strip_doc(doc))


@router.delete("/{coupon_id}")
async def delete_coupon(coupon_id: str, user=Depends(get_current_user)):
    tenant_filter = get_tenant_filter(user)
    result = await db.coupons.delete_one({**tenant_filter, "id": coupon_id})
    if result.deleted_count == 0:
        raise HTTPException(status_code=404, detail="Kuponi s'u gjet")
    try:
        await log_audit(user, "delete", "coupon", coupon_id, {})
    except Exception:
        pass
    return {"ok": True, "deleted": coupon_id}


@router.post("/validate", response_model=CouponValidateResponse)
async def validate_coupon(data: CouponValidateRequest, user=Depends(get_current_user)):
    code = _normalize_code(data.code)
    tenant_filter = get_tenant_filter(user)
    doc = await db.coupons.find_one({**tenant_filter, "code": code})

    if not doc:
        return CouponValidateResponse(valid=False, error=f"Kodi '{code}' nuk u gjet")

    if not doc.get("active", True):
        return CouponValidateResponse(valid=False, code=code, error="Kuponi nuk eshte aktiv")

    now = datetime.now(timezone.utc)

    def _to_dt(v):
        if v is None:
            return None
        if isinstance(v, str):
            v = datetime.fromisoformat(v.replace("Z", "+00:00"))
        if v.tzinfo is None:
            v = v.replace(tzinfo=timezone.utc)
        return v

    vf = _to_dt(doc.get("valid_from"))
    vu = _to_dt(doc.get("valid_until"))

    if vf and now < vf:
        return CouponValidateResponse(valid=False, code=code, error="Kuponi nuk eshte aktiv ende")
    if vu and now > vu:
        return CouponValidateResponse(valid=False, code=code, error="Kuponi ka skaduar")

    max_uses = doc.get("max_uses")
    used_count = doc.get("used_count", 0)
    if max_uses is not None and used_count >= max_uses:
        return CouponValidateResponse(valid=False, code=code, error="Kuponi ka arritur limitin e perdorimit")

    min_purchase = doc.get("min_purchase_amount")
    subtotal = float(data.subtotal or 0)
    if min_purchase is not None and subtotal < float(min_purchase):
        return CouponValidateResponse(
            valid=False, code=code,
            error=f"Shuma minimale per kete kupon eshte {float(min_purchase):.2f} EUR"
        )

    discount_type = doc.get("discount_type", "percent")
    discount_value = float(doc.get("discount_value", 0))

    if discount_type == "percent":
        discount_amount = subtotal * (discount_value / 100.0) if subtotal else 0.0
    else:
        discount_amount = min(discount_value, subtotal) if subtotal else discount_value

    return CouponValidateResponse(
        valid=True,
        code=code,
        name=doc.get("name"),
        discount_type=discount_type,
        discount_value=discount_value,
        discount_amount=round(discount_amount, 2),
    )