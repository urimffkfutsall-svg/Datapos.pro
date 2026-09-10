"""FedEx carrier provider (stub-safe; wire in real FedEx REST API when credentials exist)."""
from typing import Any, Dict
import uuid
import requests

from .base import ShippingProviderBase, ProviderConnectionError


class FedExProvider(ShippingProviderBase):
    name = "fedex"

    def supported_operations(self) -> set:
        return {
            "create_shipment", "get_shipment", "get_tracking",
            "cancel_shipment", "generate_label", "get_rates", "test_connection",
        }

    def _base_url(self) -> str:
        if self.config.get("environment") == "production":
            return "https://apis.fedex.com"
        return "https://apis-sandbox.fedex.com"

    async def _oauth_token(self) -> str:
        resp = requests.post(
            f"{self._base_url()}/oauth/token",
            data={
                "grant_type": "client_credentials",
                "client_id": self.config.get("client_id", ""),
                "client_secret": self.config.get("client_secret", ""),
            },
            timeout=10,
        )
        resp.raise_for_status()
        return resp.json().get("access_token")

    async def test_connection(self) -> Dict[str, Any]:
        if not self.config.get("client_id") or not self.config.get("client_secret"):
            return {"success": False, "message": "Client ID / Client Secret missing."}
        try:
            await self._oauth_token()
            return {"success": True, "message": "Connected to FedEx successfully."}
        except requests.RequestException as exc:
            return {"success": False, "message": f"Could not reach FedEx: {exc}"}

    async def create_shipment(self, shipment: Dict[str, Any]) -> Dict[str, Any]:
        if not self.config.get("client_id"):
            fake_tracking = f"FDX{uuid.uuid4().hex[:10].upper()}"
            return {
                "tracking_number": fake_tracking,
                "external_shipment_id": fake_tracking,
                "label_url": None,
                "estimated_delivery_date": None,
                "stub": True,
            }
        try:
            token = await self._oauth_token()
            resp = requests.post(
                f"{self._base_url()}/ship/v1/shipments",
                json=shipment,
                headers={"Authorization": f"Bearer {token}"},
                timeout=20,
            )
            resp.raise_for_status()
            data = resp.json()
            return {
                "tracking_number": data.get("trackingNumber"),
                "external_shipment_id": data.get("shipmentId"),
                "label_url": data.get("labelUrl"),
                "estimated_delivery_date": data.get("estimatedDeliveryDate"),
            }
        except requests.RequestException as exc:
            raise ProviderConnectionError(str(exc))

    async def get_shipment(self, external_shipment_id: str) -> Dict[str, Any]:
        return {"id": external_shipment_id}

    async def get_tracking(self, tracking_number: str) -> Dict[str, Any]:
        if not self.config.get("client_id"):
            return {"carrier_status": "unknown", "events": []}
        try:
            token = await self._oauth_token()
            resp = requests.post(
                f"{self._base_url()}/track/v1/trackingnumbers",
                json={"trackingInfo": [{"trackingNumberInfo": {"trackingNumber": tracking_number}}]},
                headers={"Authorization": f"Bearer {token}"},
                timeout=15,
            )
            resp.raise_for_status()
            data = resp.json()
            results = data.get("output", {}).get("completeTrackResults", [])
            events = []
            status = "unknown"
            if results:
                track = results[0].get("trackResults", [{}])[0]
                status = track.get("latestStatusDetail", {}).get("code", "unknown")
                for e in track.get("scanEvents", []):
                    events.append({
                        "carrier_status_raw": e.get("eventType"),
                        "description": e.get("eventDescription"),
                        "location": (e.get("scanLocation") or {}).get("city"),
                        "occurred_at": e.get("date"),
                    })
            return {"carrier_status": status, "events": events}
        except requests.RequestException as exc:
            raise ProviderConnectionError(str(exc))

    async def cancel_shipment(self, external_shipment_id: str) -> Dict[str, Any]:
        return {"success": True}

    async def generate_label(self, external_shipment_id: str, fmt: str = "pdf") -> Dict[str, Any]:
        return {"label_url": None}

    async def get_rates(self, shipment: Dict[str, Any]) -> Dict[str, Any]:
        return {"rates": []}
