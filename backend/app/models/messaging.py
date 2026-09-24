"""Messaging, disputes, and notifications."""

import uuid
from datetime import datetime, timezone
from enum import Enum as PyEnum

from sqlalchemy import String, Boolean, DateTime, ForeignKey, Text, Integer, Enum, JSON
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base


def _utcnow():
    return datetime.now(timezone.utc)


def _uuid():
    return str(uuid.uuid4())


class Message(Base):
    __tablename__ = "messages"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=_uuid)
    order_id: Mapped[str | None] = mapped_column(String(36), ForeignKey("orders.id"), nullable=True)
    listing_id: Mapped[str | None] = mapped_column(String(36), ForeignKey("listings.id"), nullable=True)
    sender_id: Mapped[str] = mapped_column(String(36), ForeignKey("users.id"), nullable=False)
    recipient_id: Mapped[str | None] = mapped_column(String(36), ForeignKey("users.id"), nullable=True)

    body: Mapped[str] = mapped_column(Text, nullable=False)
    attachment_paths: Mapped[list | None] = mapped_column(JSON, nullable=True)

    is_read: Mapped[bool] = mapped_column(Boolean, default=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_utcnow)


class DisputeType(str, PyEnum):
    WEIGHT_DIFFERENCE = "weight_difference"
    MATERIAL_QUALITY = "material_quality"
    DELIVERY_DAMAGE = "delivery_damage"
    PAYMENT = "payment"
    ADDITIONAL_COSTS = "additional_costs"
    OTHER = "other"


class Dispute(Base):
    __tablename__ = "disputes"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=_uuid)
    order_id: Mapped[str] = mapped_column(String(36), ForeignKey("orders.id"), nullable=False)
    raised_by: Mapped[str] = mapped_column(String(36), ForeignKey("users.id"), nullable=False)

    dispute_type: Mapped[str] = mapped_column(Enum(DisputeType), nullable=False)
    description: Mapped[str] = mapped_column(Text, nullable=False)
    evidence_paths: Mapped[list | None] = mapped_column(JSON, nullable=True)
    agreed_specification: Mapped[str | None] = mapped_column(Text, nullable=True)
    inspection_evidence: Mapped[str | None] = mapped_column(Text, nullable=True)
    relevant_weights: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    requested_resolution: Mapped[str | None] = mapped_column(Text, nullable=True)

    status: Mapped[str] = mapped_column(String(50), default="open")  # open, under_review, resolved, closed
    admin_resolution: Mapped[str | None] = mapped_column(Text, nullable=True)
    resolved_by: Mapped[str | None] = mapped_column(String(36), ForeignKey("users.id"), nullable=True)
    resolved_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_utcnow, onupdate=_utcnow)


class Notification(Base):
    __tablename__ = "notifications"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=_uuid)
    user_id: Mapped[str] = mapped_column(String(36), ForeignKey("users.id"), nullable=False)
    notification_type: Mapped[str] = mapped_column(String(50), nullable=False)
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    content: Mapped[str] = mapped_column(Text, nullable=False)
    link: Mapped[str | None] = mapped_column(String(500), nullable=True)
    is_read: Mapped[bool] = mapped_column(Boolean, default=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_utcnow)

    user = relationship("User", back_populates="notifications")
