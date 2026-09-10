"""Shipping / Posta module API routes.

Covers: per-tenant settings (superadmin managed), shipment CRUD + actions,
shipping dashboard stats, and reports. Public tracking and webhooks live in
routers/shipping_public.py and routers/shipping_webhooks.py respectively so
they can be mounted without the auth dependency used here.
"""
from fastapi import APIRouter, HTTPException, Depends, Query
from typing import List, Optional
from datetime import datetime, timezone
import os

from database import db
from models import UserRole
from auth import get_current_user, get_tenant_filter, add_tenant_id, log_audit

from shipping.models import (
    ShippingSettingsCreate, ShippingSettingsUpdate, ShippingSettingsResponse,
    ShipmentCreate, ShipmentUpdate, ShipmentResponse, Shipment,
    ShipmentTrackingEvent, ShipmentStatus, ShipmentReturnCreate,
)
from shipping.providers import get_provider, ProviderNotSupportedError
from shipping.providers.factory import list_supported_carriers
from shipping.status_mapping import map_carrier_status
from shipping.qr_utils import generate_tracking_token, build_tracking_url, generate_qr_code_base64

router = APIRouter(prefix="/shipping", tags=["Shipping"])
shipments_router = APIRouter(prefix="/shipments", tags=["Shipments"])

PUBLIC_TRACKING_BASE_URL = os.environ.get("PUBLIC_TRACKING_BASE_URL", "https://datapos.pro")


# ============ helpers ============

def _require_permission(current_user: dict, permission: str):
    """SuperAdmin and Admin always pass. Other roles need it explicitly granted
    via current_user['permissions'] (list) -- mirrors existing DataPos pattern
    of role + permission checks used elsewhere in the app."""
    role = current_user.get("role")
    if role in (UserRole.SUPER_ADMIN.value, UserRole.ADMIN.value):
        return
    permissions = current_user.get("permissions") or []
    if permission not in permissions:
        raise HTTPException(status_code=403, detail="Nuk keni leje për këtë veprim (Posta)")


async def _get_settings_doc(tenant_id: str) -> Optional[dict]:
    return await db.shipping_settings.find_one({"tenant_id": tenant_id}, {"_id": 0})


def _mask_settings(doc: dict) -> ShippingSettingsResponse:
    return ShippingSettingsResponse(
        id=doc["id"],
        tenant_id=doc["tenant_id"],
        enabled=doc.get("enabled", False),
        carrier=doc.get("carrier"),
        environment=doc.get("environment", "sandbox"),
        default_service=doc.get("default_service"),
        default_package_type=doc.get("default_package_type"),
        default_sender_name=doc.get("default_sender_name"),
        default_sender_address=doc.get("default_sender_address"),
        default_sender_city=doc.get("default_sender_city"),
        default_sender_country=doc.get("default_sender_country"),
        default_sender_zip=doc.get("default_sender_zip"),
        default_sender_phone=doc.get("default_sender_phone"),
        default_sender_email=doc.get("default_sender_email"),
        has_api_key=bool(doc.get("api_key")),
        has_api_secret=bool(doc.get("api_secret")),
        has_account_number=bool(doc.get("account_number")),
        has_client_id=bool(doc.get("client_id")),
        has_client_secret=bool(doc.get("client_secret")),
        connection_status=doc.get("connection_status"),
        connection_tested_at=doc.get("connection_tested_at"),
        created_at=doc.get("created_at"),
        updated_at=doc.get("updated_at"),
    )


async def _generate_shipment_number(tenant_id: str) -> str:
    today = datetime.now(timezone.utc).strftime("%Y%m%d")
    prefix = f"SHP-{today}"
    count = await db.shipments.count_documents({
        "tenant_id": tenant_id,
        "shipment_number": {"$regex": f"^{prefix}"},
    })
    return f"{prefix}-{str(count + 1).zfill(4)}"


# ============ SETTINGS (SuperAdmin: per-tenant carrier config) ============

