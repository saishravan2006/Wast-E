"""Order and approval models."""

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


class OrderStatus(str, PyEnum):
    CREATED = "created"
    INSPECTION_CONFIRMED = "inspection_confirmed"
    PICKUP_ARRANGED = "pickup_arranged"
    IN_TRANSIT = "in_transit"
    DELIVERED = "delivered"
    BUYER_INSPECTING = "buyer_inspecting"
    ACCEPTED = "accepted"
    DISPUTED = "disputed"
    SETTLEMENT_RECORDED = "settlement_recorded"
    CLOSED = "closed"
    CANCELLED = "cancelled"


# Valid state transitions
ORDER_TRANSITIONS = {
    OrderStatus.CREATED: [OrderStatus.INSPECTION_CONFIRMED, OrderStatus.CANCELLED],
    OrderStatus.INSPECTION_CONFIRMED: [OrderStatus.PICKUP_ARRANGED, OrderStatus.CANCELLED],
    OrderStatus.PICKUP_ARRANGED: [OrderStatus.IN_TRANSIT, OrderStatus.CANCELLED],
    OrderStatus.IN_TRANSIT: [OrderStatus.DELIVERED],
    OrderStatus.DELIVERED: [OrderStatus.BUYER_INSPECTING],
    OrderStatus.BUYER_INSPECTING: [OrderStatus.ACCEPTED, OrderStatus.DISPUTED],
    OrderStatus.ACCEPTED: [OrderStatus.SETTLEMENT_RECORDED],
    OrderStatus.DISPUTED: [OrderStatus.ACCEPTED, OrderStatus.CANCELLED, OrderStatus.SETTLEMENT_RECORDED],
    OrderStatus.SETTLEMENT_RECORDED: [OrderStatus.CLOSED],
    OrderStatus.CLOSED: [],
    OrderStatus.CANCELLED: [],
}


class Order(Base):
    __tablename__ = "orders"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=_uuid)
    listing_id: Mapped[str] = mapped_column(String(36), ForeignKey("listings.id"), nullable=False)
    offer_id: Mapped[str | None] = mapped_column(String(36), ForeignKey("offers.id"), nullable=True)
    quote_id: Mapped[str | None] = mapped_column(String(36), ForeignKey("quotes.id"), nullable=True)

    seller_org_id: Mapped[str] = mapped_column(String(36), ForeignKey("organisations.id"), nullable=False)
    buyer_org_id: Mapped[str] = mapped_column(String(36), ForeignKey("organisations.id"), nullable=False)

    # Agreed terms snapshot
    agreed_material: Mapped[str] = mapped_column(String(255), nullable=False)
    agreed_quantity_grams: Mapped[int] = mapped_column(Integer, nullable=False)
    agreed_price_paise: Mapped[int] = mapped_column(Integer, nullable=False)
    price_unit: Mapped[str] = mapped_column(String(20), default="per_kg")
    delivery_terms: Mapped[str | None] = mapped_column(Text, nullable=True)
    cost_responsibility: Mapped[str | None] = mapped_column(Text, nullable=True)

    status: Mapped[str] = mapped_column(Enum(OrderStatus), default=OrderStatus.CREATED)
    order_type: Mapped[str] = mapped_column(String(20), default="direct")  # direct or recovery

    is_demo: Mapped[bool] = mapped_column(Boolean, default=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_utcnow, onupdate=_utcnow)


class Approval(Base):
    """Records an approval decision on any entity (quote, order, etc.)."""
    __tablename__ = "approvals"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=_uuid)
    entity_type: Mapped[str] = mapped_column(String(50), nullable=False)  # quote, order, listing
    entity_id: Mapped[str] = mapped_column(String(36), nullable=False)
    approver_id: Mapped[str] = mapped_column(String(36), ForeignKey("users.id"), nullable=False)
    decision: Mapped[str] = mapped_column(String(20), nullable=False)  # approved, rejected
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)
    version: Mapped[int | None] = mapped_column(Integer, nullable=True)  # for versioned entities

    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_utcnow)
