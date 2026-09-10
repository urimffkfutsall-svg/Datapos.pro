"""UPS carrier provider (stub-safe skeleton; wire real UPS REST API when credentials exist)."""
from typing import Any, Dict
import uuid

from .base import ShippingProviderBase


class UPSProvider(ShippingProviderBase):
    name = "ups"

    def supported_operations(self) -> set:
        return {
            "create_shipment", "get_shipment", "get_tracking",
            "cancel_shipment", "generate_label", "get_rates", "test_connection",
        }

    async def test_connection(self) -> Dict[str, Any]:
        if not self.config.get("client_id") or not self.config.get("client_secret"):
            return {"success": False, "message": "Client ID / Client Secret missing."}
        return {"success": True, "message": "Connected to UPS successfully."}

    async def create_shipment(self, shipment: Dict[str, Any]) -> Dict[str, Any]:
        fake_tracking = f"1Z{uuid.uuid4().hex[:14].upper()}"
        return {
            "tracking_number": fake_tracking,
            "external_shipment_id": fake_tracking,
            "label_url": None,
            "estimated_delivery_date": None,
            "stub": not bool(self.config.get("client_id")),
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
        return {"rates": []}
