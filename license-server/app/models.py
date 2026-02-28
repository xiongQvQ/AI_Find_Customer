"""Database models for license management."""

import uuid
from datetime import datetime, timezone

from sqlalchemy import Boolean, DateTime, Enum, ForeignKey, Integer, String, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base


def _now() -> datetime:
    return datetime.now(timezone.utc)


class LicenseKey(Base):
    """A license key sold to a customer."""

    __tablename__ = "license_keys"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    key: Mapped[str] = mapped_column(String(32), unique=True, nullable=False, index=True)
    plan: Mapped[str] = mapped_column(
        Enum("personal", "team", "enterprise", name="plan_type"),
        nullable=False,
        default="personal",
    )
    max_devices: Mapped[int] = mapped_column(Integer, nullable=False, default=1)
    customer_email: Mapped[str] = mapped_column(String(255), nullable=False)
    customer_name: Mapped[str] = mapped_column(String(255), nullable=False, default="")
    notes: Mapped[str] = mapped_column(Text, nullable=False, default="")

    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    expires_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_now)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_now, onupdate=_now)

    activations: Mapped[list["DeviceActivation"]] = relationship(
        "DeviceActivation", back_populates="license_key", cascade="all, delete-orphan"
    )


class DeviceActivation(Base):
    """A device that has activated a license key."""

    __tablename__ = "device_activations"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    license_key_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("license_keys.id"), nullable=False
    )
    machine_id: Mapped[str] = mapped_column(String(64), nullable=False, index=True)
    machine_label: Mapped[str] = mapped_column(String(255), nullable=False, default="")

    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    last_seen_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_now)
    token_expires_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_now)

    license_key: Mapped["LicenseKey"] = relationship("LicenseKey", back_populates="activations")
