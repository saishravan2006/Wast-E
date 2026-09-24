/* ── Create Listing — 4-step mobile-friendly form ── */
import { useState } from "react";
import { useNavigate } from "react-router-dom";
import api from "../api";
import { MATERIAL_CATEGORIES, PHYSICAL_FORMS, REJECTION_REASONS } from "../types";

const STEPS = ["Material Details", "Rejection Details", "Location & Price", "Review & Submit"];

export default function CreateListing() {
  const navigate = useNavigate();
  const [step, setStep] = useState(0);
  const [saving, setSaving] = useState(false);
  const [form, setForm] = useState({
    title: "", material_category: "plastics", material_grade: "", grade_unknown: false,
    quantity_kg: "", quantity_unit: "kg", physical_form: "loose", description: "",
    rejection_reason: "mixed_materials", rejection_details: "", material_source: "",
    known_contents: "", has_hazardous_contamination: false,
    city: "", state: "", pincode: "", pickup_address: "",
    price_per_kg: "", request_quote: false, loading_arrangements: "",
    pickup_availability: "", ownership_confirmed: false, preferred_route: "help_me_decide",
  });

  const set = (k: string, v: any) => setForm({ ...form, [k]: v });

  const submit = async (status: string) => {
    setSaving(true);
    try {
      const data = {
        ...form,
        quantity_grams: Math.round(parseFloat(form.quantity_kg || "0") * 1000),
        asking_price_paise: form.request_quote ? null : Math.round(parseFloat(form.price_per_kg || "0") * 100),
        status,
      };
      const r = await api.post("/listings", data);
      if (status === "pending_review") await api.post(`/listings/${r.data.id}/submit`);
      navigate("/dashboard");
    } catch (e: any) {
      alert(e.response?.data?.detail || "Failed to create listing");
    } finally {
      setSaving(false);
    }
  };

  return (
    <div className="page-container max-w-3xl mx-auto animate-fade-in">
      <h1 className="section-title mb-2">List a Rejected Batch</h1>
      <p className="section-subtitle">Describe your material so buyers can find it</p>

      {/* Stepper */}
      <div className="flex items-center gap-2 mb-8 overflow-x-auto pb-2">
        {STEPS.map((s, i) => (
          <div key={i} className="flex items-center gap-2 shrink-0">
            <button onClick={() => setStep(i)}
              className={`w-8 h-8 rounded-full text-sm font-bold flex items-center justify-center transition-colors ${
                i === step ? "bg-primary-700 text-white" :
                i < step ? "bg-primary-200 text-primary-700" : "bg-gray-200 text-gray-400"
              }`}>{i + 1}</button>
            <span className={`text-sm font-medium ${i === step ? "text-charcoal" : "text-charcoal-lighter"}`}>{s}</span>
            {i < STEPS.length - 1 && <div className="w-8 h-0.5 bg-gray-200" />}
          </div>
        ))}
      </div>

      <div className="card p-6 sm:p-8">
        {/* Step 1: Material */}
        {step === 0 && (
          <div className="space-y-5 animate-fade-in">
            <div>
              <label className="input-label">Title *</label>
              <input className="input-field" placeholder='e.g. "Mixed HDPE bags — rejected for contamination"'
                value={form.title} onChange={e => set("title", e.target.value)} />
            </div>
            <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
              <div>
                <label className="input-label">Material Category *</label>
                <select className="input-field" value={form.material_category}
                  onChange={e => set("material_category", e.target.value)}>
                  {MATERIAL_CATEGORIES.map(c => <option key={c.value} value={c.value}>{c.label}</option>)}
                </select>
              </div>
              <div>
                <label className="input-label">Grade / Polymer</label>
                <input className="input-field" placeholder="e.g. HDPE, PET clear" disabled={form.grade_unknown}
                  value={form.material_grade} onChange={e => set("material_grade", e.target.value)} />
                <label className="flex items-center gap-2 mt-2 text-sm text-charcoal-lighter cursor-pointer">
                  <input type="checkbox" checked={form.grade_unknown}
                    onChange={e => set("grade_unknown", e.target.checked)} className="w-4 h-4 rounded" />
                  I don't know the grade
                </label>
              </div>
            </div>
            <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
              <div>
                <label className="input-label">Quantity (kg) *</label>
                <input type="number" className="input-field" placeholder="e.g. 2500"
                  value={form.quantity_kg} onChange={e => set("quantity_kg", e.target.value)} />
              </div>
              <div>
                <label className="input-label">Physical Form *</label>
                <select className="input-field" value={form.physical_form}
                  onChange={e => set("physical_form", e.target.value)}>
                  {PHYSICAL_FORMS.map(f => <option key={f.value} value={f.value}>{f.label}</option>)}
                </select>
              </div>
            </div>
            <div>
              <label className="input-label">Description</label>
              <textarea className="input-field" rows={3} placeholder="Any additional details about the material..."
                value={form.description} onChange={e => set("description", e.target.value)} />
            </div>
          </div>
        )}

        {/* Step 2: Rejection */}
        {step === 1 && (
          <div className="space-y-5 animate-fade-in">
            <div>
              <label className="input-label">Why was this batch rejected? *</label>
              <select className="input-field" value={form.rejection_reason}
                onChange={e => set("rejection_reason", e.target.value)}>
                {REJECTION_REASONS.map(r => <option key={r.value} value={r.value}>{r.label}</option>)}
              </select>
            </div>
            <div>
              <label className="input-label">What did the buyer report?</label>
              <textarea className="input-field" rows={4} placeholder="Describe what the buyer found..."
                value={form.rejection_details} onChange={e => set("rejection_details", e.target.value)} />
            </div>
            <div>
              <label className="input-label">Material Source</label>
              <input className="input-field" placeholder="e.g. Municipal collection, factory floor waste"
                value={form.material_source} onChange={e => set("material_source", e.target.value)} />
            </div>
            <label className="flex items-center gap-3 p-4 bg-red-50 rounded-xl cursor-pointer">
              <input type="checkbox" checked={form.has_hazardous_contamination}
                onChange={e => set("has_hazardous_contamination", e.target.checked)} className="w-5 h-5 rounded" />
              <div>
                <p className="font-semibold text-red-700 text-sm">Known hazardous contamination</p>
                <p className="text-xs text-red-600">Check this if the material contains or may contain hazardous substances</p>
              </div>
            </label>
          </div>
        )}

        {/* Step 3: Location & Commercial */}
        {step === 2 && (
          <div className="space-y-5 animate-fade-in">
            <div className="grid grid-cols-1 sm:grid-cols-3 gap-4">
              <div>
                <label className="input-label">City *</label>
                <input className="input-field" placeholder="e.g. Chennai" value={form.city}
                  onChange={e => set("city", e.target.value)} />
              </div>
              <div>
                <label className="input-label">State *</label>
                <input className="input-field" placeholder="e.g. Tamil Nadu" value={form.state}
                  onChange={e => set("state", e.target.value)} />
              </div>
              <div>
                <label className="input-label">Pincode *</label>
                <input className="input-field" placeholder="e.g. 600032" value={form.pincode}
                  onChange={e => set("pincode", e.target.value)} maxLength={6} />
              </div>
            </div>
            <div>
              <label className="input-label">Pickup Address (private — not shown publicly)</label>
              <textarea className="input-field" rows={2} value={form.pickup_address}
                onChange={e => set("pickup_address", e.target.value)} />
            </div>
            <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
              <div>
                <label className="input-label">Asking Price (₹ per kg)</label>
                <input type="number" className="input-field" placeholder="e.g. 12" disabled={form.request_quote}
                  value={form.price_per_kg} onChange={e => set("price_per_kg", e.target.value)} step="0.01" />
                <label className="flex items-center gap-2 mt-2 text-sm text-charcoal-lighter cursor-pointer">
                  <input type="checkbox" checked={form.request_quote}
                    onChange={e => set("request_quote", e.target.checked)} className="w-4 h-4 rounded" />
                  Request assessment / quote instead
                </label>
              </div>
              <div>
                <label className="input-label">Preferred Route *</label>
                <select className="input-field" value={form.preferred_route}
                  onChange={e => set("preferred_route", e.target.value)}>
                  <option value="direct_sale">Direct sale</option>
                  <option value="managed_recovery">Managed recovery</option>
                  <option value="help_me_decide">Help me decide</option>
                </select>
              </div>
            </div>
            <div>
              <label className="input-label">Loading Arrangements</label>
              <input className="input-field" placeholder="e.g. Forklift available, ground floor"
                value={form.loading_arrangements} onChange={e => set("loading_arrangements", e.target.value)} />
            </div>
            <label className="flex items-center gap-3 p-4 bg-primary-50 rounded-xl cursor-pointer">
              <input type="checkbox" checked={form.ownership_confirmed}
                onChange={e => set("ownership_confirmed", e.target.checked)} className="w-5 h-5 rounded" />
              <div>
                <p className="font-semibold text-primary-700 text-sm">I confirm ownership of this material</p>
              </div>
            </label>
          </div>
        )}

        {/* Step 4: Review */}
        {step === 3 && (
          <div className="space-y-4 animate-fade-in">
            <h3 className="font-bold text-lg">Review Your Listing</h3>
            <div className="bg-warm-50 rounded-xl p-4 space-y-2 text-sm">
              <Row label="Title" value={form.title} />
              <Row label="Category" value={form.material_category} />
              <Row label="Grade" value={form.grade_unknown ? "Unknown" : form.material_grade || "—"} />
              <Row label="Quantity" value={`${form.quantity_kg} kg`} />
              <Row label="Form" value={form.physical_form} />
              <Row label="Rejection" value={form.rejection_reason.replace(/_/g, " ")} />
              <Row label="Location" value={`${form.city}, ${form.state} ${form.pincode}`} />
              <Row label="Price" value={form.request_quote ? "Request quote" : `₹${form.price_per_kg}/kg`} />
              <Row label="Route" value={form.preferred_route.replace(/_/g, " ")} />
              <Row label="Hazardous" value={form.has_hazardous_contamination ? "⚠️ Yes" : "No"} />
              <Row label="Ownership" value={form.ownership_confirmed ? "✓ Confirmed" : "Not confirmed"} />
            </div>
          </div>
        )}

        {/* Navigation */}
        <div className="flex justify-between mt-8 pt-6 border-t border-gray-100">
          <button onClick={() => setStep(Math.max(0, step - 1))} disabled={step === 0}
            className="btn-ghost !py-2">← Previous</button>
          <div className="flex gap-3">
            {step === 3 && (
              <>
                <button onClick={() => submit("draft")} disabled={saving} className="btn-secondary !py-2">
                  {saving ? "Saving..." : "Save Draft"}
                </button>
                <button onClick={() => submit("pending_review")} disabled={saving || !form.ownership_confirmed}
                  className="btn-primary !py-2">
                  {saving ? "Submitting..." : "Submit for Review"}
                </button>
              </>
            )}
            {step < 3 && (
              <button onClick={() => setStep(step + 1)} className="btn-primary !py-2">Next →</button>
            )}
          </div>
        </div>
      </div>
    </div>
  );
}

function Row({ label, value }: { label: string; value: string }) {
  return (
    <div className="flex justify-between gap-4">
      <span className="text-charcoal-lighter">{label}</span>
      <span className="text-charcoal font-medium text-right">{value}</span>
    </div>
  );
}