@router.get("/settings/{tenant_id}", response_model=ShippingSettingsResponse)
async def get_shipping_settings(tenant_id: str, current_user: dict = Depends(get_current_user)):
    if current_user.get("role") != UserRole.SUPER_ADMIN.value and current_user.get("tenant_id") != tenant_id:
        raise HTTPException(status_code=403, detail="Nuk keni akses te ky konfigurim")
    _require_permission(current_user, "shipping.manage_settings")
    doc = await _get_settings_doc(tenant_id)
    if not doc:
        raise HTTPException(status_code=404, detail="Konfigurimi i Postës nuk ekziston për këtë firmë")
    return _mask_settings(doc)


@router.put("/settings/{tenant_id}", response_model=ShippingSettingsResponse)
async def upsert_shipping_settings(
    tenant_id: str,
    payload: ShippingSettingsUpdate,
    current_user: dict = Depends(get_current_user),
):
    """Create or update a tenant's shipping/carrier configuration.
    Restricted to SuperAdmin (per spec, this is configured at firm creation/edit time).
    Only Admin of the same tenant can also manage it if given shipping.manage_settings.
    """
    if current_user.get("role") != UserRole.SUPER_ADMIN.value and current_user.get("tenant_id") != tenant_id:
        raise HTTPException(status_code=403, detail="Nuk keni akses te ky konfigurim")
    _require_permission(current_user, "shipping.manage_settings")

    now = datetime.now(timezone.utc).isoformat()
    existing = await _get_settings_doc(tenant_id)
    data = payload.model_dump(exclude_unset=True)

    # Never overwrite a stored secret with an empty value coming from a masked form.
    for secret_field in ("api_key", "api_secret", "account_number", "client_id", "client_secret"):
        if secret_field in data and not data[secret_field]:
            data.pop(secret_field)

    if existing:
        data["updated_at"] = now
        data["connection_status"] = None  # config changed -> must re-test
        await db.shipping_settings.update_one({"tenant_id": tenant_id}, {"$set": data})
        doc = await _get_settings_doc(tenant_id)
    else:
        import uuid
        doc = {
            "id": str(uuid.uuid4()),
            "tenant_id": tenant_id,
            "created_at": now,
            "updated_at": now,
            "connection_status": None,
            **data,
        }
        await db.shipping_settings.insert_one(dict(doc))

    await log_audit(current_user["id"], "update_shipping_settings", "shipping_settings", tenant_id)
    return _mask_settings(doc)


@router.post("/settings/{tenant_id}/test-connection")
async def test_shipping_connection(tenant_id: str, current_user: dict = Depends(get_current_user)):
    if current_user.get("role") != UserRole.SUPER_ADMIN.value and current_user.get("tenant_id") != tenant_id:
        raise HTTPException(status_code=403, detail="Nuk keni akses te ky konfigurim")
    _require_permission(current_user, "shipping.manage_settings")

    doc = await _get_settings_doc(tenant_id)
    if not doc or not doc.get("carrier"):
        raise HTTPException(status_code=400, detail="Zgjidhni një kompani postare para se ta testoni lidhjen")

    provider = get_provider(doc["carrier"], doc)
    result = await provider.test_connection()
    await db.shipping_settings.update_one(
        {"tenant_id": tenant_id},
        {"$set": {
            "connection_status": "connected" if result.get("success") else "failed",
            "connection_tested_at": datetime.now(timezone.utc).isoformat(),
        }},
    )
    return result


@router.get("/providers")
async def get_providers():
    """List of shipping providers/carriers DataPos knows how to talk to."""
    return {"providers": list_supported_carriers()}


@router.get("/carriers")
async def get_carriers():
    return {"carriers": list_supported_carriers()}


# ============ DASHBOARD ============

