"""Seed realistic demo data — all clearly marked as fictional."""

from datetime import datetime, timezone, timedelta

from sqlalchemy.orm import Session

from app.auth import hash_password
from app.models.user import User
from app.models.organisation import Organisation, OrgMembership, VerificationStatus
from app.models.listing import (
    Listing, ListingPhoto, ListingStatus, MaterialCategory,
    PhysicalForm, RejectionReason, PreferredRoute,
)
from app.models.requirement import BuyerRequirement
from app.models.offer import Offer, OfferStatus
from app.models.assessment import Assessment, AssessmentOutcome, AssessmentMeasurement
from app.models.quote import Quote, QuoteVersion, QuoteStatus, CommercialModel
from app.models.order import Order, OrderStatus, Approval
from app.models.recovery import (
    RecoveryJob, RecoveryStatus, WeightRecord, ProcessingEvent, QualityCheck,
    ResidualDestination,
)
from app.models.payment import PaymentRecord, PaymentStatus, Settlement
from app.models.messaging import Notification
from app.models.audit import AuditEvent


def seed_database(db: Session):
    """Create demo accounts and realistic sample data. All marked is_demo=True."""

    # Check if already seeded
    if db.query(User).filter(User.is_demo == True).first():
        return

    now = datetime.now(timezone.utc)
    pw = hash_password("demo1234")

    # ═══════════════════════════════════════════════════
    #  USERS & ORGANISATIONS
    # ═══════════════════════════════════════════════════

    # Seller: Kavitha Plastics (Chennai)
    seller_user = User(
        id="demo-seller-001", email="seller@demo.waste.in", hashed_password=pw,
        full_name="Kavitha Sundaram", phone="+91-9800000001",
        is_seller=True, is_demo=True,
    )
    seller_org = Organisation(
        id="demo-org-seller-001", name="Kavitha Plastics",
        org_type="aggregator", city="Chennai", state="Tamil Nadu",
        pincode="600032", verification_status=VerificationStatus.VERIFIED, is_demo=True,
        description="[DEMO] Plastic waste aggregator in Chennai",
    )
    db.add_all([seller_user, seller_org])
    db.flush()
    db.add(OrgMembership(user_id=seller_user.id, org_id=seller_org.id, role="owner"))

    # Buyer: GreenMelt Recyclers (Bengaluru)
    buyer_user = User(
        id="demo-buyer-001", email="buyer@demo.waste.in", hashed_password=pw,
        full_name="Rajesh Menon", phone="+91-9800000002",
        is_buyer=True, is_demo=True,
    )
    buyer_org = Organisation(
        id="demo-org-buyer-001", name="GreenMelt Recyclers",
        org_type="recycler", city="Bengaluru", state="Karnataka",
        pincode="560067", verification_status=VerificationStatus.VERIFIED, is_demo=True,
        description="[DEMO] HDPE recycling plant in Bengaluru",
    )
    db.add_all([buyer_user, buyer_org])
    db.flush()
    db.add(OrgMembership(user_id=buyer_user.id, org_id=buyer_org.id, role="owner"))

    # Operator
    operator_user = User(
        id="demo-operator-001", email="operator@demo.waste.in", hashed_password=pw,
        full_name="Priya Nair", phone="+91-9800000003",
        is_operator=True, is_demo=True,
    )
    op_org = Organisation(
        id="demo-org-op-001", name="Wast-e Operations",
        org_type="other", city="Hyderabad", state="Telangana",
        pincode="500034", verification_status=VerificationStatus.VERIFIED, is_demo=True,
    )
    db.add_all([operator_user, op_org])
    db.flush()
    db.add(OrgMembership(user_id=operator_user.id, org_id=op_org.id, role="owner"))

    # Admin
    admin_user = User(
        id="demo-admin-001", email="admin@demo.waste.in", hashed_password=pw,
        full_name="Arjun Sharma", phone="+91-9800000004",
        is_admin=True, is_seller=True, is_buyer=True, is_demo=True,
    )
    db.add(admin_user)
    db.flush()
    db.add(OrgMembership(user_id=admin_user.id, org_id=op_org.id, role="admin"))

    # Dual seller+buyer: Metalworks Pune
    dual_user = User(
        id="demo-dual-001", email="dual@demo.waste.in", hashed_password=pw,
        full_name="Sunita Patil", phone="+91-9800000005",
        is_seller=True, is_buyer=True, is_demo=True,
    )
    dual_org = Organisation(
        id="demo-org-dual-001", name="Patil Metalworks",
        org_type="factory", city="Pune", state="Maharashtra",
        pincode="411001", verification_status=VerificationStatus.VERIFIED, is_demo=True,
        description="[DEMO] Metal fabrication unit in Pune",
    )
    db.add_all([dual_user, dual_org])
    db.flush()
    db.add(OrgMembership(user_id=dual_user.id, org_id=dual_org.id, role="owner"))

    # Extra buyer org: Coimbatore Polymers
    buyer2_org = Organisation(
        id="demo-org-buyer-002", name="Coimbatore Polymers",
        org_type="manufacturer", city="Coimbatore", state="Tamil Nadu",
        pincode="641001", verification_status=VerificationStatus.PENDING, is_demo=True,
        description="[DEMO] Polymer product manufacturer",
    )
    db.add(buyer2_org)

    # ═══════════════════════════════════════════════════
    #  LISTINGS — 7 scenarios
    # ═══════════════════════════════════════════════════

    # 1. Mixed-plastic batch needing sorting (Chennai)
    listing1 = Listing(
        id="demo-listing-001", org_id=seller_org.id, created_by=seller_user.id,
        title="Mixed HDPE/LDPE bags — rejected for contamination",
        material_category=MaterialCategory.PLASTICS,
        material_grade="HDPE/LDPE mix", quantity_grams=2500000,  # 2500 kg
        quantity_unit="kg", physical_form=PhysicalForm.BALED,
        description="[DEMO DATA] Baled mixed polyethylene bags from post-consumer collection. Rejected by previous buyer due to mixed polymer content and soil contamination.",
        rejection_reason=RejectionReason.MIXED_MATERIALS,
        rejection_details="Buyer reported >30% LDPE content in what was declared as HDPE-only bales. Also noted soil and food residue on approx. 15% of material.",
        material_source="Municipal collection route, South Chennai",
        city="Chennai", state="Tamil Nadu", pincode="600032",
        asking_price_paise=1200, price_unit="per_kg",
        preferred_route=PreferredRoute.MANAGED_RECOVERY,
        status=ListingStatus.ACTIVE, is_demo=True, ownership_confirmed=True,
        created_at=now - timedelta(days=5),
    )

    # 2. Batch suitable for direct sale (Bengaluru)
    listing2 = Listing(
        id="demo-listing-002", org_id=seller_org.id, created_by=seller_user.id,
        title="Clear PET bottles — rejected for quantity mismatch",
        material_category=MaterialCategory.PLASTICS,
        material_grade="PET clear", quantity_grams=800000,  # 800 kg
        quantity_unit="kg", physical_form=PhysicalForm.BALED,
        description="[DEMO DATA] Clean, clear PET bottle bales. Original buyer rejected due to quantity being lower than contracted amount. Material quality is acceptable.",
        rejection_reason=RejectionReason.QUANTITY_MISMATCH,
        rejection_details="Contracted for 2 tonnes, could only supply 800 kg this month. Buyer refused partial delivery.",
        material_source="Beverage distributor returns, Koramangala",
        city="Bengaluru", state="Karnataka", pincode="560034",
        asking_price_paise=2800, price_unit="per_kg",
        preferred_route=PreferredRoute.DIRECT_SALE,
        status=ListingStatus.ACTIVE, is_demo=True, ownership_confirmed=True,
        has_assessment=True, assessment_date=now - timedelta(days=2),
        created_at=now - timedelta(days=4),
    )

    # 3. Batch awaiting moisture assessment (Hyderabad)
    listing3 = Listing(
        id="demo-listing-003", org_id=dual_org.id, created_by=dual_user.id,
        title="PP woven sacks — excess moisture after rain exposure",
        material_category=MaterialCategory.PLASTICS,
        material_grade="PP woven", quantity_grams=1200000,  # 1200 kg
        quantity_unit="kg", physical_form=PhysicalForm.LOOSE,
        description="[DEMO DATA] Used PP cement sacks stored outdoors. Got wet in monsoon. Previous buyer rejected on moisture grounds. Needs assessment to determine if drying is viable.",
        rejection_reason=RejectionReason.EXCESS_MOISTURE,
        rejection_details="Moisture content measured at 18% at buyer's facility. Their limit was 5%.",
        material_source="Construction site waste, Hitech City area",
        city="Hyderabad", state="Telangana", pincode="500081",
        asking_price_paise=None, request_quote=True,
        preferred_route=PreferredRoute.HELP_ME_DECIDE,
        status=ListingStatus.ACTIVE, is_demo=True, ownership_confirmed=True,
        created_at=now - timedelta(days=3),
    )

    # 4. Recovery job with quote awaiting approval (Coimbatore)
    listing4 = Listing(
        id="demo-listing-004", org_id=seller_org.id, created_by=seller_user.id,
        title="Coloured HDPE crates — colour mismatch rejection",
        material_category=MaterialCategory.PLASTICS,
        material_grade="HDPE coloured", quantity_grams=3000000,  # 3000 kg
        quantity_unit="kg", physical_form=PhysicalForm.LOOSE,
        description="[DEMO DATA] Mixed-colour HDPE crates and containers. Rejected by recycler who needed only blue and white HDPE. Contains red, green, yellow variants.",
        rejection_reason=RejectionReason.COLOUR_MISMATCH,
        rejection_details="Required blue/white only. Batch contains approximately 40% red, 25% green, 20% yellow, 15% blue/white.",
        material_source="Dairy and beverage distributors, Coimbatore region",
        city="Coimbatore", state="Tamil Nadu", pincode="641001",
        asking_price_paise=1500, price_unit="per_kg",
        preferred_route=PreferredRoute.MANAGED_RECOVERY,
        status=ListingStatus.UNDER_ASSESSMENT, has_assessment=True,
        assessment_date=now - timedelta(days=1),
        is_demo=True, ownership_confirmed=True,
        created_at=now - timedelta(days=7),
    )

    # 5. Recovery job that failed QC (Pune)
    listing5 = Listing(
        id="demo-listing-005", org_id=dual_org.id, created_by=dual_user.id,
        title="Industrial PE film — contamination after factory use",
        material_category=MaterialCategory.PLASTICS,
        material_grade="LDPE film", quantity_grams=500000,  # 500 kg
        quantity_unit="kg", physical_form=PhysicalForm.LOOSE,
        description="[DEMO DATA] Stretch wrap and shrink film from factory floor. Contaminated with adhesive tape and staples. First QC check failed.",
        rejection_reason=RejectionReason.CONTAMINATION,
        rejection_details="Mixed with adhesive tape and metal staples. Previous buyer rejected on sight.",
        material_source="Packaging waste from auto parts factory, Pune",
        city="Pune", state="Maharashtra", pincode="411001",
        asking_price_paise=800, price_unit="per_kg",
        preferred_route=PreferredRoute.MANAGED_RECOVERY,
        status=ListingStatus.IN_RECOVERY, has_assessment=True,
        is_demo=True, ownership_confirmed=True,
        created_at=now - timedelta(days=10),
    )

    # 6. Declined batch — no viable route found
    listing6 = Listing(
        id="demo-listing-006", org_id=seller_org.id, created_by=seller_user.id,
        title="Multi-layer laminate pouches — no separation route",
        material_category=MaterialCategory.PLASTICS,
        material_grade="Multi-layer laminate", quantity_grams=400000,  # 400 kg
        quantity_unit="kg", physical_form=PhysicalForm.BALED,
        description="[DEMO DATA] Metallised multi-layer laminate pouches. No viable mechanical recycling route found. Assessment concluded material is not suitable for our current recovery capabilities.",
        rejection_reason=RejectionReason.MIXED_MATERIALS,
        rejection_details="Aluminium-PET-PE laminate structure. Cannot be mechanically separated with available equipment.",
        material_source="Food packaging waste, various sources",
        city="Chennai", state="Tamil Nadu", pincode="600042",
        asking_price_paise=200, price_unit="per_kg",
        preferred_route=PreferredRoute.MANAGED_RECOVERY,
        status=ListingStatus.ACTIVE, has_assessment=True,
        is_demo=True, ownership_confirmed=True,
        created_at=now - timedelta(days=15),
    )

    # 7. Completed delivery with settlement (Chennai → Bengaluru)
    listing7 = Listing(
        id="demo-listing-007", org_id=seller_org.id, created_by=seller_user.id,
        title="Natural HDPE bottles — documentation issue resolved",
        material_category=MaterialCategory.PLASTICS,
        material_grade="HDPE natural", quantity_grams=1500000,  # 1500 kg
        quantity_unit="kg", physical_form=PhysicalForm.BALED,
        description="[DEMO DATA] Clean HDPE bottles originally rejected for missing origin documentation. Documentation was later provided and material sold directly to recycler.",
        rejection_reason=RejectionReason.DOCUMENTATION_ISSUE,
        rejection_details="Missing GST invoice and transporter documentation. Since resolved.",
        material_source="Personal care product manufacturer, Ambattur",
        city="Chennai", state="Tamil Nadu", pincode="600053",
        asking_price_paise=3200, price_unit="per_kg",
        preferred_route=PreferredRoute.DIRECT_SALE,
        status=ListingStatus.SOLD, has_assessment=True,
        is_demo=True, ownership_confirmed=True,
        created_at=now - timedelta(days=20),
    )

    db.add_all([listing1, listing2, listing3, listing4, listing5, listing6, listing7])
    db.flush()

    # ═══════════════════════════════════════════════════
    #  BUYER REQUIREMENTS
    # ═══════════════════════════════════════════════════

    req1 = BuyerRequirement(
        id="demo-req-001", org_id=buyer_org.id, created_by=buyer_user.id,
        title="Clean HDPE for pelletising",
        material_category=MaterialCategory.PLASTICS,
        material_grade="HDPE", acceptable_forms=["baled", "shredded", "loose"],
        required_quantity_grams=5000000, quantity_unit="kg",
        delivery_city="Bengaluru", delivery_state="Karnataka", delivery_pincode="560067",
        target_price_min_paise=2000, target_price_max_paise=3500, price_unit="per_kg",
        quality_specs={
            "max_moisture_pct": 3, "max_contamination_pct": 2,
            "allowed_colours": ["natural", "white", "blue"],
            "required_polymer": "HDPE", "min_mfi": 0.5, "max_mfi": 12,
        },
        sampling_method="Random 5 kg sample from 3 bales",
        acceptance_method="Visual + MFI test at buyer facility",
        description="[DEMO DATA] Ongoing requirement for clean HDPE feedstock for pelletising line.",
        is_demo=True,
    )

    req2 = BuyerRequirement(
        id="demo-req-002", org_id=dual_org.id, created_by=dual_user.id,
        title="PP woven material for recycled products",
        material_category=MaterialCategory.PLASTICS,
        material_grade="PP woven", acceptable_forms=["baled", "loose"],
        required_quantity_grams=2000000, quantity_unit="kg",
        delivery_city="Pune", delivery_state="Maharashtra", delivery_pincode="411001",
        target_price_min_paise=1000, target_price_max_paise=2000, price_unit="per_kg",
        quality_specs={
            "max_moisture_pct": 5, "max_contamination_pct": 5,
        },
        description="[DEMO DATA] Need PP woven material for recycled bag manufacturing.",
        is_demo=True,
    )
    db.add_all([req1, req2])

    # ═══════════════════════════════════════════════════
    #  ASSESSMENT for listing 2 (PET bottles — good quality)
    # ═══════════════════════════════════════════════════

    assessment2 = Assessment(
        id="demo-assess-002", listing_id=listing2.id, assessor_id=operator_user.id,
        sampling_date=now - timedelta(days=2), sampling_method="Random selection from 3 bales",
        sample_size="5 kg from each bale", observed_composition={"pet_clear": 95, "pet_coloured": 3, "other": 2},
        moisture_pct=1.2, contamination_pct=2.0,
        estimated_recoverable_min_grams=750000, estimated_recoverable_max_grams=780000,
        proposed_processing_steps=["Visual sorting", "Label removal"],
        suitable_buyer_requirements="Suitable for PET recyclers accepting clear post-consumer bottles",
        uncertainties="Small sample size — composition may vary across remaining bales",
        outcome=AssessmentOutcome.SUITABLE_DIRECT_SALE, is_demo=True,
    )
    db.add(assessment2)

    # Assessment for listing 4 (coloured HDPE)
    assessment4 = Assessment(
        id="demo-assess-004", listing_id=listing4.id, assessor_id=operator_user.id,
        sampling_date=now - timedelta(days=1), sampling_method="Systematic sampling, 1 in 10 items",
        sample_size="15 kg total", observed_composition={"hdpe_red": 38, "hdpe_green": 26, "hdpe_yellow": 21, "hdpe_blue_white": 15},
        moisture_pct=0.5, contamination_pct=1.5,
        estimated_recoverable_min_grams=2700000, estimated_recoverable_max_grams=2850000,
        proposed_processing_steps=["Colour sorting", "Grinding", "Washing", "Pelletising by colour"],
        suitable_buyer_requirements="Individual colour fractions can be sold to separate buyers",
        uncertainties="Colour sorting yields are estimated from sample — actual split may differ by ±5%",
        outcome=AssessmentOutcome.NEEDS_PROCESSING, is_demo=True,
    )
    db.add(assessment4)
    db.flush()

    # Measurement for assessment 4
    db.add(AssessmentMeasurement(
        assessment_id=assessment4.id, parameter="moisture", value=0.5, unit="%",
        test_method="Oven drying 105°C for 2 hours", is_estimated=False,
    ))
    db.add(AssessmentMeasurement(
        assessment_id=assessment4.id, parameter="contamination", value=1.5, unit="%",
        test_method="Visual separation and weighing", is_estimated=False,
    ))

    # Assessment for listing 6 (declined)
    assessment6 = Assessment(
        id="demo-assess-006", listing_id=listing6.id, assessor_id=operator_user.id,
        sampling_date=now - timedelta(days=12), sampling_method="Random pouch selection",
        sample_size="2 kg", observed_composition={"aluminium": 8, "pet": 45, "pe": 40, "ink_adhesive": 7},
        estimated_recoverable_min_grams=0, estimated_recoverable_max_grams=0,
        proposed_processing_steps=[],
        suitable_buyer_requirements="None identified for current capabilities",
        uncertainties="Material structure prevents mechanical separation",
        outcome=AssessmentOutcome.NOT_VIABLE, is_demo=True,
        notes="Multi-layer laminate cannot be mechanically recycled with available equipment. Possible future route via chemical recycling (not currently available).",
    )
    db.add(assessment6)

    # ═══════════════════════════════════════════════════
    #  QUOTE for listing 4 (awaiting seller approval)
    # ═══════════════════════════════════════════════════

    quote4 = Quote(
        id="demo-quote-004", listing_id=listing4.id, assessment_id=assessment4.id,
        created_by=operator_user.id, commercial_model=CommercialModel.SERVICE,
        current_version=1, status=QuoteStatus.ISSUED, is_demo=True,
    )
    db.add(quote4)
    db.flush()

    quote4_v1 = QuoteVersion(
        quote_id=quote4.id, version_number=1,
        estimated_incoming_weight_grams=3000000,
        expected_output_min_grams=2700000, expected_output_max_grams=2850000,
        sale_price_paise_per_kg=2200,  # indicative sale price after sorting
        transport_cost_paise=800000,   # ₹8,000
        assessment_cost_paise=300000,  # ₹3,000
        processing_cost_paise=1500000, # ₹15,000
        packaging_cost_paise=200000,   # ₹2,000
        residue_handling_cost_paise=100000, # ₹1,000
        platform_fee_paise=500000,     # ₹5,000
        tax_paise=612000,              # ₹6,120
        estimated_seller_proceeds_paise=5288000,  # ₹52,880 (estimated)
        assumptions="Assumes 90-95% recovery rate after sorting. Sale price based on current market for sorted single-colour HDPE. Actual proceeds depend on final accepted weights and prices.",
        additional_cost_responsibility="Additional transport beyond 100 km to be quoted separately. Residue handling assumes <10% non-recoverable.",
        is_estimate=True,
        expires_at=now + timedelta(days=7),
    )
    db.add(quote4_v1)

    # ═══════════════════════════════════════════════════
    #  RECOVERY JOB for listing 5 (failed QC)
    # ═══════════════════════════════════════════════════

    job5 = RecoveryJob(
        id="demo-job-005", listing_id=listing5.id, operator_id=operator_user.id,
        seller_org_id=dual_org.id, status=RecoveryStatus.REASSESSMENT_REQUIRED,
        incoming_weight_grams=500000, processed_output_grams=380000,
        residue_grams=95000, loss_grams=25000,
        loss_notes="Process moisture loss and fine dust extraction",
        batch_code="WE-DEMO5001", is_demo=True,
    )
    db.add(job5)
    db.flush()

    # Weight records
    db.add(WeightRecord(job_id=job5.id, stage="incoming", weight_grams=500000,
                        recorded_by=operator_user.id, notes="Weighed on platform scale"))
    db.add(WeightRecord(job_id=job5.id, stage="sorted", weight_grams=450000,
                        recorded_by=operator_user.id, notes="After manual removal of tape and staples"))
    db.add(WeightRecord(job_id=job5.id, stage="output", weight_grams=380000,
                        recorded_by=operator_user.id, notes="After washing and drying"))
    db.add(WeightRecord(job_id=job5.id, stage="residue", weight_grams=95000,
                        recorded_by=operator_user.id, notes="Tape, staples, and soil"))

    db.add(ProcessingEvent(job_id=job5.id, event_type="manual_sorting",
                           description="Removed adhesive tape and metal staples by hand", operator_id=operator_user.id))
    db.add(ProcessingEvent(job_id=job5.id, event_type="washing",
                           description="Hot water wash at 60°C", operator_id=operator_user.id))

    db.add(QualityCheck(
        job_id=job5.id, checker_id=operator_user.id, passed=False,
        notes="Adhesive residue still present on approximately 20% of output",
        failure_reason="Adhesive contamination above acceptable threshold (>5% by visual inspection)",
        measurements={"adhesive_contamination_visual_pct": 20},
    ))

    db.add(ResidualDestination(
        job_id=job5.id, destination_type="additional_recovery",
        handler="Manual adhesive scraping planned", quantity_grams=None,
        description="Re-sort output to separate adhesive-affected material",
    ))

    # ═══════════════════════════════════════════════════
    #  ORDER + SETTLEMENT for listing 7 (completed)
    # ═══════════════════════════════════════════════════

    offer7 = Offer(
        id="demo-offer-007", listing_id=listing7.id,
        buyer_org_id=buyer_org.id, buyer_user_id=buyer_user.id,
        offered_price_paise=3000, price_unit="per_kg",
        offered_quantity_grams=1500000,
        terms="FOB Chennai. Buyer arranges transport.",
        message="[DEMO] Interested in your HDPE natural bottles. Can collect from Chennai.",
        status=OfferStatus.ACCEPTED,
    )
    db.add(offer7)
    db.flush()

    order7 = Order(
        id="demo-order-007", listing_id=listing7.id, offer_id=offer7.id,
        seller_org_id=seller_org.id, buyer_org_id=buyer_org.id,
        agreed_material="HDPE natural bottles, baled",
        agreed_quantity_grams=1500000, agreed_price_paise=3000, price_unit="per_kg",
        delivery_terms="FOB Chennai — buyer arranges transport",
        status=OrderStatus.CLOSED, order_type="direct", is_demo=True,
    )
    db.add(order7)
    db.flush()

    # Payment
    payment7 = PaymentRecord(
        order_id=order7.id, amount_paise=4500000,  # 1500 kg × ₹30/kg = ₹45,000
        status=PaymentStatus.PAID, payment_method="simulated", is_simulated=True,
        notes="[DEMO] Simulated bank transfer",
    )
    db.add(payment7)

    # Settlement
    settlement7 = Settlement(
        order_id=order7.id,
        breakdown={
            "material_value_paise": 4500000,
            "platform_fee_paise": -225000,
            "description": "[DEMO] Direct sale: 1500 kg HDPE natural @ ₹30/kg. Platform fee 5%.",
        },
        total_seller_proceeds_paise=4275000,  # ₹42,750
        total_buyer_payment_paise=4500000,    # ₹45,000
        is_simulated=True,
    )
    db.add(settlement7)

    # Audit trail for order 7
    for action in ["created", "inspection_confirmed", "pickup_arranged", "in_transit",
                   "delivered", "buyer_inspecting", "accepted", "settlement_recorded", "closed"]:
        db.add(AuditEvent(
            actor_id=admin_user.id, entity_type="order", entity_id=order7.id,
            action=f"status_change", new_values={"status": action},
            created_at=now - timedelta(days=20) + timedelta(days=list(range(9))[
                ["created", "inspection_confirmed", "pickup_arranged", "in_transit",
                 "delivered", "buyer_inspecting", "accepted", "settlement_recorded", "closed"].index(action)
            ]),
        ))

    # ═══════════════════════════════════════════════════
    #  NOTIFICATIONS
    # ═══════════════════════════════════════════════════

    db.add(Notification(
        user_id=seller_user.id, notification_type="offer",
        title="New offer on your listing", content="[DEMO] GreenMelt Recyclers offered ₹30/kg for HDPE natural bottles",
        link="/orders/demo-order-007",
    ))
    db.add(Notification(
        user_id=seller_user.id, notification_type="quote",
        title="Quote ready for review", content="[DEMO] Recovery quote for coloured HDPE crates is ready",
        link="/listings/demo-listing-004",
    ))
    db.add(Notification(
        user_id=operator_user.id, notification_type="assignment",
        title="New assessment assigned", content="[DEMO] PP woven sacks in Hyderabad need moisture assessment",
        link="/listings/demo-listing-003",
    ))

    db.commit()
    print("[OK] Demo data seeded successfully")
