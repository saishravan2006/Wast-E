"""Offer model for direct-trade workflow."""

import uuid
from datetime import datetime, timezone
from enum import Enum as PyEnum

from sqlalchemy import String, DateTime, ForeignKey, Text, Integer, Enum
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base


def _utcnow():
    return datetime.now(timezone.utc)


def _uuid():
    return str(uuid.uuid4())


class OfferStatus(str, PyEnum):
    SUBMITTED = "submitted"
    COUNTER_OFFERED = "counter_offered"
    NEGOTIATING = "negotiating"
    ACCEPTED = "accepted"
    REJECTED = "rejected"
    WITHDRAWN = "withdrawn"
    EXPIRED = "expired"


class Offer(Base):
    __tablename__ = "offers"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=_uuid)
    listing_id: Mapped[str] = mapped_column(String(36), ForeignKey("listings.id"), nullable=False)
    buyer_org_id: Mapped[str] = mapped_column(String(36), ForeignKey("organisations.id"), nullable=False)
    buyer_user_id: Mapped[str] = mapped_column(String(36), ForeignKey("users.id"), nullable=False)

    offered_price_paise: Mapped[int] = mapped_column(Integer, nullable=False)
    price_unit: Mapped[str] = mapped_column(String(20), default="per_kg")
    offered_quantity_grams: Mapped[int] = mapped_column(Integer, nullable=False)
    terms: Mapped[str | None] = mapped_column(Text, nullable=True)
    message: Mapped[str | None] = mapped_column(Text, nullable=True)

    status: Mapped[str] = mapped_column(Enum(OfferStatus), default=OfferStatus.SUBMITTED)

    # Counter-offer chain
    parent_offer_id: Mapped[str | None] = mapped_column(String(36), ForeignKey("offers.id"), nullable=True)

    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_utcnow, onupdate=_utcnow)

    listing = relationship("Listing", back_populates="offers")
