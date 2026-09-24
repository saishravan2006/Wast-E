"""Assessment and measurement models for recovery evaluation."""

import uuid
from datetime import datetime, timezone
from enum import Enum as PyEnum

from sqlalchemy import String, Boolean, DateTime, ForeignKey, Text, Integer, Enum, JSON, Float
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base


def _utcnow():
    return datetime.now(timezone.utc)


def _uuid():
    return str(uuid.uuid4())


class AssessmentOutcome(str, PyEnum):
    SUITABLE_DIRECT_SALE = "suitable_direct_sale"
    NEEDS_PROCESSING = "needs_processing"
    CONTAINS_RECOVERABLE_RESIDUALS = "contains_recoverable_residuals"
    NOT_VIABLE = "not_viable"
    FURTHER_ASSESSMENT_NEEDED = "further_assessment_needed"


class Assessment(Base):
    __tablename__ = "assessments"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=_uuid)
    listing_id: Mapped[str] = mapped_column(String(36), ForeignKey("listings.id"), nullable=False)
    assessor_id: Mapped[str] = mapped_column(String(36), ForeignKey("users.id"), nullable=False)

    # Sampling
    sampling_date: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    sampling_method: Mapped[str] = mapped_column(String(255), nullable=False)
    sample_size: Mapped[str] = mapped_column(String(100), nullable=False)  # e.g. "5 kg from 3 locations"

    # Composition
    observed_composition: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    # e.g. {"hdpe": 60, "ldpe": 25, "pp": 10, "contaminants": 5}

    moisture_pct: Mapped[float | None] = mapped_column(Float, nullable=True)
    contamination_pct: Mapped[float | None] = mapped_column(Float, nullable=True)

    # Recovery estimate
    estimated_recoverable_min_grams: Mapped[int | None] = mapped_column(Integer, nullable=True)
    estimated_recoverable_max_grams: Mapped[int | None] = mapped_column(Integer, nullable=True)
    proposed_processing_steps: Mapped[str | None] = mapped_column(JSON, nullable=True)  # list of steps
    suitable_buyer_requirements: Mapped[str | None] = mapped_column(Text, nullable=True)

    uncertainties: Mapped[str | None] = mapped_column(Text, nullable=True)
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)

    outcome: Mapped[str] = mapped_column(Enum(AssessmentOutcome), nullable=False)

    is_demo: Mapped[bool] = mapped_column(Boolean, default=False)

    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_utcnow, onupdate=_utcnow)

    measurements = relationship("AssessmentMeasurement", back_populates="assessment", cascade="all, delete-orphan")


class AssessmentMeasurement(Base):
    """Individual test result within an assessment."""
    __tablename__ = "assessment_measurements"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=_uuid)
    assessment_id: Mapped[str] = mapped_column(String(36), ForeignKey("assessments.id"), nullable=False)

    parameter: Mapped[str] = mapped_column(String(100), nullable=False)  # e.g. "moisture", "MFI"
    value: Mapped[float] = mapped_column(Float, nullable=False)
    unit: Mapped[str] = mapped_column(String(50), nullable=False)
    test_method: Mapped[str | None] = mapped_column(String(255), nullable=True)
    uncertainty: Mapped[float | None] = mapped_column(Float, nullable=True)
    is_estimated: Mapped[bool] = mapped_column(Boolean, default=False)  # never turn estimate into measured

    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_utcnow)

    assessment = relationship("Assessment", back_populates="measurements")
