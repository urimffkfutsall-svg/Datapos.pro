"""Authentication routes"""
import re
from fastapi import APIRouter, HTTPException, Depends, Request
from datetime import datetime, timezone
from dateutil import parser as date_parser

from database import db
from models import LoginRequest, TokenResponse, UserResponse, UserRole, TenantPublicInfo
from auth import hash_password, verify_password, create_token, get_current_user

router = APIRouter(prefix="/auth", tags=["Authentication"])

# Subdomain e nje firme te vertete production, p.sh. "pos.datapos.pro" -> "pos"
_TENANT_HOST_RE = re.compile(r'^([a-z0-9-]+)\.datapos\.pro$', re.IGNORECASE)


def _extract_subdomain_from_host(host: str):
    """Nxjerr subdomain-in nga header-i Host i kerkeses HTTP (jo nga input i klientit)."""
    if not host:
        return None
    host = host.split(':')[0].strip().lower()
    match = _TENANT_HOST_RE.match(host)
    if not match:
        return None
    subdomain = match.group(1)
    if subdomain in ('www', 'app'):
        return None
    return subdomain


async def _resolve_tenant_id_from_request(http_request: Request):
    """
    Percakton tenant_id-n VETEM nga domain-i real i kerkeses (Host header),
    jo nga cfare i thote frontend-i. Kjo mbyll boshllekun ku nje deshtim/race
    condition ne frontend do te lejonte login global cross-tenant.
    Kthen (tenant_id, is_strict). is_strict=True do te thote qe jemi ne nje
    subdomain firme te vertete dhe login-i DUHET kufizuar rreptesisht aty.
    """
    host = http_request.headers.get('x-forwarded-host') or http_request.headers.get('host')
    subdomain = _extract_subdomain_from_host(host)
    if not subdomain:
        return None, False

    tenant = await db.tenants.find_one(
        {"$or": [
            {"name": subdomain},
            {"name": {"$regex": f"^{subdomain}$", "$options": "i"}}
        ]},
        {"_id": 0}
    )
    if not tenant:
        # Subdomain nuk perputhet me asnje firme - refuzo qarte, mos bjer ne global lookup
        raise HTTPException(status_code=404, detail="Firma nuk u gjet për këtë domain")
    return tenant.get("id"), True


