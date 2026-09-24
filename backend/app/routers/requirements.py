"""Buyer requirements CRUD and matching engine."""

import math
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from app.database import get_db
from app.auth import get_current_user, get_optional_user, get_user_org_id, require_buyer
from app.models.user import User
from app.models.requirement import BuyerRequirement
from app.models.listing import Listing, ListingStatus
from app.models.organisation import Organisation
from app.schemas import RequirementCreate, RequirementResponse, MatchResult, PaginatedResponse

router = APIRouter(prefix="/api/requirements", tags=["requirements"])


def _enrich(req: BuyerRequirement, db: Session) -> RequirementResponse:
    org = db.query(Organisation).filter(Organisation.id == req.org_id).first()
    return RequirementResponse(
        **{c.name: getattr(req, c.name) for c in req.__table__.columns},
        org_name=org.name if org else None,
    )


@router.get("", response_model=PaginatedResponse)
def list_requirements(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    material_category: str | None = None,
    city: str | None = None,
    db: Session = Depends(get_db),
):
    q = db.query(BuyerRequirement).filter(BuyerRequirement.is_active == True)
    if material_category:
        q = q.filter(BuyerRequirement.material_category == material_category)
    if city:
        q = q.filter(BuyerRequirement.delivery_city.ilike(f"%{city}%"))
    q = q.order_by(BuyerRequirement.created_at.desc())
    total = q.count()
    items = q.offset((page - 1) * page_size).limit(page_size).all()
    return PaginatedResponse(
        items=[_enrich(r, db) for r in items],
        total=total, page=page, page_size=page_size,
        pages=math.ceil(total / page_size) if total > 0 else 0,
    )


@router.get("/my", response_model=list[RequirementResponse])
def my_requirements(user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    org_id = get_user_org_id(user, db)
    reqs = db.query(BuyerRequirement).filter(BuyerRequirement.org_id == org_id).order_by(
        BuyerRequirement.created_at.desc()).all()
    return [_enrich(r, db) for r in reqs]


@router.post("", response_model=RequirementResponse)
def create_requirement(
    req: RequirementCreate,
    user: User = Depends(require_buyer),
    db: Session = Depends(get_db),
):
    org_id = get_user_org_id(user, db)
    requirement = BuyerRequirement(org_id=org_id, created_by=user.id, **req.model_dump())
    db.add(requirement)
    db.commit()
    db.refresh(requirement)
    return _enrich(requirement, db)


@router.get("/{req_id}", response_model=RequirementResponse)
def get_requirement(req_id: str, db: Session = Depends(get_db)):
    requirement = db.query(BuyerRequirement).filter(BuyerRequirement.id == req_id).first()
    if not requirement:
        raise HTTPException(status_code=404, detail="Requirement not found")
    return _enrich(requirement, db)


@router.get("/{req_id}/matches", response_model=list[MatchResult])
def find_matches(req_id: str, db: Session = Depends(get_db)):
    """Rules-based matching — no AI scores, transparent logic."""
    requirement = db.query(BuyerRequirement).filter(BuyerRequirement.id == req_id).first()
    if not requirement:
        raise HTTPException(status_code=404, detail="Requirement not found")

    listings = db.query(Listing).filter(
        Listing.status == ListingStatus.ACTIVE,
        Listing.material_category == requirement.material_category,
    ).all()

    results = []
    for listing in listings:
        matches = []
        mismatches = []
        info_needed = []
        may_need_treatment = False

        # Material type match
        matches.append(f"Material category: {listing.material_category}")

        # Grade
        if requirement.material_grade and listing.material_grade:
            if listing.material_grade.lower() == requirement.material_grade.lower():
                matches.append(f"Grade matches: {listing.material_grade}")
            else:
                mismatches.append(f"Grade: listing has {listing.material_grade}, requirement needs {requirement.material_grade}")
        elif requirement.material_grade and listing.grade_unknown:
            info_needed.append("Material grade not declared by seller")

        # Quantity
        if listing.quantity_grams >= requirement.required_quantity_grams:
            matches.append("Sufficient quantity available")
        elif listing.quantity_grams >= requirement.required_quantity_grams * 0.5:
            mismatches.append(f"Partial quantity: {listing.quantity_grams}g available vs {requirement.required_quantity_grams}g needed")
        else:
            mismatches.append("Insufficient quantity")

        # Location
        if listing.state.lower() == requirement.delivery_state.lower():
            matches.append(f"Same state: {listing.state}")
            if listing.city.lower() == requirement.delivery_city.lower():
                matches.append(f"Same city: {listing.city}")
        else:
            info_needed.append(f"Listing in {listing.city}, {listing.state} — delivery to {requirement.delivery_city}")

        # Physical form
        if requirement.acceptable_forms:
            if listing.physical_form in requirement.acceptable_forms:
                matches.append(f"Acceptable form: {listing.physical_form}")
            else:
                mismatches.append(f"Form: listing is {listing.physical_form}, buyer accepts {requirement.acceptable_forms}")

        # Rejection reason implies possible treatment
        if listing.rejection_reason in ("contamination", "excess_moisture", "mixed_materials"):
            may_need_treatment = True
            info_needed.append(f"Rejected for {listing.rejection_reason} — treatment may be needed")

        # Assessment status
        if not listing.has_assessment:
            info_needed.append("No Wast-e assessment available yet")

        # Score determination
        if len(mismatches) == 0 and len(info_needed) <= 1:
            score = "strong"
        elif len(mismatches) <= 1:
            score = "potential"
        else:
            score = "partial"

        results.append(MatchResult(
            listing_id=listing.id,
            requirement_id=requirement.id,
            listing_title=listing.title,
            requirement_title=requirement.title,
            match_score=score,
            matches=matches,
            mismatches=mismatches,
            info_needed=info_needed,
            may_need_treatment=may_need_treatment,
        ))

    # Sort by score quality
    score_order = {"strong": 0, "potential": 1, "partial": 2}
    results.sort(key=lambda r: score_order.get(r.match_score, 3))
    return results
