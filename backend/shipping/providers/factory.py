"""Factory that maps a carrier name to its provider implementation.

DataPos never talks to a carrier directly -- it always goes through this
factory: DataPos -> ShippingProvider (abstraction) -> Carrier.
"""
from typing import Any, Dict

from .base import ShippingProviderBase
from .dhl import DHLProvider
from .fedex import FedExProvider
from .ups import UPSProvider
from .dpd import DPDProvider
from .custom import CustomCarrierProvider

_PROVIDERS = {
    "dhl": DHLProvider,
    "fedex": FedExProvider,
    "ups": UPSProvider,
    "dpd": DPDProvider,
    "gls": CustomCarrierProvider,
    "local": CustomCarrierProvider,
    "custom": CustomCarrierProvider,
}


def get_provider(carrier: str, config: Dict[str, Any]) -> ShippingProviderBase:
    """Return a provider instance for the given carrier name.

    Unknown carriers fall back to CustomCarrierProvider so new carriers can
    be onboarded without code changes to the rest of the shipping module.
    """
    cls = _PROVIDERS.get((carrier or "").lower(), CustomCarrierProvider)
    return cls(config)


def list_supported_carriers():
    return sorted(_PROVIDERS.keys())
