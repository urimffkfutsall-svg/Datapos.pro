"""Public, unauthenticated shipment tracking.

GET /api/public/track/{token} deliberately returns only non-sensitive fields
(no full address/phone/email) and uses an opaque UUID4 token rather than a
sequential id, so tracking links cannot be enumerated (see spec section 24).
"""
from fastapi import APIRouter, HTTPException

from database import db
from shipping.models import PublicTrackingResponse
from shipping.qr_utils import mask_city

router = APIRouter(prefix="/public", tags=["Public Tracking"])


@router.get("/track/{token}", response_model=PublicTrackingResponse)
async def public_track(token: str):
    shipment = await db.shipments.find_one({"qr_token": token}, {"_id": 0})
    if not shipment:
        raise HTTPException(status_code=404, detail="Dërgesa nuk u gjet")

    recipient = shipment.get("recipient") or {}
    return PublicTrackingResponse(
        order_number=shipment.get("order_id"),
        shipment_number=shipment["shipment_number"],
        tracking_number=shipment.get("tracking_number"),
        carrier=shipment.get("carrier"),
        status=shipment.get("status"),
        estimated_delivery_date=shipment.get("estimated_delivery_date"),
        recipient_first_name=recipient.get("first_name"),
        city_masked=mask_city(recipient.get("city")),
        timeline=shipment.get("tracking_events", []),
    )
