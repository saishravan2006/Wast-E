/* ── Recovery Jobs list ── */
import { useState, useEffect } from "react";
import { Link } from "react-router-dom";
import api from "../api";
import type { RecoveryJob } from "../types";
import { RECOVERY_STATUSES } from "../types";
import { formatWeight, formatDate } from "../utils";

export default function RecoveryJobs() {
  const [jobs, setJobs] = useState<RecoveryJob[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    api.get("/recovery").then(r => setJobs(r.data)).catch(() => {}).finally(() => setLoading(false));
  }, []);

  return (
    <div className="page-container animate-fade-in">
      <h1 className="section-title mb-6">Recovery Jobs</h1>
      {loading ? <p className="text-charcoal-lighter">Loading...</p> :
       jobs.length === 0 ? (
        <div className="card p-12 text-center text-charcoal-lighter">
          <p className="text-2xl mb-2">🔧</p>
          <p>No recovery jobs.</p>
        </div>
      ) : (
        <div className="space-y-4">
          {jobs.map(j => {
            const s = RECOVERY_STATUSES[j.status] || { label: j.status, color: "neutral" };
            return (
              <Link to={`/recovery/${j.id}`} key={j.id} className="card p-5 hover:border-primary-300 block">
                <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3">
                  <div>
                    <p className="font-mono font-bold text-charcoal">{j.batch_code || j.id.slice(0, 12)}</p>
                    <div className="flex flex-wrap gap-4 text-sm text-charcoal-lighter mt-1">
                      {j.incoming_weight_grams && <span>In: {formatWeight(j.incoming_weight_grams)}</span>}
                      {j.processed_output_grams && <span>Out: {formatWeight(j.processed_output_grams)}</span>}
                      {j.residue_grams && <span>Residue: {formatWeight(j.residue_grams)}</span>}
                    </div>
                  </div>
                  <div className="flex items-center gap-3">
                    <span className={`badge-${s.color}`}>{s.label}</span>
                    <span className="text-xs text-charcoal-lighter">{formatDate(j.created_at)}</span>
                  </div>
                </div>
                {j.is_demo && <span className="text-[10px] text-pending-500 mt-1 block">DEMO DATA</span>}
              </Link>
            );
          })}
        </div>
      )}
    </div>
  );
}
