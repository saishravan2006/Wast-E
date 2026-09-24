"""Offers, assessments, quotes, orders, recovery jobs, payments, messages, disputes, admin, uploads."""

from __future__ import annotations
import math, os, uuid, shutil
from datetime import datetime, timezone
from typing import Any

from fastapi import APIRouter, Depends, HTTPException, Query, UploadFile, File
from sqlalchemy.orm import Session

from app.database import get_db
from app.auth import (
    get_current_user, get_user_org_id, require_buyer, require_seller,
    require_operator, require_admin,
)
from app.config import settings
from app.models.user import User
from app.models.listing import Listing, ListingStatus
from app.models.organisation import Organisation, OrgMembership
from app.models.offer import Offer, OfferStatus
from app.models.assessment import Assessment, AssessmentMeasurement
from app.models.quote import Quote, QuoteVersion, QuoteStatus
from app.models.order import Order, OrderStatus, ORDER_TRANSITIONS, Approval
from app.models.recovery import (
    RecoveryJob, RecoveryStatus, RECOVERY_TRANSITIONS,
    WeightRecord, ProcessingEvent, QualityCheck, Shipment, ResidualDestination, BatchSplit,
)
from app.models.payment import PaymentRecord, PaymentStatus, Settlement
from app.models.messaging import Message, Dispute, Notification
from app.models.audit import AuditEvent
from app.schemas import (
    OfferCreate, OfferResponse, AssessmentCreate, AssessmentResponse,
    QuoteVersionCreate, QuoteResponse, QuoteVersionResponse,
    OrderCreate, OrderResponse, RecoveryJobResponse,
    PaymentResponse, SettlementResponse,
    MessageCreate, MessageResponse, DisputeCreate, DisputeResponse,
    NotificationResponse, PaginatedResponse, UserResponse, OrgResponse,
)


# ═══════════════════════════════════════════════════
#  OFFERS
# ═══════════════════════════════════════════════════
offers_router = APIRouter(prefix="/api/offers", tags=["offers"])


@offers_router.post("", response_model=OfferResponse)
def create_offer(req: OfferCreate, user: User = Depends(require_buyer), db: Session = Depends(get_db)):
    listing = db.query(Listing).filter(Listing.id == req.listing_id).first()
    if not listing:
        raise HTTPException(status_code=404, detail="Listing not found")
    if listing.status != ListingStatus.ACTIVE:
        raise HTTPException(status_code=400, detail="Listing is not accepting offers")

    org_id = get_user_org_id(user, db)
    offer = Offer(
        listing_id=req.listing_id, buyer_org_id=org_id, buyer_user_id=user.id,
        offered_price_paise=req.offered_price_paise, price_unit=req.price_unit,
        offered_quantity_grams=req.offered_quantity_grams,
        terms=req.terms, message=req.message,
    )
    db.add(offer)
    db.add(AuditEvent(actor_id=user.id, entity_type="offer", entity_id=offer.id, action="created"))
    db.commit()
    db.refresh(offer)
    org = db.query(Organisation).filter(Organisation.id == org_id).first()
    return OfferResponse(**{c.name: getattr(offer, c.name) for c in offer.__table__.columns},
                         buyer_name=org.name if org else None)


