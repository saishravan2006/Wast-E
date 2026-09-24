/* ── Requirements page & Create Requirement ── */
import { useState, useEffect } from "react";
import { Link } from "react-router-dom";
import api from "../api";
import { useAuth } from "../auth";
import type { BuyerRequirement } from "../types";
import { humanise, categoryIcon } from "../types";
import { formatPrice, formatWeight, formatDate } from "../utils";

export default function Requirements() {
  const { user } = useAuth();
  const [reqs, setReqs] = useState<BuyerRequirement[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    api.get("/requirements?page_size=50").then(r => setReqs(r.data.items || [])).catch(() => {}).finally(() => setLoading(false));
  }, []);

  return (
    <div className="page-container animate-fade-in">
      <div className="flex items-center justify-between mb-6">
        <div>
          <h1 className="section-title">Buyer Requirements</h1>
          <p className="section-subtitle">Buyers looking for specific materials</p>
        </div>
        {user?.is_buyer && (
          <Link to="/create-requirement" className="btn-primary !py-2 text-sm">Post Requirement</Link>
        )}
      </div>
      {loading ? <p className="text-charcoal-lighter">Loading...</p> :
       reqs.length === 0 ? <p className="text-charcoal-lighter">No requirements posted yet.</p> : (
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-6">
          {reqs.map(r => (
            <Link to={`/requirements/${r.id}`} key={r.id} className="card p-5 hover:border-primary-300 animate-slide-up">
              <div className="flex items-center gap-2 mb-2">
                <span className="badge-active text-xs">{categoryIcon(r.material_category)} {humanise(r.material_category)}</span>
              </div>
              <h3 className="font-bold text-charcoal mb-2">{r.title}</h3>
              <div className="space-y-1 text-sm text-charcoal-lighter">
                <p>{r.material_grade || "Any grade"}</p>
                <p>Need: {formatWeight(r.required_quantity_grams)}</p>
                <p>📍 {r.delivery_city}, {r.delivery_state}</p>
                {r.target_price_min_paise && r.target_price_max_paise && (
                  <p className="text-primary-700 font-medium">
                    {formatPrice(r.target_price_min_paise)} — {formatPrice(r.target_price_max_paise)}
                  </p>
                )}
                {r.required_by && <p className="text-xs">Needed by: {formatDate(r.required_by)}</p>}
              </div>
              <p className="text-xs text-charcoal-lighter mt-3">{r.org_name}</p>
            </Link>
          ))}
        </div>
      )}
    </div>
  );
}