@router.get("/dashboard")
async def shipping_dashboard(current_user: dict = Depends(get_current_user)):
    _require_permission(current_user, "shipping.view")
    tenant_filter = get_tenant_filter(current_user)
    today = datetime.now(timezone.utc).strftime("%Y-%m-%d")

    async def count(extra: dict) -> int:
        return await db.shipments.count_documents({**tenant_filter, **extra})

    total = await count({})
    today_count = await count({"created_at": {"$regex": f"^{today}"}})
    in_transit = await count({"status": ShipmentStatus.IN_TRANSIT.value})
    delivered = await count({"status": ShipmentStatus.DELIVERED.value})
    pending = await count({"status": {"$in": [ShipmentStatus.PENDING_SHIPMENT.value, ShipmentStatus.PENDING_SYNC.value]}})
    failed = await count({"status": ShipmentStatus.DELIVERY_FAILED.value})
    cancelled = await count({"status": ShipmentStatus.CANCELLED.value})
    exception = await count({"status": ShipmentStatus.EXCEPTION.value})
    no_tracking = await count({"tracking_number": None})
    ready_for_pickup = await count({"status": ShipmentStatus.READY_FOR_PICKUP.value})

    return {
        "total_shipments": total,
        "today": today_count,
        "in_transit": in_transit,
        "delivered": delivered,
        "pending": pending,
        "failed": failed,
        "cancelled": cancelled,
        "exception": exception,
        "no_tracking": no_tracking,
        "ready_for_pickup": ready_for_pickup,
    }


# ============ REPORTS ============

@router.get("/reports")
async def shipping_reports(
    current_user: dict = Depends(get_current_user),
    date_from: Optional[str] = None,
    date_to: Optional[str] = None,
    carrier: Optional[str] = None,
):
    _require_permission(current_user, "shipping.view_reports")
    tenant_filter = get_tenant_filter(current_user)
    query: dict = dict(tenant_filter)
    if carrier:
        query["carrier"] = carrier
    if date_from or date_to:
        date_query = {}
        if date_from:
            date_query["$gte"] = date_from
        if date_to:
            date_query["$lte"] = date_to
        query["created_at"] = date_query

    shipments = await db.shipments.find(query, {"_id": 0}).to_list(10000)
    by_carrier: dict = {}
    total_revenue = 0.0
    total_cost = 0.0
    total_cod = 0.0
    delivered_count = 0
    for s in shipments:
        c = s.get("carrier") or "unknown"
        by_carrier.setdefault(c, {"orders": 0, "cost": 0.0})
        by_carrier[c]["orders"] += 1
        by_carrier[c]["cost"] += s.get("shipping_cost") or 0
        total_revenue += s.get("shipping_cost") or 0
        total_cost += s.get("shipping_cost") or 0
        total_cod += s.get("cod_amount") or 0
        if s.get("status") == ShipmentStatus.DELIVERED.value:
            delivered_count += 1

    total = len(shipments)
    return {
        "total_shipments": total,
        "delivered": delivered_count,
        "in_transit": sum(1 for s in shipments if s.get("status") == ShipmentStatus.IN_TRANSIT.value),
        "failed": sum(1 for s in shipments if s.get("status") == ShipmentStatus.DELIVERY_FAILED.value),
        "returned": sum(1 for s in shipments if s.get("status") == ShipmentStatus.RETURNED.value),
        "cancelled": sum(1 for s in shipments if s.get("status") == ShipmentStatus.CANCELLED.value),
        "shipping_revenue": total_revenue,
        "shipping_costs": total_cost,
        "cod_total": total_cod,
        "delivery_success_rate": round((delivered_count / total) * 100, 2) if total else 0,
        "by_carrier": by_carrier,
    }


# ============ SHIPMENTS ============

@shipments_router.get("", response_model=List[ShipmentResponse])
async def list_shipments(
    current_user: dict = Depends(get_current_user),
    status: Optional[str] = None,
    carrier: Optional[str] = None,
    search: Optional[str] = None,
    limit: int = Query(50, le=200),
    skip: int = 0,
):
    _require_permission(current_user, "shipping.view")
    tenant_filter = get_tenant_filter(current_user)
    query: dict = dict(tenant_filter)
    if status:
        query["status"] = status
    if carrier:
        query["carrier"] = carrier
    if search:
        query["$or"] = [
            {"shipment_number": {"$regex": search, "$options": "i"}},
            {"order_id": {"$regex": search, "$options": "i"}},
            {"tracking_number": {"$regex": search, "$options": "i"}},
            {"recipient.first_name": {"$regex": search, "$options": "i"}},
            {"recipient.last_name": {"$regex": search, "$options": "i"}},
        ]
    cursor = db.shipments.find(query, {"_id": 0}).sort("created_at", -1).skip(skip).limit(limit)
    return await cursor.to_list(limit)


