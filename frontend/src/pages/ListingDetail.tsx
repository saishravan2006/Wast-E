/* ── Listing Detail Page ── */
import { useState, useEffect } from "react";
import { useParams, useNavigate, Link } from "react-router-dom";
import api from "../api";
import { useAuth } from "../auth";
import type { Listing, Assessment, Quote, Offer } from "../types";
import { LISTING_STATUSES, humanise, categoryIcon } from "../types";
import { formatPrice, formatWeight, formatDate, formatINR } from "../utils";

export default function ListingDetail() {
  const { id } = useParams();
  const { user } = useAuth();
  const navigate = useNavigate();
  const [listing, setListing] = useState<Listing | null>(null);
  const [assessments, setAssessments] = useState<Assessment[]>([]);
  const [quotes, setQuotes] = useState<Quote[]>([]);
  const [offers, setOffers] = useState<Offer[]>([]);
  const [loading, setLoading] = useState(true);
  const [tab, setTab] = useState("details");

  // Offer form
  const [showOffer, setShowOffer] = useState(false);
  const [offerPrice, setOfferPrice] = useState("");
  const [offerQty, setOfferQty] = useState("");
  const [offerMsg, setOfferMsg] = useState("");

  useEffect(() => {
    api.get(`/listings/${id}`).then(r => setListing(r.data)).catch(() => navigate("/browse")).finally(() => setLoading(false));
    if (user) {
      api.get(`/assessments/listing/${id}`).then(r => setAssessments(r.data)).catch(() => {});
      api.get(`/quotes/listing/${id}`).then(r => setQuotes(r.data)).catch(() => {});
      api.get(`/offers/listing/${id}`).then(r => setOffers(r.data)).catch(() => {});
    }
  }, [id, user]);

  const submitOffer = async () => {
    if (!listing) return;
    try {
      await api.post("/offers", {
        listing_id: listing.id,
        offered_price_paise: Math.round(parseFloat(offerPrice) * 100),
        offered_quantity_grams: Math.round(parseFloat(offerQty) * 1000),
        message: offerMsg,
      });
      setShowOffer(false);
      const r = await api.get(`/offers/listing/${id}`);
      setOffers(r.data);
    } catch (e: any) {
      alert(e.response?.data?.detail || "Failed to submit offer");
    }
  };

  const acceptOffer = async (offerId: string) => {
    try {
      const r = await api.post(`/offers/${offerId}/accept`);
      navigate(`/orders/${r.data.order_id}`);
    } catch (e: any) {
      alert(e.response?.data?.detail || "Failed");
    }
  };

  const approveQuote = async (quoteId: string, version: number) => {
    try {
      await api.post(`/quotes/${quoteId}/approve?version=${version}`);
      const r = await api.get(`/quotes/listing/${id}`);
      setQuotes(r.data);
    } catch (e: any) {
      alert(e.response?.data?.detail || "Failed");
    }
  };

  const requestRecovery = async () => {
    if (!listing) return;
    try {
      const r = await api.post(`/recovery?listing_id=${listing.id}`);
      navigate(`/recovery/${r.data.id}`);
    } catch (e: any) {
      alert(e.response?.data?.detail || "Failed");
    }
  };

  if (loading) return <div className="page-container text-center py-20 text-charcoal-lighter">Loading...</div>;
  if (!listing) return <div className="page-container text-center py-20">Listing not found</div>;

  const status = LISTING_STATUSES[listing.status] || { label: listing.status, color: "neutral" };
  const isOwner = user && listing.org_id === (user as any).org_id;

  return (
    <div className="page-container animate-fade-in">
      {/* Breadcrumb */}
      <nav className="text-sm text-charcoal-lighter mb-4">
        <Link to="/browse" className="hover:text-primary-700">Browse</Link> / <span className="text-charcoal">{listing.title}</span>
      </nav>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
        {/* Main content */}
        <div className="lg:col-span-2">
          {/* Header */}
          <div className="mb-6">
            <div className="flex items-center gap-2 mb-2 flex-wrap">
              <span className="badge-active">{categoryIcon(listing.material_category)} {humanise(listing.material_category)}</span>
              <span className={`badge-${status.color}`}>{status.label}</span>
              {listing.has_assessment && <span className="badge-info">Wast-e assessment available</span>}
              {listing.is_demo && <span className="badge-pending">DEMO DATA</span>}
            </div>
            <h1 className="text-2xl sm:text-3xl font-bold text-charcoal mb-2">{listing.title}</h1>
            <p className="text-charcoal-lighter">Listed {formatDate(listing.created_at)} by {listing.org_name || "Unknown"}</p>
          </div>

          {/* Tabs */}
          <div className="flex gap-1 border-b border-gray-200 mb-6 overflow-x-auto">
            {["details", "rejection", "assessment", "offers", "quotes"].map(t => (
              <button key={t} onClick={() => setTab(t)}
                className={`px-4 py-2.5 text-sm font-medium border-b-2 transition-colors whitespace-nowrap ${
                  tab === t ? "border-primary-700 text-primary-700" : "border-transparent text-charcoal-lighter hover:text-charcoal"
                }`}>
                {humanise(t)} {t === "offers" && offers.length > 0 ? `(${offers.length})` : ""}
              </button>
            ))}
          </div>

          {/* Tab content */}
          {tab === "details" && (
            <div className="space-y-4 animate-fade-in">
              <InfoRow label="Material Grade" value={listing.material_grade || (listing.grade_unknown ? "Unknown" : "Not specified")} />
              <InfoRow label="Physical Form" value={humanise(listing.physical_form)} />
              <InfoRow label="Available Quantity" value={formatWeight(listing.quantity_grams)} />
              <InfoRow label="Location" value={`${listing.city}, ${listing.state} — ${listing.pincode}`} />
              <InfoRow label="Preferred Route" value={humanise(listing.preferred_route)} />
              {listing.material_source && <InfoRow label="Material Source" value={listing.material_source} />}
              {listing.description && (
                <div className="card p-4">
                  <h4 className="text-sm font-semibold text-charcoal mb-2">Description</h4>
                  <p className="text-sm text-charcoal-lighter whitespace-pre-line">{listing.description}</p>
                </div>
              )}
              <p className="text-xs text-charcoal-lighter italic">ℹ️ Information above is declared by the seller and has not been independently verified unless an assessment is noted.</p>
            </div>
          )}

          {tab === "rejection" && (
            <div className="space-y-4 animate-fade-in">
              <InfoRow label="Reason for Rejection" value={humanise(listing.rejection_reason)} />
              {listing.rejection_details && (
                <div className="card p-4">
                  <h4 className="text-sm font-semibold text-charcoal mb-2">What the buyer reported</h4>
                  <p className="text-sm text-charcoal-lighter whitespace-pre-line">{listing.rejection_details}</p>
                </div>
              )}
              <InfoRow label="Hazardous Contamination Declared" value={listing.has_hazardous_contamination ? "Yes — see details" : "No"} />
            </div>
          )}

          {tab === "assessment" && (
            <div className="animate-fade-in">
              {assessments.length === 0 ? (
                <p className="text-charcoal-lighter">No assessment available for this listing.</p>
              ) : assessments.map(a => (
                <div key={a.id} className="card p-6 space-y-4">
                  <h4 className="font-bold text-charcoal">Assessment — {formatDate(a.sampling_date)}</h4>
                  <p className="text-xs text-charcoal-lighter italic">Assessment of a sample — does not guarantee every part of the batch is identical.</p>
                  <InfoRow label="Sampling Method" value={a.sampling_method} />
                  <InfoRow label="Sample Size" value={a.sample_size} />
                  <InfoRow label="Outcome" value={humanise(a.outcome)} />
                  {a.moisture_pct != null && <InfoRow label="Moisture" value={`${a.moisture_pct}%`} />}
                  {a.contamination_pct != null && <InfoRow label="Contamination" value={`${a.contamination_pct}%`} />}
                  {a.observed_composition && (
                    <div>
                      <h5 className="text-sm font-semibold mb-2">Observed Composition</h5>
                      <div className="flex flex-wrap gap-2">
                        {Object.entries(a.observed_composition).map(([k, v]) => (
                          <span key={k} className="badge-neutral">{humanise(k)}: {v}%</span>
                        ))}
                      </div>
                    </div>
                  )}
                  {a.estimated_recoverable_min_grams != null && (
                    <InfoRow label="Estimated Recoverable" value={`${formatWeight(a.estimated_recoverable_min_grams)} — ${formatWeight(a.estimated_recoverable_max_grams)}`} />
                  )}
                  {a.proposed_processing_steps && a.proposed_processing_steps.length > 0 && (
                    <div>
                      <h5 className="text-sm font-semibold mb-2">Proposed Processing</h5>
                      <ol className="list-decimal list-inside text-sm text-charcoal-lighter space-y-1">
                        {a.proposed_processing_steps.map((s, i) => <li key={i}>{s}</li>)}
                      </ol>
                    </div>
                  )}
                  {a.uncertainties && <InfoRow label="Uncertainties" value={a.uncertainties} />}
                </div>
              ))}
            </div>
          )}

          {tab === "offers" && (
            <div className="animate-fade-in space-y-4">
              {offers.map(o => (
                <div key={o.id} className="card p-4">
                  <div className="flex items-start justify-between">
                    <div>
                      <p className="font-semibold">{o.buyer_name || "Buyer"}</p>
                      <p className="text-sm text-charcoal-lighter">
                        {formatPrice(o.offered_price_paise)} for {formatWeight(o.offered_quantity_grams)}
                      </p>
                      {o.message && <p className="text-sm text-charcoal-lighter mt-1">{o.message}</p>}
                    </div>
                    <div className="flex items-center gap-2">
                      <span className={`badge-${o.status === "accepted" ? "success" : o.status === "rejected" ? "error" : "pending"}`}>
                        {humanise(o.status)}
                      </span>
                      {isOwner && o.status === "submitted" && (
                        <button onClick={() => acceptOffer(o.id)} className="btn-primary btn-sm">Accept</button>
                      )}
                    </div>
                  </div>
                </div>
              ))}
              {offers.length === 0 && <p className="text-charcoal-lighter">No offers yet.</p>}
            </div>
          )}

          {tab === "quotes" && (
            <div className="animate-fade-in space-y-4">
              {quotes.map(q => (
                <div key={q.id} className="card p-6">
                  <div className="flex items-center justify-between mb-4">
                    <h4 className="font-bold">Recovery Quote — v{q.current_version}</h4>
                    <span className={`badge-${q.status.includes("approved") ? "success" : q.status === "issued" ? "pending" : "neutral"}`}>
                      {humanise(q.status)}
                    </span>
                  </div>
                  <p className="text-sm text-charcoal-lighter mb-4">Model: {humanise(q.commercial_model)}</p>
                  {q.versions.filter(v => v.version_number === q.current_version).map(v => (
                    <div key={v.id} className="space-y-3">
                      <InfoRow label="Incoming Weight (est.)" value={formatWeight(v.estimated_incoming_weight_grams)} />
                      <InfoRow label="Expected Output" value={`${formatWeight(v.expected_output_min_grams)} — ${formatWeight(v.expected_output_max_grams)}`} />
                      <div className="border-t border-gray-100 pt-3 space-y-2">
                        <h5 className="text-sm font-semibold">Itemised Costs</h5>
                        <CostRow label="Transport" paise={v.transport_cost_paise} />
                        <CostRow label="Assessment" paise={v.assessment_cost_paise} />
                        <CostRow label="Processing" paise={v.processing_cost_paise} />
                        <CostRow label="Packaging" paise={v.packaging_cost_paise} />
                        <CostRow label="Residue Handling" paise={v.residue_handling_cost_paise} />
                        <CostRow label="Platform Fee" paise={v.platform_fee_paise} />
                        <CostRow label="Tax" paise={v.tax_paise} />
                        <div className="border-t border-gray-200 pt-2 font-bold flex justify-between">
                          <span>Estimated Seller Proceeds</span>
                          <span className="text-primary-700">{formatINR(v.estimated_seller_proceeds_paise)}</span>
                        </div>
                      </div>
                      {v.assumptions && (
                        <div className="bg-pending-50 p-3 rounded-lg text-xs text-pending-600">
                          <strong>Assumptions:</strong> {v.assumptions}
                        </div>
                      )}
                      {v.is_estimate && (
                        <p className="text-xs text-charcoal-lighter italic">⚠️ This is an estimate, not a fixed commercial commitment.</p>
                      )}
                    </div>
                  ))}
                  {isOwner && q.status === "issued" && (
                    <button onClick={() => approveQuote(q.id, q.current_version)}
                      className="btn-primary mt-4">Approve Quote v{q.current_version}</button>
                  )}
                </div>
              ))}
              {quotes.length === 0 && <p className="text-charcoal-lighter">No quotes available.</p>}
            </div>
          )}
        </div>

        {/* Sidebar */}
        <div className="space-y-4">
          {/* Price card */}
          <div className="card p-6">
            <p className="text-2xl font-bold text-primary-700 mb-1">
              {formatPrice(listing.asking_price_paise, listing.price_unit)}
            </p>
            <p className="text-sm text-charcoal-lighter mb-4">{formatWeight(listing.quantity_grams)} available</p>

            {user && !isOwner && (
              <div className="space-y-3">
                <button onClick={() => setShowOffer(true)} className="btn-primary w-full">Make an Offer</button>
                <button onClick={requestRecovery} className="btn-secondary w-full">Request Managed Recovery</button>
              </div>
            )}
            {!user && (
              <Link to="/login" className="btn-primary w-full block text-center">Sign in to make an offer</Link>
            )}
          </div>

          {/* Seller info */}
          <div className="card p-6">
            <h4 className="text-sm font-semibold text-charcoal mb-3">Seller</h4>
            <p className="font-medium">{listing.org_name || "Unknown"}</p>
            <p className="text-sm text-charcoal-lighter">📍 {listing.city}, {listing.state}</p>
            {listing.is_demo && <p className="text-[10px] text-pending-500 mt-2">DEMO ACCOUNT</p>}
          </div>

          {/* Quick info */}
          <div className="card p-6 space-y-3">
            <h4 className="text-sm font-semibold text-charcoal">Quick Info</h4>
            <InfoRow label="Category" value={humanise(listing.material_category)} />
            <InfoRow label="Form" value={humanise(listing.physical_form)} />
            <InfoRow label="Rejection" value={humanise(listing.rejection_reason)} />
            <InfoRow label="Route" value={humanise(listing.preferred_route)} />
            <InfoRow label="Listed" value={formatDate(listing.created_at)} />
            {listing.assessment_date && (
              <InfoRow label="Assessed" value={formatDate(listing.assessment_date)} />
            )}
          </div>
        </div>
      </div>

      {/* Offer modal */}
      {showOffer && (
        <div className="fixed inset-0 bg-black/50 z-50 flex items-center justify-center p-4" onClick={() => setShowOffer(false)}>
          <div className="bg-white rounded-2xl p-6 max-w-md w-full" onClick={e => e.stopPropagation()}>
            <h3 className="text-xl font-bold mb-4">Make an Offer</h3>
            <div className="space-y-4">
              <div>
                <label className="input-label">Offer Price (₹ per kg)</label>
                <input type="number" className="input-field" placeholder="e.g. 25" value={offerPrice}
                  onChange={e => setOfferPrice(e.target.value)} step="0.01" />
              </div>
              <div>
                <label className="input-label">Quantity (kg)</label>
                <input type="number" className="input-field" placeholder="e.g. 500" value={offerQty}
                  onChange={e => setOfferQty(e.target.value)} />
              </div>
              <div>
                <label className="input-label">Message (optional)</label>
                <textarea className="input-field" rows={3} placeholder="Terms, delivery preference..."
                  value={offerMsg} onChange={e => setOfferMsg(e.target.value)} />
              </div>
              <div className="flex gap-3">
                <button onClick={submitOffer} className="btn-primary flex-1">Submit Offer</button>
                <button onClick={() => setShowOffer(false)} className="btn-ghost flex-1">Cancel</button>
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}

function InfoRow({ label, value }: { label: string; value: string }) {
  return (
    <div className="flex justify-between text-sm gap-4">
      <span className="text-charcoal-lighter shrink-0">{label}</span>
      <span className="text-charcoal font-medium text-right">{value}</span>
    </div>
  );
}

function CostRow({ label, paise }: { label: string; paise: number }) {
  if (!paise) return null;
  return (
    <div className="flex justify-between text-sm">
      <span className="text-charcoal-lighter">{label}</span>
      <span className="text-charcoal">{formatINR(paise)}</span>
    </div>
  );
}
