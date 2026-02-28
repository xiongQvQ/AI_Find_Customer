"""License API routes: activate, refresh, deactivate."""

from datetime import datetime, timezone
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, Field
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.config import get_settings
from app.crypto import create_device_token, verify_device_token
from app.database import get_db
from app.models import DeviceActivation, LicenseKey

router = APIRouter(prefix="/api/v1/license", tags=["license"])
settings = get_settings()


# ── Request / Response schemas ────────────────────────────────────────────────

class ActivateRequest(BaseModel):
    license_key: str = Field(..., min_length=10)
    machine_id: str = Field(..., min_length=8, max_length=64)
    machine_label: str = Field(default="", max_length=255)
    app_version: str = Field(default="")


class ActivateResponse(BaseModel):
    token: str
    expires_at: datetime
    plan: str
    customer_name: str
    max_devices: int
    active_devices: int


class RefreshRequest(BaseModel):
    token: str
    machine_id: str = Field(..., min_length=8, max_length=64)


class RefreshResponse(BaseModel):
    token: str
    expires_at: datetime


class DeactivateRequest(BaseModel):
    token: str
    machine_id: str


# ── Helpers ───────────────────────────────────────────────────────────────────

async def _get_license(key: str, db: AsyncSession) -> LicenseKey:
    """Load license key with activations, raise 404 if not found."""
    result = await db.execute(
        select(LicenseKey)
        .where(LicenseKey.key == key.upper().strip())
        .options(selectinload(LicenseKey.activations))
    )
    lic = result.scalar_one_or_none()
    if not lic:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="License key not found")
    return lic


def _check_license_valid(lic: LicenseKey) -> None:
    """Raise 403 if license is disabled or expired."""
    if not lic.is_active:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="License key is disabled")
    if lic.expires_at and lic.expires_at < datetime.now(timezone.utc):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="License key has expired")


# ── Routes ────────────────────────────────────────────────────────────────────

@router.post("/activate", response_model=ActivateResponse)
async def activate(req: ActivateRequest, db: Annotated[AsyncSession, Depends(get_db)]):
    """Activate a license key on a device. Binds machine_id to the key."""
    lic = await _get_license(req.license_key, db)
    _check_license_valid(lic)

    active_activations = [a for a in lic.activations if a.is_active]

    # Check if this machine is already activated
    existing = next((a for a in active_activations if a.machine_id == req.machine_id), None)

    if existing is None:
        # New device — check slot availability
        if len(active_activations) >= lic.max_devices:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Device limit reached ({lic.max_devices} device(s) allowed). "
                       "Deactivate another device first.",
            )
        # Create new activation
        existing = DeviceActivation(
            license_key_id=lic.id,
            machine_id=req.machine_id,
            machine_label=req.machine_label,
        )
        db.add(existing)

    # Count before commit (relationship still valid in this session)
    was_new = existing not in db.new  # False if just added above
    active_count_before = len(active_activations)
    is_new_device = existing not in active_activations  # True for brand-new activations

    # Issue token
    token, expires_at = create_device_token(lic.key, req.machine_id, lic.plan)
    existing.token_expires_at = expires_at
    existing.last_seen_at = datetime.now(timezone.utc)
    existing.is_active = True

    await db.commit()

    active_devices = active_count_before + (1 if is_new_device else 0)

    return ActivateResponse(
        token=token,
        expires_at=expires_at,
        plan=lic.plan,
        customer_name=lic.customer_name,
        max_devices=lic.max_devices,
        active_devices=active_devices,
    )


@router.post("/refresh", response_model=RefreshResponse)
async def refresh(req: RefreshRequest, db: Annotated[AsyncSession, Depends(get_db)]):
    """Refresh an expiring token. Called automatically every ~5 days by the client."""
    payload = verify_device_token(req.token)
    if not payload:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid or expired token")

    if payload.get("sub") != req.machine_id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Machine ID mismatch")

    # Verify license is still valid
    lic = await _get_license(payload["lic"], db)
    _check_license_valid(lic)

    # Verify device activation still exists
    result = await db.execute(
        select(DeviceActivation).where(
            DeviceActivation.license_key_id == lic.id,
            DeviceActivation.machine_id == req.machine_id,
            DeviceActivation.is_active == True,  # noqa: E712
        )
    )
    activation = result.scalar_one_or_none()
    if not activation:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Device not activated")

    # Issue new token
    token, expires_at = create_device_token(lic.key, req.machine_id, lic.plan)
    activation.token_expires_at = expires_at
    activation.last_seen_at = datetime.now(timezone.utc)
    await db.commit()

    return RefreshResponse(token=token, expires_at=expires_at)


@router.post("/deactivate", status_code=status.HTTP_204_NO_CONTENT)
async def deactivate(req: DeactivateRequest, db: Annotated[AsyncSession, Depends(get_db)]):
    """Deactivate a device (free up a slot). Used when user wants to switch devices."""
    payload = verify_device_token(req.token)
    if not payload:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token")

    if payload.get("sub") != req.machine_id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Machine ID mismatch")

    result = await db.execute(
        select(DeviceActivation).where(
            DeviceActivation.machine_id == req.machine_id,
            DeviceActivation.is_active == True,  # noqa: E712
        )
    )
    activation = result.scalar_one_or_none()
    if activation:
        activation.is_active = False
        await db.commit()
