"""Pydantic models for the Shipping / Posta module.

All shipping data is namespaced by tenant_id so that multi-tenant isolation
is enforced the same way as the rest of DataPos.pro (see auth.get_tenant_filter).
"""
from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any
from datetime import datetime, timezone
from enum import Enum
import uuid


# ============ ENUMS ============

class ShippingCarrier(str, Enum):
    DHL = "dhl"
    FEDEX = "fedex"
    UPS = "ups"
    DPD = "dpd"
    GLS = "gls"
    LOCAL = "local"
    CUSTOM = "custom"


class ShippingEnvironment(str, Enum):
    SANDBOX = "sandbox"
    PRODUCTION = "production"


class FulfillmentMethod(str, Enum):
    STORE_PICKUP = "store_pickup"
    SHIPPING = "shipping"


class ShipmentStatus(str, Enum):
    """Internal, carrier-agnostic status. Carrier statuses are mapped to this
    via shipping.status_mapping.map_carrier_status()."""
    PENDING_SHIPMENT = "pending_shipment"      # order created, shipment not yet sent to carrier
    PENDING_SYNC = "pending_sync"              # created offline, waiting to sync
    CREATED = "created"
    LABEL_CREATED = "label_created"
    READY_FOR_PICKUP = "ready_for_pickup"
    PICKED_UP = "picked_up"
    IN_TRANSIT = "in_transit"
    ARRIVED_AT_DESTINATION = "arrived_at_destination"
    OUT_FOR_DELIVERY = "out_for_delivery"
    DELIVERED = "delivered"
    DELIVERY_FAILED = "delivery_failed"
    RETURNED = "returned"
    CANCELLED = "cancelled"
    EXCEPTION = "exception"


class ReturnReason(str, Enum):
    CUSTOMER_CHANGED_MIND = "customer_changed_mind"
    WRONG_PRODUCT = "wrong_product"
    DAMAGED = "damaged"
    OTHER = "other"


# ============ SHIPPING SETTINGS (per-company / tenant) ============

class ShippingSettingsBase(BaseModel):
    enabled: bool = False
    carrier: Optional[ShippingCarrier] = None
    environment: ShippingEnvironment = ShippingEnvironment.SANDBOX
    default_service: Optional[str] = None
    default_package_type: Optional[str] = None
    default_sender_name: Optional[str] = None
    default_sender_address: Optional[str] = None
    default_sender_city: Optional[str] = None
    default_sender_country: Optional[str] = None
    default_sender_zip: Optional[str] = None
    default_sender_phone: Optional[str] = None
    default_sender_email: Optional[str] = None


class ShippingSettingsCreate(ShippingSettingsBase):
    """Credentials are accepted on write only. They are never returned in full
    by GET endpoints -- see ShippingSettingsResponse which masks them."""
    api_key: Optional[str] = None
    api_secret: Optional[str] = None
    account_number: Optional[str] = None
    client_id: Optional[str] = None
    client_secret: Optional[str] = None


class ShippingSettingsUpdate(ShippingSettingsCreate):
    pass


class ShippingSettingsResponse(ShippingSettingsBase):
    id: str
    tenant_id: str
    has_api_key: bool = False
    has_api_secret: bool = False
    has_account_number: bool = False
    has_client_id: bool = False
    has_client_secret: bool = False
    connection_status: Optional[str] = None  # "connected" | "failed" | None (untested)
    connection_tested_at: Optional[str] = None
    created_at: str
    updated_at: str


# ============ ADDRESS ============

class ShippingAddress(BaseModel):
    first_name: str
    last_name: Optional[str] = None
    company: Optional[str] = None
    phone: Optional[str] = None
    email: Optional[str] = None
    address_line1: str
    address_line2: Optional[str] = None
    city: str
    state: Optional[str] = None
    country: str
    zip_code: Optional[str] = None
    notes_for_courier: Optional[str] = None


# ============ SHIPMENT ============

class ShipmentPackage(BaseModel):
    weight_kg: Optional[float] = None
    length_cm: Optional[float] = None
    width_cm: Optional[float] = None
    height_cm: Optional[float] = None
    quantity: int = 1


