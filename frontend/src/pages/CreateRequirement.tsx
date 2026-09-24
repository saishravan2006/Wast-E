/* ── Create Buyer Requirement ── */
import { useState } from "react";
import { useNavigate } from "react-router-dom";
import api from "../api";
import { MATERIAL_CATEGORIES, PHYSICAL_FORMS } from "../types";

export default function CreateRequirement() {
  const navigate = useNavigate();
  const [saving, setSaving] = useState(false);
  const [form, setForm] = useState({
    title: "", material_category: "plastics", material_grade: "",
    acceptable_forms: [] as string[], required_quantity_kg: "",
    delivery_city: "", delivery_state: "", delivery_pincode: "",
    target_price_min: "", target_price_max: "",
    max_moisture_pct: "", max_contamination_pct: "",
    sampling_method: "", acceptance_method: "", description: "",
  });
  const set = (k: string, v: any) => setForm({ ...form, [k]: v });

  const toggleForm = (val: string) => {
    const forms = form.acceptable_forms.includes(val)
      ? form.acceptable_forms.filter(f => f !== val) : [...form.acceptable_forms, val];
    set("acceptable_forms", forms);
  };

  const submit = async () => {
    setSaving(true);
    try {
      const quality_specs: Record<string, any> = {};
      if (form.max_moisture_pct) quality_specs.max_moisture_pct = parseFloat(form.max_moisture_pct);
      if (form.max_contamination_pct) quality_specs.max_contamination_pct = parseFloat(form.max_contamination_pct);

      await api.post("/requirements", {
        ...form,
        required_quantity_grams: Math.round(parseFloat(form.required_quantity_kg) * 1000),
        target_price_min_paise: form.target_price_min ? Math.round(parseFloat(form.target_price_min) * 100) : null,
        target_price_max_paise: form.target_price_max ? Math.round(parseFloat(form.target_price_max) * 100) : null,
        quality_specs: Object.keys(quality_specs).length > 0 ? quality_specs : null,
        acceptable_forms: form.acceptable_forms.length > 0 ? form.acceptable_forms : null,
      });
      navigate("/requirements");
    } catch (e: any) {
      alert(e.response?.data?.detail || "Failed");
    } finally { setSaving(false); }
  };

  return (
    <div className="page-container max-w-2xl mx-auto animate-fade-in">
      <h1 className="section-title mb-6">Post a Material Requirement</h1>
      <div className="card p-6 sm:p-8 space-y-5">
        <div>
          <label className="input-label">Title *</label>
          <input className="input-field" placeholder='e.g. "Clean HDPE for pelletising"'
            value={form.title} onChange={e => set("title", e.target.value)} />
        </div>
        <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
          <div>
            <label className="input-label">Material Category *</label>
            <select className="input-field" value={form.material_category} onChange={e => set("material_category", e.target.value)}>
              {MATERIAL_CATEGORIES.map(c => <option key={c.value} value={c.value}>{c.label}</option>)}
            </select>
          </div>
          <div>
            <label className="input-label">Grade</label>
            <input className="input-field" placeholder="e.g. HDPE" value={form.material_grade} onChange={e => set("material_grade", e.target.value)} />
          </div>
        </div>
        <div>
          <label className="input-label">Acceptable Physical Forms</label>
          <div className="flex flex-wrap gap-2 mt-1">
            {PHYSICAL_FORMS.map(f => (
              <button key={f.value} type="button" onClick={() => toggleForm(f.value)}
                className={`px-3 py-1.5 rounded-lg text-sm border transition-colors ${
                  form.acceptable_forms.includes(f.value)
                    ? "bg-primary-100 border-primary-300 text-primary-700"
                    : "bg-white border-gray-200 text-charcoal-lighter hover:border-primary-200"
                }`}>{f.label}</button>
            ))}
          </div>
        </div>
        <div className="grid grid-cols-1 sm:grid-cols-3 gap-4">
          <div>
            <label className="input-label">Required Quantity (kg) *</label>
            <input type="number" className="input-field" value={form.required_quantity_kg} onChange={e => set("required_quantity_kg", e.target.value)} />
          </div>
          <div>
            <label className="input-label">Min Price (₹/kg)</label>
            <input type="number" className="input-field" value={form.target_price_min} onChange={e => set("target_price_min", e.target.value)} step="0.01" />
          </div>
          <div>
            <label className="input-label">Max Price (₹/kg)</label>
            <input type="number" className="input-field" value={form.target_price_max} onChange={e => set("target_price_max", e.target.value)} step="0.01" />
          </div>
        </div>
        <div className="grid grid-cols-1 sm:grid-cols-3 gap-4">
          <div>
            <label className="input-label">Delivery City *</label>
            <input className="input-field" value={form.delivery_city} onChange={e => set("delivery_city", e.target.value)} />
          </div>
          <div>
            <label className="input-label">Delivery State *</label>
            <input className="input-field" value={form.delivery_state} onChange={e => set("delivery_state", e.target.value)} />
          </div>
          <div>
            <label className="input-label">Pincode</label>
            <input className="input-field" value={form.delivery_pincode} onChange={e => set("delivery_pincode", e.target.value)} maxLength={6} />
          </div>
        </div>
        <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
          <div>
            <label className="input-label">Max Moisture (%)</label>
            <input type="number" className="input-field" value={form.max_moisture_pct} onChange={e => set("max_moisture_pct", e.target.value)} step="0.1" />
          </div>
          <div>
            <label className="input-label">Max Contamination (%)</label>
            <input type="number" className="input-field" value={form.max_contamination_pct} onChange={e => set("max_contamination_pct", e.target.value)} step="0.1" />
          </div>
        </div>
        <div>
          <label className="input-label">Description</label>
          <textarea className="input-field" rows={3} value={form.description} onChange={e => set("description", e.target.value)} />
        </div>
        <button onClick={submit} disabled={saving} className="btn-primary w-full">{saving ? "Posting..." : "Post Requirement"}</button>
      </div>
    </div>
  );
}