@shipments_router.get("/{shipment_id}", response_model=ShipmentResponse)
async def get_shipment(shipment_id: str, current_user: dict = Depends(get_current_user)):
    _require_permission(current_user, "shipping.view")
    tenant_filter = get_tenant_filter(current_user)
    doc = await db.shipments.find_one({"id": shipment_id, **tenant_filter}, {"_id": 0})
    if not doc:
        raise HTTPException(status_code=404, detail="Dërgesa nuk u gjet")
    return doc


@shipments_router.post("", response_model=ShipmentResponse)
async def create_shipment(payload: ShipmentCreate, current_user: dict = Depends(get_current_user)):
    """Create the shipment record and, if possible, immediately send it to the
    carrier. Never fabricates a shipment if the carrier call fails -- it is
    left in PENDING_SHIPMENT for retry instead (see spec section 26/27/28).
    """
    _require_permission(current_user, "shipping.create")
    tenant_id = current_user.get("tenant_id")
    if not tenant_id:
        raise HTTPException(status_code=400, detail="Përdoruesi nuk i përket asnjë firme")

    settings_doc = await _get_settings_doc(tenant_id)
    if not settings_doc or not settings_doc.get("enabled"):
        raise HTTPException(status_code=400, detail="Posta/Shipping nuk është aktivizuar për këtë firmë")

    # Idempotency: company_id + order_id (or explicit idempotency_key) must not double-create.
    idem_key = payload.idempotency_key or (f"{tenant_id}:{payload.order_id}" if payload.order_id else None)
    if idem_key:
        dup = await db.shipments.find_one({"tenant_id": tenant_id, "idempotency_key": idem_key}, {"_id": 0})
        if dup:
            return dup

    carrier = (payload.carrier or settings_doc.get("carrier"))
    if not carrier:
        raise HTTPException(status_code=400, detail="Nuk është zgjedhur asnjë kompani postare")

    shipment_number = await _generate_shipment_number(tenant_id)
    now = datetime.now(timezone.utc).isoformat()

    shipment = Shipment(
        tenant_id=tenant_id,
        branch_id=payload.branch_id,
        order_id=payload.order_id,
        customer_id=payload.customer_id,
        shipment_number=shipment_number,
        carrier=carrier,
        service=payload.service or settings_doc.get("default_service"),
        environment=settings_doc.get("environment", "sandbox"),
        status=ShipmentStatus.PENDING_SHIPMENT,
        recipient=payload.recipient,
        package=payload.package,
        shipping_cost=payload.shipping_cost or 0,
        cod_amount=payload.cod_amount,
        insurance=payload.insurance,
        notes=payload.notes,
        idempotency_key=idem_key,
        created_by=current_user["id"],
        tracking_events=[ShipmentTrackingEvent(status=ShipmentStatus.PENDING_SHIPMENT, description="Porosia dhe dërgesa u krijuan", source="system")],
    )

    provider_config = {
        **settings_doc,
        "default_service": shipment.service,
    }
    provider = get_provider(carrier, provider_config)

    try:
        result = await provider.create_shipment({
            "shipment_number": shipment_number,
            "recipient": payload.recipient.model_dump(),
            "package": payload.package.model_dump() if payload.package else None,
            "service": shipment.service,
            "cod_amount": payload.cod_amount,
            "insurance": payload.insurance,
            "sender": {
                "name": settings_doc.get("default_sender_name"),
                "address": settings_doc.get("default_sender_address"),
                "city": settings_doc.get("default_sender_city"),
                "country": settings_doc.get("default_sender_country"),
                "zip": settings_doc.get("default_sender_zip"),
                "phone": settings_doc.get("default_sender_phone"),
                "email": settings_doc.get("default_sender_email"),
            },
        })
        shipment.tracking_number = result.get("tracking_number")
        shipment.external_shipment_id = result.get("external_shipment_id")
        shipment.label_url = result.get("label_url") if payload.auto_generate_label else None
        shipment.estimated_delivery_date = result.get("estimated_delivery_date")
        shipment.status = ShipmentStatus.LABEL_CREATED if shipment.label_url else ShipmentStatus.CREATED
        shipment.tracking_events.append(ShipmentTrackingEvent(status=shipment.status, description="Dërgesa u pranua nga carrier-i", source="system"))
    except ProviderNotSupportedError as exc:
        raise HTTPException(status_code=422, detail=str(exc))
    except Exception as exc:  # noqa: BLE001 - surfaced as a clear, non-fabricated failure
        shipment.status = ShipmentStatus.PENDING_SHIPMENT
        shipment.last_error = str(exc)
        shipment.tracking_events.append(ShipmentTrackingEvent(status=ShipmentStatus.PENDING_SHIPMENT, description=f"Dështoi krijimi te carrier-i: {exc}", source="system"))

    doc = shipment.model_dump()
    await db.shipments.insert_one(dict(doc))
    await log_audit(current_user["id"], "create_shipment", "shipment", shipment.id, {"carrier": carrier})
    return doc


