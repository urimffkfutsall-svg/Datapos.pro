"""Local courier / custom carrier provider.

Used for GLS, local postal companies, or any carrier without a dedicated
integration yet. Tracking updates for these carriers are expected to arrive
via manual status updates or a generic webhook rather than a carrier API.
"""
from typing import Any, Dict
import uuid

from .base import ShippingProviderBase, ProviderNotSupportedError


class CustomCarrierProvider(ShippingProviderBase):
    name = "custom"

    def supported_operations(self) -> set:
        return {"create_shipment", "get_shipment", "cancel_shipment", "test_connection"}

    async def test_connection(self) -> Dict[str, Any]:
        return {"success": True, "message": "Local/custom carrier does not require API credentials."}

    async def create_shipment(self, shipment: Dict[str, Any]) -> Dict[str, Any]:
        fake_tracking = f"LOC{uuid.uuid4().hex[:10].upper()}"
        return {
            "tracking_number": fake_tracking,
            "external_shipment_id": fake_tracking,
            "label_url": None,
            "estimated_delivery_date": None,
            "stub": True,
        }

    async def get_shipment(self, external_shipment_id: str) -> Dict[str, Any]:
        return {"id": external_shipment_id}

    async def get_tracking(self, tracking_number: str) -> Dict[str, Any]:
        raise ProviderNotSupportedError(self.name, "get_tracking")

    async def cancel_shipment(self, external_shipment_id: str) -> Dict[str, Any]:
        return {"success": True}

    async def generate_label(self, external_shipment_id: str, fmt: str = "pdf") -> Dict[str, Any]:
        raise ProviderNotSupportedError(self.name, "generate_label")

    async def get_rates(self, shipment: Dict[str, Any]) -> Dict[str, Any]:
        raise ProviderNotSupportedError(self.name, "get_rates")