class ShipmentCreate(BaseModel):
    order_id: Optional[str] = None
    customer_id: Optional[str] = None
    branch_id: Optional[str] = None
    recipient: ShippingAddress
    carrier: Optional[ShippingCarrier] = None   # falls back to tenant default
    service: Optional[str] = None
    package_type: Optional[str] = None
    package: Optional[ShipmentPackage] = None
    shipping_cost: Optional[float] = 0
    cod_amount: Optional[float] = None
    insurance: bool = False
    notes: Optional[str] = None
    auto_generate_label: bool = True
    auto_generate_qr: bool = True
    idempotency_key: Optional[str] = None


class ShipmentUpdate(BaseModel):
    recipient: Optional[ShippingAddress] = None
    service: Optional[str] = None
    package: Optional[ShipmentPackage] = None
    shipping_cost: Optional[float] = None
    cod_amount: Optional[float] = None
    insurance: Optional[bool] = None
    notes: Optional[str] = None
    status: Optional[ShipmentStatus] = None


class ShipmentTrackingEvent(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    status: ShipmentStatus
    carrier_status_raw: Optional[str] = None
    description: Optional[str] = None
    location: Optional[str] = None
    occurred_at: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    source: str = "system"  # "system" | "webhook" | "manual" | "poll"


class Shipment(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    tenant_id: str
    branch_id: Optional[str] = None
    order_id: Optional[str] = None
    customer_id: Optional[str] = None
    shipment_number: str
    carrier: Optional[ShippingCarrier] = None
    service: Optional[str] = None
    environment: ShippingEnvironment = ShippingEnvironment.SANDBOX
    status: ShipmentStatus = ShipmentStatus.PENDING_SHIPMENT
    recipient: ShippingAddress
    package: Optional[ShipmentPackage] = None
    shipping_cost: float = 0
    cod_amount: Optional[float] = None
    insurance: bool = False
    notes: Optional[str] = None
    tracking_number: Optional[str] = None
    external_shipment_id: Optional[str] = None
    label_url: Optional[str] = None
    label_format: Optional[str] = None
    qr_token: str = Field(default_factory=lambda: uuid.uuid4().hex)
    idempotency_key: Optional[str] = None
    estimated_delivery_date: Optional[str] = None
    tracking_events: List[ShipmentTrackingEvent] = Field(default_factory=list)
    created_by: Optional[str] = None
    created_at: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    updated_at: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    cancelled_at: Optional[str] = None
    last_error: Optional[str] = None


class ShipmentResponse(Shipment):
    pass


class PublicTrackingResponse(BaseModel):
    """Deliberately excludes sensitive customer data (full address, phone, email)."""
    order_number: Optional[str] = None
    shipment_number: str
    tracking_number: Optional[str] = None
    carrier: Optional[str] = None
    status: ShipmentStatus
    estimated_delivery_date: Optional[str] = None
    recipient_first_name: Optional[str] = None
    city_masked: Optional[str] = None
    timeline: List[ShipmentTrackingEvent] = Field(default_factory=list)


# ============ RETURNS ============

class ShipmentReturnCreate(BaseModel):
    reason: ReturnReason
    notes: Optional[str] = None


# ============ WEBHOOK EVENT LOG ============

class WebhookEvent(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    provider: str
    event_type: Optional[str] = None
    payload: Dict[str, Any] = Field(default_factory=dict)
    shipment_id: Optional[str] = None
    tenant_id: Optional[str] = None
    received_at: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    processed_at: Optional[str] = None
    status: str = "received"  # received | processed | error | ignored
    error: Optional[str] = None


# ============ SHIPPING PERMISSIONS ============

SHIPPING_PERMISSIONS = [
    "shipping.view",
    "shipping.create",
    "shipping.edit",
    "shipping.cancel",
    "shipping.track",
    "shipping.print_label",
    "shipping.print_qr",
    "shipping.manage_settings",
    "shipping.view_reports",
]