@shipments_router.put("/{shipment_id}", response_model=ShipmentResponse)
async def update_shipment(shipment_id: str, payload: ShipmentUpdate, current_user: dict = Depends(get_current_user)):
    _require_permission(current_user, "shipping.edit")
    tenant_filter = get_tenant_filter(current_user)
    existing = await db.shipments.find_one({"id": shipment_id, **tenant_filter}, {"_id": 0})
    if not existing:
        raise HTTPException(status_code=404, detail="Dërgesa nuk u gjet")

    update_data = payload.model_dump(exclude_unset=True)
    if "recipient" in update_data and update_data["recipient"] is not None:
        update_data["recipient"] = payload.recipient.model_dump()
    if "package" in update_data and update_data["package"] is not None:
        update_data["package"] = payload.package.model_dump()
    update_data["updated_at"] = datetime.now(timezone.utc).isoformat()

    await db.shipments.update_one({"id": shipment_id, **tenant_filter}, {"$set": update_data})
    await log_audit(current_user["id"], "edit_shipment", "shipment", shipment_id)
    return await db.shipments.find_one({"id": shipment_id, **tenant_filter}, {"_id": 0})


@shipments_router.post("/{shipment_id}/cancel", response_model=ShipmentResponse)
async def cancel_shipment(shipment_id: str, current_user: dict = Depends(get_current_user)):
    _require_permission(current_user, "shipping.cancel")
    tenant_filter = get_tenant_filter(current_user)
    tenant_id = current_user.get("tenant_id")
    shipment = await db.shipments.find_one({"id": shipment_id, **tenant_filter}, {"_id": 0})
    if not shipment:
        raise HTTPException(status_code=404, detail="Dërgesa nuk u gjet")

    settings_doc = await _get_settings_doc(shipment["tenant_id"])
    provider = get_provider(shipment.get("carrier"), settings_doc or {})
    try:
        if shipment.get("external_shipment_id"):
            await provider.cancel_shipment(shipment["external_shipment_id"])
    except ProviderNotSupportedError as exc:
        raise HTTPException(status_code=422, detail=str(exc))

    now = datetime.now(timezone.utc).isoformat()
    event = ShipmentTrackingEvent(status=ShipmentStatus.CANCELLED, description="Dërgesa u anulua", source="manual").model_dump()
    await db.shipments.update_one(
        {"id": shipment_id, **tenant_filter},
        {"$set": {"status": ShipmentStatus.CANCELLED.value, "cancelled_at": now, "updated_at": now}, "$push": {"tracking_events": event}},
    )
    await log_audit(current_user["id"], "cancel_shipment", "shipment", shipment_id)
    return await db.shipments.find_one({"id": shipment_id, **tenant_filter}, {"_id": 0})


