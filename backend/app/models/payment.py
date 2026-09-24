"""Payment and settlement models — amounts in integer paise."""

import uuid
from datetime import datetime, timezone
from enum import Enum as PyEnum

from sqlalchemy import String, Boolean, DateTime, ForeignKey, Text, Integer, Enum, JSON
from sqlalchemy.orm import Mapped, mapped_column

from app.database import Base


def _utcnow():
    return datetime.now(timezone.utc)


def _uuid():
    return str(uuid.uuid4())


class PaymentStatus(str, PyEnum):
    NOT_INITIATED = "not_initiated"
    PENDING = "pending"
    PARTIALLY_PAID = "partially_paid"
    PAID = "paid"
    REFUNDED = "refunded"
    DISPUTED = "disputed"


class PaymentRecord(Base):
    __tablename__ = "payment_records"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=_uuid)
    order_id: Mapped[str] = mapped_column(String(36), ForeignKey("orders.id"), nullable=False)

    amount_paise: Mapped[int] = mapped_column(Integer, nullable=False)
    currency: Mapped[str] = mapped_column(String(3), default="INR")
    status: Mapped[str] = mapped_column(Enum(PaymentStatus), default=PaymentStatus.NOT_INITIATED)

    payment_method: Mapped[str | None] = mapped_column(String(50), nullable=True)
    provider_ref: Mapped[str | None] = mapped_column(String(255), nullable=True)
    idempotency_key: Mapped[str] = mapped_column(String(100), unique=True, default=_uuid)

    is_simulated: Mapped[bool] = mapped_column(Boolean, default=True)  # demo mode flag
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)

    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_utcnow, onupdate=_utcnow)


class Settlement(Base):
    __tablename__ = "settlements"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=_uuid)
    order_id: Mapped[str] = mapped_column(String(36), ForeignKey("orders.id"), nullable=False, unique=True)

    # Breakdown stored as JSON for flexibility
    breakdown: Mapped[dict] = mapped_column(JSON, nullable=False)
    # e.g. {"material_value": 150000, "transport": -5000, "processing": -8000, "platform_fee": -3000, ...}

    total_seller_proceeds_paise: Mapped[int] = mapped_column(Integer, nullable=False)
    total_buyer_payment_paise: Mapped[int] = mapped_column(Integer, nullable=False)

    is_simulated: Mapped[bool] = mapped_column(Boolean, default=True)
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)

    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_utcnow)
