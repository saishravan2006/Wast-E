"""Pydantic schemas for API request/response validation."""

from __future__ import annotations

from datetime import datetime
from pydantic import BaseModel, EmailStr, Field
from typing import Any


# ── Auth ─────────────────────────────────────────
class RegisterRequest(BaseModel):
    email: EmailStr
    password: str = Field(min_length=6)
    full_name: str = Field(min_length=1)
    phone: str | None = None
    is_seller: bool = False
    is_buyer: bool = False
    org_name: str | None = None
    org_type: str = "other"

class LoginRequest(BaseModel):
    email: EmailStr
    password: str

class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"

class UserResponse(BaseModel):
    id: str
    email: str
    full_name: str
    phone: str | None
    is_seller: bool
    is_buyer: bool
    is_operator: bool
    is_admin: bool
    is_demo: bool
    org_id: str | None = None
    org_name: str | None = None
    created_at: datetime

    class Config:
        from_attributes = True


# ── Organisation ──────────────────────────────────
class OrgResponse(BaseModel):
    id: str
    name: str
    org_type: str
    gstin: str | None
    city: str | None
    state: str | None
    pincode: str | None
    verification_status: str
    is_demo: bool

    class Config:
        from_attributes = True


# ── Listings ──────────────────────────────────────
class ListingCreate(BaseModel):
    title: str = Field(min_length=3)
    material_category: str
    material_grade: str | None = None
    grade_unknown: bool = False
    quantity_grams: int = Field(gt=0)
    quantity_unit: str = "kg"
    physical_form: str = "loose"
    description: str | None = None

    rejection_reason: str
    rejection_details: str | None = None
    material_source: str | None = None
    known_contents: str | None = None
    has_hazardous_contamination: bool = False

    city: str
    state: str
    pincode: str
    pickup_address: str | None = None
    asking_price_paise: int | None = None
    price_unit: str = "per_kg"
    request_quote: bool = False
    loading_arrangements: str | None = None
    pickup_availability: str | None = None
    ownership_confirmed: bool = False
    preferred_route: str = "help_me_decide"
    status: str = "draft"

class ListingUpdate(BaseModel):
    title: str | None = None
    material_grade: str | None = None
    quantity_grams: int | None = None
    physical_form: str | None = None
    description: str | None = None
    rejection_details: str | None = None
    asking_price_paise: int | None = None
    request_quote: bool | None = None
    preferred_route: str | None = None
    status: str | None = None

class ListingResponse(BaseModel):
    id: str
    org_id: str
    created_by: str
    title: str
    material_category: str
    material_grade: str | None
    grade_unknown: bool
    quantity_grams: int
    quantity_unit: str
    physical_form: str
    description: str | None
    rejection_reason: str
    rejection_details: str | None
    material_source: str | None
    has_hazardous_contamination: bool
    city: str
    state: str
    pincode: str
    asking_price_paise: int | None
    price_unit: str
    request_quote: bool
    preferred_route: str
    status: str
    has_assessment: bool
    assessment_date: datetime | None
    is_demo: bool
    created_at: datetime
    updated_at: datetime
    photos: list[PhotoResponse] = []
    org_name: str | None = None
    seller_name: str | None = None

    class Config:
        from_attributes = True

class PhotoResponse(BaseModel):
    id: str
    file_path: str
    caption: str | None
    sort_order: int

    class Config:
        from_attributes = True


# ── Buyer Requirements ────────────────────────────
class RequirementCreate(BaseModel):
    title: str
    material_category: str
    material_grade: str | None = None
    acceptable_forms: list[str] | None = None
    required_quantity_grams: int = Field(gt=0)
    quantity_unit: str = "kg"
    delivery_city: str
    delivery_state: str
    delivery_pincode: str | None = None
    target_price_min_paise: int | None = None
    target_price_max_paise: int | None = None
    price_unit: str = "per_kg"
    required_by: datetime | None = None
    quality_specs: dict | None = None
    sampling_method: str | None = None
    acceptance_method: str | None = None
    description: str | None = None

