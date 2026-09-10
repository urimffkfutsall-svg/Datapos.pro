"""Maps carrier-specific status codes to DataPos internal ShipmentStatus.

Frontend and reports always read the internal status, never the raw carrier
status, so every new carrier only needs an entry here to plug in cleanly.
"""
from .models import ShipmentStatus

_DHL_MAP = {
    "pre-transit": ShipmentStatus.LABEL_CREATED,
    "transit": ShipmentStatus.IN_TRANSIT,
    "delivered": ShipmentStatus.DELIVERED,
    "failure": ShipmentStatus.DELIVERY_FAILED,
    "returned": ShipmentStatus.RETURNED,
    "unknown": ShipmentStatus.EXCEPTION,
}

_FEDEX_MAP = {
    "PU": ShipmentStatus.PICKED_UP,
    "IT": ShipmentStatus.IN_TRANSIT,
    "OD": ShipmentStatus.OUT_FOR_DELIVERY,
    "DL": ShipmentStatus.DELIVERED,
    "DE": ShipmentStatus.EXCEPTION,
    "CA": ShipmentStatus.CANCELLED,
}

_UPS_MAP = {
    "M": ShipmentStatus.LABEL_CREATED,
    "P": ShipmentStatus.PICKED_UP,
    "I": ShipmentStatus.IN_TRANSIT,
    "O": ShipmentStatus.OUT_FOR_DELIVERY,
    "D": ShipmentStatus.DELIVERED,
    "X": ShipmentStatus.EXCEPTION,
    "RS": ShipmentStatus.RETURNED,
}

_DPD_MAP = {
    "created": ShipmentStatus.LABEL_CREATED,
    "collected": ShipmentStatus.PICKED_UP,
    "in_transit": ShipmentStatus.IN_TRANSIT,
    "out_for_delivery": ShipmentStatus.OUT_FOR_DELIVERY,
    "delivered": ShipmentStatus.DELIVERED,
    "exception": ShipmentStatus.EXCEPTION,
}

_CARRIER_MAPS = {
    "dhl": _DHL_MAP,
    "fedex": _FEDEX_MAP,
    "ups": _UPS_MAP,
    "dpd": _DPD_MAP,
}


def map_carrier_status(carrier: str, carrier_status_raw: str) -> ShipmentStatus:
    """Translate a raw carrier status code into the internal ShipmentStatus.

    Unknown/unrecognized codes map to EXCEPTION rather than silently failing,
    so operators can see something needs manual review.
    """
    carrier_map = _CARRIER_MAPS.get((carrier or "").lower(), {})
    return carrier_map.get(carrier_status_raw, ShipmentStatus.EXCEPTION)
