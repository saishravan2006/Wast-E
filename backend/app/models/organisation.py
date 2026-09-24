"""Organisation, membership, and verification models."""

import uuid
from datetime import datetime, timezone
from enum import Enum as PyEnum

from sqlalchemy import String, Boolean, DateTime, ForeignKey, Text, Enum
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base


def _utcnow():
    return datetime.now(timezone.utc)


def _uuid():
    return str(uuid.uuid4())


class VerificationStatus(str, PyEnum):
    PENDING = "pending"
    SUBMITTED = "submitted"
    UNDER_REVIEW = "under_review"
    VERIFIED = "verified"
    REJECTED = "rejected"


class OrgType(str, PyEnum):
    KABADIWALA = "kabadiwala"
    AGGREGATOR = "aggregator"
    FACTORY = "factory"
    RECYCLER = "recycler"
    MANUFACTURER = "manufacturer"
    OTHER = "other"


class Organisation(Base):
    __tablename__ = "organisations"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=_uuid)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    org_type: Mapped[str] = mapped_column(Enum(OrgType), default=OrgType.OTHER)
    gstin: Mapped[str | None] = mapped_column(String(20), nullable=True)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)

    # Location
    address: Mapped[str | None] = mapped_column(Text, nullable=True)
    city: Mapped[str | None] = mapped_column(String(100), nullable=True)
    state: Mapped[str | None] = mapped_column(String(100), nullable=True)
    pincode: Mapped[str | None] = mapped_column(String(10), nullable=True)

    phone: Mapped[str | None] = mapped_column(String(20), nullable=True)
    email: Mapped[str | None] = mapped_column(String(255), nullable=True)

    verification_status: Mapped[str] = mapped_column(
        Enum(VerificationStatus), default=VerificationStatus.PENDING
    )
    is_demo: Mapped[bool] = mapped_column(Boolean, default=False)

    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_utcnow, onupdate=_utcnow)

    # Relationships
    memberships = relationship("OrgMembership", back_populates="organisation", cascade="all, delete-orphan")
    verifications = relationship("BusinessVerification", back_populates="organisation", cascade="all, delete-orphan")
    listings = relationship("Listing", back_populates="organisation")

    def __repr__(self):
        return f"<Organisation {self.name}>"


class OrgMembership(Base):
    __tablename__ = "org_memberships"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=_uuid)
    user_id: Mapped[str] = mapped_column(String(36), ForeignKey("users.id"), nullable=False)
    org_id: Mapped[str] = mapped_column(String(36), ForeignKey("organisations.id"), nullable=False)
    role: Mapped[str] = mapped_column(String(50), default="member")  # owner, admin, member
    is_primary: Mapped[bool] = mapped_column(Boolean, default=True)

    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_utcnow)

    user = relationship("User", back_populates="memberships")
    organisation = relationship("Organisation", back_populates="memberships")


class BusinessVerification(Base):
    __tablename__ = "business_verifications"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=_uuid)
    org_id: Mapped[str] = mapped_column(String(36), ForeignKey("organisations.id"), nullable=False)

    document_type: Mapped[str | None] = mapped_column(String(100), nullable=True)
    document_path: Mapped[str | None] = mapped_column(String(500), nullable=True)

    status: Mapped[str] = mapped_column(Enum(VerificationStatus), default=VerificationStatus.PENDING)
    reviewer_id: Mapped[str | None] = mapped_column(String(36), ForeignKey("users.id"), nullable=True)
    reviewer_notes: Mapped[str | None] = mapped_column(Text, nullable=True)
    verified_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_utcnow)

    organisation = relationship("Organisation", back_populates="verifications")