class RequirementResponse(BaseModel):
    id: str
    org_id: str
    title: str
    material_category: str
    material_grade: str | None
    acceptable_forms: list[str] | None
    required_quantity_grams: int
    quantity_unit: str
    delivery_city: str
    delivery_state: str
    target_price_min_paise: int | None
    target_price_max_paise: int | None
    quality_specs: dict | None
    required_by: datetime | None
    is_active: bool
    created_at: datetime
    org_name: str | None = None

    class Config:
        from_attributes = True


# ── Offers ────────────────────────────────────────
class OfferCreate(BaseModel):
    listing_id: str
    offered_price_paise: int = Field(gt=0)
    price_unit: str = "per_kg"
    offered_quantity_grams: int = Field(gt=0)
    terms: str | None = None
    message: str | None = None

class OfferResponse(BaseModel):
    id: str
    listing_id: str
    buyer_org_id: str
    offered_price_paise: int
    price_unit: str
    offered_quantity_grams: int
    terms: str | None
    message: str | None
    status: str
    created_at: datetime
    buyer_name: str | None = None

    class Config:
        from_attributes = True


# ── Assessments ───────────────────────────────────
class AssessmentCreate(BaseModel):
    listing_id: str
    sampling_date: datetime
    sampling_method: str
    sample_size: str
    observed_composition: dict | None = None
    moisture_pct: float | None = None
    contamination_pct: float | None = None
    estimated_recoverable_min_grams: int | None = None
    estimated_recoverable_max_grams: int | None = None
    proposed_processing_steps: list[str] | None = None
    suitable_buyer_requirements: str | None = None
    uncertainties: str | None = None
    notes: str | None = None
    outcome: str

class AssessmentResponse(BaseModel):
    id: str
    listing_id: str
    assessor_id: str
    sampling_date: datetime
    sampling_method: str
    sample_size: str
    observed_composition: dict | None
    moisture_pct: float | None
    contamination_pct: float | None
    estimated_recoverable_min_grams: int | None
    estimated_recoverable_max_grams: int | None
    proposed_processing_steps: list | None
    uncertainties: str | None
    outcome: str
    created_at: datetime

    class Config:
        from_attributes = True


# ── Quotes ────────────────────────────────────────
class QuoteVersionCreate(BaseModel):
    listing_id: str
    assessment_id: str | None = None
    commercial_model: str
    estimated_incoming_weight_grams: int
    expected_output_min_grams: int | None = None
    expected_output_max_grams: int | None = None
    sale_price_paise_per_kg: int | None = None
    purchase_price_paise_per_kg: int | None = None
    transport_cost_paise: int = 0
    assessment_cost_paise: int = 0
    processing_cost_paise: int = 0
    packaging_cost_paise: int = 0
    residue_handling_cost_paise: int = 0
    platform_fee_paise: int = 0
    tax_paise: int = 0
    estimated_seller_proceeds_paise: int | None = None
    assumptions: str | None = None
    additional_cost_responsibility: str | None = None
    is_estimate: bool = True
    expires_at: datetime | None = None

class QuoteResponse(BaseModel):
    id: str
    listing_id: str
    commercial_model: str
    current_version: int
    status: str
    created_at: datetime
    versions: list[QuoteVersionResponse] = []

    class Config:
        from_attributes = True

class QuoteVersionResponse(BaseModel):
    id: str
    version_number: int
    estimated_incoming_weight_grams: int
    expected_output_min_grams: int | None
    expected_output_max_grams: int | None
    sale_price_paise_per_kg: int | None
    purchase_price_paise_per_kg: int | None
    transport_cost_paise: int
    assessment_cost_paise: int
    processing_cost_paise: int
    packaging_cost_paise: int
    residue_handling_cost_paise: int
    platform_fee_paise: int
    tax_paise: int
    estimated_seller_proceeds_paise: int | None
    assumptions: str | None
    is_estimate: bool
    expires_at: datetime | None
    created_at: datetime

    class Config:
        from_attributes = True


