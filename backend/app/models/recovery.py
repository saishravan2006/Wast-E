"""Recovery job, batch splits, weight records, processing events, QC, shipments, residuals."""

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


class RecoveryStatus(str, PyEnum):
    REQUESTED = "requested"
    SCREENING = "screening"
    SAMPLE_SCHEDULED = "sample_scheduled"
    ASSESSMENT_RECORDED = "assessment_recorded"
    ROUTE_PROPOSED = "route_proposed"
    QUOTE_ISSUED = "quote_issued"
    SELLER_APPROVED = "seller_approved"
    BUYER_COMMITTED = "buyer_committed"
    PICKUP_SCHEDULED = "pickup_scheduled"
    RECEIVED = "received"
    PROCESSING = "processing"
    QUALITY_CHECK = "quality_check"
    DISPATCH = "dispatch"
    BUYER_ACCEPTANCE = "buyer_acceptance"
    SETTLEMENT = "settlement"
    CLOSED = "closed"
    DECLINED = "declined"
    CANCELLED = "cancelled"
    ON_HOLD = "on_hold"
    REASSESSMENT_REQUIRED = "reassessment_required"
    DISPUTED = "disputed"


RECOVERY_TRANSITIONS = {
    RecoveryStatus.REQUESTED: [RecoveryStatus.SCREENING, RecoveryStatus.DECLINED, RecoveryStatus.CANCELLED],
    RecoveryStatus.SCREENING: [RecoveryStatus.SAMPLE_SCHEDULED, RecoveryStatus.DECLINED, RecoveryStatus.CANCELLED],
    RecoveryStatus.SAMPLE_SCHEDULED: [RecoveryStatus.ASSESSMENT_RECORDED, RecoveryStatus.CANCELLED],
    RecoveryStatus.ASSESSMENT_RECORDED: [RecoveryStatus.ROUTE_PROPOSED, RecoveryStatus.DECLINED],
    RecoveryStatus.ROUTE_PROPOSED: [RecoveryStatus.QUOTE_ISSUED, RecoveryStatus.DECLINED],
    RecoveryStatus.QUOTE_ISSUED: [RecoveryStatus.SELLER_APPROVED, RecoveryStatus.DECLINED, RecoveryStatus.CANCELLED],
    RecoveryStatus.SELLER_APPROVED: [RecoveryStatus.BUYER_COMMITTED, RecoveryStatus.ON_HOLD, RecoveryStatus.CANCELLED],
    RecoveryStatus.BUYER_COMMITTED: [RecoveryStatus.PICKUP_SCHEDULED, RecoveryStatus.CANCELLED],
    RecoveryStatus.PICKUP_SCHEDULED: [RecoveryStatus.RECEIVED, RecoveryStatus.CANCELLED],
    RecoveryStatus.RECEIVED: [RecoveryStatus.PROCESSING, RecoveryStatus.REASSESSMENT_REQUIRED],
    RecoveryStatus.PROCESSING: [RecoveryStatus.QUALITY_CHECK, RecoveryStatus.ON_HOLD],
    RecoveryStatus.QUALITY_CHECK: [RecoveryStatus.DISPATCH, RecoveryStatus.REASSESSMENT_REQUIRED],
    RecoveryStatus.REASSESSMENT_REQUIRED: [RecoveryStatus.ASSESSMENT_RECORDED, RecoveryStatus.DECLINED],
    RecoveryStatus.DISPATCH: [RecoveryStatus.BUYER_ACCEPTANCE],
    RecoveryStatus.BUYER_ACCEPTANCE: [RecoveryStatus.SETTLEMENT, RecoveryStatus.DISPUTED],
    RecoveryStatus.DISPUTED: [RecoveryStatus.SETTLEMENT, RecoveryStatus.CANCELLED],
    RecoveryStatus.SETTLEMENT: [RecoveryStatus.CLOSED],
    RecoveryStatus.ON_HOLD: [RecoveryStatus.PROCESSING, RecoveryStatus.CANCELLED, RecoveryStatus.REASSESSMENT_REQUIRED],
    RecoveryStatus.DECLINED: [],
    RecoveryStatus.CANCELLED: [],
    RecoveryStatus.CLOSED: [],
}


