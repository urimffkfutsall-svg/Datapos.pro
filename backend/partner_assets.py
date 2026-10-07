"""Validated public partner profiles and durable, bounded raster logos."""
import base64
import io
from urllib.parse import urlsplit, quote
from typing import Literal, Optional
from pydantic import BaseModel, Field, ConfigDict, field_validator
from PIL import Image, UnidentifiedImageError

MAX_UPLOAD = 2 * 1024 * 1024
MAX_STORED = 384 * 1024
SOCIAL_HOSTS = {
    'facebook': {'facebook.com', 'www.facebook.com', 'm.facebook.com', 'fb.com', 'www.fb.com'},
    'instagram': {'instagram.com', 'www.instagram.com'},
    'tiktok': {'tiktok.com', 'www.tiktok.com', 'vm.tiktok.com', 'vt.tiktok.com'},
}

class PartnerWrite(BaseModel):
    model_config = ConfigDict(extra='forbid', str_strip_whitespace=True)
    name: str = Field(min_length=2, max_length=120)
    kind: Literal['sponsor', 'company'] = 'company'
    address: str = Field(default='', max_length=300)
    phone: str = Field(default='', max_length=40)
    facebook: str = Field(default='', max_length=500)
    instagram: str = Field(default='', max_length=500)
    tiktok: str = Field(default='', max_length=500)
    is_active: bool = True
    sort_order: int = Field(default=0, ge=0, le=10000)
    logo_data: Optional[str] = Field(default=None, max_length=550000)

    @field_validator('facebook', 'instagram', 'tiktok')
    @classmethod
    def social_url(cls, value, info):
        if not value:
            return ''
        url = urlsplit(value)
        if url.scheme != 'https' or url.hostname not in SOCIAL_HOSTS[info.field_name] or url.username or url.password or url.port not in (None, 443):
            raise ValueError('Vendosni një lidhje HTTPS të platformës përkatëse, jo vetëm @emrin.')
        return value


def normalize_logo(raw: bytes) -> bytes:
    if not raw or len(raw) > MAX_UPLOAD:
        raise ValueError('Logoja duhet të jetë deri në 2 MB.')
    try:
        with Image.open(io.BytesIO(raw)) as image:
            if image.format not in {'PNG', 'JPEG', 'WEBP'}:
                raise ValueError('Përdorni PNG, JPG ose WebP; SVG dhe skedarët aktivë nuk lejohen.')
            if image.width * image.height > 16000000:
                raise ValueError('Logoja ka rezolucion tepër të madh.')
            image.load()
            clean = image.convert('RGBA')
            clean.thumbnail((512, 320), Image.Resampling.LANCZOS)
            # Re-encode pixels only: no embedded scripts, EXIF or arbitrary metadata.
            for _ in range(4):
                output = io.BytesIO()
                clean.save(output, format='PNG', optimize=True)
                if output.tell() <= MAX_STORED:
                    return output.getvalue()
                clean.thumbnail((max(1, int(clean.width*.75)), max(1, int(clean.height*.75))), Image.Resampling.LANCZOS)
    except (UnidentifiedImageError, OSError, Image.DecompressionBombError) as error:
        raise ValueError('Skedari nuk është një figurë e vlefshme.') from error
    raise ValueError('Logoja nuk mund të optimizohet brenda kufirit të lejuar.')


def decode_logo(value: str) -> bytes:
    if not value.startswith('data:image/png;base64,'):
        raise ValueError('Ngarkoni logon nga PC-ja me formularin e logove.')
    try:
        raw = base64.b64decode(value.split(',', 1)[1], validate=True)
    except (ValueError, TypeError) as error:
        raise ValueError('Të dhënat e logos janë të pavlefshme.') from error
    return normalize_logo(raw)


def public_partner(record):
    """Explicit allowlist. Never expose tenant records, internal metadata or image bytes."""
    return {
        'id': record['id'], 'name': record.get('name', ''), 'kind': record.get('kind', 'company'),
        'address': record.get('address', ''), 'phone': record.get('phone', ''),
        'facebook': record.get('facebook', ''), 'instagram': record.get('instagram', ''),
        'tiktok': record.get('tiktok', ''),
        'logo_url': f"/api/partners/{record['id']}/logo?v={quote(str(record.get('updated_at', '')), safe='')}" if record.get('has_logo') else '',
    }