@offers_router.get("/listing/{listing_id}", response_model=list[OfferResponse])
def get_listing_offers(listing_id: str, user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    listing = db.query(Listing).filter(Listing.id == listing_id).first()
    if not listing:
        raise HTTPException(status_code=404, detail="Listing not found")
    org_id = get_user_org_id(user, db)
    if listing.org_id != org_id and not user.is_admin:
        # Buyers can only see their own offers
        offers = db.query(Offer).filter(Offer.listing_id == listing_id, Offer.buyer_org_id == org_id).all()
    else:
        offers = db.query(Offer).filter(Offer.listing_id == listing_id).all()
    results = []
    for o in offers:
        org = db.query(Organisation).filter(Organisation.id == o.buyer_org_id).first()
        results.append(OfferResponse(**{c.name: getattr(o, c.name) for c in o.__table__.columns},
                                     buyer_name=org.name if org else None))
    return results


@offers_router.post("/{offer_id}/accept")
def accept_offer(offer_id: str, user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    offer = db.query(Offer).filter(Offer.id == offer_id).first()
    if not offer:
        raise HTTPException(status_code=404, detail="Offer not found")
    listing = db.query(Listing).filter(Listing.id == offer.listing_id).first()
    org_id = get_user_org_id(user, db)
    if listing.org_id != org_id:
        raise HTTPException(status_code=403, detail="Not authorised")

    offer.status = OfferStatus.ACCEPTED
    listing.status = ListingStatus.OFFER_ACCEPTED

    # Create order from accepted offer
    order = Order(
        listing_id=listing.id, offer_id=offer.id,
        seller_org_id=listing.org_id, buyer_org_id=offer.buyer_org_id,
        agreed_material=listing.title, agreed_quantity_grams=offer.offered_quantity_grams,
        agreed_price_paise=offer.offered_price_paise, price_unit=offer.price_unit,
        order_type="direct",
    )
    db.add(order)
    db.add(AuditEvent(actor_id=user.id, entity_type="offer", entity_id=offer.id, action="accepted"))
    db.add(AuditEvent(actor_id=user.id, entity_type="order", entity_id=order.id, action="created"))
    db.commit()
    return {"status": "accepted", "order_id": order.id}


@offers_router.post("/{offer_id}/reject")
def reject_offer(offer_id: str, user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    offer = db.query(Offer).filter(Offer.id == offer_id).first()
    if not offer:
        raise HTTPException(status_code=404, detail="Offer not found")
    listing = db.query(Listing).filter(Listing.id == offer.listing_id).first()
    org_id = get_user_org_id(user, db)
    if listing.org_id != org_id:
        raise HTTPException(status_code=403, detail="Not authorised")
    offer.status = OfferStatus.REJECTED
    db.commit()
    return {"status": "rejected"}


# ═══════════════════════════════════════════════════
#  ASSESSMENTS
# ═══════════════════════════════════════════════════
assessments_router = APIRouter(prefix="/api/assessments", tags=["assessments"])


@assessments_router.post("", response_model=AssessmentResponse)
def create_assessment(req: AssessmentCreate, user: User = Depends(require_operator), db: Session = Depends(get_db)):
    assessment = Assessment(assessor_id=user.id, **req.model_dump())
    db.add(assessment)

    listing = db.query(Listing).filter(Listing.id == req.listing_id).first()
    if listing:
        listing.has_assessment = True
        listing.assessment_date = datetime.now(timezone.utc)
        listing.status = ListingStatus.UNDER_ASSESSMENT

    db.add(AuditEvent(actor_id=user.id, entity_type="assessment", entity_id=assessment.id, action="created"))
    db.commit()
    db.refresh(assessment)
    return AssessmentResponse(**{c.name: getattr(assessment, c.name) for c in assessment.__table__.columns})


@assessments_router.get("/listing/{listing_id}", response_model=list[AssessmentResponse])
def get_listing_assessments(listing_id: str, user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    assessments = db.query(Assessment).filter(Assessment.listing_id == listing_id).order_by(
        Assessment.created_at.desc()).all()
    return [AssessmentResponse(**{c.name: getattr(a, c.name) for c in a.__table__.columns}) for a in assessments]


# ═══════════════════════════════════════════════════
#  QUOTES
# ═══════════════════════════════════════════════════
quotes_router = APIRouter(prefix="/api/quotes", tags=["quotes"])


@quotes_router.post("", response_model=QuoteResponse)
def create_quote(req: QuoteVersionCreate, user: User = Depends(require_operator), db: Session = Depends(get_db)):
    # Create quote + first version
    quote = Quote(
        listing_id=req.listing_id, assessment_id=req.assessment_id,
        created_by=user.id, commercial_model=req.commercial_model,
    )
    db.add(quote)
    db.flush()

    version = QuoteVersion(
        quote_id=quote.id, version_number=1,
        **{k: v for k, v in req.model_dump().items()
           if k not in ("listing_id", "assessment_id", "commercial_model")},
    )
    db.add(version)
    quote.status = QuoteStatus.ISSUED
    db.add(AuditEvent(actor_id=user.id, entity_type="quote", entity_id=quote.id, action="created"))
    db.commit()
    db.refresh(quote)
    return _quote_response(quote, db)


@quotes_router.post("/{quote_id}/new-version", response_model=QuoteResponse)
def add_quote_version(quote_id: str, req: QuoteVersionCreate, user: User = Depends(require_operator), db: Session = Depends(get_db)):
    quote = db.query(Quote).filter(Quote.id == quote_id).first()
    if not quote:
        raise HTTPException(status_code=404, detail="Quote not found")
    # Supersede old version
    quote.current_version += 1
    quote.status = QuoteStatus.ISSUED  # re-issue with new version

    version = QuoteVersion(
        quote_id=quote.id, version_number=quote.current_version,
        **{k: v for k, v in req.model_dump().items()
           if k not in ("listing_id", "assessment_id", "commercial_model")},
    )
    db.add(version)
    db.add(AuditEvent(actor_id=user.id, entity_type="quote", entity_id=quote.id,
                      action="new_version", new_values={"version": quote.current_version}))
    db.commit()
    db.refresh(quote)
    return _quote_response(quote, db)


@quotes_router.get("/listing/{listing_id}", response_model=list[QuoteResponse])
def get_listing_quotes(listing_id: str, user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    quotes = db.query(Quote).filter(Quote.listing_id == listing_id).all()
    return [_quote_response(q, db) for q in quotes]


@quotes_router.post("/{quote_id}/approve")
def approve_quote(quote_id: str, version: int = Query(...), user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    """Seller approves a specific quote version."""
    quote = db.query(Quote).filter(Quote.id == quote_id).first()
    if not quote:
        raise HTTPException(status_code=404, detail="Quote not found")
    listing = db.query(Listing).filter(Listing.id == quote.listing_id).first()
    org_id = get_user_org_id(user, db)
    if listing.org_id != org_id:
        raise HTTPException(status_code=403, detail="Only the seller can approve quotes")
    if version != quote.current_version:
        raise HTTPException(status_code=400, detail=f"Version {version} is not the current version ({quote.current_version})")

    quote.status = QuoteStatus.SELLER_APPROVED
    db.add(Approval(entity_type="quote", entity_id=quote.id, approver_id=user.id,
                    decision="approved", version=version))
    db.add(AuditEvent(actor_id=user.id, entity_type="quote", entity_id=quote.id,
                      action="seller_approved", new_values={"version": version}))
    db.commit()
    return {"status": "approved", "version": version}


def _quote_response(quote: Quote, db: Session) -> QuoteResponse:
    versions = db.query(QuoteVersion).filter(QuoteVersion.quote_id == quote.id).order_by(
        QuoteVersion.version_number).all()
    return QuoteResponse(
        id=quote.id, listing_id=quote.listing_id, commercial_model=quote.commercial_model,
        current_version=quote.current_version, status=quote.status, created_at=quote.created_at,
        versions=[QuoteVersionResponse(**{c.name: getattr(v, c.name) for c in v.__table__.columns}) for v in versions],
    )


# ═══════════════════════════════════════════════════
#  ORDERS
# ═══════════════════════════════════════════════════
orders_router = APIRouter(prefix="/api/orders", tags=["orders"])


@orders_router.get("", response_model=list[OrderResponse])
def list_orders(user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    org_id = get_user_org_id(user, db)
    if user.is_admin:
        orders = db.query(Order).order_by(Order.created_at.desc()).all()
    else:
        orders = db.query(Order).filter(
            (Order.seller_org_id == org_id) | (Order.buyer_org_id == org_id)
        ).order_by(Order.created_at.desc()).all()
    return [_order_response(o, db) for o in orders]


@orders_router.get("/{order_id}", response_model=OrderResponse)
def get_order(order_id: str, user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    order = db.query(Order).filter(Order.id == order_id).first()
    if not order:
        raise HTTPException(status_code=404, detail="Order not found")
    org_id = get_user_org_id(user, db)
    if order.seller_org_id != org_id and order.buyer_org_id != org_id and not user.is_admin and not user.is_operator:
        raise HTTPException(status_code=403, detail="Not authorised")
    return _order_response(order, db)


@orders_router.post("/{order_id}/transition")
def transition_order(order_id: str, new_status: str = Query(...), user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    order = db.query(Order).filter(Order.id == order_id).first()
    if not order:
        raise HTTPException(status_code=404, detail="Order not found")
    current = OrderStatus(order.status)
    target = OrderStatus(new_status)
    allowed = ORDER_TRANSITIONS.get(current, [])
    if target not in allowed:
        raise HTTPException(status_code=400, detail=f"Cannot transition from {current.value} to {target.value}")

    old_status = order.status
    order.status = target
    db.add(AuditEvent(actor_id=user.id, entity_type="order", entity_id=order.id,
                      action="status_change", old_values={"status": old_status}, new_values={"status": new_status}))
    db.commit()
    return {"status": new_status}


def _order_response(order: Order, db: Session) -> OrderResponse:
    seller = db.query(Organisation).filter(Organisation.id == order.seller_org_id).first()
    buyer = db.query(Organisation).filter(Organisation.id == order.buyer_org_id).first()
    return OrderResponse(
        **{c.name: getattr(order, c.name) for c in order.__table__.columns},
        seller_name=seller.name if seller else None,
        buyer_name=buyer.name if buyer else None,
    )


# ═══════════════════════════════════════════════════
#  RECOVERY JOBS
# ═══════════════════════════════════════════════════
recovery_router = APIRouter(prefix="/api/recovery", tags=["recovery"])


@recovery_router.post("", response_model=RecoveryJobResponse)
def create_recovery_job(listing_id: str = Query(...), user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    listing = db.query(Listing).filter(Listing.id == listing_id).first()
    if not listing:
        raise HTTPException(status_code=404, detail="Listing not found")
    org_id = get_user_org_id(user, db)
    batch_code = f"WE-{uuid.uuid4().hex[:8].upper()}"
    job = RecoveryJob(listing_id=listing_id, seller_org_id=listing.org_id, batch_code=batch_code)
    listing.status = ListingStatus.IN_RECOVERY
    db.add(job)
    db.add(AuditEvent(actor_id=user.id, entity_type="recovery_job", entity_id=job.id, action="created"))
    db.commit()
    db.refresh(job)
    return RecoveryJobResponse(**{c.name: getattr(job, c.name) for c in job.__table__.columns})


@recovery_router.get("", response_model=list[RecoveryJobResponse])
def list_recovery_jobs(user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    if user.is_operator or user.is_admin:
        jobs = db.query(RecoveryJob).order_by(RecoveryJob.created_at.desc()).all()
    else:
        org_id = get_user_org_id(user, db)
        jobs = db.query(RecoveryJob).filter(
            (RecoveryJob.seller_org_id == org_id) | (RecoveryJob.buyer_org_id == org_id)
        ).order_by(RecoveryJob.created_at.desc()).all()
    return [RecoveryJobResponse(**{c.name: getattr(j, c.name) for c in j.__table__.columns}) for j in jobs]


@recovery_router.get("/{job_id}", response_model=RecoveryJobResponse)
def get_recovery_job(job_id: str, user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    job = db.query(RecoveryJob).filter(RecoveryJob.id == job_id).first()
    if not job:
        raise HTTPException(status_code=404, detail="Recovery job not found")
    return RecoveryJobResponse(**{c.name: getattr(job, c.name) for c in job.__table__.columns})


@recovery_router.post("/{job_id}/transition")
def transition_recovery(job_id: str, new_status: str = Query(...), user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    job = db.query(RecoveryJob).filter(RecoveryJob.id == job_id).first()
    if not job:
        raise HTTPException(status_code=404, detail="Recovery job not found")
    current = RecoveryStatus(job.status)
    target = RecoveryStatus(new_status)
    allowed = RECOVERY_TRANSITIONS.get(current, [])
    if target not in allowed:
        raise HTTPException(status_code=400, detail=f"Cannot transition from {current.value} to {target.value}")
    old = job.status
    job.status = target
    db.add(AuditEvent(actor_id=user.id, entity_type="recovery_job", entity_id=job.id,
                      action="status_change", old_values={"status": old}, new_values={"status": new_status}))
    db.commit()
    return {"status": new_status}


@recovery_router.post("/{job_id}/weight")
def record_weight(job_id: str, stage: str = Query(...), weight_grams: int = Query(..., gt=0),
                  notes: str | None = Query(None), uncertainty: str | None = Query(None),
                  user: User = Depends(require_operator), db: Session = Depends(get_db)):
    job = db.query(RecoveryJob).filter(RecoveryJob.id == job_id).first()
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")
    record = WeightRecord(job_id=job_id, stage=stage, weight_grams=weight_grams,
                          recorded_by=user.id, notes=notes, measurement_uncertainty=uncertainty)
    db.add(record)
    if stage == "incoming":
        job.incoming_weight_grams = weight_grams
    elif stage == "output":
        job.processed_output_grams = weight_grams
    elif stage == "residue":
        job.residue_grams = weight_grams
    db.add(AuditEvent(actor_id=user.id, entity_type="weight_record", entity_id=record.id,
                      action="recorded", new_values={"stage": stage, "weight_grams": weight_grams}))
    db.commit()
    return {"recorded": True}


@recovery_router.post("/{job_id}/processing-event")
def add_processing_event(job_id: str, event_type: str = Query(...), description: str = Query(""),
                         user: User = Depends(require_operator), db: Session = Depends(get_db)):
    job = db.query(RecoveryJob).filter(RecoveryJob.id == job_id).first()
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")
    event = ProcessingEvent(job_id=job_id, event_type=event_type, description=description, operator_id=user.id)
    db.add(event)
    db.commit()
    return {"recorded": True}


@recovery_router.post("/{job_id}/quality-check")
def record_quality_check(job_id: str, passed: bool = Query(...), notes: str = Query(""),
                         failure_reason: str | None = Query(None),
                         user: User = Depends(require_operator), db: Session = Depends(get_db)):
    job = db.query(RecoveryJob).filter(RecoveryJob.id == job_id).first()
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")
    qc = QualityCheck(job_id=job_id, checker_id=user.id, passed=passed, notes=notes, failure_reason=failure_reason)
    db.add(qc)
    if not passed:
        # Failed QC → reassessment required
        old = job.status
        job.status = RecoveryStatus.REASSESSMENT_REQUIRED
        db.add(AuditEvent(actor_id=user.id, entity_type="recovery_job", entity_id=job.id,
                          action="qc_failed", old_values={"status": old},
                          new_values={"status": "reassessment_required", "reason": failure_reason}))
    else:
        db.add(AuditEvent(actor_id=user.id, entity_type="recovery_job", entity_id=job.id, action="qc_passed"))
    db.commit()
    return {"passed": passed}


@recovery_router.get("/{job_id}/timeline")
def get_timeline(job_id: str, user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    events = db.query(AuditEvent).filter(
        AuditEvent.entity_id == job_id,
    ).order_by(AuditEvent.created_at.asc()).all()
    # Also include weight records and processing events
    weights = db.query(WeightRecord).filter(WeightRecord.job_id == job_id).all()
    proc_events = db.query(ProcessingEvent).filter(ProcessingEvent.job_id == job_id).all()
    qcs = db.query(QualityCheck).filter(QualityCheck.job_id == job_id).all()

    timeline = []
    for e in events:
        actor = db.query(User).filter(User.id == e.actor_id).first()
        timeline.append({
            "type": "audit", "action": e.action, "actor": actor.full_name if actor else "System",
            "old_values": e.old_values, "new_values": e.new_values, "timestamp": e.created_at.isoformat(),
        })
    for w in weights:
        recorder = db.query(User).filter(User.id == w.recorded_by).first()
        timeline.append({
            "type": "weight", "stage": w.stage, "weight_grams": w.weight_grams,
            "recorded_by": recorder.full_name if recorder else "Unknown",
            "notes": w.notes, "timestamp": w.created_at.isoformat(),
        })
    for p in proc_events:
        op = db.query(User).filter(User.id == p.operator_id).first()
        timeline.append({
            "type": "processing", "event_type": p.event_type, "description": p.description,
            "operator": op.full_name if op else "Unknown", "timestamp": p.created_at.isoformat(),
        })
    for q in qcs:
        checker = db.query(User).filter(User.id == q.checker_id).first()
        timeline.append({
            "type": "quality_check", "passed": q.passed, "notes": q.notes,
            "failure_reason": q.failure_reason, "checker": checker.full_name if checker else "Unknown",
            "timestamp": q.created_at.isoformat(),
        })

    timeline.sort(key=lambda x: x["timestamp"])
    return timeline


# ═══════════════════════════════════════════════════
#  PAYMENTS
# ═══════════════════════════════════════════════════
payments_router = APIRouter(prefix="/api/payments", tags=["payments"])


@payments_router.get("/order/{order_id}", response_model=list[PaymentResponse])
def get_order_payments(order_id: str, user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    payments = db.query(PaymentRecord).filter(PaymentRecord.order_id == order_id).all()
    return [PaymentResponse(**{c.name: getattr(p, c.name) for c in p.__table__.columns}) for p in payments]


@payments_router.post("/simulate")
def simulate_payment(order_id: str = Query(...), amount_paise: int = Query(..., gt=0),
                     user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    """Simulated payment event — demo mode only."""
    payment = PaymentRecord(
        order_id=order_id, amount_paise=amount_paise, status=PaymentStatus.PAID,
        payment_method="simulated", is_simulated=True, notes="DEMO: Simulated payment",
    )
    db.add(payment)
    db.add(AuditEvent(actor_id=user.id, entity_type="payment", entity_id=payment.id,
                      action="simulated_payment", new_values={"amount_paise": amount_paise}))
    db.commit()
    return {"status": "paid", "payment_id": payment.id, "simulated": True}


@payments_router.get("/settlement/{order_id}", response_model=SettlementResponse | None)
def get_settlement(order_id: str, user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    settlement = db.query(Settlement).filter(Settlement.order_id == order_id).first()
    if not settlement:
        return None
    return SettlementResponse(**{c.name: getattr(settlement, c.name) for c in settlement.__table__.columns})


@payments_router.post("/settlement")
def create_settlement(order_id: str = Query(...), breakdown: dict = None,
                      seller_proceeds_paise: int = Query(...), buyer_payment_paise: int = Query(...),
                      user: User = Depends(require_admin), db: Session = Depends(get_db)):
    settlement = Settlement(
        order_id=order_id, breakdown=breakdown or {},
        total_seller_proceeds_paise=seller_proceeds_paise,
        total_buyer_payment_paise=buyer_payment_paise,
    )
    db.add(settlement)
    order = db.query(Order).filter(Order.id == order_id).first()
    if order:
        order.status = OrderStatus.SETTLEMENT_RECORDED
    db.add(AuditEvent(actor_id=user.id, entity_type="settlement", entity_id=settlement.id, action="created"))
    db.commit()
    return {"settlement_id": settlement.id}


# ═══════════════════════════════════════════════════
#  MESSAGES
# ═══════════════════════════════════════════════════
messages_router = APIRouter(prefix="/api/messages", tags=["messages"])


@messages_router.post("", response_model=MessageResponse)
def send_message(req: MessageCreate, user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    msg = Message(sender_id=user.id, **req.model_dump())
    db.add(msg)
    db.commit()
    db.refresh(msg)
    return MessageResponse(**{c.name: getattr(msg, c.name) for c in msg.__table__.columns},
                           sender_name=user.full_name)


@messages_router.get("/order/{order_id}", response_model=list[MessageResponse])
def get_order_messages(order_id: str, user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    msgs = db.query(Message).filter(Message.order_id == order_id).order_by(Message.created_at.asc()).all()
    results = []
    for m in msgs:
        sender = db.query(User).filter(User.id == m.sender_id).first()
        results.append(MessageResponse(**{c.name: getattr(m, c.name) for c in m.__table__.columns},
                                       sender_name=sender.full_name if sender else None))
    return results


@messages_router.get("/listing/{listing_id}", response_model=list[MessageResponse])
def get_listing_messages(listing_id: str, user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    msgs = db.query(Message).filter(Message.listing_id == listing_id).order_by(Message.created_at.asc()).all()
    results = []
    for m in msgs:
        sender = db.query(User).filter(User.id == m.sender_id).first()
        results.append(MessageResponse(**{c.name: getattr(m, c.name) for c in m.__table__.columns},
                                       sender_name=sender.full_name if sender else None))
    return results


# ═══════════════════════════════════════════════════
#  DISPUTES
# ═══════════════════════════════════════════════════
disputes_router = APIRouter(prefix="/api/disputes", tags=["disputes"])


@disputes_router.post("", response_model=DisputeResponse)
def create_dispute(req: DisputeCreate, user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    dispute = Dispute(raised_by=user.id, **req.model_dump())
    db.add(dispute)
    # Update order status
    order = db.query(Order).filter(Order.id == req.order_id).first()
    if order:
        order.status = OrderStatus.DISPUTED
    db.add(AuditEvent(actor_id=user.id, entity_type="dispute", entity_id=dispute.id, action="created"))
    db.commit()
    db.refresh(dispute)
    return DisputeResponse(**{c.name: getattr(dispute, c.name) for c in dispute.__table__.columns})


@disputes_router.get("", response_model=list[DisputeResponse])
def list_disputes(user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    if user.is_admin:
        disputes = db.query(Dispute).order_by(Dispute.created_at.desc()).all()
    else:
        disputes = db.query(Dispute).filter(Dispute.raised_by == user.id).order_by(Dispute.created_at.desc()).all()
    return [DisputeResponse(**{c.name: getattr(d, c.name) for c in d.__table__.columns}) for d in disputes]


@disputes_router.post("/{dispute_id}/resolve")
def resolve_dispute(dispute_id: str, resolution: str = Query(...),
                    user: User = Depends(require_admin), db: Session = Depends(get_db)):
    dispute = db.query(Dispute).filter(Dispute.id == dispute_id).first()
    if not dispute:
        raise HTTPException(status_code=404, detail="Dispute not found")
    dispute.admin_resolution = resolution
    dispute.resolved_by = user.id
    dispute.resolved_at = datetime.now(timezone.utc)
    dispute.status = "resolved"
    db.add(AuditEvent(actor_id=user.id, entity_type="dispute", entity_id=dispute.id,
                      action="resolved", new_values={"resolution": resolution}))
    db.commit()
    return {"status": "resolved"}


# ═══════════════════════════════════════════════════
#  NOTIFICATIONS
# ═══════════════════════════════════════════════════
notifications_router = APIRouter(prefix="/api/notifications", tags=["notifications"])


@notifications_router.get("", response_model=list[NotificationResponse])
def list_notifications(user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    notifs = db.query(Notification).filter(Notification.user_id == user.id).order_by(
        Notification.created_at.desc()).limit(50).all()
    return [NotificationResponse(**{c.name: getattr(n, c.name) for c in n.__table__.columns}) for n in notifs]


@notifications_router.post("/{notif_id}/read")
def mark_read(notif_id: str, user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    notif = db.query(Notification).filter(Notification.id == notif_id, Notification.user_id == user.id).first()
    if not notif:
        raise HTTPException(status_code=404, detail="Notification not found")
    notif.is_read = True
    db.commit()
    return {"read": True}


# ═══════════════════════════════════════════════════
#  ADMIN
# ═══════════════════════════════════════════════════
admin_router = APIRouter(prefix="/api/admin", tags=["admin"])


@admin_router.get("/users", response_model=list[UserResponse])
def list_users(user: User = Depends(require_admin), db: Session = Depends(get_db)):
    users = db.query(User).order_by(User.created_at.desc()).all()
    results = []
    for u in users:
        membership = db.query(OrgMembership).filter(OrgMembership.user_id == u.id, OrgMembership.is_primary == True).first()
        org = db.query(Organisation).filter(Organisation.id == membership.org_id).first() if membership else None
        results.append(UserResponse(
            id=u.id, email=u.email, full_name=u.full_name, phone=u.phone,
            is_seller=u.is_seller, is_buyer=u.is_buyer, is_operator=u.is_operator,
            is_admin=u.is_admin, is_demo=u.is_demo, created_at=u.created_at,
            org_id=membership.org_id if membership else None,
            org_name=org.name if org else None,
        ))
    return results


@admin_router.get("/verification-queue", response_model=list[OrgResponse])
def verification_queue(user: User = Depends(require_admin), db: Session = Depends(get_db)):
    from app.models.organisation import VerificationStatus
    orgs = db.query(Organisation).filter(Organisation.verification_status.in_([
        VerificationStatus.PENDING, VerificationStatus.SUBMITTED, VerificationStatus.UNDER_REVIEW,
    ])).all()
    return [OrgResponse(**{c.name: getattr(o, c.name) for c in o.__table__.columns}) for o in orgs]


@admin_router.post("/verify/{org_id}")
def verify_org(org_id: str, decision: str = Query(...), notes: str = Query(""),
               user: User = Depends(require_admin), db: Session = Depends(get_db)):
    from app.models.organisation import VerificationStatus, BusinessVerification
    org = db.query(Organisation).filter(Organisation.id == org_id).first()
    if not org:
        raise HTTPException(status_code=404, detail="Organisation not found")
    if decision == "approved":
        org.verification_status = VerificationStatus.VERIFIED
    else:
        org.verification_status = VerificationStatus.REJECTED
    verification = BusinessVerification(
        org_id=org_id, status=org.verification_status,
        reviewer_id=user.id, reviewer_notes=notes,
        verified_at=datetime.now(timezone.utc) if decision == "approved" else None,
    )
    db.add(verification)
    db.add(AuditEvent(actor_id=user.id, entity_type="organisation", entity_id=org_id,
                      action=f"verification_{decision}", new_values={"notes": notes}))
    db.commit()
    return {"status": org.verification_status}


@admin_router.get("/audit", response_model=list[dict])
def audit_log(page: int = Query(1, ge=1), page_size: int = Query(50, ge=1, le=200),
              user: User = Depends(require_admin), db: Session = Depends(get_db)):
    events = db.query(AuditEvent).order_by(AuditEvent.created_at.desc()).offset(
        (page - 1) * page_size).limit(page_size).all()
    results = []
    for e in events:
        actor = db.query(User).filter(User.id == e.actor_id).first()
        results.append({
            "id": e.id, "actor": actor.full_name if actor else "Unknown", "actor_id": e.actor_id,
            "entity_type": e.entity_type, "entity_id": e.entity_id, "action": e.action,
            "old_values": e.old_values, "new_values": e.new_values, "timestamp": e.created_at.isoformat(),
        })
    return results


@admin_router.post("/assign-role")
def assign_role(user_id: str = Query(...), role: str = Query(...), value: bool = Query(True),
                admin: User = Depends(require_admin), db: Session = Depends(get_db)):
    target = db.query(User).filter(User.id == user_id).first()
    if not target:
        raise HTTPException(status_code=404, detail="User not found")
    if role == "operator":
        target.is_operator = value
    elif role == "admin":
        target.is_admin = value
    else:
        raise HTTPException(status_code=400, detail="Invalid role — use 'operator' or 'admin'")
    db.add(AuditEvent(actor_id=admin.id, entity_type="user", entity_id=user_id,
                      action=f"role_{role}_{'granted' if value else 'revoked'}"))
    db.commit()
    return {"assigned": True}


# ═══════════════════════════════════════════════════
#  FILE UPLOADS
# ═══════════════════════════════════════════════════
uploads_router = APIRouter(prefix="/api/uploads", tags=["uploads"])

ALLOWED_TYPES = {"image/jpeg", "image/png", "image/webp", "application/pdf"}
MAX_SIZE = settings.MAX_UPLOAD_SIZE_MB * 1024 * 1024


@uploads_router.post("")
async def upload_file(file: UploadFile = File(...), user: User = Depends(get_current_user)):
    if file.content_type not in ALLOWED_TYPES:
        raise HTTPException(status_code=400, detail=f"File type {file.content_type} not allowed")
    content = await file.read()
    if len(content) > MAX_SIZE:
        raise HTTPException(status_code=400, detail=f"File exceeds {settings.MAX_UPLOAD_SIZE_MB}MB limit")

    ext = file.filename.rsplit(".", 1)[-1] if "." in file.filename else "bin"
    filename = f"{uuid.uuid4().hex}.{ext}"
    filepath = os.path.join(settings.UPLOAD_DIR, filename)
    os.makedirs(settings.UPLOAD_DIR, exist_ok=True)
    with open(filepath, "wb") as f:
        f.write(content)
    return {"filename": filename, "path": f"/api/uploads/files/{filename}"}


@uploads_router.get("/files/{filename}")
async def serve_file(filename: str):
    filepath = os.path.join(settings.UPLOAD_DIR, filename)
    if not os.path.exists(filepath):
        raise HTTPException(status_code=404, detail="File not found")
    from fastapi.responses import FileResponse
    return FileResponse(filepath)
