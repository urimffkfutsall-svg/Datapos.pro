"""QR code + secure tracking token helpers.

Tracking tokens are opaque, unpredictable, non-sequential UUID4 hex strings
(not based on the Order ID) so that /track/{token} cannot be enumerated.
"""
import base64
import io
import uuid

import qrcode


def generate_tracking_token() -> str:
    """Generate a unique, unpredictable tracking token (not sequential, not order-based)."""
    return uuid.uuid4().hex


def build_tracking_url(base_url: str, token: str) -> str:
    base_url = (base_url or "https://datapos.pro").rstrip("/")
    return f"{base_url}/track/{token}"


def generate_qr_code_base64(data: str) -> str:
    """Generate a QR code PNG for `data` and return it as a base64 data URL.

    The QR code only ever encodes the public tracking URL/token, never any
    personal customer data.
    """
    img = qrcode.make(data)
    buffer = io.BytesIO()
    img.save(buffer, format="PNG")
    encoded = base64.b64encode(buffer.getvalue()).decode("utf-8")
    return f"data:image/png;base64,{encoded}"


def mask_city(city: str) -> str:
    """Mask a city name for public display, e.g. 'Prishtina' -> 'Pri*****'."""
    if not city:
        return ""
    if len(city) <= 3:
        return city[0] + "*" * (len(city) - 1)
    return city[:3] + "*" * (len(city) - 3)