class RecoveryJob(Base):
    __tablename__ = "recovery_jobs"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=_uuid)
    listing_id: Mapped[str] = mapped_column(String(36), ForeignKey("listings.id"), nullable=False)
    order_id: Mapped[str | None] = mapped_column(String(36), ForeignKey("orders.id"), nullable=True)
    quote_id: Mapped[str | None] = mapped_column(String(36), ForeignKey("quotes.id"), nullable=True)
    operator_id: Mapped[str | None] = mapped_column(String(36), ForeignKey("users.id"), nullable=True)

    seller_org_id: Mapped[str] = mapped_column(String(36), ForeignKey("organisations.id"), nullable=False)
    buyer_org_id: Mapped[str | None] = mapped_column(String(36), ForeignKey("organisations.id"), nullable=True)

    status: Mapped[str] = mapped_column(Enum(RecoveryStatus), default=RecoveryStatus.REQUESTED)

    incoming_weight_grams: Mapped[int | None] = mapped_column(Integer, nullable=True)
    processed_output_grams: Mapped[int | None] = mapped_column(Integer, nullable=True)
    residue_grams: Mapped[int | None] = mapped_column(Integer, nullable=True)
    loss_grams: Mapped[int | None] = mapped_column(Integer, nullable=True)
    loss_notes: Mapped[str | None] = mapped_column(Text, nullable=True)  # measurement uncertainty

    batch_code: Mapped[str | None] = mapped_column(String(50), nullable=True)

    is_demo: Mapped[bool] = mapped_column(Boolean, default=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_utcnow, onupdate=_utcnow)

    weight_records = relationship("WeightRecord", back_populates="job", cascade="all, delete-orphan")
    processing_events = relationship("ProcessingEvent", back_populates="job", cascade="all, delete-orphan")
    quality_checks = relationship("QualityCheck", back_populates="job", cascade="all, delete-orphan")
    children = relationship("BatchSplit", foreign_keys="BatchSplit.parent_job_id",
                            back_populates="parent_job", cascade="all, delete-orphan")
    residual_destinations = relationship("ResidualDestination", back_populates="job", cascade="all, delete-orphan")


class BatchSplit(Base):
    """Parent-child relationship for split batches."""
    __tablename__ = "batch_splits"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=_uuid)
    parent_job_id: Mapped[str] = mapped_column(String(36), ForeignKey("recovery_jobs.id"), nullable=False)
    child_job_id: Mapped[str] = mapped_column(String(36), ForeignKey("recovery_jobs.id"), nullable=False)
    split_reason: Mapped[str | None] = mapped_column(Text, nullable=True)
    fraction_description: Mapped[str | None] = mapped_column(String(255), nullable=True)
    weight_grams: Mapped[int | None] = mapped_column(Integer, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_utcnow)

    parent_job = relationship("RecoveryJob", foreign_keys=[parent_job_id], back_populates="children")


class WeightRecord(Base):
    """Immutable weight record at a processing stage."""
    __tablename__ = "weight_records"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=_uuid)
    job_id: Mapped[str] = mapped_column(String(36), ForeignKey("recovery_jobs.id"), nullable=False)
    stage: Mapped[str] = mapped_column(String(50), nullable=False)  # incoming, sorted, processed, output, residue
    weight_grams: Mapped[int] = mapped_column(Integer, nullable=False)
    recorded_by: Mapped[str] = mapped_column(String(36), ForeignKey("users.id"), nullable=False)
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)
    measurement_uncertainty: Mapped[str | None] = mapped_column(String(100), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_utcnow)

    job = relationship("RecoveryJob", back_populates="weight_records")


class ProcessingEvent(Base):
    __tablename__ = "processing_events"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=_uuid)
    job_id: Mapped[str] = mapped_column(String(36), ForeignKey("recovery_jobs.id"), nullable=False)
    event_type: Mapped[str] = mapped_column(String(100), nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    operator_id: Mapped[str] = mapped_column(String(36), ForeignKey("users.id"), nullable=False)
    data: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_utcnow)

    job = relationship("RecoveryJob", back_populates="processing_events")


class QualityCheck(Base):
    __tablename__ = "quality_checks"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=_uuid)
    job_id: Mapped[str] = mapped_column(String(36), ForeignKey("recovery_jobs.id"), nullable=False)
    checker_id: Mapped[str] = mapped_column(String(36), ForeignKey("users.id"), nullable=False)
    passed: Mapped[bool] = mapped_column(Boolean, nullable=False)
    measurements: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)
    failure_reason: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_utcnow)

    job = relationship("RecoveryJob", back_populates="quality_checks")


class Shipment(Base):
    __tablename__ = "shipments"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=_uuid)
    order_id: Mapped[str] = mapped_column(String(36), ForeignKey("orders.id"), nullable=False)
    shipment_type: Mapped[str] = mapped_column(String(20), default="delivery")  # pickup, delivery
    carrier: Mapped[str | None] = mapped_column(String(255), nullable=True)
    tracking_number: Mapped[str | None] = mapped_column(String(255), nullable=True)
    status: Mapped[str] = mapped_column(String(50), default="scheduled")
    pickup_date: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    delivery_date: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_utcnow, onupdate=_utcnow)


class ResidualDestination(Base):
    """Where non-recoverable residues go."""
    __tablename__ = "residual_destinations"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=_uuid)
    job_id: Mapped[str] = mapped_column(String(36), ForeignKey("recovery_jobs.id"), nullable=False)
    destination_type: Mapped[str] = mapped_column(String(100), nullable=False)
    # additional_recovery, energy_recovery, specialist_treatment, disposal
    handler: Mapped[str | None] = mapped_column(String(255), nullable=True)
    quantity_grams: Mapped[int | None] = mapped_column(Integer, nullable=True)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_utcnow)

    job = relationship("RecoveryJob", back_populates="residual_destinations")
