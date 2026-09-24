"""Buyer requirement model with material-specific quality fields."""

import uuid
from datetime import datetime, timezone

from sqlalchemy import String, Boolean, DateTime, ForeignKey, Text, Integer, JSON, Enum
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base
from app.models.listing import MaterialCategory, PhysicalForm


def _utcnow():
    return datetime.now(timezone.utc)


def _uuid():
    return str(uuid.uuid4())


class BuyerRequirement(Base):
    __tablename__ = "buyer_requirements"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=_uuid)
    org_id: Mapped[str] = mapped_column(String(36), ForeignKey("organisations.id"), nullable=False)
    created_by: Mapped[str] = mapped_column(String(36), ForeignKey("users.id"), nullable=False)

    title: Mapped[str] = mapped_column(String(255), nullable=False)
    material_category: Mapped[str] = mapped_column(Enum(MaterialCategory), nullable=False)
    material_grade: Mapped[str | None] = mapped_column(String(100), nullable=True)
    acceptable_forms: Mapped[str | None] = mapped_column(JSON, nullable=True)  # list of PhysicalForm values

    # Quantity
    required_quantity_grams: Mapped[int] = mapped_column(Integer, nullable=False)
    quantity_unit: Mapped[str] = mapped_column(String(10), default="kg")

    # Location
    delivery_city: Mapped[str] = mapped_column(String(100), nullable=False)
    delivery_state: Mapped[str] = mapped_column(String(100), nullable=False)
    delivery_pincode: Mapped[str | None] = mapped_column(String(10), nullable=True)

    # Commercial
    target_price_min_paise: Mapped[int | None] = mapped_column(Integer, nullable=True)
    target_price_max_paise: Mapped[int | None] = mapped_column(Integer, nullable=True)
    price_unit: Mapped[str] = mapped_column(String(20), default="per_kg")
    required_by: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    # Quality specifications — material-specific, stored as JSON
    # Examples: {"max_moisture_pct": 5, "max_contamination_pct": 2, "allowed_colours": ["natural", "white"]}
    quality_specs: Mapped[dict | None] = mapped_column(JSON, nullable=True)

    # Sampling
    sampling_method: Mapped[str | None] = mapped_column(String(255), nullable=True)
    acceptance_method: Mapped[str | None] = mapped_column(String(255), nullable=True)

    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    spec_document_path: Mapped[str | None] = mapped_column(String(500), nullable=True)

    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    is_demo: Mapped[bool] = mapped_column(Boolean, default=False)

    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_utcnow, onupdate=_utcnow)
