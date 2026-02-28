"""Admin API routes: generate keys, list/revoke licenses."""

from datetime import datetime, timezone
from typing import Annotated

from fastapi import APIRouter, Depends, Header, HTTPException, Query, status
from pydantic import BaseModel, EmailStr, Field
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.config import get_settings
from app.crypto import generate_license_key
from app.database import get_db
from app.models import DeviceActivation, LicenseKey

router = APIRouter(prefix="/api/v1/admin", tags=["admin"])
settings = get_settings()


# ── Auth ──────────────────────────────────────────────────────────────────────

def _require_admin(x_admin_key: Annotated[str, Header()] = "") -> None:
    if x_admin_key != settings.admin_api_key:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid admin key")


AdminDep = Annotated[None, Depends(_require_admin)]


# ── Schemas ───────────────────────────────────────────────────────────────────

class CreateKeyRequest(BaseModel):
    customer_email: str = Field(..., min_length=3)
    customer_name: str = Field(default="")
    plan: str = Field(default="personal")          # personal | team | enterprise
    max_devices: int = Field(default=1, ge=1)
    expires_at: datetime | None = None             # None = never expires
    notes: str = Field(default="")


class KeyResponse(BaseModel):
    id: str
    key: str
    plan: str
    max_devices: int
    customer_email: str
    customer_name: str
    is_active: bool
    expires_at: datetime | None
    created_at: datetime
    active_devices: int


class DeviceResponse(BaseModel):
    id: str
    machine_id: str
    machine_label: str
    is_active: bool
    last_seen_at: datetime
    token_expires_at: datetime | None
    created_at: datetime


class RevokeDeviceRequest(BaseModel):
    machine_id: str


# ── Routes ────────────────────────────────────────────────────────────────────

@router.post("/keys", response_model=KeyResponse, status_code=status.HTTP_201_CREATED)
async def create_key(
    req: CreateKeyRequest,
    db: Annotated[AsyncSession, Depends(get_db)],
    _: AdminDep,
):
    """Generate a new license key for a customer."""
    key_str = generate_license_key()
    lic = LicenseKey(
        key=key_str,
        plan=req.plan,
        max_devices=req.max_devices,
        customer_email=req.customer_email,
        customer_name=req.customer_name,
        expires_at=req.expires_at,
        notes=req.notes,
    )
    db.add(lic)
    await db.commit()
    await db.refresh(lic)
    return _to_key_response(lic)


@router.get("/keys", response_model=list[KeyResponse])
async def list_keys(
    db: Annotated[AsyncSession, Depends(get_db)],
    _: AdminDep,
    email: str | None = Query(default=None),
    active_only: bool = Query(default=False),
):
    """List all license keys, optionally filtered."""
    q = select(LicenseKey).options(selectinload(LicenseKey.activations))
    if email:
        q = q.where(LicenseKey.customer_email.ilike(f"%{email}%"))
    if active_only:
        q = q.where(LicenseKey.is_active == True)  # noqa: E712
    q = q.order_by(LicenseKey.created_at.desc())
    result = await db.execute(q)
    return [_to_key_response(r) for r in result.scalars().all()]


@router.get("/keys/{key}", response_model=KeyResponse)
async def get_key(
    key: str,
    db: Annotated[AsyncSession, Depends(get_db)],
    _: AdminDep,
):
    lic = await _load_key(key, db)
    return _to_key_response(lic)


@router.patch("/keys/{key}/disable", response_model=KeyResponse)
async def disable_key(
    key: str,
    db: Annotated[AsyncSession, Depends(get_db)],
    _: AdminDep,
):
    """Disable a license key (e.g. chargeback / refund)."""
    lic = await _load_key(key, db)
    lic.is_active = False
    await db.commit()
    await db.refresh(lic)
    return _to_key_response(lic)


@router.patch("/keys/{key}/enable", response_model=KeyResponse)
async def enable_key(
    key: str,
    db: Annotated[AsyncSession, Depends(get_db)],
    _: AdminDep,
):
    lic = await _load_key(key, db)
    lic.is_active = True
    await db.commit()
    await db.refresh(lic)
    return _to_key_response(lic)


@router.get("/keys/{key}/devices", response_model=list[DeviceResponse])
async def list_devices(
    key: str,
    db: Annotated[AsyncSession, Depends(get_db)],
    _: AdminDep,
):
    """List all devices activated for a license key."""
    lic = await _load_key(key, db)
    return [_to_device_response(a) for a in lic.activations]


@router.post("/keys/{key}/devices/revoke", status_code=status.HTTP_204_NO_CONTENT)
async def revoke_device(
    key: str,
    req: RevokeDeviceRequest,
    db: Annotated[AsyncSession, Depends(get_db)],
    _: AdminDep,
):
    """Force-deactivate a specific device (admin override for device transfer)."""
    lic = await _load_key(key, db)
    activation = next((a for a in lic.activations if a.machine_id == req.machine_id), None)
    if not activation:
        raise HTTPException(status_code=404, detail="Device not found")
    activation.is_active = False
    await db.commit()


# ── Helpers ───────────────────────────────────────────────────────────────────

async def _load_key(key: str, db: AsyncSession) -> LicenseKey:
    result = await db.execute(
        select(LicenseKey)
        .where(LicenseKey.key == key.upper().strip())
        .options(selectinload(LicenseKey.activations))
    )
    lic = result.scalar_one_or_none()
    if not lic:
        raise HTTPException(status_code=404, detail="License key not found")
    return lic


def _to_key_response(lic: LicenseKey) -> KeyResponse:
    return KeyResponse(
        id=str(lic.id),
        key=lic.key,
        plan=lic.plan,
        max_devices=lic.max_devices,
        customer_email=lic.customer_email,
        customer_name=lic.customer_name,
        is_active=lic.is_active,
        expires_at=lic.expires_at,
        created_at=lic.created_at,
        active_devices=sum(1 for a in lic.activations if a.is_active),
    )


def _to_device_response(a: DeviceActivation) -> DeviceResponse:
    return DeviceResponse(
        id=str(a.id),
        machine_id=a.machine_id,
        machine_label=a.machine_label,
        is_active=a.is_active,
        last_seen_at=a.last_seen_at,
        token_expires_at=a.token_expires_at,
        created_at=a.created_at,
    )
