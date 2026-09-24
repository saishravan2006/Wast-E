"""Listings CRUD, search, and status transitions."""

import math
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from sqlalchemy import or_

from app.database import get_db
from app.auth import get_current_user, get_optional_user, get_user_org_id, require_seller, require_admin
from app.models.user import User
from app.models.listing import Listing, ListingStatus, MaterialCategory
from app.models.organisation import Organisation, OrgMembership
from app.models.audit import AuditEvent
from app.schemas import ListingCreate, ListingUpdate, ListingResponse, PaginatedResponse

router = APIRouter(prefix="/api/listings", tags=["listings"])


def _enrich(listing: Listing, db: Session) -> ListingResponse:
    org = db.query(Organisation).filter(Organisation.id == listing.org_id).first()
    creator = db.query(User).filter(User.id == listing.created_by).first()
    photos = [{"id": p.id, "file_path": p.file_path, "caption": p.caption, "sort_order": p.sort_order}
              for p in listing.photos]
    return ListingResponse(
        **{c.name: getattr(listing, c.name) for c in listing.__table__.columns},
        photos=photos,
        org_name=org.name if org else None,
        seller_name=creator.full_name if creator else None,
    )


@router.get("", response_model=PaginatedResponse)
def list_listings(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    material_category: str | None = None,
    material_grade: str | None = None,
    city: str | None = None,
    state: str | None = None,
    pincode: str | None = None,
    min_quantity_grams: int | None = None,
    max_quantity_grams: int | None = None,
    min_price_paise: int | None = None,
    max_price_paise: int | None = None,
    rejection_reason: str | None = None,
    status: str | None = None,
    preferred_route: str | None = None,
    has_assessment: bool | None = None,
    search: str | None = None,
    sort_by: str = "created_at",
    sort_order: str = "desc",
    db: Session = Depends(get_db),
    user: User | None = Depends(get_optional_user),
):
    q = db.query(Listing)

    # Public browse shows only active listings
    if not user or not user.is_admin:
        if status:
            q = q.filter(Listing.status == status)
        else:
            q = q.filter(Listing.status == ListingStatus.ACTIVE)

    if material_category:
        q = q.filter(Listing.material_category == material_category)
    if material_grade:
        q = q.filter(Listing.material_grade.ilike(f"%{material_grade}%"))
    if city:
        q = q.filter(Listing.city.ilike(f"%{city}%"))
    if state:
        q = q.filter(Listing.state.ilike(f"%{state}%"))
    if pincode:
        q = q.filter(Listing.pincode == pincode)
    if min_quantity_grams:
        q = q.filter(Listing.quantity_grams >= min_quantity_grams)
    if max_quantity_grams:
        q = q.filter(Listing.quantity_grams <= max_quantity_grams)
    if min_price_paise:
        q = q.filter(Listing.asking_price_paise >= min_price_paise)
    if max_price_paise:
        q = q.filter(Listing.asking_price_paise <= max_price_paise)
    if rejection_reason:
        q = q.filter(Listing.rejection_reason == rejection_reason)
    if preferred_route:
        q = q.filter(Listing.preferred_route == preferred_route)
    if has_assessment is not None:
        q = q.filter(Listing.has_assessment == has_assessment)
    if search:
        q = q.filter(or_(
            Listing.title.ilike(f"%{search}%"),
            Listing.description.ilike(f"%{search}%"),
            Listing.material_grade.ilike(f"%{search}%"),
        ))

    # Sorting
    sort_col = getattr(Listing, sort_by, Listing.created_at)
    if sort_order == "asc":
        q = q.order_by(sort_col.asc())
    else:
        q = q.order_by(sort_col.desc())

    total = q.count()
    items = q.offset((page - 1) * page_size).limit(page_size).all()

    return PaginatedResponse(
        items=[_enrich(item, db) for item in items],
        total=total, page=page, page_size=page_size,
        pages=math.ceil(total / page_size) if total > 0 else 0,
    )


@router.get("/my", response_model=list[ListingResponse])
def my_listings(
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    org_id = get_user_org_id(user, db)
    listings = db.query(Listing).filter(Listing.org_id == org_id).order_by(Listing.created_at.desc()).all()
    return [_enrich(l, db) for l in listings]


@router.get("/{listing_id}", response_model=ListingResponse)
def get_listing(listing_id: str, db: Session = Depends(get_db)):
    listing = db.query(Listing).filter(Listing.id == listing_id).first()
    if not listing:
        raise HTTPException(status_code=404, detail="Listing not found")
    return _enrich(listing, db)


@router.post("", response_model=ListingResponse)
def create_listing(
    req: ListingCreate,
    user: User = Depends(require_seller),
    db: Session = Depends(get_db),
):
    org_id = get_user_org_id(user, db)
    listing = Listing(
        org_id=org_id, created_by=user.id,
        **req.model_dump(),
    )
    db.add(listing)

    # Audit
    db.add(AuditEvent(actor_id=user.id, entity_type="listing", entity_id=listing.id,
                      action="created", new_values=req.model_dump()))
    db.commit()
    db.refresh(listing)
    return _enrich(listing, db)


@router.patch("/{listing_id}", response_model=ListingResponse)
def update_listing(
    listing_id: str,
    req: ListingUpdate,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    listing = db.query(Listing).filter(Listing.id == listing_id).first()
    if not listing:
        raise HTTPException(status_code=404, detail="Listing not found")

    # Permission check
    org_id = get_user_org_id(user, db)
    if listing.org_id != org_id and not user.is_admin:
        raise HTTPException(status_code=403, detail="Not authorised")

    updates = req.model_dump(exclude_unset=True)
    old_values = {k: getattr(listing, k) for k in updates}
    for k, v in updates.items():
        setattr(listing, k, v)

    db.add(AuditEvent(actor_id=user.id, entity_type="listing", entity_id=listing.id,
                      action="updated", old_values=old_values, new_values=updates))
    db.commit()
    db.refresh(listing)
    return _enrich(listing, db)


@router.post("/{listing_id}/submit")
def submit_for_review(listing_id: str, user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    listing = db.query(Listing).filter(Listing.id == listing_id).first()
    if not listing:
        raise HTTPException(status_code=404, detail="Listing not found")
    org_id = get_user_org_id(user, db)
    if listing.org_id != org_id:
        raise HTTPException(status_code=403, detail="Not authorised")
    if listing.status != ListingStatus.DRAFT:
        raise HTTPException(status_code=400, detail="Only draft listings can be submitted")

    listing.status = ListingStatus.PENDING_REVIEW
    db.add(AuditEvent(actor_id=user.id, entity_type="listing", entity_id=listing.id,
                      action="submitted_for_review"))
    db.commit()
    return {"status": "submitted"}


@router.post("/{listing_id}/approve")
def approve_listing(listing_id: str, user: User = Depends(require_admin), db: Session = Depends(get_db)):
    listing = db.query(Listing).filter(Listing.id == listing_id).first()
    if not listing:
        raise HTTPException(status_code=404, detail="Listing not found")
    if listing.status != ListingStatus.PENDING_REVIEW:
        raise HTTPException(status_code=400, detail="Listing is not pending review")

    listing.status = ListingStatus.ACTIVE
    db.add(AuditEvent(actor_id=user.id, entity_type="listing", entity_id=listing.id,
                      action="approved"))
    db.commit()
    return {"status": "active"}
