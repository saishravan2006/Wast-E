"""Listing, photo, and document models for material marketplace."""

import uuid
from datetime import datetime, timezone
from enum import Enum as PyEnum

from sqlalchemy import (
    String, Boolean, DateTime, ForeignKey, Text, Integer, Enum, JSON,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base


def _utcnow():
    return datetime.now(timezone.utc)


def _uuid():
    return str(uuid.uuid4())


class MaterialCategory(str, PyEnum):
    PLASTICS = "plastics"
    PAPER_CARDBOARD = "paper_cardboard"
    METALS = "metals"
    GLASS = "glass"
    TEXTILES = "textiles"


class PhysicalForm(str, PyEnum):
    LOOSE = "loose"
    BALED = "baled"
    SHREDDED = "shredded"
    GRANULATED = "granulated"
    OTHER = "other"


class RejectionReason(str, PyEnum):
    MIXED_MATERIALS = "mixed_materials"
    CONTAMINATION = "contamination"
    EXCESS_MOISTURE = "excess_moisture"
    COLOUR_MISMATCH = "colour_mismatch"
    WRONG_GRADE = "wrong_grade"
    QUANTITY_MISMATCH = "quantity_mismatch"
    DOCUMENTATION_ISSUE = "documentation_issue"
    OTHER = "other"


class ListingStatus(str, PyEnum):
    DRAFT = "draft"
    PENDING_REVIEW = "pending_review"
    ACTIVE = "active"
    UNDER_ASSESSMENT = "under_assessment"
    OFFER_ACCEPTED = "offer_accepted"
    IN_RECOVERY = "in_recovery"
    SOLD = "sold"
    WITHDRAWN = "withdrawn"
    REJECTED = "rejected"


class PreferredRoute(str, PyEnum):
    DIRECT_SALE = "direct_sale"
    MANAGED_RECOVERY = "managed_recovery"
    HELP_ME_DECIDE = "help_me_decide"


class Listing(Base):
    __tablename__ = "listings"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=_uuid)
    org_id: Mapped[str] = mapped_column(String(36), ForeignKey("organisations.id"), nullable=False)
    created_by: Mapped[str] = mapped_column(String(36), ForeignKey("users.id"), nullable=False)

    # Step 1 — Material details
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    material_category: Mapped[str] = mapped_column(Enum(MaterialCategory), nullable=False)
    material_grade: Mapped[str | None] = mapped_column(String(100), nullable=True)  # polymer/grade
    grade_unknown: Mapped[bool] = mapped_column(Boolean, default=False)
    quantity_grams: Mapped[int] = mapped_column(Integer, nullable=False)  # stored in grams
    quantity_unit: Mapped[str] = mapped_column(String(10), default="kg")  # display unit
    physical_form: Mapped[str] = mapped_column(Enum(PhysicalForm), default=PhysicalForm.LOOSE)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)

    # Step 2 — Rejection details
    rejection_reason: Mapped[str] = mapped_column(Enum(RejectionReason), nullable=False)
    rejection_details: Mapped[str | None] = mapped_column(Text, nullable=True)
    material_source: Mapped[str | None] = mapped_column(String(255), nullable=True)
    known_contents: Mapped[str | None] = mapped_column(Text, nullable=True)
    has_hazardous_contamination: Mapped[bool] = mapped_column(Boolean, default=False)

    # Step 3 — Location and commercial
    city: Mapped[str] = mapped_column(String(100), nullable=False)
    state: Mapped[str] = mapped_column(String(100), nullable=False)
    pincode: Mapped[str] = mapped_column(String(10), nullable=False)
    pickup_address: Mapped[str | None] = mapped_column(Text, nullable=True)  # private
    asking_price_paise: Mapped[int | None] = mapped_column(Integer, nullable=True)  # per kg in paise
    price_unit: Mapped[str] = mapped_column(String(20), default="per_kg")
    request_quote: Mapped[bool] = mapped_column(Boolean, default=False)
    loading_arrangements: Mapped[str | None] = mapped_column(String(255), nullable=True)
    pickup_availability: Mapped[str | None] = mapped_column(String(255), nullable=True)
    ownership_confirmed: Mapped[bool] = mapped_column(Boolean, default=False)
    preferred_route: Mapped[str] = mapped_column(Enum(PreferredRoute), default=PreferredRoute.HELP_ME_DECIDE)

    # Status
    status: Mapped[str] = mapped_column(Enum(ListingStatus), default=ListingStatus.DRAFT)
    is_demo: Mapped[bool] = mapped_column(Boolean, default=False)

    # Assessment info
    has_assessment: Mapped[bool] = mapped_column(Boolean, default=False)
    assessment_date: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_utcnow, onupdate=_utcnow)

    # Relationships
    organisation = relationship("Organisation", back_populates="listings")
    photos = relationship("ListingPhoto", back_populates="listing", cascade="all, delete-orphan")
    documents = relationship("ListingDocument", back_populates="listing", cascade="all, delete-orphan")
    offers = relationship("Offer", back_populates="listing")

    def __repr__(self):
        return f"<Listing {self.title}>"


class ListingPhoto(Base):
    __tablename__ = "listing_photos"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=_uuid)
    listing_id: Mapped[str] = mapped_column(String(36), ForeignKey("listings.id"), nullable=False)
    file_path: Mapped[str] = mapped_column(String(500), nullable=False)
    caption: Mapped[str | None] = mapped_column(String(255), nullable=True)
    sort_order: Mapped[int] = mapped_column(Integer, default=0)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_utcnow)

    listing = relationship("Listing", back_populates="photos")


class ListingDocument(Base):
    __tablename__ = "listing_documents"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=_uuid)
    listing_id: Mapped[str] = mapped_column(String(36), ForeignKey("listings.id"), nullable=False)
    file_path: Mapped[str] = mapped_column(String(500), nullable=False)
    document_type: Mapped[str] = mapped_column(String(100), nullable=False)  # rejection_report, lab_test, etc.
    original_name: Mapped[str] = mapped_column(String(255), nullable=False)
    access_level: Mapped[str] = mapped_column(String(50), default="owner")  # owner, buyer, public
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_utcnow)

    listing = relationship("Listing", back_populates="documents")
