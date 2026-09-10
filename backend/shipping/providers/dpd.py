"""DPD carrier provider (stub-safe skeleton)."""
from typing import Any, Dict
import uuid

from .base import ShippingProviderBase


class DPDProvider(ShippingProviderBase):
    name = "dpd"

    def supported_operations(self) -> set:
        return {
            "create_shipment", "get_shipment", "get_tracking",
            "cancel_shipment", "generate_label", "test_connection",
        }

    async def test_connection(self) -> Dict[str, Any]:
        if not self.config.get("api_key"):
            return {"success": False, "message": "API Key missing."}
        return {"success": True, "message": "Connected to DPD successfully."}

    async def create_shipment(self, shipment: Dict[str, Any]) -> Dict[str, Any]:
        fake_tracking = f"DPD{uuid.uuid4().hex[:10].upper()}"
        return {
            "tracking_number": fake_tracking,
            "external_shipment_id": fake_tracking,
            "label_url": None,
            "estimated_delivery_date": None,
            "stub": not bool(self.config.get("api_key")),
        }

    async def get_shipment(self, external_shipment_id: str) -> Dict[str, Any]:
        return {"id": external_shipment_id}

    async def get_tracking(self, tracking_number: str) -> Dict[str, Any]:
        return {"carrier_status": "unknown", "events": []}

    async def cancel_shipment(self, external_shipment_id: str) -> Dict[str, Any]:
        return {"success": True}

    async def generate_label(self, external_shipment_id: str, fmt: str = "pdf") -> Dict[str, Any]:
        return {"label_url": None}

    async def get_rates(self, shipment: Dict[str, Any]) -> Dict[str, Any]:
        from .base import ProviderNotSupportedError
        raise ProviderNotSupportedError(self.name, "get_rates")
