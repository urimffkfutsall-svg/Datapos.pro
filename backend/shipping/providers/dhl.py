"""DHL carrier provider.

Uses DHL's Shipment/Tracking REST APIs when credentials are configured,
with a safe stub fallback so the module works end-to-end before real
DHL credentials are supplied by a company.
"""
from typing import Any, Dict
import uuid
import requests

from .base import ShippingProviderBase, ProviderConnectionError


class DHLProvider(ShippingProviderBase):
    name = "dhl"

    def supported_operations(self) -> set:
        return {
            "create_shipment", "get_shipment", "get_tracking",
            "cancel_shipment", "generate_label", "get_rates", "test_connection",
        }

    def _base_url(self) -> str:
        if self.config.get("environment") == "production":
            return "https://api-eu.dhl.com"
        return "https://api-sandbox.dhl.com"

    def _auth(self):
        return (self.config.get("api_key", ""), self.config.get("api_secret", ""))

    async def test_connection(self) -> Dict[str, Any]:
        api_key = self.config.get("api_key")
        api_secret = self.config.get("api_secret")
        if not api_key or not api_secret:
            return {"success": False, "message": "API Key / API Secret missing."}
        try:
            resp = requests.get(
                f"{self._base_url()}/track/shipments",
                params={"trackingNumber": "000000000000"},
                auth=self._auth(),
                timeout=10,
            )
            if resp.status_code in (200, 404):
                return {"success": True, "message": "Connected to DHL successfully."}
            return {"success": False, "message": f"DHL responded with status {resp.status_code}."}
        except requests.RequestException as exc:
            return {"success": False, "message": f"Could not reach DHL: {exc}"}

    async def create_shipment(self, shipment: Dict[str, Any]) -> Dict[str, Any]:
        if not self.config.get("api_key"):
            fake_tracking = f"DHL{uuid.uuid4().hex[:10].upper()}"
            return {
                "tracking_number": fake_tracking,
                "external_shipment_id": fake_tracking,
                "label_url": None,
                "estimated_delivery_date": None,
                "stub": True,
            }
        try:
            resp = requests.post(
                f"{self._base_url()}/shipments",
                json=shipment,
                auth=self._auth(),
                timeout=20,
            )
            resp.raise_for_status()
            data = resp.json()
            docs = data.get("documents") or []
            return {
                "tracking_number": data.get("shipmentTrackingNumber"),
                "external_shipment_id": data.get("shipmentTrackingNumber"),
                "label_url": docs[0].get("url") if docs else None,
                "estimated_delivery_date": data.get("estimatedDeliveryDate"),
            }
        except requests.RequestException as exc:
            raise ProviderConnectionError(str(exc))

    async def get_shipment(self, external_shipment_id: str) -> Dict[str, Any]:
        resp = requests.get(
            f"{self._base_url()}/shipments/{external_shipment_id}",
            auth=self._auth(), timeout=15,
        )
        resp.raise_for_status()
        return resp.json()

    async def get_tracking(self, tracking_number: str) -> Dict[str, Any]:
        if not self.config.get("api_key"):
            return {"carrier_status": "unknown", "events": []}
        resp = requests.get(
            f"{self._base_url()}/track/shipments",
            params={"trackingNumber": tracking_number},
            auth=self._auth(), timeout=15,
        )
        resp.raise_for_status()
        data = resp.json()
        shipments = data.get("shipments", [])
        if not shipments:
            return {"carrier_status": "unknown", "events": []}
        s = shipments[0]
        events = [
            {
                "carrier_status_raw": e.get("status"),
                "description": e.get("description"),
                "location": (e.get("location") or {}).get("address", {}).get("addressLocality"),
                "occurred_at": e.get("timestamp"),
            }
            for e in s.get("events", [])
        ]
        return {"carrier_status": s.get("status", {}).get("statusCode"), "events": events}

    async def cancel_shipment(self, external_shipment_id: str) -> Dict[str, Any]:
        resp = requests.delete(
            f"{self._base_url()}/shipments/{external_shipment_id}",
            auth=self._auth(), timeout=15,
        )
        return {"success": resp.status_code in (200, 202, 204)}

    async def generate_label(self, external_shipment_id: str, fmt: str = "pdf") -> Dict[str, Any]:
        data = await self.get_shipment(external_shipment_id)
        docs = data.get("documents", [])
        return {"label_url": docs[0].get("url") if docs else None}

    async def get_rates(self, shipment: Dict[str, Any]) -> Dict[str, Any]:
        return {"rates": []}
