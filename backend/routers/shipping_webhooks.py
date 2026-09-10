"""Carrier webhook intake.

POST /api/webhooks/shipping/{provider} is how carriers push status changes
to DataPos instead of relying only on polling. Every event is logged to
webhook_events (id, provider, event_type, payload, shipment_id, received_at,
processed_at, status, error) for debugging, per spec section 13.
"""
from fastapi import APIRouter, Request
from datetime import datetime, timezone

from database import db
from shipping.models import ShipmentTrackingEvent, WebhookEvent
from shipping.status_mapping import map_carrier_status

router = APIRouter(prefix="/webhooks/shipping", tags=["Shipping Webhooks"])


def _extract_tracking_number(provider: str, payload: dict) -> str | None:
    for key in ("tracking_number", "trackingNumber", "shipmentTrackingNumber"):
        if payload.get(key):
            return payload[key]
    return None


def _extract_carrier_status(provider: str, payload: dict) -> str | None:
    for key in ("status", "eventType", "statusCode"):
        if payload.get(key):
            return payload[key]
    return None


@router.post("/{provider}")
async def receive_webhook(provider: str, request: Request):
    """Always return 200 quickly; carriers retry aggressively on non-2xx.
    Processing errors are recorded on the log row, never thrown back at the
    carrier, so DataPos does not lose events."""
    try:
        payload = await request.json()
    except Exception:
        payload = {}

    event_log = WebhookEvent(provider=provider, payload=payload)
    event_log.event_type = _extract_carrier_status(provider, payload)

    try:
        tracking_number = _extract_tracking_number(provider, payload)
        shipment = None
        if tracking_number:
            shipment = await db.shipments.find_one({"tracking_number": tracking_number}, {"_id": 0})

        if not shipment:
            event_log.status = "ignored"
            event_log.error = "No matching shipment for tracking number"
            await db.shipment_webhook_events.insert_one(event_log.model_dump())
            return {"received": True}

        event_log.shipment_id = shipment["id"]
        event_log.tenant_id = shipment.get("tenant_id")

        carrier_status_raw = _extract_carrier_status(provider, payload)
        mapped_status = map_carrier_status(provider, carrier_status_raw)

        tracking_event = ShipmentTrackingEvent(
            status=mapped_status,
            carrier_status_raw=carrier_status_raw,
            description=payload.get("description"),
            location=payload.get("location"),
            source="webhook",
        ).model_dump()

        now = datetime.now(timezone.utc).isoformat()
        await db.shipments.update_one(
            {"id": shipment["id"]},
            {"$set": {"status": mapped_status.value, "updated_at": now}, "$push": {"tracking_events": tracking_event}},
        )

        # Update the linked order status, if an orders collection/order_id exists.
        if shipment.get("order_id"):
            await db.orders.update_one(
                {"id": shipment["order_id"]},
                {"$set": {"shipment_status": mapped_status.value}},
            )

        event_log.status = "processed"
        event_log.processed_at = now
    except Exception as exc:  # noqa: BLE001 - never let a webhook 500; log and move on
        event_log.status = "error"
        event_log.error = str(exc)

    await db.shipment_webhook_events.insert_one(event_log.model_dump())
    return {"received": True}
