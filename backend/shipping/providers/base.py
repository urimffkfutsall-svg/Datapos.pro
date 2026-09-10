"""Common ShippingProvider interface.

Every carrier integration (DHL, FedEx, UPS, DPD, GLS, local, custom) implements
this interface. If a carrier does not support a given operation, it must raise
ProviderNotSupportedError so the API layer can respond clearly instead of
failing silently or faking data.
"""
from abc import ABC, abstractmethod
from typing import Any, Dict, Optional


class ProviderNotSupportedError(Exception):
    """Raised when a carrier does not support a requested operation."""

    def __init__(self, carrier: str, operation: str):
        self.carrier = carrier
        self.operation = operation
        super().__init__(
            f"Carrier '{carrier}' does not support operation '{operation}'"
        )


class ProviderConnectionError(Exception):
    """Raised when the carrier API is unreachable or rejects credentials."""


class ShippingProviderBase(ABC):
    """Abstract base class every carrier provider must implement.

    config: decrypted credential/config dict for this tenant + carrier, e.g.
        { api_key, api_secret, account_number, client_id, client_secret,
          environment, default_service, default_package_type, ... }
    """

    name: str = "base"

    def __init__(self, config: Dict[str, Any]):
        self.config = config or {}

    # ---- capability introspection -------------------------------------
    def supports(self, operation: str) -> bool:
        return operation in self.supported_operations()

    def supported_operations(self) -> set:
        """Override in subclasses to declare which operations are implemented."""
        return {
            "create_shipment",
            "get_shipment",
            "get_tracking",
            "cancel_shipment",
            "generate_label",
            "get_rates",
            "test_connection",
        }

    def _require(self, operation: str):
        if not self.supports(operation):
            raise ProviderNotSupportedError(self.name, operation)

    # ---- interface ------------------------------------------------------
    @abstractmethod
    async def test_connection(self) -> Dict[str, Any]:
        """Validate credentials. Returns {success: bool, message: str}."""

    @abstractmethod
    async def create_shipment(self, shipment: Dict[str, Any]) -> Dict[str, Any]:
        """Create a shipment with the carrier.

        Returns a dict with at least: tracking_number, external_shipment_id,
        label_url (optional), estimated_delivery_date (optional).
        """

    @abstractmethod
    async def get_shipment(self, external_shipment_id: str) -> Dict[str, Any]:
        """Fetch current shipment info from the carrier."""

    @abstractmethod
    async def get_tracking(self, tracking_number: str) -> Dict[str, Any]:
        """Fetch tracking events from the carrier. Returns raw carrier status
        plus a list of events; callers should map via status_mapping."""

    @abstractmethod
    async def cancel_shipment(self, external_shipment_id: str) -> Dict[str, Any]:
        """Cancel a shipment with the carrier."""

    @abstractmethod
    async def generate_label(self, external_shipment_id: str, fmt: str = "pdf") -> Dict[str, Any]:
        """Return {label_url} or {label_base64} for the shipment label."""

    @abstractmethod
    async def get_rates(self, shipment: Dict[str, Any]) -> Dict[str, Any]:
        """Return available service rates for a prospective shipment."""
