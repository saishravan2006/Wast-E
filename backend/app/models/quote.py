"""Quote and quote-version models with itemised costs."""

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


class CommercialModel(str, PyEnum):
    SERVICE = "service"  # seller retains ownership, Wast-e charges fees
    PURCHASE_RESALE = "purchase_resale"  # Wast-e buys material outright


class QuoteStatus(str, PyEnum):
    DRAFT = "draft"
    ISSUED = "issued"
    SELLER_APPROVED = "seller_approved"
    SELLER_REJECTED = "seller_rejected"
    EXPIRED = "expired"
    SUPERSEDED = "superseded"


class Quote(Base):
    """Top-level quote entity. Versions track changes that need re-approval."""
    __tablename__ = "quotes"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=_uuid)
    listing_id: Mapped[str] = mapped_column(String(36), ForeignKey("listings.id"), nullable=False)
    assessment_id: Mapped[str | None] = mapped_column(String(36), ForeignKey("assessments.id"), nullable=True)
    created_by: Mapped[str] = mapped_column(String(36), ForeignKey("users.id"), nullable=False)

    commercial_model: Mapped[str] = mapped_column(Enum(CommercialModel), nullable=False)
    current_version: Mapped[int] = mapped_column(Integer, default=1)
    status: Mapped[str] = mapped_column(Enum(QuoteStatus), default=QuoteStatus.DRAFT)

    is_demo: Mapped[bool] = mapped_column(Boolean, default=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_utcnow, onupdate=_utcnow)

    versions = relationship("QuoteVersion", back_populates="quote", cascade="all, delete-orphan",
                            order_by="QuoteVersion.version_number")


class QuoteVersion(Base):
    """Immutable version of a quote with itemised costs in paise."""
    __tablename__ = "quote_versions"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=_uuid)
    quote_id: Mapped[str] = mapped_column(String(36), ForeignKey("quotes.id"), nullable=False)
    version_number: Mapped[int] = mapped_column(Integer, nullable=False)

    # All amounts in paise (1 INR = 100 paise)
    estimated_incoming_weight_grams: Mapped[int] = mapped_column(Integer, nullable=False)
    expected_output_min_grams: Mapped[int | None] = mapped_column(Integer, nullable=True)
    expected_output_max_grams: Mapped[int | None] = mapped_column(Integer, nullable=True)

    # For service model: agreed/indicative sale price
    # For purchase model: purchase price offered to seller
    sale_price_paise_per_kg: Mapped[int | None] = mapped_column(Integer, nullable=True)
    purchase_price_paise_per_kg: Mapped[int | None] = mapped_column(Integer, nullable=True)

    # Itemised costs in paise
    transport_cost_paise: Mapped[int] = mapped_column(Integer, default=0)
    assessment_cost_paise: Mapped[int] = mapped_column(Integer, default=0)
    processing_cost_paise: Mapped[int] = mapped_column(Integer, default=0)
    packaging_cost_paise: Mapped[int] = mapped_column(Integer, default=0)
    residue_handling_cost_paise: Mapped[int] = mapped_column(Integer, default=0)
    platform_fee_paise: Mapped[int] = mapped_column(Integer, default=0)
    tax_paise: Mapped[int] = mapped_column(Integer, default=0)

    estimated_seller_proceeds_paise: Mapped[int | None] = mapped_column(Integer, nullable=True)

    assumptions: Mapped[str | None] = mapped_column(Text, nullable=True)
    additional_cost_responsibility: Mapped[str | None] = mapped_column(Text, nullable=True)
    is_estimate: Mapped[bool] = mapped_column(Boolean, default=True)

    expires_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_utcnow)

    quote = relationship("Quote", back_populates="versions")