@shipments_router.post("/{shipment_id}/return", response_model=ShipmentResponse)
async def create_return(shipment_id: str, payload: ShipmentReturnCreate, current_user: dict = Depends(get_current_user)):
    _require_permission(current_user, "shipping.edit")
    tenant_filter = get_tenant_filter(current_user)
    shipment = await db.shipments.find_one({"id": shipment_id, **tenant_filter}, {"_id": 0})
    if not shipment:
        raise HTTPException(status_code=404, detail="Dërgesa nuk u gjet")

    now = datetime.now(timezone.utc).isoformat()
    event = ShipmentTrackingEvent(
        status=ShipmentStatus.RETURNED,
        description=f"Kthim i kërkuar: {payload.reason.value}" + (f" - {payload.notes}" if payload.notes else ""),
        source="manual",
    ).model_dump()
    await db.shipments.update_one(
        {"id": shipment_id, **tenant_filter},
        {"$set": {"status": ShipmentStatus.RETURNED.value, "updated_at": now}, "$push": {"tracking_events": event}},
    )
    await log_audit(current_user["id"], "create_return", "shipment", shipment_id, {"reason": payload.reason.value})
    return await db.shipments.find_one({"id": shipment_id, **tenant_filter}, {"_id": 0})


@shipments_router.get("/{shipment_id}/tracking")
async def get_shipment_tracking(shipment_id: str, current_user: dict = Depends(get_current_user)):
    """Poll the carrier for the latest tracking status (fallback for carriers
    without webhooks, or for manual refresh)."""
    _require_permission(current_user, "shipping.track")
    tenant_filter = get_tenant_filter(current_user)
    shipment = await db.shipments.find_one({"id": shipment_id, **tenant_filter}, {"_id": 0})
    if not shipment:
        raise HTTPException(status_code=404, detail="Dërgesa nuk u gjet")
    if not shipment.get("tracking_number"):
        return {"status": shipment["status"], "events": shipment.get("tracking_events", [])}

    settings_doc = await _get_settings_doc(shipment["tenant_id"])
    provider = get_provider(shipment.get("carrier"), settings_doc or {})
    try:
        result = await provider.get_tracking(shipment["tracking_number"])
    except ProviderNotSupportedError:
        return {"status": shipment["status"], "events": shipment.get("tracking_events", [])}

    mapped_status = map_carrier_status(shipment.get("carrier"), result.get("carrier_status"))
    if mapped_status.value != shipment["status"]:
        new_event = ShipmentTrackingEvent(
            status=mapped_status, carrier_status_raw=result.get("carrier_status"), source="poll",
        ).model_dump()
        await db.shipments.update_one(
            {"id": shipment_id},
            {"$set": {"status": mapped_status.value, "updated_at": datetime.now(timezone.utc).isoformat()}, "$push": {"tracking_events": new_event}},
        )
    return {"status": mapped_status.value, "carrier_raw": result}


@shipments_router.get("/{shipment_id}/label")
async def get_shipment_label(shipment_id: str, current_user: dict = Depends(get_current_user)):
    _require_permission(current_user, "shipping.print_label")
    tenant_filter = get_tenant_filter(current_user)
    shipment = await db.shipments.find_one({"id": shipment_id, **tenant_filter}, {"_id": 0})
    if not shipment:
        raise HTTPException(status_code=404, detail="Dërgesa nuk u gjet")
    if shipment.get("label_url"):
        return {"label_url": shipment["label_url"]}

    settings_doc = await _get_settings_doc(shipment["tenant_id"])
    provider = get_provider(shipment.get("carrier"), settings_doc or {})
    try:
        result = await provider.generate_label(shipment.get("external_shipment_id"))
    except ProviderNotSupportedError as exc:
        raise HTTPException(status_code=422, detail=str(exc))
    if result.get("label_url"):
        await db.shipments.update_one({"id": shipment_id}, {"$set": {"label_url": result["label_url"]}})
    return result


@shipments_router.get("/{shipment_id}/qr")
async def get_shipment_qr(shipment_id: str, current_user: dict = Depends(get_current_user)):
    _require_permission(current_user, "shipping.print_qr")
    tenant_filter = get_tenant_filter(current_user)
    shipment = await db.shipments.find_one({"id": shipment_id, **tenant_filter}, {"_id": 0})
    if not shipment:
        raise HTTPException(status_code=404, detail="Dërgesa nuk u gjet")
    token = shipment.get("qr_token") or generate_tracking_token()
    url = build_tracking_url(PUBLIC_TRACKING_BASE_URL, token)
    return {"qr_token": token, "tracking_url": url, "qr_code_base64": generate_qr_code_base64(url)}