# ── Orders ────────────────────────────────────────
class OrderCreate(BaseModel):
    listing_id: str
    offer_id: str | None = None
    quote_id: str | None = None
    buyer_org_id: str
    agreed_material: str
    agreed_quantity_grams: int
    agreed_price_paise: int
    price_unit: str = "per_kg"
    delivery_terms: str | None = None
    order_type: str = "direct"

class OrderResponse(BaseModel):
    id: str
    listing_id: str
    seller_org_id: str
    buyer_org_id: str
    agreed_material: str
    agreed_quantity_grams: int
    agreed_price_paise: int
    price_unit: str
    delivery_terms: str | None
    status: str
    order_type: str
    is_demo: bool
    created_at: datetime
    updated_at: datetime
    seller_name: str | None = None
    buyer_name: str | None = None

    class Config:
        from_attributes = True


# ── Recovery Jobs ─────────────────────────────────
class RecoveryJobResponse(BaseModel):
    id: str
    listing_id: str
    order_id: str | None
    quote_id: str | None
    operator_id: str | None
    seller_org_id: str
    buyer_org_id: str | None
    status: str
    incoming_weight_grams: int | None
    processed_output_grams: int | None
    residue_grams: int | None
    loss_grams: int | None
    loss_notes: str | None
    batch_code: str | None
    is_demo: bool
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


# ── Payments ──────────────────────────────────────
class PaymentResponse(BaseModel):
    id: str
    order_id: str
    amount_paise: int
    currency: str
    status: str
    is_simulated: bool
    created_at: datetime

    class Config:
        from_attributes = True

class SettlementResponse(BaseModel):
    id: str
    order_id: str
    breakdown: dict
    total_seller_proceeds_paise: int
    total_buyer_payment_paise: int
    is_simulated: bool
    created_at: datetime

    class Config:
        from_attributes = True


# ── Messages ──────────────────────────────────────
class MessageCreate(BaseModel):
    order_id: str | None = None
    listing_id: str | None = None
    recipient_id: str | None = None
    body: str

class MessageResponse(BaseModel):
    id: str
    order_id: str | None
    listing_id: str | None
    sender_id: str
    body: str
    is_read: bool
    created_at: datetime
    sender_name: str | None = None

    class Config:
        from_attributes = True


# ── Disputes ──────────────────────────────────────
class DisputeCreate(BaseModel):
    order_id: str
    dispute_type: str
    description: str
    agreed_specification: str | None = None
    inspection_evidence: str | None = None
    relevant_weights: dict | None = None
    requested_resolution: str | None = None

class DisputeResponse(BaseModel):
    id: str
    order_id: str
    raised_by: str
    dispute_type: str
    description: str
    status: str
    requested_resolution: str | None
    admin_resolution: str | None
    created_at: datetime

    class Config:
        from_attributes = True


# ── Matching ──────────────────────────────────────
class MatchResult(BaseModel):
    listing_id: str | None = None
    requirement_id: str | None = None
    listing_title: str | None = None
    requirement_title: str | None = None
    match_score: str  # "potential", "partial", "strong" — not a numeric AI score
    matches: list[str]  # what matches
    mismatches: list[str]  # known mismatches
    info_needed: list[str]  # information still needed
    may_need_treatment: bool = False


# ── Notifications ─────────────────────────────────
class NotificationResponse(BaseModel):
    id: str
    notification_type: str
    title: str
    content: str
    link: str | None
    is_read: bool
    created_at: datetime

    class Config:
        from_attributes = True


# ── Generic ───────────────────────────────────────
class PaginatedResponse(BaseModel):
    items: list[Any]
    total: int
    page: int
    page_size: int
    pages: int