@router.post("/login", response_model=TokenResponse)
async def login(request: LoginRequest, http_request: Request):
    """Login with username/password or PIN"""
    # Tenant-i percaktohet SERVER-SIDE nga Host header i vertete i kerkeses,
    # jo nga tenant_id qe dergon frontend-i (qe mund te mos jete i sakte per
    # shkak te race conditions ose defekteve ne klient).
    host_tenant_id, is_strict_host = await _resolve_tenant_id_from_request(http_request)

    # Perdor tenant-in e Host-it kur eshte i disponueshem; perndryshe bjer mbrapa
    # te tenant_id qe dergoi klienti (backward-compat per domain-e jo-subdomain).
    effective_tenant_id = host_tenant_id or request.tenant_id

    if effective_tenant_id:
        user = await db.users.find_one(
            {"$or": [
                {"tenant_id": effective_tenant_id, "username": request.username},
                {"tenant_id": effective_tenant_id, "pin": request.username},
                {"role": "super_admin", "username": request.username},
            ]},
            {"_id": 0}
        )
    else:
        # ------------------------------------------------------------------
        # DOMAIN KRYESOR (datapos.pro / www / app) - pa subdomain firme.
        # Ketu lejohet TE KYCET VETEM super-administratori.
        # Perdoruesit e firmave duhet te perdorin subdomain-in e firmes se tyre,
        # p.sh. nlagje.datapos.pro
        # ------------------------------------------------------------------
        user = await db.users.find_one(
            {"role": "super_admin", "username": request.username}, {"_id": 0}
        )
        if not user:
            # Kontrollo nese ekziston si perdorues firme, per nje mesazh te qarte
            tenant_user = await db.users.find_one(
                {"$or": [{"username": request.username}, {"pin": request.username}]},
                {"_id": 0},
            )
            if tenant_user and tenant_user.get("tenant_id"):
                tenant = await db.tenants.find_one(
                    {"id": tenant_user["tenant_id"]}, {"_id": 0}
                )
                sub = (tenant or {}).get("name")
                if sub:
                    raise HTTPException(
                        status_code=403,
                        detail=(
                            "Kycja nuk lejohet ne kete adrese. "
                            f"Perdorni adresen e firmes suaj: {sub}.datapos.pro"
                        ),
                    )
            raise HTTPException(
                status_code=403,
                detail=(
                    "Ne kete adrese mund te kycet vetem super-administratori. "
                    "Perdorni adresen e firmes suaj (p.sh. firma.datapos.pro)."
                ),
            )
    
    if not user:
        raise HTTPException(status_code=401, detail="Kredencialet e gabuara")

    # Extra tenant guard: nese login vjen me tenant_id (nga Host ose nga klienti),
    # useri s'lejohet cross-tenant (perjashtim super_admin qe eshte cross-tenant by design).
    # Kur jemi ne nje subdomain firme te vertete (is_strict_host=True), kjo eshte
    # e DETYRUESHME - asnje perdorues i nje firme tjeter s'mund te hyje ketu.
    if effective_tenant_id and user.get("role") != "super_admin":
        if user.get("tenant_id") != effective_tenant_id:
            raise HTTPException(status_code=401, detail="Kredencialet e gabuara")
    
    # Ne domain-in kryesor (pa subdomain firme) lejohet vetem super_admin.
    if not effective_tenant_id and user.get("role") != "super_admin":
        raise HTTPException(
            status_code=403,
            detail=(
                "Ne kete adrese mund te kycet vetem super-administratori. "
                "Perdorni adresen e firmes suaj (p.sh. firma.datapos.pro)."
            ),
        )

    if not user.get("is_active", True):
        raise HTTPException(status_code=401, detail="Llogaria është e çaktivizuar")
    
    if user.get("pin") == request.password:
        pass
    elif not verify_password(request.password, user.get("password_hash", "")):
        raise HTTPException(status_code=401, detail="Kredencialet e gabuara")
    
    tenant_id = user.get("tenant_id")
    
    if tenant_id and user.get("role") != UserRole.SUPER_ADMIN and user.get("role") != "super_admin":
        tenant = await db.tenants.find_one({"id": tenant_id}, {"_id": 0})
        if tenant:
            # Check if tenant is suspended
            if tenant.get("status") == "suspended":
                raise HTTPException(status_code=403, detail="Firma juaj është pezulluar. Kontaktoni administratorin.")
            
            # Check subscription expiration
            subscription_expires = tenant.get("subscription_expires")
            if subscription_expires:
                try:
                    # Parse the expiration date
                    if isinstance(subscription_expires, str):
                        expires_date = date_parser.parse(subscription_expires)
                    else:
                        expires_date = subscription_expires
                    
                    # Make sure it's timezone aware
                    if expires_date.tzinfo is None:
                        expires_date = expires_date.replace(tzinfo=timezone.utc)
                    
                    # Check if subscription has expired
                    now = datetime.now(timezone.utc)
                    if expires_date < now:
                        # Calculate days expired
                        days_expired = (now - expires_date).days
                        raise HTTPException(
                            status_code=402,  # 402 Payment Required
                            detail=f"SUBSCRIPTION_EXPIRED|{days_expired}"
                        )
                except HTTPException:
                    raise
                except Exception:
                    # If date parsing fails, allow login but log the issue
                    pass
    
    token = create_token(
        user_id=user["id"],
        username=user["username"],
        role=user["role"],
        tenant_id=tenant_id
    )
    
    created_at = user.get("created_at")
    if isinstance(created_at, datetime):
        created_at = created_at.isoformat()
    
    return TokenResponse(
        access_token=token,
        user=UserResponse(
            id=user["id"],
            username=user["username"],
            full_name=user.get("full_name", ""),
            role=user["role"],
            branch_id=user.get("branch_id"),
            is_active=user.get("is_active", True),
            created_at=created_at or datetime.now(timezone.utc).isoformat(),
            pin=user.get("pin"),
            tenant_id=user.get("tenant_id")
        )
    )


@router.get("/me", response_model=UserResponse)
async def get_me(current_user: dict = Depends(get_current_user)):
    """Get current user info"""
    created_at = current_user.get("created_at")
    if isinstance(created_at, datetime):
        created_at = created_at.isoformat()
    
    return UserResponse(
        id=current_user["id"],
        username=current_user["username"],
        full_name=current_user.get("full_name", ""),
        role=current_user["role"],
        branch_id=current_user.get("branch_id"),
        is_active=current_user.get("is_active", True),
        created_at=created_at or "",
        pin=current_user.get("pin"),
        tenant_id=current_user.get("tenant_id")
    )
